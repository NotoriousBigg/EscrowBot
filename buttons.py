from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import *


def terms_regulations():
    m = InlineKeyboardMarkup()
    m1 = InlineKeyboardButton("Terms And Conditions", callback_data="tnc")
    m.add(m1)
    return m


def accept_regulations():
    m = InlineKeyboardMarkup()
    m1 = InlineKeyboardButton("Accept", callback_data="accept")
    m2 = InlineKeyboardButton("Reject", callback_data="reject")
    m.add(m1, m2)
    return

def check_deposit_status(trackid):
    m = InlineKeyboardMarkup()
    m1 = InlineKeyboardButton("CHECK STATUS", callback_data=f"status_{trackid}")
    m.add(m1)
    return m
