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
    return m


def check_deposit_status(trackid):
    m = InlineKeyboardMarkup()
    m1 = InlineKeyboardButton("CHECK STATUS", callback_data=f"status_{trackid}")
    m.add(m1)
    return m


def finalize_trade():
    m = InlineKeyboardMarkup()
    m1 = InlineKeyboardButton("RELEASE", callback_data="finalize")
    m2 = InlineKeyboardButton("REPORT FRAUD", callback_data="report")
    m.add(m1, m2)
    return m


def check_pay_status(track_id):
    m = InlineKeyboardMarkup()
    m1 = InlineKeyboardButton("CHECK STATUS", callback_data=f"pstatus_{track_id}")
    m.add(m1)
    return m
