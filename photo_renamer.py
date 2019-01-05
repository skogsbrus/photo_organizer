#!/usr/bin/env python3

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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix',     type=str,   nargs='+',      default=['.png', '.jpg', '.raw', '.mov'],  help='Filter on suffix')
    parser.add_argument('--prefix',     type=str,   nargs='+',      default=[''],                      help='Filter on prefix')
    parser.add_argument('--exclude',    type=str,   nargs='+',                                         help='Exclude paths containing any of these strings')
    parser.add_argument('--dir',        type=Path,  required=True,                                     help='Working directory path')
    parser.add_argument('--out',        type=Path,  required=True,  default='./restructured',          help='Output  directory path')
    parser.add_argument('--logfile',    type=Path,                                                     help='Log file path')
    return parser.parse_args()


def setup_log_file(filename):
    log.basicConfig(filename=filename, level=log.INFO, format='%(asctime)s %(message)s')


def get_date(path: Path, exif_tag:str='EXIF DateTimeOriginal'):
    with open(path, 'rb') as img:
        tags = exifread.process_file(img)
    try:
        return str(tags[exif_tag])
    except KeyError:
        if 'MOV' in path.name:
            # .mov files don't have exif tags but it seems
            # that the original creation date is preserved in st_mtime
            return str(datetime.fromtimestamp(int(path.stat().st_mtime)))
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


def create_dirs(base_dir, failed_dirname='failed'):
    failed_dir = base_dir/Path(failed_dirname)
    try:
        base_dir.mkdir()
        failed_dir.mkdir()
    except FileExistsError:
        pass
    return base_dir, failed_dir


def assert_different_dirs(base_dir, out_dir):
    assert out_dir.parent != base_dir, 'Output directory should not be placed inside the directory being scanned'


def rename_file(file, new_name, new_dir, failed_dir):
    directory = new_dir/Path(new_name[:4]) if new_name else failed_dir/Path(file.parent.name)

    if not directory.is_dir():
        directory.mkdir()
    try:
        copy(file, directory)
    except SameFileError:
        log.info(f'copy for file {file} failed since it was already in the destination folder {directory}')
    file_copy = directory/file.name
    if new_name:
        file_copy.rename(directory/new_name)
    log.info(f'copied {file.resolve()} -> {(directory/file).resolve()}')


if __name__ == "__main__":
    args = get_args()
    assert_different_dirs(args.dir, args.out)
    if args.logfile:
        setup_log_file(args.logfile)
    suffices = []
    prefices = args.prefix
    for suf in args.suffix:
        suffices.append(suf.lower())
        suffices.append(suf.upper())

    # show parameter options
    print(f'Selecting files that start with any of {args.prefix} and end with any of {suffices}')
    if args.exclude:
        print(f'Ignoring all files in directories {args.exclude}')
    prompt_proceed()
    new_dir, failed_dir = create_dirs(args.out)

    for prefix, suffix in tqdm(product(prefices, suffices)):
        for file in tqdm(glob.iglob(f'{args.dir}/**/{prefix}*{suffix}', recursive=True)):
            file = Path(file)
            if file.is_dir():
                continue
            if not args.exclude or args.exclude and not any([ex in str(file.parent.resolve()) for ex in args.exclude]):
                file, new_name = (file, get_new_name(file))
                rename_file(file, new_name, new_dir, failed_dir)
