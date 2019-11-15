#!/usr/bin/env python3
import copy
import json
import os
import os.path as osp
from pprint import pprint, pformat as pf
import time


# get config
with open('./utils/config.json', 'r') as f:
    config = json.load(f)
if not osp.isfile(config['user_filename']) or \
   os.stat(config['user_filename']).st_size == 0:
    with open(config['user_filename'], 'w') as f:
        json.dump([], f)


def doesUserExist(chatId):
    with open(config['user_filename'], 'r') as f:
        users = json.load(f)
    return chatId in [i['chatId'] for i in users]


def getSubbedMatches(chatId):
    with open(config['user_filename'], 'r') as f:
        users = json.load(f)

    for user in users:
        if user['chatId'] == chatId:
            return [i['match'] for i in user['subs']]


def getCurrent(messagesLengths):
    # read file fast, save contents
    # then reload file, but in writemode
    with open(config['user_filename'], 'r') as f:
        users = json.load(f)
    with open(config['user_filename'], 'w') as f:
        users_tmp = copy.deepcopy(users)
        for user in users_tmp:
            for sub in user['subs']:
                sub['lastUpdate'] = messagesLengths[sub['match']]
            # users_tmp.append(user)
        json.dump(users_tmp, f)

    return users


def addUser(chatId):
    with open(config['user_filename'], 'r') as f:
        users = json.load(f)
    with open(config['user_filename'], 'w') as f:
        if chatId in [i['chatId'] for i in users]:
            print("The chatId {} exists already. What to do?".format(
                chatId))
        else:
            timestamp = time.time()
            users.append(
                {'chatId': chatId,
                 'subs': [],
                 'created': timestamp,
                 'changed': timestamp,
                 'receiveUpdates': True,
                 })
            print("Chat with chatId {} was created at {}.".format(
                chatId, timestamp))
        json.dump(users, f)


def toggleMute(chatId, muteness):
    with open(config['user_filename'], 'r') as f:
        users = json.load(f)
    with open(config['user_filename'], 'w') as f:
        for user in users:
            if user['chatId'] != chatId:
                continue
            user['receiveUpdates'] = muteness
        json.dump(users, f)


def switchSub(chatId, match):
    with open(config['user_filename'], 'r') as f:
        users = json.load(f)
    with open(config['user_filename'], 'w') as f:
        foundUser = False
        for user in users:
            if user['chatId'] != chatId:
                continue

            users.remove(user)
            found_tmp = False
            for sub in user['subs']:
                if sub['match'] == match:
                    user['subs'].remove(sub)
                    found_tmp = True
            if not found_tmp:
                user['subs'].append(
                    {'match': match,
                     'added': time.time(),
                     'lastUpdate': 0,
                     })
            user['changed'] = time.time()
            users.append(user)
            foundUser = True
        if not foundUser:
            print("______ Serious Problem, didn't find user")
        json.dump(users, f)
        return found_tmp


def updateUsers(bot):
    feedParser = bot.feedParser
    with open(config['matches_filename'], 'r') as f:
        matches_old = json.load(f)

    matches_new = sorted([i[0] for i in feedParser.returnMatches().values()])

    if matches_new != matches_old:
        # need for reset?
        # determine if all old matches are part of the new ones
        reset_needed = False
        for match in matches_old:
            if match not in matches_new:
                reset_needed = True
                break

        if reset_needed:
            with open(config['user_filename'], 'r') as f:
                users = json.load(f)
            # reset all the subscriptions
            with open(config['user_filename'], 'w') as f:
                for user in users:
                    user['subs'] = []
                json.dump(users, f)

        # save the current matches
        with open(config['matches_filename'], 'w') as f:
            json.dump(matches_new, f)

        # notify the users
        for user in users:
            if user['receiveUpdates']:
                bot.sendMessage(user['chatId'],
                                config['text_updates'] if not reset_needed else config['text_updates_reset'],
                                addListMatches=True)
