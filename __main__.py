from cmemsapi import *
import fire

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
