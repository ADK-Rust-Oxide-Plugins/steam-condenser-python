#!/usr/bin/env python

from distutils.core import setup

setup(
    name='steam-condenser',
    version='0.0.0',
    description='Python library for querying the Steam Community, Source,'
                ' GoldSrc servers and Steam master servers',
    author='Peter Rowlands',
    author_email='peter@pmrowla.com',
    url='https://github.com/pmrowla/steam-condenser-python',
    packages=['steamcondenser'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Ruby',
        'Programming Language :: PHP',
        'Programming Language :: Java',
        'Topic :: Games/Entertainment :: First Person Shooters',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    long_description=
'''
===============
steam-condenser
===============

The Steam Condenser is a multi-language library for querying the Steam
Community, Source and GoldSrc game servers as well as the Steam master servers.
Currently it is implemented in Java, PHP, Ruby and Python.

License
=======

steam-condenser is distributed under the BSD license.
''',
)
