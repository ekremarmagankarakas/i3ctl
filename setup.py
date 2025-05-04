#!/usr/bin/env python3
"""
Setup script for i3ctl.
"""

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="i3ctl",
    version="0.1.0",
    author="i3ctl Developers",
    author_email="ekremarmagankarakas@gmail.com",
    description="Command line utility for managing i3 window manager settings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ekremarmagankarakas/i3ctl",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications",
    ],
    python_requires=">=3.6",
    install_requires=[
        "i3ipc>=2.2.1",
        "python-xlib>=0.31",
        "pydbus>=0.6.0",
    ],
    extras_require={},
    entry_points={
        "console_scripts": [
            "i3ctl=i3ctl.cli:main",
        ],
    },
)