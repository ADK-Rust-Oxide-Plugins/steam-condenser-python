#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is free software; you can redistribute it and/or modify it under
# the terms of the new BSD License.
#
# Copyright (c) 2013 Sebastian Staudt

from __future__ import absolute_import

from ..errors import SteamCondenserError


class WebApiError(SteamCondenserError):
    """A Steam Web API error occured"""
    pass
