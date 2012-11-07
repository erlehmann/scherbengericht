#!/usr/bin/python
# -*- coding: utf-8 -*-

# Python IRC bot
# based on <http://web.archive.org/web/20070226174611/http://gfxfor.us/general/
# tutorial-how-to-make-a-simple-irc-bot-from-scratch-in-python>

# DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                    Version 2, December 2004
#
# Copyright (C) 2004 Sam Hocevar
#  14 rue de Plaisance, 75014 Paris, France
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#  0. You just DO WHAT THE FUCK YOU WANT TO.

import sys
import socket
import string
from time import time, sleep

HOST = "irc.freenode.net"
PORT = 6667
NICK = "nudelgericht"
IDENT = "nudelgericht"
REALNAME = "ὀστρακισμός"
CHANNEL = "#nodrama.de"
VOTEQUOTA = 0.3
WAITTIME = 2  # seconds to wait after each message to avoid flood detection
VOTING_TIMEOUT = 60*3  # seconds a vote is valid
VOTING_MINAGE = 60*3
VOTING_MAXAGE = 60*60*24

s = socket.socket()

s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
s.send("JOIN :%s\r\n" % CHANNEL)


def emit(message):
    s.send("NOTICE " + CHANNEL + " :" + message + "\r\n")
    sleep(WAITTIME)

constituents_firstmessage = {}
constituents_lastmessage = {}

def add_constituent(hostmask):
    global constituents_firstmessage
    global constituents_lastmessage
    if hostmask not in constituents_firstmessage:
        constituents_firstmessage[hostmask] = time()
    constituents_lastmessage[hostmask] = time()

def remove_constituent(hostmask):
    global constituents_firstmessage
    global constituents_lastmessage
    del constituents_firstmessage[hostmask]
    del constituents_lastmessage[hostmask]

def clean_constituents():
    global constituents_lastmessage
    for hostmask in constituents_lastmessage:
        if constituents_lastmessage[hostmask] + VOTING_MAXAGE < time():
            remove_constituent(hostmask)

def get_valid_constituents():
    return [
        hostmask for hostmask in constituents_lastmessage \
            if is_constituent(hostmask)
    ]

def is_constituent(hostmask):
    if constituents_firstmessage[hostmask] + VOTING_MINAGE > constituents_lastmessage[hostmask]:
        return True
    return False

votes = {}

def add_vote(target, votetype, origin):
    global votes
    votetime = time()
    try:
        votes[target][votetype][origin] = votetime
    except KeyError:
        try:
            votes[target][votetype] = { origin: votetime }
        except KeyError:
            try:
                votes[target] = { votetype: { origin: votetime } }
            except KeyError:
                votes = { target: { votetype: { origin: votetime } } }

def clean_votes():
    global votes
    for target in votes:
        for votetype in target:
            for origin in votetype:
                votetime = votes[target][votetype][origin]
                if votetime + TIMEOUT < time():
                    del votes[target][votetype][origin]
    print  votes

def execute():
    global votes
    for target in votes:
        for votetype in target:
            print target, votes[target][votetype]
            # raise NotImplementedError

kick = lambda user: s.send("KICK " + CHANNEL + " " + user + "\r\n")
ban = lambda user: s.send("MODE " + CHANNEL + " +b " + user + "!*@*\r\n")

op = lambda user: s.send("MODE " + CHANNEL + " +o " + user + "\r\n")
deop = lambda user: s.send("MODE " + CHANNEL + " -o " + user + "\r\n")

identity = lambda hostmask: hostmask.split("!")[1]

readbuffer = ''

while True:
    readbuffer = readbuffer + s.recv(1024)
    temp = string.split(readbuffer, '\n')
    readbuffer = temp.pop()

    execute()
    clean_constituents()
    clean_votes()

    for line in temp:
        line = string.rstrip(line)
        line = string.split(line)
        print line

        messagetype = line[1]

        if (line[0] == "PING"):
            s.send("PONG %s\r\n" % messagetype)
            continue

        elif messagetype in ("PART", "JOIN"):
            s.send("NAMES %s\r\n" % (CHANNEL))

        elif messagetype == "PRIVMSG":
            hostmask = identity(line[0][1:])
            add_constituent(hostmask)

            channel = line[2]
            if channel != CHANNEL:
                continue

            command = line[3][1:]
            try:
                argument = line[4]
            except IndexError:
                argument = ''

            if command == '!info':
                emit("Gültigkeit einer Stimme: %s Sekunden. Volk: %s" % \
                    (VOTING_TIMEOUT, get_valid_constituents()))

            elif command == '!gegen':
                if is_constituent(user):
                    add_vote(argument, 'gegen', hostmask)
                else:
                    emit("%s ist nicht wahlberechtigt." % hostmask)

            elif command == '!für':
                if is_constituent(user):
                    add_vote(argument, 'für', hostmask)
                else:
                    emit("%s ist nicht wahlberechtigt." % hostmask)
