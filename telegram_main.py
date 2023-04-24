# @rebootstr
import logging
from random import Random

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Bot, ReplyKeyboardRemove
from telegram.error import Unauthorized
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher, MessageHandler, Filters

import psutiNetUpdater
from PropertiesManager import PropertiesManager
from Repository import Repository
from dictionary import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def run():
    global bot
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    dispatcher: Dispatcher
    bot = updater.bot

    handlers = [
        CommandHandler("start", commandStartHandler),
        CommandHandler("admin", commandAdminHandler),
        MessageHandler(Filters.reply, replyHandler),
        MessageHandler(Filters.text, messageHandler),
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    dispatcher.add_error_handler(errorHandler)

    updater.start_polling()
    updater.idle()


MESSAGE_TO_ALL = "all"


def commandStartHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("method: %s, userid: %d", "commandStartHandler", userId)

    TEXT: str
    if userId in subscribedUsers:
        TEXT = YOU_ALREADY_SUBSCRIBED
    else:
        TEXT = HELLO_MESSAGE
        trySaveUserId(userId)
    context.bot.sendMessage(chat_id=userId,
                            text=TEXT,
                            reply_markup=getKeyboard(isUserAdmin(userId)))


def commandAdminHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("method: %s, userid: %d", "commandAdminHandler", userId)

    generateAdminCode(userId, update.effective_user.username)


def messageHandler(update: Update, context: CallbackContext):
    if isUserAdmin(update.effective_user.id):
        adminTextHandler(update, context)
    else:
        userTextHandler(update, context)


def replyHandler(update: Update, context: CallbackContext):
    if isUserAdmin(update.effective_user.id):
        adminReplyHandler(update, context)
    else:
        userTextHandler(update, context)


def adminTextHandler(update: Update, context: CallbackContext):
    message = update.effective_message.text
    if message[:3] == MESSAGE_TO_ALL:
        text = update.effective_message.text.split("\n", 1)[1]
        silent = 1
        if update.effective_message.text[3] != "\n":
            silent = 0
        send_status(text, silent=silent)
    elif message == SUBSCRIBERS:
        onSubscribersClicked(update)
    elif message == NORMAL_MODE:
        pass  # todo
    elif message == SILENT_MODE:
        pass  # todo
    else:
        userTextHandler(update, context)


def onSubscribersClicked(update: Update):
    trySendMessage(chat_id=update.effective_chat.id,
                   text=f"{len(subscribedUsers)}:{str(subscribedUsers)}")


def userTextHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("unknown text, userid: %d", userId)
    adminCode = _repository.getAdminCode(userId)

    if adminCode is not None:  # проверка, есть ли сохраненный админкод у пользователя
        isSuccess = onHasAdminCode(userId, adminCode, update.effective_message.text)
        if not isSuccess:
            userTextHandler(update, context)  # повторная обработка сообщения
    else:
        onUnhandledMessage(userId, update.effective_message.message_id, update)


def adminReplyHandler(update: Update, context: CallbackContext):
    try:
        text_to_reply = update.effective_message.text
        text = update.effective_message.reply_to_message.text
        userId = text.split("|")[0]
        mesId = text.split("|")[1]
        trySendMessage(chat_id=int(userId),
                       text=text_to_reply,
                       silent=1,
                       reply_to_message_id=mesId)
    except Exception:
        logging.error("reply parsing error")
        trySendMessage(chat_id=_adminId,
                       text=ERROR)


def onHasAdminCode(userId: int, adminCode: str, message: str):
    if message == adminCode:  # админкод введен вверно
        setAdmin(userId)
        trySendMessage(chat_id=userId,
                       text=YOU_ADMIN)
        return True
    else:  # админкод введен НЕ вверно
        _repository.setAdminCode(userId, None)  # очистка админкода
        return False


def onUnhandledMessage(userId: int, messageId: int, update: Update):
    trySendMessage(chat_id=userId,
                   text=MESSAGE_SENT,
                   reply_to_message_id=update.effective_message.message_id)
    if not isUserAdmin(userId):
        trySendMessage(chat_id=_adminId,
                       text=putDataForReply(update),
                       silent=True)


def generateAdminCode(userId: int, username: str):
    code = Random().randint(1000000000, 9999999999)
    _repository.setAdminCode(userId, str(code))
    logging.error("ADMIN_CODE FOR USER %s: %d", username, code)


def errorHandler():
    pass


def putDataForReply(update: Update):
    mesId = update.effective_message.message_id
    userId = update.effective_chat.id
    username = update.effective_user.name
    return f"{userId}|{mesId}|\n{username}:\n\n{update.effective_message.text}"


def onAliveReceived():
    for user in notifyUsers:
        logging.info("method: %s, userid: %d", "onAliveReceived", user)
        trySendMessage(chat_id=user,
                       text=INTERNET_IS_ALIVE_MESSAGE,
                       reply_markup=getKeyboard(isUserAdmin(user)))
        notifyUsers.remove(user)


def trySendMessage(chat_id, text, reply_markup=None, silent=0, reply_to_message_id=None):
    if reply_markup is None:
        reply_markup = getKeyboard(isUserAdmin(chat_id))

    if chat_id is None:
        logging.info("method: %s, chat_id is none", "trySendMessage")
        return

    try:
        logging.info("method: %s, userid: %d", "trySendMessage", chat_id)
        bot.sendMessage(chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        disable_notification=(silent == 1),
                        reply_to_message_id=reply_to_message_id)
    except Unauthorized as e:
        logging.info("unsubscribed user, userid: %d", chat_id)
        removeUser(chat_id)
    except Exception as e:
        logging.error(e)


def fillSubscribers():
    for row in _repository.getAllUsers():
        subscribedUsers.append(row[0])


def trySaveUserId(userId: int):
    if userId in subscribedUsers:
        return
    logging.info("save user, userid: %d", userId)
    subscribedUsers.append(userId)
    _repository.addUser(userId)


def removeUser(userId: int):
    logging.info("remove user, userid: %d", userId)

    subscribedUsers.remove(userId)
    _repository.removeUser(userId)


def send_status(status: str, silent=0):
    for user in subscribedUsers:
        logging.info("method: %s, userid: %d", "send_status", user)
        trySendMessage(chat_id=user,
                       text=status,
                       reply_markup=getKeyboard(isUserAdmin(user)),
                       silent=silent)


def isUserAdmin(userId: int):
    return userId == _adminId


def getKeyboard(isAdmin):
    if isAdmin:
        buttons = [
            [KeyboardButton(NORMAL_MODE), KeyboardButton(SILENT_MODE)],
            [KeyboardButton(SUBSCRIBERS)]
        ]
    else:
        return ReplyKeyboardRemove()

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def setAdmin(userId: int):
    global _adminId
    _adminId = userId
    _propertyManager.addOrEdit(ADMIN_ID_PROPERTY, str(userId))


bot: Bot
ADMIN_ID_PROPERTY = "admin_id"
_repository = Repository("users.db")
_propertyManager = PropertiesManager(_repository)
_adminId = None

if __name__ == '__main__':
    subscribedUsers = []
    notifyUsers = []

    token = _propertyManager.getOrInput("tg_token")
    _adminId = int(_propertyManager.get(ADMIN_ID_PROPERTY))
    fillSubscribers()

    psutiNetUpdater.run(send_status, onAliveReceived)

    run()
