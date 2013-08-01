#!/usr/bin/env python

import os
from distutils.core import setup

PROJECT_DIR = os.path.dirname(__file__)

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
    license='BSD',
    long_description=open(os.path.join(PROJECT_DIR, 'README.rst')).read(),
)
