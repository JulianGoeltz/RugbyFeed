#!/usr/bin/env python3
"""Bot that fetches the current matches from totalrugby and offers them as a
feed.

    * what happens when userfile is accessed simulatenously
"""
import json
from pprint import pprint, pformat as pf
from utils import Parser, Bot, Users
import time


# get config
with open('./utils/config.json', 'r') as f:
    config = json.load(f)


if __name__ == '__main__':
    print("Initiating parser and bot.")
    bot = Bot.BOT()
    feedParser = bot.feedParser

    print("Starting to run bot in loop.")
    while True:
        timestamp = time.time()
        print("Starting with the loop at {}.".format(
            time.strftime("%Y%m%d-%H%M%S", time.gmtime(timestamp))))
        # fetch current feed
        feedParser.update(config['retry_connection_number'])

        # Updating the users to inform them of new matches
        print("    Updating the users.")
        Users.updateUsers(bot)

        # load users and go through users
        print("    Deploying messages")
        messages = feedParser.returnMessages()
        matches = feedParser.returnMatches()
        messagesLengths = {key: len(lst) for key, lst in messages.items()}
        for user in Users.getCurrent(messagesLengths):
            # print("Dealing with chatId {}".format(user['chatId']))
            # decide whether there are new matches, and offer them
            # distribute new messages
            for sub in user['subs']:
                lastUpdate = sub['lastUpdate']
                # print(lastUpdate, feedParser.returnNumberOfMessages())
                current_messages = messages[sub['match']][lastUpdate:]
                if len(current_messages) > 10:
                    current_messages = current_messages[-10:]
                    bot.sendMessage(user['chatId'],
                                    config['text_tooManyNewMessages'],
                                    markdown=True,
                                    addListMatches=True)
                for message in current_messages:
                    # send message
                    match = matches[sub['match']]
                    text = "_{}_ *{}* ({}): \n{}".format(
                        message['time'],
                        match[0],
                        match[1],
                        message['text'])
                    # print("about to send the message:")
                    # print(text)
                    bot.sendMessage(
                        user['chatId'],
                        text,
                        markdown=True,
                        addListMatches=True)
        # sleep until timestamp+60s
        sleeping = timestamp + config['update_every_x_seconds'] - time.time()
        if sleeping > 0.:
            time.sleep(sleeping)
