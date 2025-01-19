import time

import telebot
import logging
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
successful = db.successfultrades

user_messages = {}

forwarded_messages = {}

logging.basicConfig(level=logging.INFO)


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
                f"We recommend verified wallets like Binance, OKX or Bitget.\n\n"
                f"To proceed, please send your LiteCoin[LTC] wallet address. Additional coins will be supported in the "
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
                'address': address
            })
            bot.send_message(
                message.chat.id,
                f"Hello {fname}, \n"
                f"Address: {address} has been added to your account. You are now set to start your selling and buying.\n"
                f"Initiate a new trade with /newtrade"
            )
            bot.send_message(
                message.chat.id,
                GET_CRYPTO,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id,
                f"Please provide a valid LTC Address."
            )


# To Initialize a new trade between two parties.
@bot.message_handler(commands=['newtrade'])
def newt_rade(message):
    sender = message.from_user.id
    fname = message.from_user.first_name
    try:
        # Check if the user is in the required channels
        check_results = check_user_in_channels(sender, MUST_JOIN)
        not_in_channels = [channel for channel, status in check_results.items() if status != 'Present']

        if not_in_channels:
            # Notify user of missing channels and exit
            missing_channels = ', '.join(not_in_channels)
            bot.send_message(
                message.chat.id,
                f"To use this bot, you need to join the following channels:\n{missing_channels}\n"
                f"Please join and try again."
            )
            return  # Exit after notifying about missing channels

        # Check if the user already has an active trade
        get_trade = trades.find_one({
            "$or": [
                {"partyone": sender},
                {"partytwo": sender}
            ]
        })

        if get_trade:
            # Check if the trade is active
            active = get_trade.get('active', False)
            if active:
                bot.send_message(
                    message.chat.id,
                    "Sorry, You can have a single trade active at once."
                )
                return  # Exit since the trade is active

        # Create a new trade if no active trade exists
        code = generate_linking_code()  # Ensure this function generates unique codes
        trades.insert_one({
            "_id": code,
            "partyone": sender,
            "active": True  # Optional: Set as active if your logic requires it
        })
        bot.send_message(
            message.chat.id,
            f"Hello {fname},\n"
            f"Please use this link to initiate a new trade. Send it to the other partner to establish a connection.\n\n"
            f"Trade Link: `https://t.me/{bot.get_me().username}?start=trade_{code}` (Click to Copy)\n"
            f"Wishing you safe trading on Telegram!",
            parse_mode="Markdown"
        )

    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(message.chat.id, f"Error Occurred: {e}")

    except Exception as e:
        # Catch other potential exceptions, such as database errors
        bot.send_message(message.chat.id, f"An unexpected error occurred: {e}")


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
    if not float(amount):
        bot.reply_to(message, "Please enter a valid amount.")
    else:
        # new_amount = calculate_total_deposit(amount)

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
                status, address, qrcode, track_id = generate_payment_request(amount)
                if status != 100:
                    bot.send_message(
                        message.chat.id,
                        "Request was unsuccessful, Please try again later."
                    )
                else:
                    if message.from_user.id == partyone:
                        trades.update_one({"partyone": partyone},
                                          {"$set": {'amount': amount}})
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
                        trades.update_one({"partytwo": partytwo},
                                          {"$set": {'amount': amount}})
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


def send_report(message):
    pass


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
            "Thanks for accepting to the TOS. To proceed, Send the /register command."
        )
    elif call.data == "reject":
        bot.send_message(
            call.message.chat.id,
            "Sorry to see that you cannot compile to our Terms and Conditions.Please block this bot"
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
                        f"The payment has been processed. The funds will be released to the seller upon your "
                        f"confirmation of delivery. Current Response: {resp}.\n\n"
                        f"To the seller: You can now deliver the goods/services to the buyer. The buyer should verify "
                        f"the received items. If satisfied, please send /release.\n\n"
                        f"The seller can also initiate the /release command and await the buyer's confirmation.",
                        reply_markup=finalize_trade()
                    )

        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(
                call.message.chat.id,
                "Error Occurred: {e}."
            )
    elif call.data == "report":
        bot.send_message(
            call.message.chat.id,
            "Please send us your complains.(It can be either photo or text We will take an action as soon as possible."
        )
        bot.register_next_step_handler(call.message, send_report)
    elif call.data == 'finalize':
        sender = call.message.from_user.id
        fname = call.message.from_user.first_name
        try:
            get_trade_id = trades.find_one({
                "$or": [
                    {"partyone": sender},
                    {"partytwo": sender}
                ]
            })
            if get_trade_id:
                trade_id = get_trade_id.get("_id")
                partyone = get_trade_id.get("partyone")
                partytwo = get_trade_id.get("partytwo")
                amount = get_trade_id.get("amount")
                party_one = users.find_one({'_id': partyone})
                party_two = users.find_one({'_id': partytwo})
                pone_address = party_one.get("address")
                ptwo_address = party_two.get("address")
                try:
                    if sender == partyone:
                        status, track_id, result = create_payout_to_seller(ptwo_address, amount)
                        if status != 100:
                            bot.send_message(
                                call.message.chat.id,
                                f"Some error occurred.\n Current Response: {result}\nPlease forward this message to"
                                f"the support."
                            )
                        elif status == 100:
                            if status != 100:
                                bot.send_message(
                                    call.message.chat.id,
                                    f"Payment has been Initiated.Check status by clicking below button.\n Current "
                                    f"Response: {result}\n",
                                    reply_markup=check_pay_status(track_id)
                                )

                    if sender == partytwo:
                        status, track_id, result = create_payout_to_seller(pone_address, amount)
                        if status != 100:
                            bot.send_message(
                                call.message.chat.id,
                                f"Some error occurred during initiation of the payment.\n Current Response: {result}\n"
                                f"Please forward this message to"
                                f"the support."
                            )
                        elif status == 100:
                            if status != 100:
                                bot.send_message(
                                    call.message.chat.id,
                                    f"Payment has been Initiated.Check status by clicking below button.\n Current "
                                    f"Response: {result}\n",
                                    reply_markup=check_pay_status(track_id)
                                )
                except telebot.apihelper.ApiTelegramException as e:
                    bot.send_message(
                        call.message.chat.id,
                        f"Error Occurred: {e}."
                    )

        except Exception as e:
            bot.send_message(
                call.message.chat.id,
                f"Error Occurred: {e}."
            )
    elif call.data.startswith('pstatus_'):
        sender = call.message.from_user.id
        get_trade_id = trades.find_one({
            "$or": [
                {"partyone": sender},
                {"partytwo": sender}
            ]
        })
        if get_trade_id:
            trade_id = get_trade_id.get("_id")
            partyone = get_trade_id.get("partyone")
            partytwo = get_trade_id.get("partytwo")
            amount = get_trade_id.get("amount")
            party_one = users.find_one({'_id': partyone})
            party_two = users.find_one({'_id': partytwo})
            pone_address = party_one.get("address")
            ptwo_address = party_two.get("address")
            try:
                trackid = call.data.split("_")[1]
                status, result = check_pay_status(trackid)
                if sender == partyone:
                    status, track_id, result = create_payout_to_seller(ptwo_address, amount)
                    if status != 100:
                        bot.send_message(
                            call.message.chat.id,
                            f"Some error occurred.\n Current Response: {result}\nPlease forward this message to"
                            f"the support."
                        )
                    elif status == 100:
                        if result == "Processing":
                            bot.send_message(
                                call.message.chat.id,
                                f"Please be patient as we process your payment.\n Current Response: {result}"
                            )
                        elif result == "Confirming":
                            bot.send_message(
                                call.message.chat.id,
                                "Your payment has been sent and is awaiting blockchain confirmation. Please be patient.\n"
                                f"Current Response: {result}"
                            )
                        elif result == "Complete":
                            trades.update_one({"partyone": partyone},
                                              {"$set": {'active': False}})
                            bot.send_message(
                                call.message.chat.id,
                                "Please check your wallet to confirm your payment.\n"
                                f"Current Response: {result}. If not yet, Please wait and keep checking.\n"
                                f"You can contact support if no payment is received after 30 minutes"
                            )
                            mess = f"""
***New Trade Finalized.***

***Status:*** _{result}_
***Trade ID:*** _{trade_id}_
***Party One:*** _{party_one}_
***Party Two:*** _{party_two}_
***Amount:*** _{amount}_
***P.O Address:*** _{pone_address}_
***P.T Address:*** _{ptwo_address}_
"""
                            bot.send_message(
                                LOGS_CHANNEL,
                                mess,
                                parse_mode="Markdown",
                            )
                elif sender == party_two:
                    status, track_id, result = create_payout_to_seller(pone_address, amount)
                    if status != 100:
                        bot.send_message(
                            call.message.chat.id,
                            f"Some error occurred.\n Current Response: {result}\nPlease forward this message to"
                            f"the support."
                        )
                    elif status == 100:
                        if result == "Processing":
                            bot.send_message(
                                call.message.chat.id,
                                f"Please be patient as we process your payment.\n Current Response: {result}"
                            )
                        elif result == "Confirming":
                            bot.send_message(
                                call.message.chat.id,
                                "Your payment has been sent and is awaiting blockchain confirmation. Please be "
                                "patient.\n"
                                f"Current Response: {result}"
                            )
                        elif result == "Complete":
                            trades.update_one({"partytwo": partytwo},
                                              {"$set": {'active': False}})
                            bot.send_message(
                                call.message.chat.id,
                                "Please check your wallet to confirm your payment.\n"
                                f"Current Response: {result}. If not yet, Please wait and keep checking.\n"
                                f"You can contact support if no payment is received after 30 minutes"
                            )
                            mess = f"""
***New Trade Finalized.***

***Status:*** _{result}_
***Trade ID:*** _{trade_id}_
***Party One:*** _{party_one}_
***Party Two:*** _{party_two}_
***Amount:*** _{amount}_
***P.O Address:*** _{pone_address}_
***P.T Address:*** _{ptwo_address}_
"""
                            bot.send_message(
                                LOGS_CHANNEL,
                                mess,
                                parse_mode="Markdown",
                            )
            except Exception as e:
                bot.send_message(
                    call.message.chat.id,
                    f"Error: {e}"
                )


@bot.message_handler(func=lambda message: message.chat.type == 'private',
                     content_types=['text', 'photo', 'audio', 'document', 'video', 'voice', 'video_note', 'sticker',
                                    'location', 'contact'])
def handle_all_messages(message):
    if message.chat.id in ADMINS_ID:
        # Handle admin's reply
        if message.reply_to_message and message.reply_to_message.message_id in forwarded_messages:
            original_message_id = forwarded_messages[message.reply_to_message.message_id]
            original_user_id = user_messages[original_message_id]['chat_id']
            # Forward the appropriate content type back to the user
            if message.content_type == 'text':
                bot.send_message(original_user_id, message.text)
            else:
                bot.copy_message(original_user_id, message.chat.id, message.message_id)
            print(f"Admin {message.chat.id} replied to user {original_user_id}")
        else:
            bot.reply_to(message, "Please reply to a forwarded user message.")
    else:
        original_message_id = message.message_id
        user_messages[original_message_id] = {
            'chat_id': message.chat.id,
            'content_type': message.content_type,
            'user_id': message.from_user.id
        }
        for admin in ADMINS_ID:
            forwarded_message = bot.forward_message(admin, message.chat.id, original_message_id)
            forwarded_messages[forwarded_message.message_id] = original_message_id
        # bot.reply_to(message, "Your message has been forwarded to an admin. Please wait for a response.")
        print(f"User {message.chat.id} message forwarded to admin(s)")


if __name__ == '__main__':
    print(f"Bot started with id {bot.get_me().id}")
    bot.infinity_polling()
