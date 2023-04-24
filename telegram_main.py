# @rebootstr
import logging
import time

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Bot, ReplyKeyboardRemove
from telegram.error import Unauthorized
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher, MessageHandler, Filters

import DataBase
import psutiNetUpdater
from PropertiesManager import PropertiesManager
from Repository import Repository
from DataBase import DataBase

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def run():
    global bot
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    dispatcher: Dispatcher
    bot = updater.bot

    handlers = [
        # admin
        CommandHandler("subscribers", _subscribers, filters=ADMIN_FILTER),
        MessageHandler(Filters.reply & ADMIN_FILTER, _adminReply),
        MessageHandler(Filters.text & ADMIN_FILTER, _adminText),

        # users
        CommandHandler("start", _start),
        MessageHandler(Filters.text, _text)
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    dispatcher.add_error_handler(ignoreErrorsHAHAHA)

    updater.start_polling()
    updater.idle()


def _subscribers(update: Update, context: CallbackContext):
    context.bot.sendMessage(chat_id=update.effective_chat.id,
                            text=f"{len(subscribedUsers)}:{str(subscribedUsers)}")


MESSAGE_TO_ALL = "all"


def ignoreErrorsHAHAHA():
    pass


def _adminText(update: Update, context: CallbackContext):
    if update.effective_message.text[:3] == MESSAGE_TO_ALL:
        text = update.effective_message.text.split("\n", 1)[1]
        silent = 1
        if update.effective_message.text[3] != "\n":
            silent = 0
        send_status(text, silent=silent)
    else:
        _text(update, context)


def _start(update: Update, context: CallbackContext):
    logging.info("method: %s, userid: %d", "_start", update.effective_chat.id)

    TEXT: str
    if update.effective_chat.id in subscribedUsers:
        TEXT = "Вы уже подписаны на уведомления"
    else:
        TEXT = "Привет, теперь ты будешь получать уведомления о смерти и восстановлении ПгутиНета во 2 общажитии"
        trySaveUserId(update.effective_chat.id)
    context.bot.sendMessage(chat_id=update.effective_chat.id,
                            text=TEXT,
                            reply_markup=NOTIFY_KEYBOARD)


def putDataForReply(update: Update):
    mesId = update.effective_message.message_id
    userId = update.effective_chat.id
    username = update.effective_user.name
    return f"{userId}|{mesId}|\n{username}:\n\n{update.effective_message.text}"


def _text(update: Update, context: CallbackContext):
    if update.effective_message.text == NOTIFY:
        logging.info("subscribed to notify, userid: %d", update.effective_chat.id)
        TEXT = 'Вы получите уведомление о ближайшем получении "живого" сигнала ПгутиНета'
        context.bot.sendMessage(chat_id=update.effective_chat.id,
                                text=TEXT,
                                reply_markup=EMPTY_KEYBOARD)
        notifyUsers.append(update.effective_chat.id)
    else:
        logging.info("unknown text, userid: %d", update.effective_chat.id)
        TEXT = "Сообщение принято :)"
        time.sleep(5)
        context.bot.sendMessage(chat_id=update.effective_chat.id,
                                text=TEXT,
                                reply_to_message_id=update.effective_message.message_id)
        if update.effective_chat.id != ADMIN_USER_ID:
            context.bot.sendMessage(chat_id=ADMIN_USER_ID,
                                    text=putDataForReply(update),
                                    disable_notification=True)


def _adminReply(update: Update, context: CallbackContext):
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
        pass


def onAliveReceived():
    for user in notifyUsers:
        logging.info("method: %s, userid: %d", "onAliveReceived", user)
        trySendMessage(chat_id=user,
                       text="Интернет жив",
                       reply_markup=NOTIFY_KEYBOARD)
        notifyUsers.remove(user)


def trySendMessage(chat_id, text, reply_markup=None, silent=0, reply_to_message_id=None):
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


def getDatabase():
    base = DataBase("users.db")
    return base


def removeUser(userId: int):
    logging.info("remove user, userid: %d", userId)

    subscribedUsers.remove(userId)
    _repository.removeUser(userId)


def send_status(status: str, silent=0):
    for user in subscribedUsers:
        logging.info("method: %s, userid: %d", "send_status", user)
        trySendMessage(chat_id=user,
                       text=status,
                       reply_markup=NOTIFY_KEYBOARD,
                       silent=silent)


NOTIFY = "Принудительное уведомлнеие"
NOTIFY_KEYBOARD_BUTTONS = [
    [KeyboardButton(NOTIFY)]
]
NOTIFY_KEYBOARD = ReplyKeyboardMarkup(NOTIFY_KEYBOARD_BUTTONS, resize_keyboard=True)
EMPTY_KEYBOARD = ReplyKeyboardRemove()
ADMIN_USER_ID = 383120920
ADMIN_FILTER = Filters.user(user_id=ADMIN_USER_ID)
bot: Bot

_database = DataBase("users.db")
_repository = Repository(_database)
_propertyManager = PropertiesManager(_repository)

if __name__ == '__main__':
    subscribedUsers = []
    notifyUsers = []

    token = _propertyManager.get("tg_token")
    fillSubscribers()

    psutiNetUpdater.run(send_status, onAliveReceived)

    run()
