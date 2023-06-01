#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

from setuptools import find_packages, setup

GITHUB_URL = "https://github.com/miquelmassot/pyvoyis"


classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Programming Language :: Python :: 3",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Hardware :: Hardware Drivers",
]

setup(
    name="pyvoyis",
    version="0.1",
    description="Voyis Recon LS python driver",
    author="Miquel Massot",
    author_email="miquel.massot@gmail.com",
    maintainer="Miquel Massot",
    maintainer_email="miquel.massot@gmail.com",
    url=GITHUB_URL,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=classifiers,
    license="GPLv3",
    install_requires=[
        "nest_asyncio",
        "python-statemachine",
    ],
    project_urls={"Bug Reports": GITHUB_URL + "/issues", "Source": GITHUB_URL},
    entry_points={"console_scripts": ["pyvoyis = pyvoyis.cli:main"]},
)
