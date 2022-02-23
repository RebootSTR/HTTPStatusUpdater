# @rebootstr
import logging
import time

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Bot
from telegram.error import Unauthorized
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher, MessageHandler, Filters

import properties
import psutiNetUpdater
from properties import DataBase

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def run():
    global bot
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    dispatcher: Dispatcher
    bot = updater.bot

    handlers = [
        CommandHandler("start", _start),
        MessageHandler(Filters.text, _text)
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()


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


def _text(update: Update, context: CallbackContext):
    if update.effective_message.text == NOTIFY:
        logging.info("subscribed to notify, userid: %d", update.effective_chat.id)
        TEXT = 'Вы получите уведомление о ближайшем получении "живого" сигнала ПгутиНета'
        context.bot.sendMessage(chat_id=update.effective_chat.id,
                                text=TEXT)
        notifyUsers.append(update.effective_chat.id)
    else:
        logging.info("unknown text, userid: %d", update.effective_chat.id)
        TEXT = "Чел ты...."
        time.sleep(5)
        context.bot.sendMessage(chat_id=update.effective_chat.id,
                                text=TEXT,
                                reply_to_message_id=update.effective_message.message_id)


def onAliveReceived():
    for user in notifyUsers:
        logging.info("method: {}, userid: {}", "onAliveReceived", user)
        trySendMessage(chat_id=user,
                       text="Интернет жив",
                       reply_markup=NOTIFY_KEYBOARD)
        notifyUsers.remove(user)


def trySendMessage(chat_id, text, reply_markup=None, silent=0):
    try:
        logging.info("method: %s, userid: %d", "trySendMessage", chat_id)
        bot.sendMessage(chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        disable_notification=(silent == 1))
    except Unauthorized as e:
        logging.info("unsubscribed user, userid: %d", chat_id)
        removeUser(chat_id)
    except Exception as e:
        logging.error(e)


def fillSubscribers(database: DataBase):
    for row in database.get_all("ids", "user_id"):
        subscribedUsers.append(row[0])


def trySaveUserId(userId: int):
    if userId in subscribedUsers:
        return
    logging.info("save user, userid: %d", userId)
    subscribedUsers.append(userId)
    getDatabase().append("ids", userId)


def getDatabase():
    base = DataBase("users.db")
    base.create("ids(user_id INTEGER)")
    return base


def removeUser(userId: int):
    logging.info("remove user, userid: %d", userId)

    subscribedUsers.remove(userId)
    getDatabase().remove("ids", "user_id", userId)


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
NOTIFY_KEYBOARD = ReplyKeyboardMarkup(NOTIFY_KEYBOARD_BUTTONS, one_time_keyboard=True, resize_keyboard=True)
bot: Bot

if __name__ == '__main__':
    subscribedUsers = []
    notifyUsers = []
    token = properties.get("tg_token")
    fillSubscribers(getDatabase())

    psutiNetUpdater.run(send_status, onAliveReceived)

    run()
