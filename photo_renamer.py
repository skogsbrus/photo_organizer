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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix',     type=str,   nargs='+',      default=['.png', '.jpg', '.raw'],  help='Filter on suffix')
    parser.add_argument('--prefix',     type=str,   nargs='+',      default=[''],              help='Filter on prefix')
    parser.add_argument('--exclude',    type=str,   nargs='+',                                 help='Exclude paths containing any of these strings')
    parser.add_argument('--dir',        type=Path,  required=True,                             help='Working directory path')
    parser.add_argument('--logfile',    type=Path,                                             help='Log file path')
    return parser.parse_args()


def setup_log_file(filename):
    log.basicConfig(filename=filename, level=log.INFO, format='%(asctime)s %(message)s')


def get_exif_tag(path: Path, tag:str='Image DateTime'):
    with open(path, 'rb') as img:
        tags = exifread.process_file(img)
    try:
        return str(tags[tag])
    except KeyError:
        return None


def get_new_name(path: Path):
    date = get_exif_tag(path)
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


def rename_file(file_and_new_name: tuple, base_dir, new_dir='restructured', failed_dir='failed'):
    new_dir = base_dir/Path(new_dir)
    failed_dir = new_dir/Path(failed_dir)
    try:
        new_dir.mkdir()
        failed_dir.mkdir()
    except FileExistsError:
        pass

    file = file_and_new_name[0]
    new_name = file_and_new_name[1]
    if new_name: # if image has the requested exif tag
        directory = new_dir/Path(new_name[:4])
        if not directory.is_dir():
            directory.mkdir()
        try:
            copy(file, directory)
        except SameFileError:
            log.info(f'copy for file {file} failed since it was already in the destination folder {directory}')
            return
        file_copy = directory/file.name
        file_copy.rename(directory/new_name)
        log.info(f'copied {file.resolve()} -> {(directory/new_name).resolve()}')
    else:
        directory = failed_dir/Path(file.parent.name)
        if not directory.is_dir():
            directory.mkdir()
        try:
            copy(file, directory)
        except SameFileError:
            log.info(f'copy for file {file} failed since it was already in the destination folder {directory}')
        file_copy = directory/file.name
        log.info(f'copied {file.resolve()} -> {(directory/file).resolve()}')


if __name__ == "__main__":
    args = get_args()
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

    for prefix, suffix in tqdm(product(prefices, suffices)):
        for file in tqdm(glob.iglob(f'{args.dir}/**/{prefix}*{suffix}', recursive=True)):
            file = Path(file)
            if file.is_dir():
                continue
            if not args.exclude or args.exclude and not any([ex in str(file.parent.resolve()) for ex in args.exclude]):
                file_and_new_name = (file, get_new_name(file))
                rename_file(file_and_new_name, args.dir)
