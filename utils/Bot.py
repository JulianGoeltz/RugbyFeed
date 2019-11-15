#!/usr/bin/env python3
import json
import logging
import socket
import telegram
from telegram.ext import Updater, CommandHandler
import time

from . import Parser, Users


# get config
with open('./utils/config.json', 'r') as f:
    config = json.load(f)
with open('../config_sensitive.json', 'r') as f:
    config_sensitive = json.load(f)

feedParser = Parser.PARSER()


def start(bot, update, args):
    """List all available matches, and the ones the user is subscribed to.

    Offer the registration"""
    # user already added
    if Users.doesUserExist(update.message.chat_id):
        Users.toggleMute(update.message.chat_id, False)
        BOT.sendMessageWithGivenBot(
            None,
            bot,
            chatId=update.message.chat_id, text=config['text_unmuted'],
            addListMatches=True)
        listMatches(bot, update)
        return
    # user with wrong password
    if len(args) == 0 or args[0] != config_sensitive['passwordForBot']:
        BOT.sendMessageWithGivenBot(
            None,
            bot,
            chatId=update.message.chat_id, text=config['text_wrongPassword'])
        return
    text = config['text_start']
    BOT.sendMessageWithGivenBot(
        None,
        bot,
        chatId=update.message.chat_id, text=text,
        addListMatches=True)
    Users.addUser(update.message.chat_id)
    # listMatches(bot, update)


def stop(bot, update):
    """To not annoy users make an option to remove them from the users."""

    if not Users.doesUserExist(update.message.chat_id):
        bot.send_message(chat_id=update.message.chat_id,
                         text=config['text_notstarted'])
        return
    BOT.sendMessageWithGivenBot(
        None,
        bot,
        chatId=update.message.chat_id, text=config['text_muted'])
    Users.toggleMute(update.message.chat_id, True)
    listMatches(bot, update)


def help(bot, update):
    text = config['text_help']
    BOT.sendMessageWithGivenBot(
        None,
        bot,
        chatId=update.message.chat_id, text=text,)


def listMatches(bot, update):
    """List all available matches, and the ones the user is subscribed to.

    Offer the registration"""
    if not Users.doesUserExist(update.message.chat_id):
        bot.send_message(chat_id=update.message.chat_id,
                         text=config['text_notstarted'])
        return
    hashedMatches = feedParser.returnHashedMatches()
    matches, duplicates = feedParser.returnMatches(return_duplicate_status=True)
    subbedMatches = Users.getSubbedMatches(update.message.chat_id)
    tmpString = ""
    custom_keyboard = []
    for key, match in enumerate(hashedMatches):
        name, score, status = matches[match]
        tmpString += "{}: {}, {}, {}{}\n".format(
            str(key),
            name,
            status,
            score,
            ", *subscribed*" if match in subbedMatches else "")
        custom_keyboard.append(["/switchSub " + str(key) + " " + name])
    if duplicates:
        tmpString += "\nDue to the website design, some matches can't be kept appart"
    custom_keyboard.append(["None"])
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                one_time_keyboard=True)
    text = config['text_list'].format(tmpString)
    BOT.sendMessageWithGivenBot(
        None,
        bot,
        chatId=update.message.chat_id, text=text,
        markdown=True,
        reply_markup=reply_markup)


def switchSubscription(bot, update, args):
    """(Un)subscribe the user for a match."""
    if not Users.doesUserExist(update.message.chat_id):
        bot.send_message(chat_id=update.message.chat_id,
                         text=config['text_notstarted'])
        return
    hashedMatches = feedParser.returnHashedMatches()
    wrongInput = False
    try:
        givenInt = int(args[0])
    except (ValueError, IndexError):
        wrongInput = True
        givenInt = ""
    if wrongInput or givenInt > len(hashedMatches):
        bot.send_message(chat_id=update.message.chat_id,
                         text=config['text_switch_error'].format(givenInt))
        listMatches(bot, update)
        return

    matches = feedParser.returnMatches()
    match = hashedMatches[givenInt]
    if Users.switchSub(update.message.chat_id,
                       match):
        text = config['text_switch_unsub'].format(matches[match][0])
    else:
        text = config['text_switch_sub'].format(matches[match][0])
    BOT.sendMessageWithGivenBot(
        None,
        bot,
        chatId=update.message.chat_id, text=text,
        addListMatches=True)


class BOT:
    def __init__(self):
        self.feedParser = feedParser

        # get the bot
        self.bot = telegram.Bot(token=config_sensitive['token'])
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        # print(self.bot.get_me())
        self.updater = Updater(token=config_sensitive['token'])
        self.dispatcher = self.updater.dispatcher

        handler_start = CommandHandler('start', start, pass_args=True)
        handler_stop = CommandHandler('stop', stop)
        handler_help = CommandHandler('help', help)
        handler_listMatches = CommandHandler('listMatches', listMatches)
        handler_switchSubscription = CommandHandler('switchSub',
                                                    switchSubscription,
                                                    pass_args=True)

        self.dispatcher.add_handler(handler_start)
        self.dispatcher.add_handler(handler_stop)
        self.dispatcher.add_handler(handler_help)
        self.dispatcher.add_handler(handler_listMatches)
        self.dispatcher.add_handler(handler_switchSubscription)

        self.updater.start_polling()

    def sendMessage(self, chatId, text, retries=4, markdown=False,
                    reply_markup=None, addListMatches=False):
        self.sendMessageWithGivenBot(
            self.bot,
            chatId, text, retries=retries,
            markdown=markdown,
            reply_markup=reply_markup, addListMatches=addListMatches)

    def sendMessageWithGivenBot(self, bot, chatId, text, retries=4,
                                markdown=False,
                                reply_markup=None, addListMatches=False):
        if retries < 0:
            print("Tried too hard, somehow there's a problem")
            return
        try:
            if reply_markup is None and not addListMatches:
                reply_markup = telegram.ReplyKeyboardRemove()
            if reply_markup is None and addListMatches:
                custom_keyboard = [['/listMatches']]
                reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                            one_time_keyboard=True)
            if markdown:
                bot.send_message(chat_id=chatId,
                                 text=text,
                                 parse_mode=telegram.ParseMode.MARKDOWN,
                                 reply_markup=reply_markup)
            else:
                bot.send_message(chat_id=chatId,
                                 text=text,
                                 reply_markup=reply_markup)
        except socket.timeout:
            self.sendMessageWithGivenBot(bot, chatId, text, retries - 1, markdown)
