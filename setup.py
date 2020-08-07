#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

#with open('HISTORY.rst') as history_file:
#    history = history_file.read()

requirements = ["fire motuclient xarray".split(' ')]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Copernicus Marine Service Desk",
    author_email='servicedesk.cmems@mercator-ocean.eu',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="A package to help generating reliable data requests about earth observation and marine related information from Copernicus Marine Database.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='cmemsapi',
    name='cmemsapi',
    packages=find_packages(include=['cmemsapi', 'cmemsapi.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/copernicusmarine/cmemsapi',
    version='0.1.0',
    zip_safe=False,
)
