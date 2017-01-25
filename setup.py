#!/usr/bin/env python

from setuptools import setup

setup(name='timespec',
        description='Quickly specify dates and times',
        author='Fenhl',
        packages=["timespec"],
        install_requires=[
            "pytz",
        ]
    )
