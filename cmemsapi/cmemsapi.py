#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main module."""

import calendar
import datetime as dt
import getpass as password
import hashlib
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import time
from functools import reduce
from importlib import reload
from pathlib import Path

import requests as rq
import fire
import lxml.html
import xarray as xr

DEFAULT_CURRENT_PATH = os.getcwd()
BOLD = '\033[1m'
END = '\033[0m'
LOGFILE = Path(DEFAULT_CURRENT_PATH, 'log', ''.join(
    ["CMEMS_API_", dt.datetime.now().strftime('%Y%m%d_%H%M'), ".log"]))
try:
    if not LOGFILE.parent.exists():
        LOGFILE.parent.mkdir(parents=True)
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    print(f'[INFO] Logging to: {str(LOGFILE)}')
    reload(logging)
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG,
                        format='[%(asctime)s] - [%(levelname)s] - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
except IOError:
    print("[ERROR] Failed to set logger.")


def set_target_directory(local_storage_directory=None):
    """
    Returns working directory where data is saved.

    Default value (None) creates a directory (``copernicus-tmp-data``)
    in the current working directory.

    Parameters
    ----------
    local_storage_directory : path or str, optional
        A path object or string. The default is None.

    Returns
    -------
    target_directory : path
        A path to the directory where data is saved.

    """
    if local_storage_directory:
        target_directory = Path(local_storage_directory)
    else:
        target_directory = Path(DEFAULT_CURRENT_PATH, 'copernicus-tmp-data')
    if not target_directory.exists():
        target_directory.mkdir(parents=True)
        print(f'[INFO] Directory successfully created : {target_directory}.')
    return target_directory


def multireplace(tobereplaced, substitute):
    """
    Returns replaced string given string and substitute map.

    Parameters
    ----------
    tobereplaced : str
        String to execute replacements on.
    substitute : dict
        Substitute dictionary {value to find: value to replace}.

    Returns
    -------
    str
        Replaced string.

    """
    substrings = sorted(substitute, key=len, reverse=True)
    regex = re.compile('|'.join(map(re.escape, substrings)))
    return regex.sub(lambda match: substitute[match.group(0)], tobereplaced)


def query(question, default="yes"):
    """
    Returns answer from a yes/no question, read from user\'s input.

    Parameters
    ----------
    question : str
        String written as a question, displayed to user.
    default : str, optional
        String value to be presented to user to help . The default is "yes".

    Raises
    ------
    ValueError
        Raise error to continue asking question until user inputs one of the valid choice.

    Returns
    -------
    bool
        Returns ``True`` if user validates question, ``False`` otherwise.

    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"[ERROR] Invalid default answer: '{default}'")
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("[ACTION] Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def get_credentials(file_rc=None, sep='='):
    """
    Returns Copernicus Marine Credentials.

    Credentials can be specified in a file
    or if ommitted, manually by user's input.

    Parameters
    ----------
    file_rc : str or path, optional
        Location of the file storing credentials. The default is None.
    sep : str, optional
        Character used to separate credential and its value. The default is `=`.

    Returns
    -------
    copernicus_username : str
        Copernicus Marine username.
    copernicus_password : str
        Copernicus Marine password.

    """
    lines = []
    if not file_rc:
        file_rc = Path.cwd() / 'copernicus_credentials.txt'
    try:
        with open(file_rc, 'r') as cred:
            for line in cred:
                lines.append(line)
    except FileNotFoundError:
        print(f'[INFO] Credentials must be entered hereafter, obtained from: '
              f'https://resources.marine.copernicus.eu/?option=com_sla')
        print(f'[INFO] If you have forgotten either your USERNAME '
              f'(which {BOLD}is NOT your email address{END}) or your PASSWORD, '
              f'please visit: https://marine.copernicus.eu/faq/forgotten-password/?idpage=169')
        time.sleep(2)
        usr = password.getpass(
            prompt=f"[ACTION] Please input your Copernicus {BOLD}USERNAME{END}"
            " (and hit `Enter` key):")
        time.sleep(2)
        pwd = password.getpass(
            prompt=f"[ACTION] Please input your Copernicus {BOLD}PASSWORD{END}"
            " (and hit `Enter` key):")
        lines.append(f'username{sep}{usr}')
        lines.append(f'password{sep}{pwd}')
        create_cred_file = query(
            f'[ACTION] For future usage, do you want to save credentials in a'
            ' configuration file?', 'yes')
        if create_cred_file:
            with open(file_rc, 'w') as cred:
                for line in lines:
                    cred.write(''.join([line, '\n']))
    if not all([sep in item for item in lines]):
        print('[ERROR] Sperator is not found. Must be specifed or corrected.\n'
              f'[WARNING] Please double check content of {file_rc}. '
              f'It should match (please mind the `{sep}`):'
              f'\nusername{sep}<USERNAME>\npassword{sep}<PASSWORD>')
        raise SystemExit
    copernicus_username = ''.join(lines[0].strip().split(sep)[1:])
    copernicus_password = ''.join(lines[1].strip().split(sep)[1:])
    if not check_credentials(copernicus_username, copernicus_password):
        if file_rc.exists():
            msg = f' from content of {file_rc}'
        else:
            msg = ''
        print('[ERROR] Provided username and/or password could not be validated.\n'
              f'[WARNING] Please double check it{msg}. More help at: '
              'https://marine.copernicus.eu/faq/forgotten-password/?idpage=169')
        raise SystemExit
    print('[INFO] Credentials have been succcessfully verified and loaded.')
    return copernicus_username, copernicus_password

def check_credentials(user, pwd):
    """
    Check provided Copernicus Marine Credentials are correct.

    Parameters
    ----------
    username : str
        Copernicus Marine Username, provided for free from https://marine.copernicus.eu .
    password : str
        Copernicus Marine Password, provided for free from https://marine.copernicus.eu .

    Returns
    -------
    bool
        Returns ``True`` if credentials are correst, ``False`` otherwise.

    """
    cmems_cas_url = 'https://cmems-cas.cls.fr/cas/login'
    conn_session = rq.session()
    login_session = conn_session.get(cmems_cas_url)
    login_from_html = lxml.html.fromstring(login_session.text)
    hidden_elements_from_html = login_from_html.xpath('//form//input[@type="hidden"]')
    playload = {he.attrib['name']: he.attrib['value'] for he in hidden_elements_from_html}
    playload['username'] = user
    playload['password'] = pwd
    conn_session.post(cmems_cas_url, data=playload)
    if 'CASTGC' not in conn_session.cookies:
        return False
    return True


def check_data_size(command, user, pwd):
    """
    Returns ``True`` if data volume is authorized to be downloaded
    for given user, ``False`` otherwise.

    Parameters
    ----------
    command : str
        DESCRIPTION.
    user : str
        DESCRIPTION.
    pwd : str
        DESCRIPTION.

    Returns
    -------
    ds_check : bool
        DESCRIPTION.

    """
    ds_check = True
    command_size = ' '.join([
        command.replace(
            '--out-dir <OUTPUT_DIRECTORY> --out-name <OUTPUT_FILENAME> '
            '--user <USERNAME> --pwd <PASSWORD>', '--size'),
        '-q -o console -u ', user, ' -p ', pwd
    ])
    print(command_size)
    cmd_rep = command_size.replace(command_size.split(' ')[-1], '****')
    logging.info("DATA SIZE CHECK FOR: %s", cmd_rep)
    process = subprocess.Popen(
        command_size, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    message, _ = process.communicate()
    returncode = process.returncode
    print(returncode)
    if returncode == 0:
        if b'code="005-0"' not in message:
            if convert_size_hr(
                    (float(str(message).split('=')[-1].split('"')[1]))*1000) > convert_size_hr(
                        1.0E8*1000):
                token = hashlib.md5((':'.join([command, user])).encode('utf-8')).hexdigest()
                token_url = 'https://github.com/copernicusmarine/cmemsapi/blob/master/_transactions'
                resp = rq.get(f'{token_url}/{token}')
                if resp.status_code != 200:
                    print('[ERROR] Fatal error. Please CONTACT Support Team at: '
                          'https://marine.copernicus.eu/services-portfolio/contact-us/ '
                          f'and ATTACH your logile {LOGFILE}.')
                    ds_check = False
    else:
        logging.error("Due to: %s", message)
        print('[WARNING] Failed data size check has been logged.\n')
        ds_check = False
    return ds_check

def get_data(command):
    """
    Returns flags describing the state of the submitted query.

    Parameters
    ----------
    command : str
        DESCRIPTION.

    Raises
    ------
    SystemExit
        Raise an error to exit program at fatal error (wrong credentials etc).

    Returns
    -------
    processed_flag : bool
        DESCRIPTION.

    """
    processed_flag = False
    #logging.info(f"MOTU API COMMAND: {command.replace(command.split(' ')[-1], '****')}")
    cmd_rep = command.replace(command.split(' ')[-1], '****')
    logging.info("MOTU API COMMAND: %s", cmd_rep)
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    message, _ = process.communicate()
    returncode = process.returncode
    if returncode != 0:
        logging.error("Due to: %s", message)
        print('[WARNING] Failed data extraction has been logged.\n')
        if b'HTTP Error 503' in message:
            print('HTTP Error 503 - Service is temporary down. Break for 5 minutes.')
            time.sleep(300)
        if b'HTTP Error 4' in message:
            logging.error('Permanent error. Exiting program.')
            raise SystemExit
    else:
        if b'[ERROR]' in message:
            print(f'[ERROR] MOTU API COMMAND raised error :\n {message}')
            logging.error("Due to: %s", message)
        else:
            logging.info('Downloading successful')
            print('[INFO] MOTU Download successful.')
            print('[INFO] Server is releasing the token to successfully grant next request. '
                  'It will resume AUTOMATICALLY.\n')
            time.sleep(5)
            processed_flag = True
    return processed_flag


def get_viewscript():
    """
    Ask the user to input the ``VIEW_SCRIPT`` command.

    Returns
    -------
    view_myscript : str
        String representing the ``TEMPLATE COMMAND`` generated by the
        webportal. Example is available at 'https://marine.copernicus.eu/faq/'
        'how-to-write-and-run-the-script-to-download-'
        'cmems-products-through-subset-or-direct-download-mechanisms/?idpage=169
    """
    uni_test = ['python -m motuclient --motu http://',
                ' '.join(['--out-dir <OUTPUT_DIRECTORY> --out-name <OUTPUT_FILENAME>',
                          '--user <USERNAME> --pwd <PASSWORD>'])]
    while True:
        view_myscript = input(
            f"[ACTION] Please paste the template command displayed on the webportal:\n")
        if not all([item in view_myscript for item in uni_test]):
            print('[DEBUG] Cannot parse VIEWSCRIPT. '
                  'Please paste the ``TEMPLATE COMMAND`` as shown in this article: '
                  'https://marine.copernicus.eu/faq/'
                  'how-to-write-and-run-the-script-to-download-'
                  'cmems-products-through-subset-or-direct-download-mechanisms/?idpage=169')
        else:
            return view_myscript


def process_viewscript(target_directory, view_myscript=None,
                       user=None, pwd=None,
                       dailystack=None):
    """
    Generates as many data requests as required to match init ```VIEW_SCRIPT``.

    Parameters
    ----------
    target_directory : str or path
        DESCRIPTION.
    view_myscript : str, optional
        DESCRIPTION. The default is None.
    user : str, optional
        DESCRIPTION. The default is None.
    pwd : str, optional
        DESCRIPTION. The default is None.
    dailystack : bool, optional
        DESCRIPTION. The default is None.

    Raises
    ------
    ValueError
        DESCRIPTION.

    Returns
    -------
    TYPE
        Path of the output file matching the ```VIEW_SCRIPT`` data request.

    """
    outname = False
    if not user and not pwd:
        user, pwd = get_credentials()
    if not view_myscript:
        view_myscript = get_viewscript()
    if not check_data_size(view_myscript, user, pwd):
        return outname
    if view_myscript:
        view_script_command = view_myscript.replace(
            '--out-dir <OUTPUT_DIRECTORY> --out-name <OUTPUT_FILENAME> '
            '--user <USERNAME> --pwd <PASSWORD>', '')
    else:
        raise ValueError('VIEW SCRIPT cell must contain the template command \
                         displayed on the webportal.'
                         'HELP: http://marine.copernicus.eu/faq/how-to-write-\
                             and-run-the-script-to-download-cmems-products-thr\
                                 ough-subset-or-direct-download-mechanisms/?idpage=169')
    mydict = dict([e.strip().partition(" ")[::2]
                   for e in view_script_command.split('--')])
    mydict['variable'] = [value for (var, value) in [e.strip().partition(
        " ")[::2] for e in view_script_command.split('--')] if var == 'variable']
    prefix = '_'.join(
        list((mydict['service-id'].split('-')[0]).split('_')[i] for i in [0, -2, -1]))
    suffix = '.nc'
    min_x = float(mydict['longitude-min'])
    max_x = float(mydict['longitude-max'])
    min_y = float(mydict['latitude-min'])
    max_y = float(mydict['latitude-max'])
    list_abs = [abs(max_x - min_x), abs(max_y - min_y)]
    try:
        min_z = float(mydict['depth-min'])
        max_z = float(mydict['depth-max'])
        list_abs.append(abs(max_z - min_z))
    except KeyError:
        print('[INFO] This dataset does not contain depth dimension.')
    dataset_name = mydict['product-id']
    temporal_resolution_monthly = [
        'month', 'an-fc-m', 'rean-m', '-mm-', '-MON-']
    temporal_resolution_hourly = [
        '-hi', 'hourly', 'hts', 'fc-h', '001-027', '001-032', 'rean-h', '1hr']
    if any(x in dataset_name for x in temporal_resolution_monthly):
        monthstack = False
    else:
        if len([i for i in list_abs if i > 50]) > 0:
            monthstack = True
        else:
            monthstack = False
            if max_x == min_x and max_y == min_y:
                gridpoint = 'gridpoint'
                if '-' in str(min_x):
                    gridpoint = '_'.join(
                        [gridpoint, str(min_x).replace(".", "dot").replace("-", "W")])
                else:
                    gridpoint = '_'.join(
                        [gridpoint, ''.join(['E', str(min_x).replace('.', 'dot')])])
                if '-' in str(min_y):
                    gridpoint = '_'.join(
                        [gridpoint, str(min_y).replace(".", "dot").replace("-", "S")])
                else:
                    gridpoint = '_'.join(
                        [gridpoint, ''.join(['N', str(min_y).replace('.', 'dot')])])
    if any(x in dataset_name for x in temporal_resolution_hourly):
        monthstack = True
    if len(mydict['variable']) > 6:
        monthstack = True
        out_var_name = 'several_vars'
    else:
        out_var_name = '_'.join(mydict['variable'])
    print('\n+------------------------------------+\n| ! - CONNECTION TO CMEMS'
          'HUB - OPEN |\n+------------------------------------+\n\n')
    for retry in range(1, 4):
        retry_flag = False
        date_start = dt.datetime.strptime(
            view_script_command.split('"')[1], '%Y-%m-%d %H:%M:%S')
        date_end = dt.datetime.strptime(
            view_script_command.split('"')[3], '%Y-%m-%d %H:%M:%S')
        while date_start <= date_end:
            if dailystack:
                date_end_cmd = date_start
                _, dtformat = ['_daystack-', "%Y%m%d"]
            elif monthstack:
                date_end_cmd = (dt.datetime(date_start.year,
                                            date_start.month,
                                            calendar.monthrange(date_start.year,
                                                                date_start.month)[1], 23))
                _, dtformat = ['_monthstack-', "%Y%m"]
            else:
                if date_start.year == date_end.year:
                    date_end_cmd = (dt.datetime(date_start.year,
                                                date_end.month,
                                                calendar.monthrange(date_start.year,
                                                                    date_end.month)[1], 23))
                else:
                    date_end_cmd = (dt.datetime(date_start.year, 12, 31, 23))
                _, dtformat = ['_yearstack-', "%Y"]
            date_start_cmd = dt.datetime(
                date_start.year, date_start.month, date_start.day, 0)
            substitute = {view_script_command.split('"')[1]:
                          date_start_cmd.strftime('%Y-%m-%d %H:%M:%S'),
                          view_script_command.split('"')[3]:
                              date_end_cmd.strftime('%Y-%m-%d %H:%M:%S')}
            date_end_format = date_end_cmd.strftime(dtformat)
            try:
                outname = '-'.join(['CMEMS', prefix, gridpoint, out_var_name,
                                    date_end_format + suffix])
            except UnboundLocalError:
                outname = '-'.join(['CMEMS', prefix, out_var_name,
                                    date_end_format + suffix])
            command = ' '.join([multireplace(view_script_command, substitute),
                                ' -o ', str(target_directory), ' -f ', outname,
                                ' -u ', user, ' -p ', pwd, '-q'])
            print('\n----------------------------------\n'
                  '- ! - Processing dataset request : '
                  '%s\n----------------------------------\n' % outname)
            date_start = date_end_cmd + dt.timedelta(days=1)
            if not Path(target_directory / outname).exists():
                print('## MOTU API COMMAND ##')
                print(command.replace(user, '*****').replace(pwd, '*****'))
                print('\n[INFO] CMEMS server is checking both your credentials'
                      ' and command syntax. '
                      'If successful, it will extract the data and create your'
                      ' dataset on the fly. Please wait. \n')
                flag = get_data(command)
                if flag:
                    print('[INFO] The dataset for {} has been stored in {}.'.format(
                        outname, target_directory))
                else:
                    retry_flag = True
            else:
                print(f"[INFO] The dataset for {outname} "
                      f"has already been downloaded in {target_directory}\n")
        if not retry_flag:
            break
    print("+-------------------------------------+\n| ! - CONNECTION TO CMEMS "
          "HUB - CLOSE |\n+-------------------------------------+\n")
    with open(LOGFILE) as logfile:
        if retry == 3 and 'ERROR' in logfile.read():
            print("## YOUR ATTENTION IS REQUIRED ##")
            print(
                f'Some download requests failed, though {retry} retries. '
                'Please see recommendation in {LOGFILE})')
            print('TIPS: you can also apply hereafter recommendations.'
                  '\n1.  Do not move netCDF files'
                  '\n2.  Double check if a change must be done in the '
                  'viewscript, FTR it is currently set to:\n')
            print(view_myscript)
            print('\n3.  Check there is not an ongoing maintenance by looking '
                  'at the User Notification Service and Systems & Products Status:\n',
                  'https://marine.copernicus.eu/services-portfolio/news-flash/'
                  '\n4.  Then, if relevant, do relaunch manually this python '
                  'script to automatically download only failed data request(s)'
                  '\n5.  Finally, feel free to contact our Support Team either:'
                  '\n  - By mail: servicedesk.cmems@mercator-ocean.eu or \n  - '
                  'By using the webform: '
                  'https://marine.copernicus.eu/services-portfolio/contact-us/'
                  ' or \n  - By leaving a post on the forum:'
                  ' https://forum.marine.copernicus.eu\n\n')
            return False
    return outname


def convert_size_hr(size_in_bytes):
    """
    Get size from bytes and displays to user in human readable.

    Parameters
    ----------
    size_in_bytes : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    if size_in_bytes == 0:
        return '0 Byte'
    size_standard = ('B', 'KiB', 'MiB', 'GiB', 'TiB')
    integer = int(math.floor(math.log(size_in_bytes, 1_024)))
    powmath = math.pow(1_024, integer)
    precision = 2
    size = round(size_in_bytes / powmath, precision)
    return size, size_standard[integer]


def get_disk_stat(drive=None):
    """
    Get disk size statistics.

    Parameters
    ----------
    drive : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    disk_stat : TYPE
        DESCRIPTION.

    """
    if not drive:
        drive = '/'
    disk_stat = list(shutil.disk_usage(drive))
    return disk_stat


def get_file_size(files):
    """
    Get size of file(s) in bytes.

    Parameters
    ----------
    files : TYPE
        DESCRIPTION.

    Returns
    -------
    mds_size : TYPE
        DESCRIPTION.

    """
    mds_size = 0
    for file in files:
        with xr.open_dataset(file, decode_cf=False) as sds:
            mds_size = mds_size + sds.nbytes
    return mds_size


def check_file_size(mds_size, default_nc_size=None):
    """
    Check size of file(s).

    Parameters
    ----------
    mds_size : TYPE
        DESCRIPTION.
    default_nc_size : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    check_fs : TYPE
        DESCRIPTION.

    """
    if not default_nc_size:
        default_nc_size = 16_000_000_000
    check_fs = False
    size, unit = display_disk_stat(mds_size)
    if mds_size == 0:
        print(f'[ERROR-NETCDF] There is an error to assess the size of netCDF '
              'file(s). Please check if data are not corrupted.')
    elif size == 0:
        print(f'[ERROR] Program exit.')
    elif mds_size > default_nc_size:
        print(f'[INFO-NETCDF] The size of the netCDF file would be higher than'
              ' 16 GiB.')
        force = query(
            f'[ACTION-NETCDF] Do you still want to create the netCDF file of '
            f'{BOLD}size {size} {unit}{END}?', 'no')
        if not force:
            print(
                '[ERROR-NETCDF] Writing to disk action has been aborted by '
                'user due to file size issue.')
            print(
                '[INFO-NETCDF] The script will try to write several netCDF '
                'files with lower file size.')
        else:
            check_fs = True
    else:
        check_fs = True
    return check_fs


def display_disk_stat(mds_size):
    """
    Display hard drive statistics to user.

    Parameters
    ----------
    mds_size : TYPE
        DESCRIPTION.

    Returns
    -------
    mds_size_hr : TYPE
        DESCRIPTION.

    """
    disk_stat = get_disk_stat()
    free_after = disk_stat[2] - mds_size
    disk_stat.append(free_after)
    disk_stat.append(mds_size)
    try:
        total_hr, used_hr, free_hr, free_after_hr, mds_size_hr = [
            convert_size_hr(item) for item in disk_stat]
    except ValueError as error:
        msg = f"[WARNING] Operation shall be aborted to avoid NO SPACE LEFT ON\
             DEVICE error: {error}"
        mds_size_hr = (0, 'B')
    else:
        space = '-'*37
        msg = ''.join((f"[INFO] {space}\n",
                       f"[INFO] Total Disk Space (before operation) :"
                       f" {total_hr[1]} {total_hr[0]} \n",
                       f"[INFO] Used Disk Space (before operation)  :"
                       f" {used_hr[1]} {used_hr[0]} \n",
                       f"[INFO] Free Disk Space (before operation)  :"
                       f" {free_hr[1]} {free_hr[0]} \n",
                       f"[INFO] Operation to save dataset to Disk   :"
                       " {mds_size_hr[1]} {mds_size_hr[0]} \n",
                       f"[INFO] Free Disk Space (after operation)   :"
                       f"{free_after_hr[1]} {free_after_hr[0]} \n",
                       f"[INFO] {space}"))
    print(''.join(("[INFO] CHECK DISK STATISTICS\n", msg)))
    return mds_size_hr


def get_file_pattern(outname, sep='-', rem=-1, advanced=True):
    """
    Retrieve a ``file_pattern`` from a filename and advanced regex.

    Parameters
    ----------
    outname : str
        Filename from which a pattern must be extracted.
    sep : str, optional
        Separator. The default is '-'.
    rem : TYPE, optional
        Removal parts. The default is -1.
    advanced : TYPE, optional
        Advanced regex. The default is True.

    Returns
    -------
    file_pattern : str
        The ``file_pattern`` extracted from ``filename``.

    """
    if 'pathlib' in str(type(outname)):
        outname = outname.name
    if advanced:
        file_pattern = outname.replace(outname.split(sep)[rem], '')[:-1]
    else:
        # To be coded
        pass
    return file_pattern


def get_years(ncfiles, sep='-'):
    """
    Retrieve a list of years from a list of netCDF filenames.

    Parameters
    ----------
    ncfiles : list
        List of filenames from which years will be extracted.
    sep : TYPE, optional
        Separator. The default is '-'.

    Returns
    -------
    years : set
        List of years.

    """
    years = set([str(f).split(sep)[-1][:4] for f in ncfiles])
    return years


def get_ncfiles(target_directory, file_pattern=None, year=None):
    """
    Retrieve list of files, based on parameters.

    Parameters
    ----------
    target_directory : str
        DESCRIPTION.
    file_pattern : TYPE, optional
        DESCRIPTION. The default is None.
    year : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    ncfiles : list
        List of strings containing absolute path to files.

    """
    if 'str' in str(type(target_directory)):
        target_directory = Path(target_directory)
    if file_pattern and year:
        ncfiles = list(target_directory.glob(f'{file_pattern}*{year}*.nc'))
    elif file_pattern and not year:
        ncfiles = list(target_directory.glob(f'*{file_pattern}*.nc'))
    elif year and not file_pattern:
        ncfiles = list(target_directory.glob(f'*{year}*.nc'))
    else:
        ncfiles = list(target_directory.glob('*.nc'))
    return ncfiles


def set_outputfile(file_pattern, target_directory, target_out_directory=None,
                   start_year=None, end_year=None):
    """
    Set output filename based on variables.

    Parameters
    ----------
    file_pattern : TYPE
        DESCRIPTION.
    target_directory : TYPE
        DESCRIPTION.
    target_out_directory : TYPE, optional
        DESCRIPTION. The default is None.
    start_year : TYPE, optional
        DESCRIPTION. The default is None.
    end_year : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    outputfile : TYPE
        DESCRIPTION.

    """
    if not target_out_directory:
        target_out_directory = Path(target_directory.parent, 'copernicus-processed-data')
    elif 'str' in str(type(target_out_directory)):
        target_out_directory = Path(target_out_directory)
    if not target_out_directory.exists():
        target_out_directory.mkdir(parents=True)
    if not end_year:
        outputfile = target_out_directory / f'{file_pattern}-{start_year}.nc'
    else:
        outputfile = target_out_directory / \
            f'{file_pattern}-{start_year}_{end_year}.nc'
    return outputfile


def over_write(outputfile):
    """
    Ask user if overwrite action should be performed.

    Parameters
    ----------
    outputfile : TYPE
        DESCRIPTION.

    Returns
    -------
    ow : TYPE
        DESCRIPTION.

    """
    ok_overwrite = True
    if outputfile.exists():
        ok_overwrite = query(
            f'[ACTION] The file {outputfile} already exists. Do you want'
            f'{BOLD}to overwrite{END} it?', 'no')
    return ok_overwrite


def del_ncfiles(ncfiles):
    """
    Delete files.

    Parameters
    ----------
    ncfiles : TYPE
        DESCRIPTION.

    Returns
    -------
    bool
        DESCRIPTION.

    """
    for fnc in ncfiles:
        try:
            fnc.unlink()
        except OSError as error:
            print(f'[ERROR]: {fnc} : {error.strerror}')
    print('[INFO-NETCDF] All inputs netCDF files have been successfully deleted.')
    return True


def to_nc4(mds, outputfile):
    """
    Convert file(s) to one single netCDF-4 file, based on computer limits.

    Parameters
    ----------
    mds : TYPE
        DESCRIPTION.
    outputfile : TYPE
        DESCRIPTION.

    Returns
    -------
    nc4 : TYPE
        DESCRIPTION.

    """
    if 'xarray.core.dataset.Dataset' not in str(type(mds)):
        mds = xr.open_mfdataset(mds, combine='by_coords')
    if 'str' in str(type(outputfile)):
        outputfile = Path(outputfile)
    prepare_encoding = {}
    for variable in mds.data_vars:
        prepare_encoding[variable] = mds[variable].encoding
        prepare_encoding[variable]['zlib'] = True
        prepare_encoding[variable]['complevel'] = 1
    encoding = {}
    for key_encod, var_encod in prepare_encoding.items():
        encoding.update(
            {key_encod: {key: value for key, value in var_encod.items() if key != 'coordinates'}})
    try:
        mds.to_netcdf(path=outputfile,
                      mode='w',
                      engine='netcdf4',
                      encoding=encoding)
    except ValueError as error:
        print(
            f'[INFO-NETCDF] Convertion initialized but ended in error due to : {error}')
        nc4 = False
    else:
        real_file_size = convert_size_hr(outputfile.stat().st_size)
        space = '-'*20
        msg = ''.join((f"[INFO] {space}\n", f"[INFO-NETCDF] Output file :"
                       f" {str(outputfile)}\n",
                       f"[INFO-NETCDF] File format : netCDF-4\n",
                       f"[INFO-NETCDF] File size   : {real_file_size[0]}"
                       f" {real_file_size[1]}\n",
                       f"[INFO] {space}"))
        print(''.join(("[INFO] CONVERTING TO NETCDF4\n", msg)))
        nc4 = True
    return nc4


def to_csv(mds, outputfile):
    """
    Convert file(s) to one single csv file, based on computer limits.

    Parameters
    ----------
    mds : TYPE
        DESCRIPTION.
    outputfile : TYPE
        DESCRIPTION.

    Returns
    -------
    csv : TYPE
        DESCRIPTION.

    """
    if 'xarray.core.dataset.Dataset' not in str(type(mds)):
        mds = xr.open_mfdataset(mds, combine='by_coords')
    if 'str' in str(type(outputfile)):
        outputfile = Path(outputfile)
    msg2 = 'please contact support at: https://marine.copernicus.eu/services-portfolio/contact-us/'
    csv = False
    force = False
    ms_excel_row_limit = 1_048_576
    nb_grid_pts = reduce((lambda x, y: x * y),
                         list([len(mds[c]) for c in mds.coords]))
    if nb_grid_pts > ms_excel_row_limit:
        print(f'[INFO-CSV] The total number of rows exceeds MS Excel limit.'
              ' It is {BOLD}NOT recommended{END} to continue.')
        force = query(
            f'[ACTION-CSV] Do you still want to create this CSV file with'
            f' {BOLD}{nb_grid_pts} rows{END} (though most computers will run out of memory)?', 'no')
    if nb_grid_pts < ms_excel_row_limit or force:
        try:
            dataframe = mds.to_dataframe().reset_index().dropna()
            outputfile = outputfile.with_suffix('.csv')
            dataframe.to_csv(outputfile, index=False)
        except IOError:
            print(f'[INFO-CSV] Convertion initialized but ended in error.')
        else:
            space = '-'*18
            msg = ''.join((f"[INFO] {space}\n", f"[INFO-CSV] Output file :"
                           f" {str(outputfile)}\n",
                           f"[INFO-CSV] File format : Comma-Separated Values\n",
                           f"[INFO-CSV] Preview Stat:\n {dataframe.describe()}\n",
                           f"[INFO] {space}"))
            print(''.join(("[INFO] CONVERTING TO CSV\n", msg)))
            csv = True
    else:
        print(
            f'[WARNING-CSV] Writing to disk action has been aborted by user '
            'due to very high number of rows ({nb_grid_pts}) exceeding most '
            'computers and softwares limits (such as MS Excel).')
        print(''.join(('[INFO-CSV] A new version will be proposed to handle '
                       'this use case automatically by splitting big table '
                       'in several spreadsheets.\n[INFO-CSV] To upvote this feature, ', msg2)))
    try:
        mds.close()
        del mds
    except NameError:
        print(''.join(('[DEBUG] ', msg2)))
    return csv


def to_nc4_csv(ncfiles, outputfile, skip_csv=False, default_nc_size=None):
    """
    Convert file(s) to both netCDF-4 and csv files, based on computer limits.

    Parameters
    ----------
    ncfiles : TYPE
        DESCRIPTION.
    outputfile : TYPE
        DESCRIPTION.
    skip_csv : TYPE, optional
        DESCRIPTION. The default is False.
    default_nc_size : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    nc4 : bool
        DESCRIPTION.
    csv : bool
        DESCRIPTION.
    check_ow : bool
        DESCRIPTION.

    """
    nc4 = False
    csv = False
    if not default_nc_size:
        default_nc_size = 16_000_000_000
    mds_size = get_file_size(ncfiles)
    check_fs = check_file_size(mds_size, default_nc_size)
    check_ow = over_write(outputfile)
    check_ow_csv = over_write(outputfile.with_suffix('.csv'))
    if check_ow and check_fs:
        with xr.open_mfdataset(ncfiles, combine='by_coords') as mds:
            nc4 = to_nc4(mds, outputfile)
    elif not check_ow:
        print('[WARNING-NETCDF] Writing to disk action has been aborted by '
              'user due to already existing file.')
    elif not check_fs:
        skip_csv = True
    if check_ow_csv and not skip_csv:
        with xr.open_mfdataset(ncfiles, combine='by_coords') as mds:
            csv = to_csv(mds, outputfile)
    return nc4, csv, check_ow


def post_processing(outname, target_directory, target_out_directory=None,
                    delete_files=True):
    """
    Post-process the data already located on disk.

    Concatenate a complete timerange in a single netCDF-4 file,
    or if not possible, stack periods on minimum netCDF-4 files
    (either by year or by month).
    There is a possibility to delete old files to save space,
    thanks to convertion from nc3 to nc4 and to convert to `CSV`,
    if technically feasible.

    Parameters
    ----------
    outname : TYPE
        DESCRIPTION.
    target_directory : TYPE
        DESCRIPTION.
    target_out_directory : TYPE, optional
        DESCRIPTION. The default is None.
    delete_files : TYPE, optional
        DESCRIPTION. The default is True.

    Raises
    ------
    SystemExit
        DESCRIPTION.

    Returns
    -------
    processing : bool
        DESCRIPTION.

    See Also
    --------
    get_file_pattern : called from this method
    get_ncfiles : called from this method
    get_years : called from this method
    set_outputfile : called from this method
    to_nc4_csv : called from this method
    del_ncfiles : called from this method

    """
    processing = False
    try:
        file_pattern = get_file_pattern(outname)
    except AttributeError as error:
        print(f'[ERROR] Program exits due to fatal error on server.'
              f'Please refer to points 3 and/or 5 above: {error}')
        raise SystemExit
    sel_files = get_ncfiles(target_directory, file_pattern)
    years = get_years(sel_files)
    try:
        single_outputfile = set_outputfile(
            file_pattern, target_directory, target_out_directory,
            start_year=min(years), end_year=max(years))
    except ValueError as error:
        print(
            f'[ERROR] Processing failed due to no file matching pattern : {error}')
    else:
        nc4, csv, ow_choice = to_nc4_csv(sel_files, single_outputfile)
        if not nc4 and not csv and ow_choice:
            for year in years:
                print(year)
                ncfiles = get_ncfiles(target_directory, file_pattern, year)
                outfilemerged = set_outputfile(file_pattern, target_directory,
                                               target_out_directory, start_year=year)
                to_nc4_csv(ncfiles, outfilemerged)
                if delete_files:
                    del_ncfiles(ncfiles)
        processing = True
    return processing


def get(local_storage_directory=None, target_out_directory=None,
        view_myscript=None, user=None, pwd=None, dailystack=False,
        delete_files=False):
    """Download and post-process files to both compressed and tabular formats,
    if applicable.

    Download as many subsets of dataset required
    to fulfill an initial data request based on a template command,
    called `VIEW SCRIPT` generated by Copernicus Marine website
    (https://marine.copernicus.eu).
    Then, all files are post-processed locally.
    e.g to concatenate in a single file, to save space (thanks to nc3 -> nc4),
    to convert to `CSV` (if technically possible), and to delete old files.
    End-user is guided throughout the process if no parameter is declared.
    To get started, this function is the main entry point.

    Parameters
    ----------
    local_storage_directory : TYPE, optional
        DESCRIPTION. The default is None.
    target_out_directory : TYPE, optional
        DESCRIPTION. The default is None.
    view_myscript : TYPE, optional
        DESCRIPTION. The default is None.
    user : TYPE, optional
        DESCRIPTION. The default is None.
    pwd : TYPE, optional
        DESCRIPTION. The default is None.
    dailystack : TYPE, optional
        DESCRIPTION. The default is False.
    delete_files : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    True.

    See Also
    --------
    process_viewscript : Method to parse `VIEW SCRIPT`
    post_processing : Method to convert downloaded data to other format

    Examples
    --------
    Ex 1. Let the user be guided by the script with interactive questions:

    >>> cmemstb get

    Ex 2. Get data matching a ``VIEW SCRIPT`` template command:

    >>> cmemstb get --view_myscript="python -m motuclient --motu http://nrt.cmems-du.eu/motu-web/Motu --service-id GLOBAL_ANALYSIS_FORECAST_PHY_001_024-TDS --product-id global-analysis-forecast-phy-001-024 --longitude-min -20 --longitude-max 45 --latitude-min 25 --latitude-max 72 --date-min \"2020-08-18 12:00:00\" --date-max \"2020-08-21 12:00:00\" --depth-min 0.493 --depth-max 0.4942 --variable thetao --out-dir <OUTPUT_DIRECTORY> --out-name <OUTPUT_FILENAME> --user <USERNAME> --pwd <PASSWORD>"
    """
    target_directory = set_target_directory(local_storage_directory)
    outname = process_viewscript(target_directory=target_directory,
                                 view_myscript=view_myscript,
                                 user=user, pwd=pwd, dailystack=dailystack)
    post_processing(outname=outname, target_directory=target_directory,
                    target_out_directory=target_out_directory,
                    delete_files=delete_files)
    return True

def cli():
    """
    Method to enable Command Line Interface and to expose only useful method for beginners.

    Returns
    -------
    None.

    """
    fire.Fire({
        'display_disk_stat': display_disk_stat,
        'get': get,
        'get_credentials': get_credentials,
        'get_data': get_data,
        'get_file_pattern': get_file_pattern,
        'get_ncfiles': get_ncfiles,
        'post_processing': post_processing,
        'process_viewscript': process_viewscript,
        'set_target_directory': set_target_directory,
        'to_nc4_csv': to_nc4_csv,
        'to_nc4': to_nc4,
        'to_csv': to_csv
        })

if __name__ == '__main__':
    cli()
