#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is free software; you can redistribute it and/or modify it under
# the terms of the new BSD License.
#
# Copyright (c) 2013 Sebastian Staudt


from __future__ import absolute_import, division

import datetime
import json
import re
import urllib2
import xml.etree.ElementTree as ET
import HTMLParser

from ..errors import SteamCondenserError
from .webapi import WebApi


class SteamGame(object):
    """Class to represent a game available on Steam"""

    def __init__(self, app_id, game_data):
        """Create a new SteamGame with the specified parameters

        Parameters:
            app_id: The integer application ID for this game
            game_data: A dict containing the data for this game
        """
        self.app_id = app_id
        if 'name' in game_data:
            self.icon_hash = game_data['img_icon_url']
            self.logo_hash = game_data['img_logo_url']
            self.name = game_data['name']
        else:
            url_regex = u'/%d/([0-9a-f])+.jpg' % app_id
            self.icon_hash = re.match(url_regex, game_data['gameIcon']
                                      ).group(1)
            self.logo_hash = re.match(url_regex, game_data['gameLogo']
                                      ).group(1)
            self.name = game_data['gameName']
            self.short_name = game_data['gameFriendlyName'].lower()
            if self.short_name == str(self.app_id):
                self.short_name = None


class SteamGroup(object):
    """Class to represent a group in the Steam Community

    Attributes:
        custom_url: A string containing the custom URL of this group
        members: A list of SteamIds that belong to this group (read-only)
        group_id64: An integer containing the 64-bit group ID number
    """

    def __init__(self, gid):
        """Construct a new SteamGroup instance

        Parameters:
            gid: Either a string containing the custom URL of the specified
                group, or an integer containing the 64-bit group ID number
        """
        if isinstance(gid, int):
            self.group_id64 = gid
            self.custom_url = ''
        elif isinstance(gid, str):
            self.group_id64 = 0
            self.custom_url = gid.lower()
        else:
            raise TypeError('unexpected type for parameter gid')
        self._members = None

    @property
    def members(self):
        """Return the members of this group

        If the members haven't been fetched yet, this is done now.
        """
        if self._members is None:
            self._fetch()
        return self._members

    def _base_url(self):
        if not self.custom_url:
            return u"http://steamcommunity.com/gid/%d" % self.group_id64
        else:
            return u"http://steamcommunity.com/groups/%s" % self.custom_url

    def _fetch(self):
        """Fetch the member listing of this group

        Parameters:
            page: An integer value for the page number to fetch (optional)

        Raises:
            SteamCondenserError: An error occured
        """
        url = "%s/memberslistxml/?xml=1" % (self._base_url())
        xml = ''
        try:
            xml = urllib2.urlopen(url).read()
        except urllib2.HTTPError, e:
            if e.code == 503:
                raise SteamCondenserError('the Steam Community service is '
                                          'temporarily unavailable')
            raise e
        root = ET.fromstring(xml)
        self._members = []
        for id64 in root.iter('steamID64'):
            self._members.append(SteamId(int(id64.text)))


class SteamId(object):
    """Class to represeent a Steam Community profile (also called a  Steam ID)

    Attributes:
        custom_url: A string containing the custom URL of this group
        groups: A list of SteamGroups that this user belongs to
        headline: A string containing the profile headline specified by this
            user
        hours_played: A float containing the number of hours that this user has
            played recently
        links: A list of 2-tuples in the form (str, str) containing the title
            and url (respectively) of links that this user has added to his or
            her Steam profile
        location: A string containing the location of this user
        member_since: A datetime containing the date of registration for the
            Steam account belonging to this SteamId
        most_played_games: A list of 2-tuples in the form (str, float)
            containing the title and number of hours played in the last 2 weeks
            (respectively) for games that have been played by this user
        nickname: A string containing the Steam nickname of this user
        privacy_state: A string containing the privacy state for this user
        real_name: A string containing the real name of this user
        state_message: A string containing the online state of this user
        steam_id64: An integer containing the 64-bit Steam ID number for
            this user
        steam_rating: A float containing the Steam rating for this user
        summary: A string containing this user's profile summary
        trade_ban_state: A string containing this user's tradeing ban state
        vac_banned: A boolean containing this user's VAC banned state
        visibility_state: A string containing this user's visibility state
    """

    _friends = None
    _games = None
    _recent_playtimes = None
    _total_playtimes = None

    def __init__(self, steam_id):
        """Create a new SteamId instance

        Parameters:
            steam_id: Either a string containing the custom URL for a Steam
                Community profile, a string containing a SteamID as used on
                servers, e.g. 'STEAM_0:0:12345', or an integer containing a
                64-bit Steam ID64
        """
        self.custom_url = ''
        if isinstance(steam_id, int):
            self.steam_id64 = steam_id
        elif isinstance(steam_id, str):
            try:
                self.steam_id64 = self.steam_id_to_community_id(steam_id)
            except SteamCondenserError:
                self.steam_id64 = None
                self.custom_url = steam_id.lower()
        else:
            raise TypeError('unexpected type for steam_id')

    @classmethod
    def community_id_to_steam_id(cls, community_id):
        """Convert a 64-bit numeric Steam ID64 to a String SteamID as used
        by game servers

        Parameters:
            community_id: An integer Steam ID64

        Returns:
            The converted Steam ID, e.g. 'STEAM_0:0:12345'
        """
        if not isinstance(community_id, int):
            raise TypeError('expected integer value for community_id')
        universe = (community_id & 0xff00000000000000) >> 56
        parity = community_id % 2
        id_number = (community_id & 0xffffffff - parity) // 2
        return u'STEAM_%d:%d:%d' % (universe, parity, id_number)

    @classmethod
    def steam_id_to_community_id(cls, steam_id):
        """Convert a string SteamID as used by game servers to a 64-bit
        integer Steam ID64

        Parameters:
            steam_id: The SteamID string, e.g. 'STEAM_0:0:12345'

        Returns:
            An integer containing the 64-bit Steam ID64

        Raises:
            SteamCondenserError: The specified steam_id was invalid
        """
        if not isinstance(steam_id, str):
            raise TypeError('expected string for steam_id')
        if steam_id == u'STEAM_ID_LAN' or steam_id == u'BOT':
            raise SteamCondenserError('cannot convert Steam ID "%s" to a '
                                      'community ID' % steam_id)
        # in steam-condenser-ruby the regexes only use [0-1] for acceptable
        # unvierse values, but according to the Valve dev wiki [0-5] are all
        # valid
        steam_pattern = u''.join([
            ur'STEAM_(?P<universe>[0-5]):(?P<parity>\d+):',
            ur'(?P<id_number>\d+)',
        ])
        brace_pattern = u''.join([
            ur'[(?P<universe>[0-5]):(?P<parity>\d+):',
            ur'(?P<id_number>\d+)]',
        ])
        match = re.match(steam_pattern, steam_id)
        if not match:
            match = re.match(brace_pattern, steam_id)
        if not match:
            raise SteamCondenserError('invalid Steam ID "%s"' % steam_id)
        community_id = int(match.groupdict()['id_number']) * 2
        community_id += int(match.groupdict()['parity'])
        community_id |= 1 << 32     # instance number (always 1)
        community_id |= 1 << 52     # ID type (1: individual)
        community_id |= int(match.groupdict()['universe']) << 56
        return community_id

    @classmethod
    def resolve_vanity_url(cls, url):
        """Resolve a vanity URL for a Steam Community profile to a 64-bit
        Steam ID64 value

        Parameters:
            url: A string containing the vanity URL for a Steam Community
                profile

        Returns:
            An integer containing a Steam ID64 or None if the resolution failed
        """
        data = WebApi.json('ISteamUser', 'ResolveVanityURL', 1, vanityurl=url)
        response = json.loads(data)['response']
        if response['success'] == 1:
            return response['steamid']
        else:
            return None

    @classmethod
    def from_steam_id(cls, steam_id):
        """Create a new SteamId instance from a string SteamID as used on
        servers

        Parameters:
            steam_id: A string containing the SteamID, e.g. 'STEAM_0:0:12345'

        Returns:
            A new SteamId
        """
        return cls.steam_id_to_community_id(steam_id)

    def _base_url(self):
        """Return the base URL for this Steam ID"""
        if self.custom_url:
            return "http://steamcommunity.com/id/%s" % self.custom_url
        else:
            return "http://steamcommunity.com/profiles/%d" % self.steam_id64

    def fetch(self):
        """Fetch data from the Steam Community by querying the XML version of
        the profile specified by this Steam ID

        Raises:
            SteamCondenserError: The Steam Community data is unavailable, e.g.
                the data is private
        """
        url = "%s?xml=1" % (self._base_url())
        xml = ''
        try:
            xml = urllib2.urlopen(url).read()
        except urllib2.HTTPError, e:
            if e.code == 503:
                raise SteamCondenserError('the Steam Community service is '
                                          'temporarily unavailable')
            raise e
        root = ET.fromstring(xml)
        error = root.find('error')
        if error:
            raise SteamCondenserError(error.text)
        self._set_public_fields(root)
        if self.public:
            self._set_hidden_fields(root)

    def _set_public_fields(self, root):
        """Set public profile fields from the specified ElementTree"""
        parser = HTMLParser.HTMLParser()
        self.nickname = parser.unescape(root.find('steamID').text)
        self.steam_id64 = int(root.find('steamID64').text)
        self.limited = bool(int(root.find('isLimitedAccount').text))
        self.trade_ban_state = root.find('tradeBanState').text
        self.vac_banned = bool(int(root.find('vacBanned').text))
        self.image_url = root.find('avatarIcon').text[:-5]
        self.online_state = root.find('onlineState').text
        self.privacy_state = root.find('privacyState').text
        self.state_message = root.find('stateMessage').text
        self.visibility_state = int(root.find('visibilityState').text)

    def _set_hidden_fields(self, root):
        """Set hidden profile fields from the specified ElementTree"""
        parser = HTMLParser.HTMLParser()
        custom_url = root.find('customURL')
        if custom_url:
            self.custom_url = custom_url.text.lower()
        else:
            self.custom_url = ''
        headline = root.find('headline')
        if headline:
            self.headline = parser.unescape(root.find('headline').text)
        else:
            self.headline = ''
        self.hours_played = float(root.find('hoursPlayed2Wk').text)
        self.location = root.find('location').text
        self.member_since = datetime.utcfromtimestamp(
            root.find('memberSince').text)
        realname = root.find('realname')
        if realname:
            self.real_name = parser.unescape(realname)
        else:
            self.real_name = ''
        self.steam_rating = float(root.find('steamRating').text)
        summary = root.find('summary')
        if summary:
            self.summary = parser.unescape(summary.text)
        else:
            self.summary = ''
        self.most_played_games = []
        for game in root.iter('mostPlayedGames'):
            name = game.find('gameName').text
            hours_played = float(game.find('hoursPlayed').text)
            self.most_played_games.append((name, hours_played))
        self.groups = []
        for group in root.iter('groups'):
            self.groups.append(SteamGroup(int(group.find('groupID64').text)))
        self.links = []
        for link in root.iter('weblinks'):
            title = parser.unescape(link.find('title').text)
            url = link.find('link').text
            self.links.append((title, url))

    def _fetch_friends(self):
        """Fetch the friends of this user

        Returns:
            A list of the SteamId's of this 's friends
        """
        friends_data = WebApi.json('ISteamUser', 'GetFriendList', 1,
                                   relationship='friend',
                                   steamid=self.steam_id64)
        friends_data = json.loads(friends_data)
        self._friends = []
        for friend in friends_data['friendslist']['friends']:
            self.friends.append(SteamId(int(friend['steamid'])))
        return self._friends

    def _fetch_games(self):
        """Fetch the list of games that this user owns

        Returns:
            A dict of games that this user owns
        """
        games_data = WebApi.json('IPlayerService', 'GetOwnedGames', 1,
                                 include_appinfo=1,
                                 include_played_free_games=1,
                                 steamid=self.steam_id64)
        games_data = json.loads(games_data)
        self._games = {}
        self._recent_playtimes = {}
        self._total_playtimes = {}
        for game in games_data['response']['games']:
            app_id = game['appid']
            self._games[app_id] = SteamGame(app_id, game)
            if 'playtime_2weeks' in game:
                self._recent_playtimes[app_id] = game['playtime_2weeks']
            else:
                self._recent_playtimes[app_id] = 0
            if 'playtime_forever' in game:
                self._total_playtimes[app_id] = game['playtime_forever']
            else:
                self._total_playtimes[app_id] = 0
        return self._games

    def game_stats(self, game_id):
        """Return the stats for the specified game

        Parameters:
            game_id: Either a string containing the full or short name for the
                game, or the game's integer application ID

        Returns:
            The statistics for the specified game

        Raises:
            SteamCondenserError: The user does not own the specified game or
                it has no stats
        """
        game = self._find_game(game_id)
        if not game.has_stats:
            raise SteamCondenserError('%s does not have stats' % game.name)
        return GameStats.create_game_stats(self.id, game.short_name)

    @property
    def friends(self):
        if self._friends is None:
            return self._fetch_friends()
        else:
            return self._friends

    @property
    def games(self):
        if self._games is None:
            return self._fetch_games()
        else:
            return self._games

    @property
    def full_avatar_url(self):
        """Return the URL of the full-sized version of this user's avatar"""
        return "%s_full.jpg" % self.image_url

    @property
    def medium_avatar_url(self):
        """Return the URL of the medium-sized version of this user's avatar"""
        return "%s_medium.jpg" % self.image_url

    @property
    def icon_url(self):
        """Return the URL of the icon version of this user's avatar"""
        return "%s.jpg" % self.image_url

    @property
    def id(self):
        """Return a unique identifier for this steam ID

        This is either the 64-bit Steam ID64 or the custom URL
        """
        if self.custom_url:
            return self.custom_url
        else:
            return self.steam_id64

    @property
    def in_game(self):
        """Return whether or not this user is playing a game"""
        return self.online_state == 'in-game'

    @property
    def online(self):
        """Return whether or not this user is online"""
        return self.online_state != 'offline'

    @property
    def public(self):
        """Return whether or not this Steam ID is publicly accessible"""
        return self.privacy_state == 'public'

    def recent_playtime(self, game_id):
        """Return the time in minutes that this user has played the specified
        game in the last two weeks

        Parameters:
            game_id: Either the string full or short name for the game, or the
                integer application ID

        Returns:
            An integer containing the number of minutes this user played the
            specified game over the last two weeks
        """
        game = self._find_game(game_id)
        return self.recent_playtimes[game.app_id]

    def total_playtime(self, game_id):
        """Return the time in minutes that this user has played the specified
        game

        Parameters:
            game_id: Either the string full or short name for the game, or the
                integer application ID

        Returns:
            An integer containing the total number of minutes this user played
            the specified game over the last two weeks
        """
        game = self._find_game(game_id)
        return self.total_playtimes[game.app_id]

    def _find_game(self, game_id):
        """Find a game instance with the specified application ID, full name
        or short name

        Parameters:
            game_id: Either the string full or short name for a game or the
                integer application ID

        Returns: The SteamGame for the specified game ID

        Raises:
            SteamCondenserError: The user does not own the game or the game
                does not exist
        """
        if isinstance(game_id, int):
            return self.games[game_id]
        else:
            for game in self.games.values():
                if game.short_name == game_id or game.name == id:
                    return game
        raise SteamCondenserError('This SteamID does not own the game '
                                  '%s' % game_id)
