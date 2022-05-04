<h1 align="center">Copernicus Marine Toolbox</h1>

<p align"=center">
    <a href="https://travis-ci.org/copernicusmarine/cmemsapi"><img src="https://img.shields.io/travis/copernicusmarine/cmemsapi/master.svg?logo=travis" alt="Build Status" /></a> <a href="https://cmemsapi.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/cmemsapi/badge/?version=latest" alt="Documentation Status" /></a>
    <a href="https://github.com/copernicusmarine/cmemsapi/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License badge" /></a>
    <a href="https://github.com/copernicusmarine/cmemsapi"><img src="https://img.shields.io/pypi/v/cmemsapi.svg" alt="PyPI" /></a>
    <a href="https://pyup.io/repos/github/copernicusmarine/cmemsapi/"><img src="https://pyup.io/repos/github/copernicusmarine/cmemsapi/shield.svg" alt="Updates" /></a>
    <a href="https://pyup.io/repos/github/copernicusmarine/cmemsapi/"><img src="https://pyup.io/repos/github/copernicusmarine/cmemsapi/python-3-shield.svg" alt="Python 3" /></a>
    <a href="https://github.com/copernicusmarine/cmemsapi"><img src="https://img.shields.io/pypi/pyversions/cmemsapi.svg" alt="PyPI Supported Versions" /></a>
    <a href="https://github.com/copernicusmarine/cmemsapi"><img src="https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey" alt="Supported Platforms" /></a>
</p>

## What is it?

**cmust** (Copernicus Marine User Support Toolbox - cmemsapi)
is a python package behaving as `Toolbox` to ease interaction
with [Copernicus Marine Earth Observation Database](https://marine.copernicus.eu)
(pre-process, get and post-process data) while offering
CLI & GUI capabilities.

## Main Features
Here are just a few of the things that **cmust** does well:

- Retrieving **several GB** of data **in a single file**. _At this moment, the threshold of default server capabilities is 1024 MB per data request._

- Retrieving **several years or decades** of high temporal resolution data **in a single file**. _At this moment, the threshold of default server capabilities is about ~720 layers per request._

- Retrieving the data in **an ascii format**, such as `.csv` **tabular format** or in a binary but **cloud optimized format*, such as `.nc4` (netcdf4) or `.zarr`. _At this moment, the default server capabilities deliver binary file format in `.nc` (netcdf 3)._


## Where to get it
The source code is currently hosted on GitHub at:
https://github.com/copernicusmarine/cmemsapi

Binary installers for the latest released version are available at the [Python
Package Index (PyPI)](https://pypi.org/project/cmemsapi/) and on [Conda](https://anaconda.org/cmust/cmemsapi).

```sh
# PyPI (preferred if already isolated environment)
pip install cmemsapi
```

```sh
# or Conda
conda install -c cmust cmemsapi
# or
conda create --name cmems --channel conda-forge --channel cmust python=3.8 cmemsapi --yes
```

## How to use it

To be interactively guided and get Copernicus Marine data being download locally, you can fire `get` method and follow its instructions, either:
 
```py
# from a Python environment
from cmemsapi import cmemsapi as cmust
cmust.get()
```

```sh
# from a terminal
cmust get
```

**Credits**: E.U. Copernicus Marine Service Information

## Join the community

Get in touch!
- Create your [Copernicus Marine Account](https://resources.marine.copernicus.eu/?option=com_sla)
- Chat in our [Copernicus Marine ChatRoom]()
- Contact our [Copernicus Human Service Support](https://marine.copernicus.eu/services-portfolio/contact-us/)
- Join our [training workshops](https://marine.copernicus.eu/news/events-agenda/?keywords=News%20and%20Events%2CEvents%2CNews) and improve your skills from our [Copernicus JupyterLab]()
- (re)Tweet y/our [Copernicus Stories](https://twitter.com/cmems_eu)
- Watch [our videos](https://www.youtube.com/channel/UC71ceOVy7WtVC7F04BKoEew)
