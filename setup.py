#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

from pathlib import Path

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

# read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pyvoyis",
    version="1.0.2",
    description="Voyis Recon LS python driver",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
        "pydantic",
    ],
    project_urls={"Bug Reports": GITHUB_URL + "/issues", "Source": GITHUB_URL},
    entry_points={"console_scripts": ["pyvoyis = pyvoyis.cli:main"]},
)
