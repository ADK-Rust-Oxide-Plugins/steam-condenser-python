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
import urllib
import urllib2

from .errors import WebApiError


class AppNews(object):
    """Class to represent Steam news and can be used to load a list of current
    news about specific games.

    Attributes:
        app_id: The integer value of the unique Steam Application ID of the
            game (e.g. ``440`` for Team Fortress 2). See
            <http://developer.valvesoftware.com/wiki/Steam_Application_IDs>
            for all application IDs
        author: A string containing the author of this news. *This may
            contain HTML code.*
        contents: A string containing the contents of this news.
        date: A datetime object containing the date this news item has been
            published
        feed_label: A string containing the symbolic name of the feed this
            news item belongs to
        feed_name: A string containing the symbolic name of the feed this news
            item belongs to
        gid: An integer containing a unique identifier for this news item
        title: A string containing the title of this news item
        url: A string containing the original URL for this news item
    """

    def __init__(self, app_id, news_data):
        """Construct a new AppNews object

        Args:
            app_id: The application ID of the game
            news_data: The news data extracted from JSON
        """
        self.app_id = app_id
        self.author = news_data['author']
        self.contents = news_data['contents'].strip()
        self.date = datetime.utcfromtimestamp(news_data['date'])
        self.external = news_data['is_external_url']
        self.feed_label = news_data['feedlabel']
        self.feed_name = news_data['feedname']
        self.gid = news_data['gid']
        self.title = news_data['title']
        self.url = news_data['url']

    @classmethod
    def news_for_app(cls, app_id, count=5, max_length=None):
        """Load the news for the specified game

        Args:
            app_id: The application ID of the game

        Returns:
            A list of AppNews items for the specified game
        """
        data = WebApi.json('ISteamNews', 'GetNewsForApp', 2, appid=app_id,
                           count=count, maxlength=max_length)
        news_data = json.loads(data)
        news_items = []
        for item in news_data['appnews']['newsitems']:
            news_items.append(AppNews(app_id, news_data))
        return news_items

    def __unicode__(self):
        return u"%s: %s" % (self.feed_label, self.title)

    def __str__(self):
        return unicode(self).encode('utf-8')


class WebApi(object):
    """Class that provides functionality to access Steam's Web API

    The Web API requires you to register a domain with your Steam account
    to acquire an API key. See <http://steamcommunity.com/dev> for further
    details.

    Attributes:
        api_key: The 128bit API key as a hexidecimal string
    """

    _api_key = None

    class __metaclass__(type):
        @property
        def api_key(cls):
            """Return the global Steam Web API Key for this steam-condenser
            session
            """
            return cls._api_key

        @api_key.setter
        def api_key(cls, api_key):
            """Set the global Steam Web API key for this steam-condenser
            session

            Parameters:
                api_key: The 128bit API key as a hexidecimal string

            Raises:
                WebApiError: The specified API key is invalid
            """
            if re.match(r'^[0-9A-F]{32}$', api_key.upper()):
                cls._api_key = api_key.upper()
            else:
                raise WebApiError('invalid key')

    @classmethod
    def interfaces(cls):
        """Return a raw list of interfaces and their methods that are
        available in Steam's Web API

        This can be used for reference when accessing interfaces and methods
        that have not yet been implemented by steam-condenser.

        Returns:
            A 2-tuple containing a list of interfaces a list of methods
        """
        data = cls.json('ISteamWebAPIUtil', 'GetSupportedAPIList')
        loaded_data = json.loads(data)
        return (loaded_data['apilist'], loaded_data['interfaces'])

    @classmethod
    def json(cls, interface, method, version=1, **kwargs):
        """Fetches JSON data from the Steam Web API using the specified
        parameters.

        Parameters are the same as in WebApi.get()

        Returns:
            A string containing the raw JSON data returned by the request
        """
        return cls.get('json', interface, method, version, **kwargs)

    @classmethod
    def get(cls, fmt, interface, method, version=1, **kwargs):
        """Fetch data from the Steam Web API using the specified interface,
        method and version.

        Additional parameters to the HTTP GET request can be supplied via
        **kwargs.

        Parameters:
            fmt: The format to load from the API: 'json', 'vdf' or 'xml'
            interface: The Web API interface to call, e.g. 'ISteamUser'
            method: The Web API method to call, e.g. 'GetPlayerSummaries'
            version: The API method version to use
            **kwargs: Any additional parameters to specify in the HTTP GET
                request

        Returns:
            A string containing the data returned by the Web API

        Raises:
            WebApiError: A Web API error occured
        """
        url = 'http://api.steampowered.com/%s/%s/v%04d/' % (interface, method,
                                                            version)
        params = {
            'format': fmt,
            'key': cls.api_key
        }
        params.update(kwargs)
        try:
            return urllib2.urlopen(url, urllib.urlencode(params)).read()
        except urllib2.HTTPError, e:
            raise WebApiError(e.reason)
