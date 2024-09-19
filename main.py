import time

import telebot

from config import *
from funcs import *
from buttons import *
from messages import *
from pymongo import MongoClient

bot = telebot.TeleBot(BOT_TOKEN)
client = MongoClient(
    "mongodb+srv://usanumberplug:UAc1XOXdG16HHE2M@infinityshop.dqobe8l.mongodb.net/?retryWrites=true&w=majority"
    "&appName=InfinityShop")
db = client.TGEscrow
users = db.users
trades = db.trades


# SOME FUNCS
def check_user_in_channels(user_id, channels):
    results = {}

    for channel in channels:
        try:
            member_status = bot.get_chat_member(channel, user_id)
            if member_status.status in ['member', 'administrator', 'creator']:
                results[channel] = 'Present'
            else:
                results[channel] = 'Not a member'
        except telebot.apihelper.ApiTelegramException as e:
            results[channel] = f'Error: {e.result_json["description"]}'

    return results


def get_user_first_name(user_id):
    try:
        user_info = bot.get_chat(user_id)
        return user_info.first_name
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error: {e.result_json['description']}")
        return None


@bot.message_handler(commands=['start'])
def start_handler(message):
    sender = message.from_user.id
    fname = message.from_user.first_name
    command_args = message.text.split()
    try:
        check_results = check_user_in_channels(sender, MUST_JOIN)
        not_in_channels = [channel for channel, status in check_results.items() if status != 'Present']

        if not_in_channels:
            missing_channels = ', '.join(not_in_channels)
            bot.send_message(
                message.chat.id,
                f"To use this bot, you need to join the following channels:\n{missing_channels}\nPlease join and try "
                f"again."
            )
        else:
            if len(message.text.split()) > 1:
                parameter = message.text.split()[1]
                if parameter.startswith('trade_'):
                    trade_code = parameter.split('_')[1]
                    bot.send_message(
                        message.chat.id,
                        f"Trade Code Received: {trade_code}\nConnecting with your Trading Partner..."
                    )
                    start_new_trade_func(message, trade_code)
                else:
                    bot.send_message(
                        message.chat.id,
                        "Invalid parameter received."
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    START_MESSAGE.format(fname, bot.get_me().first_name),
                    reply_markup=terms_regulations(),
                    parse_mode="Markdown"
                )
    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(message.chat.id, f"Error Occurred: {e}")


@bot.message_handler(commands=['register'])
def registration(message):
    sender = message.from_user.id
    fname = message.from_user.first_name
    try:
        check_results = check_user_in_channels(sender, MUST_JOIN)
        not_in_channels = [channel for channel, status in check_results.items() if status != 'Present']

        if not_in_channels:
            missing_channels = ', '.join(not_in_channels)
            bot.send_message(
                message.chat.id,
                f"To use this bot, you need to join the following channels:\n{missing_channels}\nPlease join and try "
                f"again."
            )
        else:
            bot.send_message(
                message.chat.id,
                f"Hello {fname},\n"
                f"To register, simply send us your wallet address where you will receive your funds. "
                f"We recommend verified wallets like Binance or the built-in Telegram wallet.\n\n"
                f"To proceed, please send your USDT TRC-20 wallet address. Additional coins will be supported in the "
                f"future."
            )
            bot.register_next_step_handler(message, add_usdt_address)
    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(message.chat.id, f"Error Occurred: {e}")


def add_usdt_address(message):
    sender = message.from_user.id
    fname = message.from_user.first_name
    address = message.text.strip()
    registered = users.find_one({'_id': sender})
    if registered:
        bot.send_message(message.chat.id, f"You are already registered in our database.\nTo change your address, "
                                          f"send /update.")
    else:

        valid = verify_address(address)
        if valid:
            users.insert_one({
                "_id": sender,
                "address": address,
            })
            bot.send_message(
                message.chat.id,
                f"Hello {fname}, \n"
                f"Address: {address} has been added to your account. You are now set to start your selling and buying."
            )
        else:
            bot.send_message(
                message.chat.id,
                f"Please provide a valid USDT TRC20 Address."
            )


# To Initialize a new trade between two parties.
@bot.message_handler(commands=['newtrade'])
def newt_rade(message):
    sender = message.from_user.id
    fname = message.from_user.first_name
    try:
        check_results = check_user_in_channels(sender, MUST_JOIN)
        not_in_channels = [channel for channel, status in check_results.items() if status != 'Present']

        if not_in_channels:
            missing_channels = ', '.join(not_in_channels)
            bot.send_message(
                message.chat.id,
                f"To use this bot, you need to join the following channels:\n{missing_channels}\nPlease join and try "
                f"again."
            )
        else:
            code = generate_linking_code()
            trades.insert_one({
                "_id": code,
                "partyone": sender
            })
            bot.send_message(
                message.chat.id,
                f"Hello {fname},\n"
                f"Please use this link to initiate a new trade. Send it to the other partner to establish a "
                f"connection.\n\n"
                f"Trade Link: `https://t.me/{bot.get_me().username}?start=trade_{code}` (Click to Copy)\n"
                f"Wishing you safe trading on Telegram!",
                parse_mode="Markdown",
            )
    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(message.chat.id, f"Error Occurred: {e}")


def start_new_trade_func(message, trade_id):
    sender = message.from_user.id
    fname = message.from_user.first_name
    trade = trades.find_one({"_id": trade_id})
    if trade:
        party_one = trade.get('partyone')
        party_two = trade.get('partytwo')
        if party_two:
            bot.reply_to(message, "The trade is already full. A trade code can only be used between two parties")
        else:
            trades.update_one({"_id": trade_id},
                              {"$set": {'partytwo': sender, 'active': True}})
            bot.send_message(message.chat.id,
                             f"Hello {fname}, \n"
                             f"Successfully Connected to Your Partner.")
            bot.send_message(party_one,
                             f"Hello {get_user_first_name(party_one)}, \n"
                             f"Your new trading partner is {fname}."
                             )

    else:
        bot.send_message(
            message.chat.id,
            "Invalid Trade ID"
        )


@bot.message_handler(commands=['requestpayment'])
def create_payout(message):
    sender = message.from_user.id
    fname = message.from_user.first_name
    try:
        check_results = check_user_in_channels(sender, MUST_JOIN)
        not_in_channels = [channel for channel, status in check_results.items() if status != 'Present']

        if not_in_channels:
            missing_channels = ', '.join(not_in_channels)
            bot.send_message(
                message.chat.id,
                f"To use this bot, you need to join the following channels:\n{missing_channels}\nPlease join and try "
                f"again."
            )
        else:
            get_trade = trades.find_one({
                "$or": [
                    {"partyone": sender},
                    {"partytwo": sender}
                ]
            })

            if get_trade:
                active = get_trade.get('active',
                                       False)
                if active:
                    party_one = get_trade.get('partyone')
                    party_two = get_trade.get('partytwo')
                    if not party_two:
                        bot.send_message(
                            message.chat.id,
                            "Sorry, You have an active trade but no trading partner. Share your link to create payout"
                        )
                    else:
                        partytwo = users.find_one({"_id": party_two})
                        partyone = users.find_one({"_id": party_one})
                        if not partyone or not partytwo:
                            bot.send_message(
                                message.chat.id,
                                "Please make sure that both of you (Active on this trade) have started the bot and "
                                "registered."
                            )
                        else:
                            bot.send_message(
                                message.chat.id,
                                "Please set the amount to be paid by the buyer."
                            )
                            bot.register_next_step_handler(message, request_payment)
                else:

                    bot.send_message(
                        message.chat.id,
                        "Sorry, You do not have an active trade. sTART one using /newtrade"
                    )
            else:
                # Handle the case where no trade was found
                bot.send_message(
                    message.chat.id,
                    "No trade found. Please create a new trade using /newtrade."
                )

    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(message.chat.id, f"Error Occurred: {e}")


def request_payment(message):
    sender = message.from_user.id
    fname = message.from_user.first_name
    amount = message.text.strip()
    if not amount.isdigit():
        bot.reply_to(message, "Please enter a valid amount.")
    else:
        new_amount = calculate_total_deposit(amount)

        trade = trades.find_one({
            "$or": [
                {"partyone": sender},
                {"partytwo": sender}
            ]
        })
        partyone = trade.get('partyone')
        partytwo = trade.get('partytwo')
        if trade:
            try:
                status, address, qrcode, track_id = generate_payment_request(new_amount)
                if status != 100:
                    bot.send_message(
                        message.chat.id,
                        "Request was unsuccessful, Please try again later."
                    )
                else:
                    if message.from_user.id == partyone:
                        bot.send_photo(
                            partytwo,
                            photo=qrcode,
                            caption=f"Payment request successful.\n\n"
                                    f"Please send your funds to this address within the next hour. After one hour, "
                                    f"any funds sent will be considered lost.\n"
                                    f"Address: `{address}` (CLICK TO COPY)\n\n"
                                    f"You can also scan the QR code in any wallet to deposit the funds directly.",
                            parse_mode='Markdown',
                            reply_markup=check_deposit_status(track_id)
                        )
                        bot.send_photo(
                            message.chat.id,
                            photo=qrcode,
                            caption=f"Your payment request has been sent successfully.\n\n"
                                    f"Use this tracking ID to monitor your partner's progress: `{track_id}`\n"
                                    f"An address has been sent to your partner's account.\n\n"
                                    f"They can also scan the QR code in any wallet to deposit the funds directly.",
                            parse_mode='Markdown',
                            reply_markup=check_deposit_status(track_id)
                        )
                    elif message.from_user.id == partytwo:
                        bot.send_photo(
                            partyone,
                            photo=qrcode,
                            caption=f"Payment request successful.\n\n"
                                    f"Please send your funds to this address within the next hour. After one hour, "
                                    f"any funds sent will be considered lost.\n"
                                    f"Address: `{address}` (CLICK TO COPY\n\n"
                                    f"You can also scan the QR code in any wallet to deposit the funds directly.",
                            parse_mode='Markdown',
                            reply_markup=check_deposit_status(track_id)
                        )
                        bot.send_photo(
                            message.chat.id,
                            photo=qrcode,
                            caption=f"Your payment request has been sent successfully.\n\n"
                                    f"Use this tracking ID to monitor your partner's progress: `{track_id}`\n"
                                    f"An address has been sent to your partner's account.\n\n"
                                    f"They can also scan the QR code in any wallet to deposit the funds directly.",
                            parse_mode='Markdown',
                            reply_markup=check_deposit_status(track_id)
                        )
            except telebot.apihelper.ApiTelegramException as e:
                bot.send_message(
                    message.chat.id,
                    f"Error Occurred: {e}."
                )


def check_payment_statuses(message, track_id):
    status = check_payment_status(track_id)
    if status != 100:
        bot.send_message(
            message.chat.id,
            "Payment not received yet."
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Deposit was successful.\n\nPlease release the service/good to receive your payment"
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "tnc":
        bot.send_message(
            call.message.chat.id,
            TERMS_AND_CONDITIONS,
            parse_mode='Markdown',
            reply_markup=accept_regulations()
        )
    elif call.data == "accept":
        bot.send_message(
            call.message.chat.id,
            "Thanks for accepting to the TOS"
        )
    elif call.data == "reject":
        bot.send_message(
            call.message.chat.id,
            "Thanks for rejecting to the TOS"
        )
    elif call.data.startswith("status_"):
        try:
            trackid = call.data.split("_")[1]
            status, resp = check_payment_status(trackid)
            if status != 100:
                bot.send_message(
                    call.message.chat.id,
                    f"Payment not received yet.Check again later.\n Current Response: {resp}"
                )
            elif status == 100:
                if resp == "Waiting":
                    bot.send_message(
                        call.message.chat.id,
                        f"Your payment have been successfully received.\n Current Response: {resp}"
                    )
                elif resp == "Rejected":
                    bot.send_message(
                        call.message.chat.id,
                        f"Your payment has been rejected.\n Current Response: {resp}"
                    )
                elif resp == "Confirming":
                    bot.send_message(
                        call.message.chat.id,
                        f"Your payment has been confirmed.\n Current Response: {resp}"
                    )
                elif resp == "Paid":
                    bot.send_message(
                        call.message.chat.id,
                        f"The payment has been.We will release it to the seller once you confirm that they "
                        f"have delivered their part.\n Current Response: {resp}. \n\n"
                        f"To the seller: You can now deliver your good/service to the buyer.\n"
                        f"The buyer should also confirm if the good/service is what he/she ordered for.If consent,"
                        f"send /release.\n\n"
                        f"Seller can also send the /release command and wait for the buyer to confirm."
                    )

        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(
                call.message.chat.id,
                "Error Occurred: {e}."
            )


if __name__ == '__main__':
    print(f"Bot started with id {bot.get_me().id}")
    bot.infinity_polling()
