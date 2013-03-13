#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is free software; you can redistribute it and/or modify it under
# the terms of the new BSD License.
#
# Copyright (c) 2013 Sebastian Staudt


from mock import Mock
from nose.tools import assert_equal, raises
from steamcondenser.community import WebApi, WebApiError

import __builtin__
import urllib
import urllib2


class TestWebApi(object):
    """Class to test WebApi"""

    @classmethod
    def setup_class(cls):
        WebApi.api_key = '0123456789ABCDEF0123456789ABCDEF'

    def test_get_api_key(self):
        assert_equal('0123456789ABCDEF0123456789ABCDEF', WebApi.api_key)

    def test_set_api_key(self):
        WebApi.api_key = 'FEDCBA9876543210FEDCBA9876543210'
        assert_equal('FEDCBA9876543210FEDCBA9876543210', WebApi.api_key)

    @raises(WebApiError)
    def test_set_invalid_api_key(self):
        WebApi.api_key = 'test'

    def test_json(self):
        WebApi.get = Mock()
        WebApi.json('interface', 'method', 2, test='param')
        WebApi.get.assert_called_once_with('json', 'interface', 'method', 2,
                                           test='param')

    def test_get(self):
        urllib2.urlopen = Mock(return_value=__builtin__)
        urllib.urlencode = Mock(return_value='urlencode')
        __builtin__.read = Mock(return_value='data')
        assert_equal('data', WebApi.get('json', 'interface', 'method', 2,
                     test='param'))
        urllib2.urlopen.assert_called_once_with(
            'http://api.steampowered.com/interface/method/v0002/',
            'urlencode')
        urllib.urlencode.assert_called_once_with(
            {'format': 'json', 'key': '0123456789ABCDEF0123456789ABCDEF',
             'test': 'param'}
        )

    @raises(WebApiError)
    def test_get_error(self):
        urllib2.urlopen = Mock(side_effect=urllib2.HTTPError('', 404,
                                                             'not found',
                                                             None, None))
        WebApi.get('json', 'interface', 'method', 2, test='param')
