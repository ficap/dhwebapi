#!/usr/bin/env python3

from setuptools import setup

setup(
    name="dhwebapi",
    version="0.1",
    description="Python library for easy communication with hub.docker.com.",
    author="Filip Čáp",
    author_email="ficap@redhat.com",
    url="https://github.com/ficap/dhwebapi",
    license="MIT",
    entry_points={
        'console_scripts': ["dhwebapi_cli = dhwebapi.dhwebapi:_main"]
    },
    packages=["dhwebapi"],
    install_requires=["requests"]
)
