#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is free software; you can redistribute it and/or modify it under
# the terms of the new BSD License.
#
# Copyright (c) 2013 Sebastian Staudt


from __future__ import absolute_import, division

import datetime
import json

from .errors import SteamCondenserError
from .steam import SteamId
from .webapi import WebApi


class GameAchievement(object):
    """Class to represent a specific achievement for a single game and a
    single user

    It also provides the ability to load the global unlock percentages of all
    achievements for a specific game

    Attributes:
        api_name: The string API name of this achievement
        description: The string description for this achievement
        game: The SteamGame that this achievement belongs to
        icon_closed_url: The string URL of the closed achievement icon
        icon_open_url: The string URL of the oepn achievement icon
        name: The string name of this achievement
        timestamp: A datetime containing the time that this achievement was
            unlocked
        user: The SteamId of this achievement's owner
    """

    def __init__(self, user, game, achievement_data):
        """Create a new GameAchievement with the specified parameters

        Parameters:
            user: The SteamId for the player that this achievement belongs to
            game: The SteamGame for the game that this achievement belongs to
            achievement_data: A dict containing the achievement data extracted
                from the Steam API XML
        """
        self.api_name = achievement_data['apiname']
        self.description = achievement_data['description']
        self.game = game
        self.icon_closed_url = achievement_data['iconClosed']
        self.icon_open_url = achievement_data['iconOpen']
        self.name = achievement_data['name']
        self.unlocked = achievement_data['closed']
        self.user = user
        if self.unlocked and achievement_data['unlockTimestamp']:
            self.timestamp = datetime.utcfromtimestamp(
                achievement_data['unlockTimestamp'])
        else:
            self.timestamp = None

    @classmethod
    def global_percentages(cls, app_id):
        """Return the global unlock percentages of all achievements for the
        specified game

        Parameters:
            app_id: The Steam application ID of the game (e.g. `440` for
                Team Fortress 2)

        Returns:
            A list of 2-tuples of the form (str, float) containing the string
            achievement names and their corresponding unlock percentages
            respectively

        Raises:
            WebApiError: The request to the Steam Web API failed
        """
        data = WebApi.json('ISteamUserStats',
                           'GetGlobalAchievementPercentagesForApp', 2,
                           gameid=app_id)
        data = json.loads(data)
        percentages = []
        for achievement in data['achievementpercentages']['achievements']:
            percentages.append((achievement['name'], achievement['percent']))
        return percentages


class GameItem(object):
    """Class representing an item in a game

    Attributes:
        attributes: This item's attributes
        backpack_position: The integer index of this item's position in an
            inventory
        count: The integer number of the quantity that the player owns of this
            item
        defindex: The index where this item is defined in an item schema
        id: The integer ID of this item
        inventory: The GameInventory that this item belongs to
        item_class: The class of this item
        item_set: The item set that this item belongs to
        level: The level of this item
        name: The string name of this item
        origin: The string origin of this item
        original_id: The integer original ID of this item
        quality: The string quality of this item
        type: The string type of this item
    """

    def __init__(self, inventory, item_data):
        """Construct a new GameItem instance

        Parameters:
            inventory: The GameInventory this item belongs to
            item_data: A dict containing the data representing this item
        """
        self.inventory = inventory
        self.defindex = item_data['defindex']
        self.backpack_position = item_data['inventory'] & 0xffff
        self.count = item_data['quantity']
        self.craftable = not item_data['flag_cannot_craft']
        self.id = item_data['id']
        self.item_class = self.schema_data['item_class']
        self.item_set = inventory.item_schema.item_sets[
            self.schema_data['item_set']]
        self.level = item_data['level']
        self.name = self.schema_data['name']
        self.original_id = item_data['original_id']
        self.preliminary = bool(item_data['inventory'] & 0x40000000)
        self.quality = inventory.item_schema.qualities[item_data['quality']]
        self.tradeable = not item_data['flag_cannot_trade']
        self.type = self.schema_data['item_type_name']
        if 'origin' in item_data:
            self.origin = inventory.item_schema.origins[item_data['origin']]
        else:
            self.origin = None
        attributes_data = self.schema_data['attributes']
        if 'attributes' in item_data:
            attributes_data.extend(item_data['attributes'])
        self.attributes = []
        for data in attributes_data:
            key = data['defindex']
            if not key:
                key = data['name']
            if key:
                schema_attribute_data = inventory.item_schema.attributes[key]
                self.attributes.append(data.update(schema_attribute_data))

    @property
    def schema_data(self):
        """Return the data for this item that is defined in the item schema"""
        return self.inventory.item_schema.items[self.defindex]


class GameItemSchema(object):
    """Class that provides item definitions and related data that specify the
    items for a game

    Attributes:
        attributes: A dict containing this schema's attributes
        effects: A dict containing the available effects for this game's items
        item_levels: A dict containing this item schema's item levels
        item_names: A dict containing a mapping of item names to object types
        item_sets: A dict containing this item schema's item sets
        items: A dict containing the items in this schema
        language: A string containing the language of this item schema
        origins: A list of strings containing the item origins defined for this
            game
        qualtiies: A list of strings containing this this item schema's
            defined qualties
    """

    def __init__(self, app_id, language=None):
        """Construct a new GameItemSchema instance

        Parameters:
            app_id: The integer application ID for this game
            lanugage: A string containing the language of description strings
                for this schema
        """
        self.app_id = app_id
        self.language = language

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode___(self):
        s = [u'%s: %d (%s) - ' % (self.__class__.__name__, self.app_id,
                                  self.language)]
        if self.fetch_time:
            s.append(u'%s', unicode(self.fetch_time))
        else:
            s.append(u'not fetched')
        return u''.join(s)

    def fetch(self):
        """Update the item definitions of this schema using the Steam Web=
        API
        """
        if self.language:
            data = WebApi.json('IEconItems_%d' % self.app_id, 'GetSchema', 1,
                               language=self.language)
        else:
            data = WebApi.json('IEconItems_%d' % self.app_id, 'GetSchema', 1)
        data = json.loads(data)['result']
        self.attributes = []
        for attribute in data['attributes']:
            self.attributes[attribute['defindex']] = attribute
            self.attributes[attribute['name']] = attribute
        self.effects = []
        for effect in data['attribute_controlled_attached_particles']:
            self.effects[effect['id']] = effect['name']
        self.items = []
        self.item_names = []
        for item in data['items']:
            self.items[item['defindex']] = item
            self.item_names[item['name']] = item['defindex']
        self.item_levels = {}
        if 'item_levels' in data:
            for item_level_type in data['item_levels']:
                self.item_levels[item_level_type['name']] = {}
                for level in item_level_type['levels']:
                    self.item_levels[item_level_type['name']][level['level']] \
                        = level['name']
        self.item_sets = {}
        for item_set in data['item_sets']:
            self.item_sets[item_set['item_set']] = item_set
        self.origins = []
        for origin in data['originNames']:
            self.origins[origin['origin']] = origin['name']
        self.qualities = []
        for key, index in enumerate(data.keys()):
            self.qualities[index] = data['qualityNames'][unicode(key).upper()]

    def inspect(self):
        """Return a short human-readable string representation of this item
        schema
        """
        return unicode(self)


class GameInventory(object):
    """Class to represent an inventory of a player in a game

    Attributes:
        app_id: The integer application ID of the game
        items: A list of all GameItems in this player's inventory
        preliminary_items: A list of all GameItems that this player just found
            or traded
        user: The SteamId of the player that owns this inventory
    """

    item_class = GameItem
    schema_language = 'en'

    def __init__(self, app_id, steam_id64):
        """Construct a new GameInventory for the specified application and
        Steam ID64

        Parameters:
            app_id: The integer application ID for the game
            steam_id64: The integer 64bit SteamID of the player
        """

        if isinstance(steam_id64, str):
            steam_id64 = SteamId.resolve_vanity_url(steam_id64)
            if not steam_id64:
                raise SteamCondenserError('user not found')
        self.app_id = app_id
        self.items = []
        self.steam_id64 = steam_id64
        self.user = SteamId(steam_id64, False)

    def __getitem__(self, index):
        return self.items[index]

    def __len__(self):
        return len(self.items)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        s = [u'%s: %d %d (%d items) - ' % (self.__class__.__name__,
                                           self.app_id, self.steam_id64,
                                           len(self))]
        if self.fetch_time:
            s.append(unicode(self.fetch_time))
        else:
            s.append(u'not fetched')
        return u''.join(s)

    def fetch(self):
        """Update the contents of this inventory using the Steam Web API"""
        data = WebApi.json('IEconItems_%d' % self.app_id, 'GetPlayerItems', 1,
                           SteamID=self.user.steam_id64)
        result = json.loads(data)['result']
        item_class = self.item_class
        self.items = []
        self.preliminary_items = []
        for item_data in result['items']:
            item = item_class.new(item_data)
            if item.preliminary:
                self.preliminary_items.append(item)
            else:
                self.items[item.backpack_position - 1] = item

    def inspect(self):
        """Return a short human-readable representation of this inventory"""
        return unicode(self)

    def item_schema(self):
        """Return the item schema for this inventory"""
        return GameItemSchema.new(self.app_id, self.schema_language)

    def size(self):
        """Return the number of items in this inventory"""
        return len(self)

    @classmethod
    def new(cls, app_id, steam_id=None, *args, **kwargs):
        """Wrap all subclasses of GameInventory so that an instance of the
        correct subclass is returned for the specified application ID. If
        no subclass for the specified application exists, a generic instance
        of GameInventory is created

        Parameters:
            app_id: The integer application ID of the game
            steam_id: The integer Steam ID64 or string vanity URL of the user

        Returns:
            A new GameInventory instance for the specified user and game

        Raises:
            SteamCondenserError: Creating the inventory failed
        """
        subclasses = {
            # Add new subclasses here
        }
        try:
            return subclasses[app_id](*args, **kwargs)
        except KeyError:
            return GameInventory(*args, **kwargs)
