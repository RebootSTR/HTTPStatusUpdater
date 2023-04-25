# @rebootstr
from telegram import KeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup

from dictionary import *


def getEmptyKeyboard():
    return ReplyKeyboardRemove()


def getKeyboard(isAdmin):
    if isAdmin:
        buttons = [
            [KeyboardButton(NORMAL_MODE_BUTTON), KeyboardButton(SILENT_MODE_BUTTON)],
            [KeyboardButton(SUBSCRIBERS)]
        ]
    else:
        return getEmptyKeyboard()

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def getCancelKeyboard():
    buttons = [
        [KeyboardButton(text=CANCEL)]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
