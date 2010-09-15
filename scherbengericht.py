#!/usr/bin/python
# -*- coding: utf-8 -*-

# Python IRC bot
# based on <http://web.archive.org/web/20070226174611/http://gfxfor.us/general/tutorial-how-to-make-a-simple-irc-bot-from-scratch-in-python>

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
import time

HOST        = "irc.freenode.net"
PORT        = 6667
NICK        = "scherbengericht"
IDENT       = "scherbengericht"
REALNAME    = "ὀστρακισμός"
CHANNEL     = "#twitter.de"
VOTEQUOTA   = 0.3
WAITTIME    = 2 # seconds to time.sleep() after each message so flood detection is not triggered

s = socket.socket()

s.connect((HOST, PORT))
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
s.send("JOIN :%s\r\n" % CHANNEL)

sendchannel = lambda message: s.send("PRIVMSG " + CHANNEL + " :" + message + "\r\n") and time.sleep(WAITTIME)

kick = lambda user: s.send("KICK " + CHANNEL + " " + user + "\r\n")
ban = lambda user: s.send("MODE " + CHANNEL + " +b " + user + "!*@*\r\n")

op = lambda user: s.send("MODE " + CHANNEL + " +o " + user + "\r\n")
deop = lambda user: s.send("MODE " + CHANNEL + " -o " + user + "\r\n")

readbuffer = ""

hatevotes = {}
lovevotes = {}

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
            users = line[6:]
            print "%d other users in channel %s." % (len(users), CHANNEL)

        # provide information about voting requirements
        if (line[1] == "PRIVMSG") and (line[2] == CHANNEL) and (line[3][1:] == "!info"):
            sendchannel("Das Scherbengericht verbannt bzw. ernennt zum König, wer von %d oder mehr der Anwesenden gewählt wird." % (int(len(users)*VOTEQUOTA)))

        if (line[1] == "PRIVMSG") and (line[2] == CHANNEL) and (len(line) >= 5):
            user = line[0]
            command = line[3][1:]
            target = line[4]

            if (command == "!gegen"):
                if target in hatevotes.keys(): # vote pending
                    if user in hatevotes[target]:
                        sendchannel("Du hast bereits gegen %s abgestimmt." % (target))
                    else:
                        hatevotes[target].append(user)
                        sendchannel("Stimme gegen %s gezählt. Noch %d Stimmmen nötig für Bann." % (target, int(len(users)*VOTEQUOTA) - len(hatevotes[target])))

                else: # no vote
                    sendchannel("Abstimmung gegen %s anberaumt. Noch %d Stimmmen nötig für Bann." % (target, int(len(users)*VOTEQUOTA) - 1))
                    hatevotes[target] = [user]

                for nickname in hatevotes.keys():
                    if len(hatevotes[nickname]) >= (int(len(users)*VOTEQUOTA)):
                        if (nickname == NICK):
                            for stupidnick in hatevotes[nickname]:
                                kick(stupidnick)
                            del hatevotes[nickname]
                            sendchannel("GOURANGA!")
                        else:
                            deop(nickname)
                            kick(nickname)
                            ban(nickname)
                            del hatevotes[nickname]

            if (command == "!für" or command == "!fuer" or command == u"!für".encode('latin_1')):
                if target in lovevotes.keys(): # vote pending
                    if user in lovevotes[target]:
                        sendchannel("Du hast bereits für %s abgestimmt." % (target))
                    else:
                        lovevotes[target].append(user)
                        sendchannel("Stimme für %s gezählt. Noch %d Stimmen nötig für OP.\r\n" % (target, int(len(users)*VOTEQUOTA) - len(lovevotes[target])))

                else:
                    sendchannel("Abstimmung für %s anberaumt. Noch %d Stimmmen nötig für OP." % (target, int(len(users)*VOTEQUOTA) - 1))
                    lovevotes[target] = [user]

                for nickname in lovevotes.keys():
                    if len(lovevotes[nickname]) >= (int(len(users)*VOTEQUOTA)):
                        op(nickname)
                        del lovevotes[nickname]
