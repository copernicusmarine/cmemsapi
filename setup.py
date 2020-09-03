#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2020 E.U. Copernicus Marine Service Information

import sys
from pathlib import Path  # noqa E402

from setuptools import find_packages, setup

assert sys.version_info >= (3, 6, 0), "cmtb requires Python 3.6+"

CURRENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CURRENT_DIR))

#def get_long_description() -> str:
#    return (
#        (CURRENT_DIR / "README.md").read_text(encoding="utf8")
#        + "\n\n"
#        + (CURRENT_DIR / "CHANGES.md").read_text(encoding="utf8")
#)

#with open('HISTORY.rst') as history_file:
#    history = history_file.read()

#with open('README.md') as readme_file:
#    README = readme_file.read()

#REQUIREMENTS = [line.strip() for line in open('requirements_prod.txt')]
REQUIREMENTS = ["dask fire funcy ipython lxml motuclient netCDF4 requests scipy toolz xarray ".split(' ')]

SETUP_REQUIREMENTS = []

TEST_REQUIREMENTS = []

setup(
    author="E.U. Copernicus Marine Service Information",
    author_email='servicedesk.cmems@mercator-ocean.eu',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering',
    ],
    description="A package to help generating reliable data requests"
    " about earth observation and marine related information "
    "from Copernicus Marine Database.",
    install_requires=REQUIREMENTS,
    license="MIT",
    long_description='long description',
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='cmemsapi',
    name='cmemsapi',
    packages=find_packages(include=['cmemsapi', 'cmemsapi.*']),
    setup_requires=SETUP_REQUIREMENTS,
    test_suite='tests',
    tests_require=TEST_REQUIREMENTS,
    url='https://github.com/copernicusmarine/cmemsapi',
    version='0.1.12',
    zip_safe=False,
    entry_points={'console_scripts':['cmemstb=cmemsapi.cmemsapi:cli']},
)
