#!/usr/bin/env python

from setuptools import setup

setup(name='timespec',
        description='Quickly specify dates and times',
        author='Fenhl',
        packages=["timespec"],
        # use_scm_version = {
        #     "write_to": "backuproll/_version.py",
        # },
        install_requires=[
            "pytz",
        ]
    )
