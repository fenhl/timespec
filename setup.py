#!/usr/bin/env python

import setuptools

setuptools.setup(
    name='timespec',
    description='Quickly specify dates and times',
    author='Fenhl',
    packages=['timespec'],
    install_requires=[
        'pytz',
    ]
)
