#!/usr/bin/env python
# Copyright (C) 2020 E.U. Copernicus Marine Service Information

"""The setup script."""

from setuptools import setup, find_packages
import sys
import os

assert sys.version_info >= (3, 6, 0), "cmtb requires Python 3.6+"
from pathlib import Path # noqa E402

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

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [line.strip() for line in open('requirements_prod.txt')]

setup_requirements = [ ]

test_requirements = [ ]

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
        'Programming Language :: Python',
        'Programming Language :: Python :: 3  Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering',
    ],
    description="A package to help generating reliable data requests about earth observation and marine related information from Copernicus Marine Database.",
    install_requires=requirements,
    license="MIT",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='cmemsapi',
    name='cmemsapi',
    packages=find_packages(include=['cmemsapi', 'cmemsapi.*']),
    python_requires=">=3.6",
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/copernicusmarine/cmemsapi',
    version='0.1.7',
    zip_safe=False,
	entry_points={'console_scripts':['cmemstb=cmemsapi.cmemsapi:cli']},
)
