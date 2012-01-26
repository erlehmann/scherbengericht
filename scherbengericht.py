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
NICK = "scherbengericht"
IDENT = "scherbengericht"
REALNAME = "ὀστρακισμός"
CHANNELS = ["#twitter.de", "#nodrama.de"]
VOTEQUOTA = 0.3
WAITTIME = 2  # sec to time.sleep() after each message to avoid flood detection
TIMEOUT = 180  # sec a vote is valid

s = socket.socket()

s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
for channel in CHANNELS:
    s.send("JOIN :%s\r\n" % channel)


def sendchannel(channel, message):
    s.send("PRIVMSG " + channel + " :" + message + "\r\n")
    sleep(WAITTIME)

kick = lambda channel, user: s.send("KICK " + channel + " " + user + "\r\n")
ban = lambda channel, user: s.send("MODE " + channel + " +b " + user + "!*@*\r\n")
unban = lambda channel, user: s.send("MODE " + channel + " -b " + user + "!*@*\r\n")

op = lambda channel, user: s.send("MODE " + channel + " +o " + user + "\r\n")
deop = lambda channel, user: s.send("MODE " + channel + " -o " + user + "\r\n")

identity = lambda hostmask: hostmask.split("!")[1]

readbuffer = ""

hatevotes = {}
hatetimes = {}
lovevotes = {}
lovetimes = {}
users = {}
for channel in CHANNELS:
    hatevotes[channel] = {}
    hatetimes[channel] = []
    lovevotes[channel] = {}
    lovetimes[channel] = []
    users[channel] = []

while True:
    readbuffer = readbuffer + s.recv(1024)
    temp = string.split(readbuffer, "\n")
    readbuffer = temp.pop()

    for line in temp:
        line = string.rstrip(line)
        line = string.split(line)
        print line

        # keep alive
        if (line[0] == "PING"):
            s.send("PONG %s\r\n" % line[1])

        # count users
        if (line[1] == "353"):
            users[line[4]] = line[6:]
            print "%d other users in channel %s." % (len(users[channel]), channel)

        # update user count
        if (line[1] == "PART") or (line[1] == "JOIN"):
            s.send("NAMES %s\r\n" % (line[2]))

        # provide information about voting requirements
        if (line[1] == "PRIVMSG") and (line[2] in CHANNELS) and \
                (line[3][1:] == "!info"):
            sendchannel(line[2], "Das Scherbengericht verbannt bzw. ernennt zum \
König, wer innerhalb von %d Sekunden von %d oder mehr der Anwesenden \
gewählt wird." % (TIMEOUT, int(round(len(users[line[2]]) * VOTEQUOTA))))

        if (line[1] == "PRIVMSG") and (line[2] in CHANNELS) and \
                (len(line) >= 5):
            channel = line[2]
            user = identity(line[0][1:])
            command = line[3][1:]
            target = line[4]

            if (command == "!gegen"):
                if target in hatevotes[channel].keys(): # vote pending
                    if user in hatevotes[channel][target]:
                        sendchannel(channel, "Du hast bereits gegen %s abgestimmt." % \
                                (target))
                    else:
                        hatevotes[channel][target].append(user)
                        hatetimes[channel].append((target, user, time()))
                        difference = int(round(len(users[channel]) * VOTEQUOTA)) - \
                                len(hatevotes[channel][target])
                        if (difference > 0):
                            sendchannel(channel, "Stimme gegen %s gezählt. Noch %d \
Stimmmen nötig für Bann." % (target, difference))
                        else:
                            sendchannel(channel, "Stimme gegen %s gezählt. \
Zuständige Stellen sind verständigt." % (target))

                else: # no vote
                    sendchannel(channel, "Abstimmung gegen %s anberaumt. Noch %d \
Stimmen nötig für Bann." % \
                            (target, int(round(len(users[channel]) * VOTEQUOTA)) - 1))
                    hatevotes[channel][target] = [user]
                    hatetimes[channel].append((target, user, time()))

                for nickname in hatevotes[channel].keys():
                    if len(hatevotes[channel][nickname]) >= \
                            (int(round(len(users[channel]) * VOTEQUOTA))):
                        if (nickname == NICK):
                            for stupidnick in hatevotes[channel][nickname]:
                                kick(channel,stupidnick)
                            del hatevotes[channel][nickname]
                            hatetimes[channel] = filter(lambda t: t[0] != nickname, \
                                    hatetimes[channel])
                            sendchannel(channel,"GOURANGA!")
                        else:
                            deop(channel,nickname)
                            kick(channel,nickname)
                            ban(channel,nickname)
                            del hatevotes[channel][nickname]
                            hatetimes[channel] = filter(lambda t: t[0] != nickname, \
                                    hatetimes[channel])

            if (command == "!für" or command == "!fuer" or \
                    command == u"!für".encode('latin_1')):
                if target in lovevotes[channel].keys(): # vote pending
                    if user in lovevotes[channel][target]:
                        sendchannel(channel,"Du hast bereits für %s abgestimmt." % \
                                (target))
                    else:
                        lovevotes[channel][target].append(user)
                        lovetimes[channel].append((target, user, time()))
                        difference = int(round(len(users[channel]) * VOTEQUOTA)) - \
                                len(lovevotes[channel][target])
                        if (difference > 0):
                            sendchannel(channel,"Stimme für %s gezählt. Noch %d \
Stimmen nötig für OP/Unban." % (target, difference))
                        else:
                            sendchannel(channel,"Stimme für %s gezählt. \
Zuständige Stellen sind verständigt." % (target))

                else:
                    sendchannel(channel,"Abstimmung für %s anberaumt. Noch %d \
Stimmen nötig für OP/Unban." % \
                            (target, int(round(len(users[channel]) * VOTEQUOTA)) - 1))
                    lovevotes[channel][target] = [user]
                    lovetimes[channel].append((target, user, time()))

                for nickname in lovevotes[channel].keys():
                    if len(lovevotes[channel][nickname]) >= \
                            int(round(len(users[channel]) * VOTEQUOTA)):
                        op(channel,nickname)
                        unban(channel,nickname)
                        del lovevotes[channel][nickname]
                        lovetimes[channel] = filter(lambda t: t[0] != nickname, \
                                lovetimes[channel])
            channel = None

    # check timeouts
    for channel in CHANNELS:
        while (len(lovetimes[channel]) > 0) and \
                (lovetimes[channel][0][2] + TIMEOUT < time()):
            target, user, t = lovetimes[channel][0]
            lovevotes[channel][target] = filter(lambda u: u != user, lovevotes[channel][target])
            sendchannel(channel,"Stimme von %s für %s ist abgelaufen. Noch %d \
Stimmen nötig für OP." % (user.partition("!")[0], target, \
                    int(round(len(users[channel]) * VOTEQUOTA)) - len(lovevotes[channel][target])))
            if lovevotes[channel][target] == []:
                del lovevotes[channel][target]
            lovetimes[channel] = lovetimes[channel][1:]

        while (len(hatetimes[channel]) > 0) and \
                (hatetimes[channel][0][2] + TIMEOUT < time()):
            target, user, t = hatetimes[channel][0]
            hatevotes[channel][target] = filter(lambda u: u != user, hatevotes[channel][target])
            sendchannel(channel,"Stimme von %s gegen %s ist abgelaufen. Noch %d \
Stimmmen nötig für Bann." % (user.partition("!")[0], target, \
                    int(round(len(users[channel]) * VOTEQUOTA)) - len(hatevotes[channel][target])))
            if hatevotes[channel][target] == []:
                del hatevotes[channel][target]
            hatetimes[channel] = hatetimes[channel][1:]
