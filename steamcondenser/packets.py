#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is free software; you can redistribute it and/or modify it under
# the terms of the new BSD License.
#
# Copyright (c) 2013 Sebastian Staudt


from __future__ import absolute_import, division

import struct
from socket import inet_ntoa

from .errors import PacketFormatError


class SteamPacket(object):
    """Base Steam packet class

    Implements the basic functionality for most of the packets used in
    communication with master, Source or GoldSrc severs.
    """

    A2M_GET_SERVERS_BATCH2_HEADER = 0x31
    A2S_INFO_HEADER = 0x54
    A2S_PLAYER_HEADER = 0x55
    A2S_RULES_HEADER = 0x56
    A2S_SERVERQUERY_GETCHALLENGE_HEADER = 0x57
    C2M_CHECKMD5_HEADER = 0x4D
    M2A_SERVER_BATCH_HEADER = 0x66
    RCON_GOLDSRC_CHALLENGE_HEADER = 0x63
    RCON_GOLDSRC_NO_CHALLENGE_HEADER = 0x39
    RCON_GOLDSRC_RESPONSE_HEADER = 0x6C
    S2A_INFO_DETAILED_HEADER = 0x6D
    S2A_INFO2_HEADER = 0x49
    S2A_PLAYER_HEADER = 0x44
    S2A_RULES_HEADER = 0x45
    S2C_CONNREJECT_HEADER = 0x39
    S2C_CHALLENGE_HEADER = 0x41

    def __init__(self, header_data, content_data=''):
        """Create a new SteamPacket based on the given parameters

        Parameters:
            header_data: The packet header
            content_data: The raw packet data
        """
        self.content_data = unicode(content_data)
        self.header_data = header_data

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return struct.pack('!IBs', 0xFFFFFFFF, self.header_data,
                           self.content_data)


class A2MGetServersBatch2Packet(SteamPacket):
    """This packet represents a A2M_GET_SERVERS_BATCH2 request sent to a
    master server

    It is used to retrieve a list of game servers matching the specified
    filters

    Filtering:
        Instead of filtering the results sent by the master server locally,
        you should at least use the following filters to narrow down the
        results sent by the master server. Retrieving all servers from the
        master server will take a long time.

    Available filters:
        `\\type\\d`: Request only dedicated servers
        `\\secure\\1`: Request only secure servers
        `\\gamedir\\[mod]`: Request only servers running a specific mod
        `\\map\\[mapname]`: Request only servers running a specific map
        `\\linux\\1`: Request only Linux servers
        `\\empty\\1`: Request only *non*-empty servers
        `\\full\\1`: Request only *not*-full servers
        `\\proxy\\1`: Request only spectator proxy servers
    """

    def __init__(self, region_code=0xFF, start_ip='0.0.0.0:0', filter=''):
        super(A2MGetServersBatch2Packet, self).\
            __init__(SteamPacket.A2M_GET_SERVERS_BATCH2_HEADER)
        self.filter = filter
        self.region_code = region_code
        self.start_ip = start_ip

    def __unicode__(self):
        return struct.pack('!BBss', self.header_data, self.region_code,
                           self.start_ip, self.filter)


class RequestWithChallengePacket(SteamPacket):
    """Class to generate packet data used by requests which send a challenge
    number to a server
    """

    def __unicode__(self):
        return struct.pack('!IBb', 0xFFFFFFFF, self.header_data,
                           int(self.content_data))


class A2SInfoPacket(SteamPacket):
    """Class to represent an A2S_INFO request

    Causes the server to send basic information about itself, e.g. the
    running game, map and number of players.
    """

    def __init__(self):
        super(A2SInfoPacket, self).__init__(SteamPacket.A2S_INFO_HEADER,
                                            u'Source Engine Query\0')


class A2SPlayerPacket(RequestWithChallengePacket):
    """Class to represent an A2S_PLAYER request

    Requests the list of players currently playing on the server. This packet
    type requires the client to challenge the server in advance, which is done
    automatically if required.
    """

    def __init__(self, challenge_number=-1):
        """Create a new A2S_PLAYER request object

        Parameters:
            challenge_number: The integer challenge number received from the
            server
        """
        super(A2SPlayerPacket, self).__init__(SteamPacket.A2S_PLAYER_HEADER,
                                              challenge_number)


class A2SRulesPacket(RequestWithChallengePacket):
    """Class to represent an A2S_RULES request

    Causes the server to return a list of active game rules, e.g.
    `mp_friendlyfire = 1`

    This packet type requires the client to challenge the server in advance
    """

    def __init__(self, challenge_number=-1):
        """Create a new A2S_RULES request object

        Parameters:
            challenge_number: The integer challenge number received from the
            server
        """
        super(A2SRulesPacket, self).__init__(SteamPacket.A2S_RULES_HEADER,
                                             challenge_number)


class A2SServerqueryGetchallengePacket(SteamPacket):
    """Class to represent an A2S_SERVERQUERY_GETCHALLENGE request

    Retrieves a challenge number from the game server, which helps to
    identify the requesting client.
    """

    def __init__(self):
        super(A2SServerqueryGetchallengePacket, self).\
            __init__(SteamPacket.A2S_SERVERQUERY_GETCHALLENGE_HEADER)


class M2AServerBatchPacket(SteamPacket):
    """Class to represent an M2A_SERVER_BATCH response

    Contains a list of IP addresses and ports of game servers matching the
    requested criteria
    """

    def __init__(self, data):
        """Create a new M2A_SERVER_BATCH response object

        Parameters:
            data: The raw packet data replied from the server

        Raises:
            PacketFormatError: The packet data was not well formatted
        """
        super(M2AServerBatchPacket, self).\
            __init__(SteamPacket.M2A_SERVER_BATCH_HEADER, data)
        if ord(self.content_data.pop()) != 0x0A:
            raise PacketFormatError('Master query response is missing'
                                    ' additional 0x0A byte')
        self.servers = []
        data = self.content_data
        while len(data) > 0:
            ip = inet_ntoa(data[:4])
            port = struct.unpack('!H', data[4:2])
            self.ervers.append(u'%s:%d' % ip, port)
            data = data[6:]
