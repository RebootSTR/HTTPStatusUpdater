# @rebootstr
import logging
from random import Random

from telegram import Update, Bot, Message
from telegram.error import Unauthorized
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher, MessageHandler, Filters

from client import StateManager
from client.PropertiesManager import PropertiesManager
from client.Repository import Repository
from client.entity.User import User
from client.keyboard import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# метод для старта бота
def run():
    global bot
    updater = Updater(token=_token)
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


# метод обработки команды start
def commandStartHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("method: %s, userid: %d", "commandStartHandler", userId)

    TEXT: str
    if userId in _subscribedUsers:
        TEXT = YOU_ALREADY_SUBSCRIBED
    else:
        TEXT = HELLO_MESSAGE
        trySaveUserId(userId)
    trySendMessage(chat_id=userId,
                   text=TEXT)


# метод обработки комманды admin
def commandAdminHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("method: %s, userid: %d", "commandAdminHandler", userId)

    code = generateAdminCode(update.effective_user.username)
    _repository.setUserState(userId, StateManager.adminCode(code))


# метод обработки сообщений
def messageHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("messageHandler, userid: %d", userId)

    trySaveUserId(userId)
    if isUserAdmin(update.effective_user.id):
        adminTextHandler(update, context)
    else:
        userTextHandler(update, context)


# метод обработки ответов на сообщения
def replyHandler(update: Update, context: CallbackContext):
    if isUserAdmin(update.effective_user.id):
        adminReplyHandler(update, context)
    else:
        userTextHandler(update, context)


# метод обработки сообщений администратора
def adminTextHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("unknown text, userid: %d", userId)
    message = update.effective_message.text
    userState = _repository.getUserState(userId)

    if StateManager.NORMAL_BIG_SENDING in userState:  # проверка на состояние нормальной рассылки
        onNormalModeState(userId, message)
    elif StateManager.SILENT_BIG_SENDING in userState:  # проверка на состояние тихой рассылки
        onSilentModeState(userId, message)
    elif message == SUBSCRIBERS:  # кнопка подписчиков
        onSubscribersClicked(update)
    elif message == NORMAL_MODE_BUTTON:  # кнопка нормальной рассылки
        onNormalMessageClicked(update)
    elif message == SILENT_MODE_BUTTON:  # кнопка тихой рассылки
        onSilentMessageClicked(update)
    else:
        userTextHandler(update, context)


# метод обработки сообщений для админа, который хочет отправить обычную рассылку
def onNormalModeState(userId: int, message: str):
    if message == CANCEL:
        onCancelMessageMode(userId)
    else:
        send_status(message, silent=0)
        _repository.setUserState(userId, StateManager.baseState())
        trySendMessage(chat_id=userId,
                       text=BIG_SENDING_COMPLETE)


# метод обработки сообщений для админа, который хочет отправить тихую рассылку
def onSilentModeState(userId: int, message: str):
    if message == CANCEL:
        onCancelMessageMode(userId)
    else:
        send_status(message, silent=1)
        _repository.setUserState(userId, StateManager.baseState())
        trySendMessage(chat_id=userId,
                       text=BIG_SENDING_COMPLETE)


# метод обработки нажатия на кнопку отмены
def onCancelMessageMode(userId: int):
    _repository.setUserState(userId, StateManager.baseState())
    trySendMessage(chat_id=userId,
                   text=CANCELED)


# метод обработки нажатия на кнопку обычной рассылки
def onNormalMessageClicked(update: Update):
    userId = update.effective_user.id
    _repository.setUserState(userId, StateManager.normalBigSending())
    trySendMessage(chat_id=userId,
                   text=NORMAL_MODE_MESSAGE,
                   reply_markup=getCancelKeyboard())


# метод обработки нажатия на кнопку тихой рассылки
def onSilentMessageClicked(update: Update):
    userId = update.effective_user.id
    _repository.setUserState(userId, StateManager.silentBigSending())
    trySendMessage(chat_id=userId,
                   text=SILENT_MODE_MESSAGE,
                   reply_markup=getCancelKeyboard())


# метод обработки нажатия на кнопку статистики подписчиков
def onSubscribersClicked(update: Update):
    trySendMessage(chat_id=update.effective_chat.id,
                   text=f"{len(_subscribedUsers)}:{str(_subscribedUsers)}")


# метод обработки сообщений обычных пользователей
def userTextHandler(update: Update, context: CallbackContext):
    userId = update.effective_chat.id
    logging.info("unknown text, userid: %d", userId)
    userState = _repository.getUserState(userId)

    if StateManager.ADMIN_CODE in userState:  # проверка, есть ли сохраненный админкод у пользователя
        adminCode = StateManager.getParams(userState)[StateManager.CODE]
        isSuccess = onHasAdminCode(userId, adminCode, update.effective_message.text)
        if not isSuccess:
            userTextHandler(update, context)  # повторная обработка сообщения
    else:
        onUnhandledMessage(userId, update)


# метод обработки ответов администратора
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


# метод обработки соятояния пользователя, который хочет получить права админа
def onHasAdminCode(userId: int, adminCode: str, message: str):
    if message == adminCode:  # админкод введен вверно
        setAdmin(userId)
        trySendMessage(chat_id=userId,
                       text=YOU_ADMIN)
        return True
    else:  # админкод введен НЕ вверно
        _repository.setUserState(userId, StateManager.baseState())  # очистка админкода
        return False


# утилитарный метод для сохранения ID администратора
def setAdmin(userId: int):
    global _adminId
    _adminId = userId
    _propertyManager.addOrEdit(ADMIN_ID_PROPERTY, str(userId))


# метод обработки сообщения, в случае если оно не подходит ни под одно условие
def onUnhandledMessage(userId: int, update: Update):
    trySendMessage(chat_id=userId,
                   text=MESSAGE_SENT,
                   reply_to_message_id=update.effective_message.message_id)
    if not isUserAdmin(userId):
        trySendMessage(chat_id=_adminId,
                       text=putDataForReply(update),
                       silent=True)


# метод генерации кода администратора
def generateAdminCode(username: str) -> int:
    code = Random().randint(1000000000, 9999999999)
    logging.error("ADMIN_CODE FOR USER %s: %d", username, code)
    return code


# обработчик ошибок сети (не нужен)
def errorHandler():
    pass


# метод, который помещает в сообщение данные об его отправителе, чтобы администратор мог на него ответить
def putDataForReply(update: Update):
    mesId = update.effective_message.message_id
    userId = update.effective_chat.id
    username = update.effective_user.name
    return f"{userId}|{mesId}|\n{username}:\n\n{update.effective_message.text}"


# утилитарный метод отоправки сообщения с обработкой ошибок
def trySendMessage(chat_id, text, reply_markup=None, silent=0, reply_to_message_id=None) -> Message or None:
    if reply_markup is None:
        reply_markup = getKeyboard(isUserAdmin(chat_id))

    if chat_id is None:
        logging.info("method: %s, chat_id is none", "trySendMessage")
        return

    try:
        logging.info("method: %s, userid: %d", "trySendMessage", chat_id)
        return bot.sendMessage(chat_id=chat_id,
                               text=text,
                               reply_markup=reply_markup,
                               disable_notification=(silent == 1),
                               reply_to_message_id=reply_to_message_id)
    except Unauthorized as e:
        logging.info("unsubscribed user, userid: %d", chat_id)
        removeUser(chat_id)
    except Exception as e:
        logging.error(e)


# утилитарный метод выгружающий пользователей из бд в оперативную память
def fillSubscribers():
    for user in _repository.getAllUsers():
        _subscribedUsers.append(user.userId)


# метод сохранения пользователя в бд (регистрация); если пользователь уже там, то ничего не делает
def trySaveUserId(userId: int):
    if userId in _subscribedUsers:
        return
    logging.info("save user, userid: %d", userId)
    _subscribedUsers.append(userId)
    _repository.addUser(User(userId, StateManager.baseState()))


# метод удаления пользователя из бд (отписка)
def removeUser(userId: int):
    logging.info("remove user, userid: %d", userId)

    _subscribedUsers.remove(userId)
    _repository.removeUser(userId)


# утилитарный метод рассылки сообщения всем пользователям
def send_status(status: str, silent=0):
    for user in _subscribedUsers:
        logging.info("method: %s, userid: %d", "send_status", user)
        trySendMessage(chat_id=user,
                       text=status,
                       silent=silent)


# утилитарный метод проверки, является ли пользователь администратором
def isUserAdmin(userId: int):
    return userId == _adminId


ADMIN_ID_PROPERTY = "admin_id"
TELEGRAM_TOKEN_PROPERTY = "tg_token"
DATABASE_NAME = "status_updater_base.sqlite3"

bot: Bot
_repository = Repository(DATABASE_NAME)
_propertyManager = PropertiesManager(_repository)
_adminId = None

_subscribedUsers = []
_token = ""


def main():
    global _adminId, _token

    _token = _propertyManager.getOrInput(TELEGRAM_TOKEN_PROPERTY)
    adminIdProperty = _propertyManager.get(ADMIN_ID_PROPERTY)
    _adminId = None if adminIdProperty is None else int(adminIdProperty)

    fillSubscribers()



    run()
