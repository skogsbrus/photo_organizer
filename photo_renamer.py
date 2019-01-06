#!/usr/bin/env python3

from pprint import pprint
import concurrent.futures
import sys
import argparse
import logging as log
import glob
from pathlib import Path
from shutil import copy, SameFileError
import exifread
from itertools import product
from tqdm import tqdm
from datetime import datetime
from dateutil.parser import parse
import re
from os.path import splitext
from pyexifinfo import get_json

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exclude',    type=str,   nargs='+',                                                                  help='Exclude paths containing any of these strings')
    parser.add_argument('--suffix',     type=str,   nargs='+',      default=['.png', '.jpg', '.jpeg', '.raw', '.mov', '.mp4'],  help='Filter on file name suffix')
    parser.add_argument('--prefix',     type=str,   nargs='+',      default=[''],                                               help='Filter on file name prefix')
    parser.add_argument('--out',        type=Path,  required=True,  default='./restructured',                                   help='Output  directory path')
    parser.add_argument('--dir',        type=Path,  required=True,                                                              help='Working directory path')
    parser.add_argument('--log',        type=Path,                                                                              help='Log file path')
    return parser.parse_args()


def setup_args(args):
    assert args.out.parent != args.dir, 'Output directory should not be put inside the input directory'
    if args.log:
        setup_log_file(args.log)

    global out_dir, failed_dir, prefices, suffices, exclude
    out_dir = create_dir(args.out)
    failed_dir = create_dir(out_dir/'failed')
    suffices = []
    prefices = args.prefix
    for suf in args.suffix:
        suffices.extend([suf.lower(), suf.upper()])
    exclude = args.exclude


def setup_log_file(filename):
    log.basicConfig(filename=filename, level=log.INFO, format='%(asctime)s %(message)s')


def parse_filename_to_date(filename:str):
    filename = splitext(filename)[0] # remove file extension
    only_numbers = re.sub('[^0-9]', '', filename)
    if len(only_numbers) != 14: # length of YYYYMMDDHHMMSS
        raise ValueError
    return str(parse(only_numbers))


def parse_filestat_to_date(path:Path):
    return str(datetime.fromtimestamp(int(path.stat().st_mtime)))


def parse_date_from_metadata(path:Path, keys:list):
    with open(path, 'rb') as f:
        metadata = get_json(path)[0]

    for key in keys:
        if key in metadata:
            return str(metadata[key])
    log.info(f'Did not find any Image metadata for {path.name}')
    raise KeyError


def get_date(path: Path):
    metadata_keys = [
        'EXIF:DateTimeOriginal',
        'MakerNotes:DateTimeOriginal',
        'QuickTime:CreateDate'
    ]

    parse_funcs = [
        lambda: parse_date_from_metadata(path, metadata_keys),
        #lambda: parse_filename_to_date(path.name),
        #lambda: parse_filestat_to_date(path)
    ]

    for func in parse_funcs:
        try:
            return func()
        except (KeyError, ValueError, OverflowError):
            pass
    return None


def get_new_name(path: Path):
    date = get_date(path)
    if date:
        date = date.replace(' ', '_')
        date = date.replace(':', '.')
        return date + path.suffix.lower()
    else:
        return None


def prompt_proceed(msg='Proceed? (y/n)', exit=True):
    if input(msg + ' ') != 'y':
        if exit:
            sys.exit(0)
        return False
    return True


def create_dir(directory:Path):
    try:
        directory.mkdir()
    except FileExistsError:
        pass
    return directory


def rename_file(filepath=str):
    file = Path(filepath)
    if file.is_dir():
        return
    if not any(file.name.startswith(prefix) for prefix in prefices):
        return
    if not any(file.name.endswith(suffix) for suffix in suffices):
        return
    if any([ex in str(file.parent.resolve()) for ex in args.exclude]):
        return

    new_name = get_new_name(file)
    directory = out_dir/Path(new_name[:4]) if new_name else failed_dir/Path(file.parent.name)

    if not directory.is_dir():
        directory.mkdir()
    try:
        copy(file, directory)
    except SameFileError:
        log.info(f'copy for file {file} failed since it was already in the destination folder {directory}')
    file_copy = directory/file.name
    if new_name:
        # TODO check for already existing
        file_copy.rename(directory/new_name)
        log.info(f'copied {file.resolve()} -> {(directory/new_name).resolve()}')


if __name__ == "__main__":
    args = get_args()
    setup_args(args)
    print(f'Selecting files that start with any of {prefices} and end with any of {suffices}')
    if args.exclude:
        print(f'Ignoring all files in directories {exclude}')
    prompt_proceed()

    with concurrent.futures.ProcessPoolExecutor() as executor:
        files = glob.iglob(f'{args.dir}/**/*', recursive=True)
        executor.map(rename_file, files)
