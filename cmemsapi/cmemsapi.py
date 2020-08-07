#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main module."""

import calendar
import datetime as dt
import getpass as password
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

import fire
import xarray as xr

DEFAULT_CURRENT_PATH = os.getcwd()

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
except:
    print("[ERROR] Failed to set logger.")


def set_target_directory(local_storage_directory=None):
    if local_storage_directory:
        target_directory = Path(local_storage_directory)
    else:
        target_directory = Path(DEFAULT_CURRENT_PATH, 'copernicus-tmp-data')
    if not target_directory.exists():
        target_directory.mkdir(parents=True)
        print(f'[INFO] Directory created : {target_directory}.')
    return target_directory


def multireplace(tobereplaced, substitute):
    substrings = sorted(substitute, key=len, reverse=True)
    regex = re.compile('|'.join(map(re.escape, substrings)))
    return regex.sub(lambda match: substitute[match.group(0)], tobereplaced)


def query(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"invalid default answer: '{default}'")

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


#################################
# TODO: Create Class DownloadData
#################################

def get_credentials(file_rc=None, sep=None):
    r"""Return Copernicus Marine Credentials: copernicus_username and copernicus_password.
    Credentials can be specified in a file or manually by user's input.

    TO DO
    -----
    add_error_handling
        To check file_rc content, search for 'user' and 'pwd' and then assign values.

    add_compatibility_cfg_motuclient
        To make sure it is compatible with the configuration file of the motuclient, located either:
        on Unix platforms: $HOME/motuclient/motuclient-python.ini
        on Windows platforms: %USERPROFILE%\motuclient\motuclient-python.ini

    """
    lines = []
    if not file_rc:
        file_rc = Path.cwd() / 'credentials.txt'
    if not sep:
        sep = '='
    try:
        with open(file_rc, 'r') as cred:
            for line in cred:
                lines.append(line)
    except IOError:
        print('[INFO] Credentials must be entered hereafter. If not already, request them free here: https://resources.marine.copernicus.eu/?option=com_sla')
        print('[INFO] If you have forgotten either your USERNAME (which is NOT your email address) or your PASSWORD, please visit: https://marine.copernicus.eu/faq/forgotten-password/?idpage=169')
        time.sleep(2)
        usr = password.getpass(
            prompt="[ACTION] Please input (and validate) your Copernicus USERNAME:")
        time.sleep(2)
        pwd = password.getpass(
            prompt="[ACTION] Please input (and validate) your Copernicus PASSWORD:")
        lines.append(f'username={usr}')
        lines.append(f'password={pwd}')
        create_cred_file = query(
            f'[ACTION] For future usage, do you want to save credentials in a configuration file?', 'yes')
        if create_cred_file:
            with open('credentials.txt', 'a') as cred:
                for line in lines:
                    cred.write(''.join([line, '\n']))
            print('[INFO] The configuration file to store credentials has a content format as follow:\
            \n    username=<USERNAME>\n    password=<PASSWORD>')
    copernicus_username = ''.join(lines[0].strip().split(sep)[1:])
    copernicus_password = ''.join(lines[1].strip().split(sep)[1:])
    print('[INFO] Credentials have been succcessfully loaded.')
    return copernicus_username, copernicus_password


def get_data(command, logging):
    processed_state = True
    processed_flag = False
    logging.info('MOTU API COMMAND: ' +
                 command.replace(command.split(' ')[-1], '****'))
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    message, error = process.communicate()
    returncode = process.returncode
    if returncode != 0:
        logging.error(f'Due to: {message}')
        print('[WARNING] Failed data extraction has been logged.\n')
        if b'HTTP Error 503' in message:
            print('HTTP Error 503 - Service is temporary down. Break for 5 minutes.')
            time.sleep(300)
            processed_state = False
        if b'HTTP Error 4' in message:
            logging.error('Permanent error. Exiting program.')
            raise SystemExit
    else:
        if b'[ERROR]' in message:
            print(f'[ERROR] MOTU API COMMAND raised error :\n {message}')
            logging.error(f'Due to :{message}')
            processed_state = False
        else:
            logging.info('Downloading successful')
            print('[INFO] MOTU Download successful.')
            print('[INFO] Server is releasing the token to successfully grant next request. '
                  'It will resume AUTOMATICALLY.\n')
            time.sleep(5)
            processed_flag = True
    return processed_flag, processed_state


def get_viewscript():
    while True:
        view_myscript = input(
            "[ACTION] Please paste the template command displayed on the webportal:\n")
        try:
            viewScriptCommand = view_myscript.replace(
                '--out-dir <OUTPUT_DIRECTORY> --out-name <OUTPUT_FILENAME> --user <USERNAME> --pwd <PASSWORD>', '')
        except ValueError:
            print('[DEBUG] Cannot parse VIEWSCRIPT')
        else:
            return view_myscript


def process_viewscript(target_directory, view_myscript=None, user=None, pwd=None, dailystack=None):
    if not user and not pwd:
        user, pwd = get_credentials()
    if not view_myscript:
        view_myscript = get_viewscript()
    if view_myscript:
        viewScriptCommand = view_myscript.replace(
            '--out-dir <OUTPUT_DIRECTORY> --out-name <OUTPUT_FILENAME> --user <USERNAME> --pwd <PASSWORD>', '')
    else:
        raise ValueError('VIEW SCRIPT cell must contain the template command displayed on the webportal.'
                         'HELP: http://marine.copernicus.eu/faq/how-to-write-and-run-the-script-to-download-cmems-products-through-subset-or-direct-download-mechanisms/?idpage=169')
    mydict = dict([e.strip().partition(" ")[::2]
                   for e in viewScriptCommand.split('--')])
    mydict['variable'] = [value for (var, value) in [e.strip().partition(
        " ")[::2] for e in viewScriptCommand.split('--')] if var == 'variable']
    prefix = '_'.join(
        list((mydict['service-id'].split('-')[0]).split('_')[i] for i in [0, -2, -1]))
    suffix = '.nc'
    minX = float(mydict['longitude-min'])
    maxX = float(mydict['longitude-max'])
    minY = float(mydict['latitude-min'])
    maxY = float(mydict['latitude-max'])
    list_abs = [abs(maxX - minX), abs(maxY - minY)]
    try:
        minZ = float(mydict['depth-min'])
        maxZ = float(mydict['depth-max'])
        list_abs.append(abs(maxZ - minZ))
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
            if maxX == minX and maxY == minX:
                key = f'_gridpoint-lon{minX}-lat{str(minX).replace(".","dot")}'
    if any(x in dataset_name for x in temporal_resolution_hourly):
        monthstack = True
    if len(mydict['variable']) > 6:
        monthstack = True
        outVarName = 'several_vars'
    else:
        outVarName = '_'.join(mydict['variable'])
    print('\n+------------------------------------+\n| ! - CONNECTION TO CMEMS HUB - OPEN |\n+------------------------------------+\n\n')
    for retry in range(1, 4):
        retry_flag = False
        date_start = dt.datetime.strptime(
            viewScriptCommand.split('"')[1], '%Y-%m-%d %H:%M:%S')
        date_end = dt.datetime.strptime(
            viewScriptCommand.split('"')[3], '%Y-%m-%d %H:%M:%S')
        while date_start <= date_end:
            if dailystack:
                date_end_cmd = date_start
                stack, dtformat = ['_daystack-', "%Y%m%d"]
            elif monthstack:
                date_end_cmd = (dt.datetime(date_start.year, date_start.month,
                                            calendar.monthrange(date_start.year, date_start.month)[1], 23))
                stack, dtformat = ['_monthstack-', "%Y%m"]
            else:
                if date_start.year == date_end.year:
                    date_end_cmd = (dt.datetime(date_start.year, date_end.month,
                                                calendar.monthrange(date_start.year, date_end.month)[1], 23))
                else:
                    date_end_cmd = (dt.datetime(date_start.year, 12, 31, 23))
                stack, dtformat = ['_yearstack-', "%Y"]
            date_start_cmd = dt.datetime(
                date_start.year, date_start.month, date_start.day, 0)
            substitute = {viewScriptCommand.split('"')[1]: date_start_cmd.strftime(
                '%Y-%m-%d %H:%M:%S'), viewScriptCommand.split('"')[3]: date_end_cmd.strftime('%Y-%m-%d %H:%M:%S')}
            dtEndFormat = date_end_cmd.strftime(dtformat)
            outname = '-'.join(['CMEMS', prefix, outVarName,
                                dtEndFormat + suffix])
            command = ' '.join([multireplace(viewScriptCommand, substitute), ' -o ', str(
                target_directory), ' -f ', outname, ' -u ', user, ' -p ', pwd, '-q'])
            print('\n----------------------------------\n- ! - Processing dataset request : '
                  '%s\n----------------------------------\n' % outname)
            date_start = date_end_cmd + dt.timedelta(days=1)
            if not Path(target_directory / outname).exists():
                print('## MOTU API COMMAND ##')
                print(command.replace(user, '*****').replace(pwd, '*****'))
                print('\n[INFO] CMEMS server is checking both your credentials and command syntax. '
                      'If successful, it will extract the data and create your dataset on the fly. Please wait. \n')
                flag, state = get_data(command, logging)
                if flag:
                    print('[INFO] The dataset for {} has been stored in {}.'.format(
                        outname, target_directory))
                else:
                    retry_flag = True
            else:
                print("[INFO] The dataset for {} has already been downloaded in {}\n".format(
                    outname, target_directory))
        if not retry_flag:
            break
    print("+-------------------------------------+\n| ! - CONNECTION TO CMEMS HUB - CLOSE |\n+-------------------------------------+\n")
    with open(LOGFILE) as f:
        if retry == 3 and 'ERROR' in f.read():
            print("## YOUR ATTENTION IS REQUIRED ##")
            print(
                f'Some download requests failed, though {retry} retries. Please see recommendation in {LOGFILE})')
            print('TIPS: you can also apply hereafter recommendations.'
                  '\n1.  Do not move netCDF files'
                  '\n2.  Double check if a change must be done in the viewscript, FTR it is currently set to:\n')
            print(view_myscript)
            print('\n3.  Check there is not an ongoing maintenance by looking at the User Notification Service and Systems & Products Status:\n',
                  'https://marine.copernicus.eu/services-portfolio/news-flash/'
                  '\n4.  Then, if relevant, do relaunch manually this python script to automatically download only failed data request(s)'
                  '\n5.  Finally, feel free to contact our Support Team either:\n  - By mail: servicedesk.cmems@mercator-ocean.eu or \n  - By using the webform: https://marine.copernicus.eu/services-portfolio/contact-us/ or \n  - By leaving a post on the forum: https://forum.marine.copernicus.eu\n\n')
            return False
        else:
            print('\n------------------------------------------------\n - ! - Your Copernicus Dataset(s) are located in '
                  '%s\n------------------------------------------------\n' % (target_directory))
    return outname

###############################
# TODO: Create Class ChDiskFile
###############################


def convert_size_hr(size_in_bytes):
    if size_in_bytes == 0:
        return '0 Byte'
    size_standard = ('B', 'KiB', 'MiB', 'GiB', 'TiB')
    integer = int(math.floor(math.log(size_in_bytes, 1_024)))
    powmath = math.pow(1_024, integer)
    precision = 2
    size = round(size_in_bytes / powmath, precision)
    return size, size_standard[integer]


def get_disk_stat(drive=None):
    if not drive:
        drive = '/'
    disk_stat = list(shutil.disk_usage(drive))
    return disk_stat


def get_file_size(files):
    mds_size = 0
    for file in files:
        with xr.open_dataset(file, decode_cf=False) as sds:
            mds_size = mds_size + sds.nbytes
    return mds_size


def check_file_size(mds_size, default_nc_size=None):
    if not default_nc_size:
        default_nc_size = 16_000_000_000
    check_fs = False
    size, unit = display_disk_stat(mds_size)
    if mds_size == 0:
        print(f'[ERROR-NETCDF] There is an error to assess the size of netCDF file(s). Please check if data are not corrupted.')
    elif size == 0:
        print(f'[ERROR] Program exit.')
    elif mds_size > default_nc_size:
        print(f'[INFO-NETCDF] The size of the netCDF file would be higher than 16 GiB.')
        force = query(
            f'[ACTION-NETCDF] Do you still want to create the netCDF file of size {size} {unit}?', 'no')
        if not force:
            print(
                '[ERROR-NETCDF] Writing to disk action has been aborted by user due to file size issue.')
            print(
                '[INFO-NETCDF] The script will try to write several netCDF files with lower file size.')
        else:
            check_fs = True
    else:
        check_fs = True
    return check_fs


def display_disk_stat(mds_size):
    disk_stat = get_disk_stat()
    free_after = disk_stat[2] - mds_size
    disk_stat.append(free_after)
    disk_stat.append(mds_size)
    try:
        total_hr, used_hr, free_hr, free_after_hr, mds_size_hr = [
            convert_size_hr(item) for item in disk_stat]
    except ValueError as e:
        msg = "[WARNING] Operation shall be aborted to avoid NO SPACE LEFT ON DEVICE error."
        mds_size_hr = (0, 'B')
    else:
        space = '-'*37
        msg = ''.join((f"[INFO] {space}\n",
                       f"[INFO] Total Disk Space (before operation) : {total_hr[1]} {total_hr[0]} \n",
                       f"[INFO] Used Disk Space (before operation)  : {used_hr[1]} {used_hr[0]} \n",
                       f"[INFO] Free Disk Space (before operation)  : {free_hr[1]} {free_hr[0]} \n",
                       f"[INFO] Operation to save dataset to Disk   : {mds_size_hr[1]} {mds_size_hr[0]} \n",
                       f"[INFO] Free Disk Space (after operation)   : {free_after_hr[1]} {free_after_hr[0]} \n",
                       f"[INFO] {space}"))
    print(''.join(("[INFO] CHECK DISK STATISTICS\n", msg)))
    return mds_size_hr


###############################
# TODO: Create Class ManipFiles
###############################

def get_file_pattern(outname, sep='-', rem=-1, advanced=True):
    if 'pathlib' in str(type(outname)):
        outname = outname.name
    if advanced:
        file_pattern = outname.replace(outname.split(sep)[rem], '')[:-1]
    else:
        # To be coded
        pass
    return file_pattern


def get_years(ncfiles, sep='-'):
    years = set([str(f).split(sep)[-1][:4] for f in ncfiles])
    return years


def get_ncfiles(target_directory, file_pattern=None, year=None):
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


def set_outputfile(file_pattern, target_out_directory=Path(DEFAULT_CURRENT_PATH, 'copernicus-processed-data'), start_year=None, end_year=None):
    if 'str' in str(type(target_out_directory)):
        target_out_directory = Path(target_out_directory)
    if not target_out_directory.exists():
        target_out_directory.mkdir(parents=True)
    if not end_year:
        outputfile = target_out_directory / f'{file_pattern}-{start_year}.nc'
    else:
        outputfile = target_out_directory / \
            f'{file_pattern}-{start_year}_{end_year}.nc'
    return outputfile


def overwrite(outputfile):
    ow = True
    if outputfile.exists():
        ow = query(
            f'[ACTION] The file {outputfile} already exists. Do you want to overwrite it?', 'no')
    return ow


def del_ncfiles(ncfiles):
    for fnc in ncfiles:
        try:
            fnc.unlink()
        except OSError as e:
            print(f'[ERROR]: {fnc} : {e.strerror}')
    print('[INFO-NETCDF] All inputs netCDF files have been successfully deleted.')
    return True


def to_nc4(mds, outputfile):
    if not 'xarray.core.dataset.Dataset' in str(type(mds)):
        mds = xr.open_mfdataset(mds, combine='by_coords')
    if 'str' in str(type(outputfile)):
        outputfile = Path(outputfile)
    prepare_encoding = {}
    for variable in mds.data_vars:
        prepare_encoding[variable] = mds[variable].encoding
        prepare_encoding[variable]['zlib'] = True
        prepare_encoding[variable]['complevel'] = 1
    encoding = {}
    for k, v in prepare_encoding.items():
        encoding.update(
            {k: {key: value for key, value in v.items() if key != 'coordinates'}})
    try:
        mds.to_netcdf(path=outputfile,
                      mode='w',
                      engine='netcdf4',
                      encoding=encoding)
    except ValueError as e:
        print(
            f'[INFO-NETCDF] Convertion initialized but ended in error due to : {e}')
        nc4 = False
    else:
        real_file_size = convert_size_hr(outputfile.stat().st_size)
        space = '-'*20
        msg = ''.join((f"[INFO] {space}\n", f"[INFO-NETCDF] Output file : {str(outputfile)}\n",
                       f"[INFO-NETCDF] File format : netCDF-4\n",
                       f"[INFO-NETCDF] File size   : {real_file_size[0]} {real_file_size[1]}\n",
                       f"[INFO] {space}"))
        print(''.join(("[INFO] CONVERTING TO NETCDF4\n", msg)))
        nc4 = True
    return nc4


def to_csv(mds, outputfile):
    if not 'xarray.core.dataset.Dataset' in str(type(mds)):
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
        print(f'[INFO-CSV] The total number of rows exceeds MS Excel limit. It is NOT recommended to continue.')
        force = query(
            f'[ACTION-CSV] Do you still want to create this CSV file with {nb_grid_pts} rows (though most computers will run out of memory)?', 'no')
    if nb_grid_pts < ms_excel_row_limit or force:
        try:
            df = mds.to_dataframe().reset_index().dropna()
            df.to_csv(outputfile.with_suffix('.csv'), index=False)
        except:
            print(f'[INFO-CSV] Convertion initialized but ended in error.')
        else:
            space = '-'*18
            msg = ''.join((f"[INFO]{space}\n", f"[INFO-CSV] Output file : {str(outputfile)}\n",
                           f"[INFO-CSV] File format : Comma-Separated Values\n",
                           f"[INFO-CSV] Preview Stat:\n {df.describe()}\n",
                           f"[INFO] {space}"))
            print(''.join(("[INFO] CONVERTING TO CSV\n", msg)))
            csv = True
    else:
        print(
            f'[WARNING-CSV] Writing to disk action has been aborted by user due to very high number of rows ({nb_grid_pts}) exceeding most computers and softwares limits (such as MS Excel).')
        print(''.join(('[INFO-CSV] A new version will be proposed to handle this use case automatically by splitting big table in several spreadsheets.\n[INFO-CSV] To upvote this feature, ', msg2)))
    try:
        mds.close()
        del mds
    except:
        print(''.join(('[DEBUG] ', msg2)))
    return csv


def to_nc4_csv(ncfiles, outputfile, skip_csv=False, default_nc_size=None):
    nc4 = False
    csv = False
    if not default_nc_size:
        default_nc_size = 16_000_000_000
    mds_size = get_file_size(ncfiles)
    check_fs = check_file_size(mds_size, default_nc_size)
    check_ow = overwrite(outputfile)
    check_ow_csv = overwrite(outputfile.with_suffix('.csv'))
    if check_ow and check_fs:
        with xr.open_mfdataset(ncfiles, combine='by_coords') as mds:
            nc4 = to_nc4(mds, outputfile)
    elif not check_ow:
        print('[WARNING-NETCDF] Writing to disk action has been aborted by user due to already existing file.')
    elif not check_fs:
        skip_csv = True
    if check_ow_csv and not skip_csv:
        with xr.open_mfdataset(ncfiles, combine='by_coords') as mds:
            csv = to_csv(mds, outputfile)
    return nc4, csv, check_ow


def post_processing(outname, target_directory, delete_files=True):
    """
    Post-process the data already located on disk: concatenate a complete timerange in a single netcdf file, or if not possible, stack periods on minimum netcdf files (either by year or by month).

    There is a possibility to delete old files to save space (thanks to nc3 -> nc4) and to convert to `CSV`, if technically feasible.

    Parameters
    ----------


    See Also
    --------
    get_file_pattern:
    get_ncfiles:
    get_years:
    set_outputfile:
    to_nc4_csv:
    del_ncfiles:
    """

    processing = False
    try:
        file_pattern = get_file_pattern(outname)
    except AttributeError as e:
        print('[ERROR] Program exits due to fatal error on server. Please refer to points 3 and/or 5 above.')
        raise SystemExit
    sel_files = get_ncfiles(target_directory, file_pattern)
    years = get_years(sel_files)
    try:
        single_outputfile = set_outputfile(
            file_pattern, start_year=min(years), end_year=max(years))
    except ValueError as e:
        print(
            f'[ERROR] Processing failed due to no file matching pattern : {e}')
    else:
        nc4, csv, overwrite = to_nc4_csv(sel_files, single_outputfile)
        if not nc4 and not csv and overwrite:
            for year in years:
                print(year)
                ncfiles = get_ncfiles(target_directory, file_pattern, year)
                outfilemerged = set_outputfile(file_pattern, start_year=year)
                to_nc4_csv(ncfiles, outfilemerged)
                if delete_files:
                    del_ncfiles(ncfiles)
        processing = True
    return processing


def download_data_and_postprocess(local_storage_directory=None, view_myscript=None, user=None, pwd=None, dailystack=False, delete_files=False):
    """
    Download and post-process files to both compressed and tabular formats, if applicable.

    Download as many subsets of dataset required to fulfill an initial data request based on a template command, called `VIEW SCRIPT` generated by Copernicus Marine website (https://marine.copernicus.eu).
    Then, all files are post-processed locally: e.g to concatenate in a single file, to save space (thanks to nc3 -> nc4), to convert to `CSV` (if technically possible), and to delete old files.
    End-user is guided throughout the process if no parameter is declared. To get started, this function is the main entry point.

    Parameters
    ----------
    It has no required parameter.

    See Also
    --------
    process_viewscript : Method to parse `VIEW SCRIPT`
    post_processing : Method to convert downloaded data to other format (netcdf4, csv etc)
    """

    target_directory = set_target_directory()
    outname = process_viewscript(target_directory=target_directory,
                                 view_myscript=view_myscript, user=user, pwd=pwd, dailystack=dailystack)
    post_processing(outname, target_directory, delete_files=delete_files)


if __name__ == '__main__':
    fire.Fire({
        'display_disk_stat': display_disk_stat,
        'download_data_and_postprocess': download_data_and_postprocess,
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
