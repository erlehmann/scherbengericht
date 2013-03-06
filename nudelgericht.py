#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python IRC bot
# based on <http://web.archive.org/web/20070226174611/http://gfxfor.us/general/
# tutorial-how-to-make-a-simple-irc-bot-from-scratch-in-python>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Dieses Programm hat das Ziel, die Medienkompetenz der Leser zu
# steigern. Gelegentlich packe ich sogar einen handfesten Buffer
# Overflow oder eine Format String Vulnerability zwischen die anderen
# Codezeilen und schreibe das auch nicht dran.

import sys
import socket
import string

from math import ceil
from random import choice
from time import time, sleep

HOST = "irc.freenode.net"
PORT = 6667
NICK = "rubelgericht"
IDENT = "nudel"
REALNAME = "Pelmeni"
CHANNEL = "#nodrama.de"
VOTING_QUOTA = 0.3  # proportion of voters that are needed for a vote to be successful
VOTING_TIMEOUT = 60*3  # seconds a vote is valid
VOTING_AGE_MIN = 60*3  # seconds from a user saying something to gaining voting rights

s = socket.socket()

s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
s.send("JOIN :%s\r\n" % CHANNEL)

def emit(message):
    s.send("NOTICE " + CHANNEL + " :" + message + "\r\n")
    sleep(1) # do not flood

people = {}

users = []

def remember_user(nickname, hostmask):
    global people
    try:
        people[hostmask]['nickname'] = nickname
    except KeyError:
        people[hostmask] = {
            'firstmessage': time(),
            'nickname': nickname
        }

def forget_user(hostmask):
    global people
    del people[hostmask]

def forget_old_users():
    for hostmask in people:
        if people[hostmask]['nickname'] not in users:
            forget_user(hostmask)
            break

def get_nickname(hostmask):
    return people[hostmask]['nickname']

def get_age(hostmask):
    return time() - people[hostmask]['firstmessage']

def old_enough_to_vote(hostmask):
    if get_age(hostmask) > VOTING_AGE_MIN:
        return True
    return False

def get_adult_users():
    adult_users = []
    for hostmask in people:
        if old_enough_to_vote(hostmask):
            adult_users.append(people[hostmask]['nickname'])
    return adult_users

def get_voting_threshold():
    threshold = ceil(len(get_adult_users()) * VOTING_QUOTA)
    if threshold < 3:
        return 3
    return threshold

votes = {}

def remember_vote(target, votetype, origin):
    global votes
    votetime = time()
    message = ''
    try:
        votes[target][votetype][origin] = votetime
        message += "Stimme gezählt von %s %s %s." % (get_nickname(origin), votetype, target)
    except KeyError:
        try:
            votes[target][votetype] = { origin: votetime }
            emit('')
        except KeyError:
            votes[target] = { votetype: { origin: votetime } }
        message += "Abstimmung gestartet von %s %s %s." % (get_nickname(origin), votetype, target)
    emit('%s Weitere Stimmen notwendig: %d.' % \
        (message, get_voting_threshold() - count_votes(target, votetype)))

def count_votes(target, votetype):
    return len(votes[target][votetype])

def forget_votes(target, votetype):
    del votes[target][votetype]

def forget_old_votes():
    global votes
    for target in votes:
        for votetype in votes[target]:
            for origin in votes[target][votetype]:
                votetime = votes[target][votetype][origin]
                if votetime + VOTING_TIMEOUT < time():
                    del votes[target][votetype][origin]
                    emit('Stimme abgelaufen von %s %s %s.' % \
                        (get_nickname(origin), votetype, target))
                    break

def execute_the_will_of_the_people():
    global votes
    for target in votes:
        for votetype in votes[target]:
            if count_votes(target, votetype) >= get_voting_threshold():
                emit('Abstimmung %s %s erfolgreich.' % (votetype, target))
                if votetype == 'für':
                    unban(target)
                elif votetype == 'gegen':
                    deop(target)
                    ban(target)
                    kick(target)
                forget_votes(target, votetype)
                break

kick = lambda user: s.send('KICK ' + CHANNEL + ' ' + user + '\r\n')
ban = lambda user: s.send('MODE ' + CHANNEL + ' +b ' + user + '!*@*\r\n')
unban = lambda user: s.send('MODE ' + CHANNEL + ' -b ' + user + '!*@*\r\n')
deop = lambda user: s.send('MODE ' + CHANNEL + ' -o ' + user + '\r\n')

def get_name_parts(name):
    parts = name.split('!')
    return parts[0], parts[1]

readbuffer = ''

while True:
    execute_the_will_of_the_people()
    forget_old_users()
    forget_old_votes()

    readbuffer = readbuffer + s.recv(1024)
    temp = string.split(readbuffer, '\n')
    readbuffer = temp.pop()

    for line in temp:
        line = string.rstrip(line)
        line = string.split(line)
        print line

        messagetype = line[1]

        if (line[0] == "PING"):
            s.send("PONG %s\r\n" % messagetype)
            continue

        elif messagetype == '353':
            users = ' '.join(line[5:])[1:].split(' ')
            for user in users:
                if user.startswith('@'):
                    del users[users.index(user)]
                    users.append(user[1:])
            print users

        elif messagetype in ('JOIN', 'PART', 'NICK'):
            s.send("NAMES %s\r\n" % (CHANNEL))

        elif messagetype == "PRIVMSG":
            nickname, hostmask = get_name_parts(line[0][1:])
            remember_user(nickname, hostmask)

            channel = line[2]
            if channel != CHANNEL:
                continue

            command = line[3][1:]
            try:
                argument = line[4]
            except IndexError:
                argument = ''

            if command == '!man':
                emit("Die vollständige Dokumentation für GNU/%s ist verfügbar als Texinfo-Handbuch." % NICK)

            elif command == '!info':
                emit(
                    "Man kann Stimme machen !für, man kann Stimme machen !gegen. " + \
                    "Stimmen verfallen nach %d Sekunden. " % VOTING_TIMEOUT + \
                    "Quorum: %d. " % get_voting_threshold() + \
                    "Wahlberechtigt: %s. " % ', '.join(get_adult_users())
                )

            elif command in ('!für', '!gegen'):
                if argument == NICK:
                    emit('An dieser Stelle habe ich einen überflüssigen Smiley hingemacht, wofür ich mich dereinst schämen werde.')
                    kick(nickname)
                elif command == '!gegen' and argument not in users:
                    emit("%s ist nicht in %s." % (argument, CHANNEL))
                    kick(nickname)
                elif old_enough_to_vote(hostmask):
                    remember_vote(argument, command[1:], hostmask)
                else:
                    emit("%s ist erst %d Sekunden alt und darf nicht wählen. Wahlalter: %d Sekunden." % \
                        (nickname, get_age(hostmask), VOTING_AGE_MIN))
                    kick(nickname)
