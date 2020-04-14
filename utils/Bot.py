#!/usr/bin/env python3
import json
import logging
import socket
import telegram
from telegram.ext import CallbackContext, CommandHandler, Updater
import time

from . import Parser, Users


# get config
with open('./utils/config.json', 'r') as f:
    config = json.load(f)
with open('../config_sensitive.json', 'r') as f:
    config_sensitive = json.load(f)

feedParser = Parser.PARSER()


def start(update: Updater, context: CallbackContext):
    """List all available matches, and the ones the user is subscribed to.

    Offer the registration"""
    # user already added
    if Users.doesUserExist(update.effective_user['id']):
        Users.toggleMute(update.effective_user['id'], False)
        BOT.sendMessageWithGivenBot(
            None,
            context.bot,
            chatId=update.effective_user['id'], text=config['text_unmuted'],
            addListMatches=True)
        listMatches(update, context)
        return
    # user with wrong password
    if len(context.args) == 0 or context.args[0] != config_sensitive['passwordForBot']:
        BOT.sendMessageWithGivenBot(
            None,
            context.bot,
            chatId=update.effective_user['id'], text=config['text_wrongPassword'])
        return
    text = config['text_start']
    BOT.sendMessageWithGivenBot(
        None,
        context.bot,
        chatId=update.effective_user['id'], text=text,
        addListMatches=True)
    Users.addUser(update.effective_user['id'])
    # listMatches(update, context)


def stop(update: Updater, context: CallbackContext):
    """To not annoy users make an option to remove them from the users."""

    if not Users.doesUserExist(update.effective_user['id']):
        context.bot.send_message(chat_id=update.effective_user['id'],
                                 text=config['text_notstarted'])
        return
    BOT.sendMessageWithGivenBot(
        None,
        context.bot,
        chatId=update.effective_user['id'], text=config['text_muted'])
    Users.toggleMute(update.effective_user['id'], True)
    listMatches(update, context)


def help(update: Updater, context: CallbackContext):
    text = config['text_help']
    BOT.sendMessageWithGivenBot(
        None,
        context.bot,
        chatId=update.effective_user['id'], text=text,)


def get_link(update: Updater, context: CallbackContext):
    """List all available matches, and the ones the user is subscribed to.

    Offer the registration"""
    if not Users.doesUserExist(update.effective_user['id']):
        context.bot.send_message(chat_id=update.effective_user['id'],
                                 text=config['text_notstarted'])
        return

    text = config_sensitive['ticker_url']
    BOT.sendMessageWithGivenBot(
        None,
        context.bot,
        chatId=update.effective_user['id'], text=text,
        addListMatches=True)


def listMatches(update: Updater, context: CallbackContext):
    """List all available matches, and the ones the user is subscribed to.

    Offer the registration"""
    if not Users.doesUserExist(update.effective_user['id']):
        context.bot.send_message(chat_id=update.effective_user['id'],
                                 text=config['text_notstarted'])
        return
    hashedMatches = feedParser.returnHashedMatches()
    matches, duplicates = feedParser.returnMatches(return_duplicate_status=True)
    subbedMatches = Users.getSubbedMatches(update.effective_user['id'])
    if len(hashedMatches) > 0:
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
        text = config['text_list'].format(tmpString)
    else:
        text = config['text_list_empty']
        custom_keyboard = [['/getLink']]

    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                one_time_keyboard=True)
    BOT.sendMessageWithGivenBot(
        None,
        context.bot,
        chatId=update.effective_user['id'], text=text,
        markdown=True,
        reply_markup=reply_markup)


def switchSubscription(update: Updater, context: CallbackContext):
    """(Un)subscribe the user for a match."""
    if not Users.doesUserExist(update.effective_user['id']):
        context.bot.send_message(chat_id=update.effective_user['id'],
                                 text=config['text_notstarted'])
        return
    hashedMatches = feedParser.returnHashedMatches()
    wrongInput = False
    try:
        givenInt = int(context.args[0])
    except (ValueError, IndexError):
        wrongInput = True
        givenInt = ""
    if wrongInput or givenInt > len(hashedMatches):
        context.bot.send_message(chat_id=update.effective_user['id'],
                                 text=config['text_switch_error'].format(givenInt))
        listMatches(update, context)
        return

    matches = feedParser.returnMatches()
    match = hashedMatches[givenInt]
    if Users.switchSub(update.effective_user['id'],
                       match):
        text = config['text_switch_unsub'].format(matches[match][0])
    else:
        text = config['text_switch_sub'].format(matches[match][0])
    BOT.sendMessageWithGivenBot(
        None,
        context.bot,
        chatId=update.effective_user['id'], text=text,
        addListMatches=True)


class BOT:
    def __init__(self):
        self.feedParser = feedParser

        # get the bot
        self.bot = telegram.Bot(token=config_sensitive['token'])
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        # print(self.bot.get_me())
        self.updater = Updater(token=config_sensitive['token'], use_context=True)
        self.dispatcher = self.updater.dispatcher

        list_of_commands = [
            ['start', start],
            ['stop', stop],
            ['help', help],
            ['listMatches', listMatches],
            ['switchSub', switchSubscription],
            ['getLink', get_link],
        ]
        for name, fn in list_of_commands:
            self.dispatcher.add_handler(
                CommandHandler(name, fn))

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
