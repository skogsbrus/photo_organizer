#!/usr/bin/env python3

import sys
import argparse
import logging as log
from pathlib import Path
from shutil import copy, SameFileError
import exifread
from itertools import product
from pprint import pprint
from tqdm import tqdm

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix',     type=str,   nargs='+',      default=['.jpg', '.raw'],  help='Filter on suffix')
    parser.add_argument('--prefix',     type=str,   nargs='+',      default=[''],              help='Filter on prefix')
    parser.add_argument('--exclude',    type=str,   nargs='+',                                 help='Exclude paths containing any of these strings')
    parser.add_argument('--dir',        type=Path,  required=True,                             help='Working directory path')
    parser.add_argument('--logfile',    type=Path,                                             help='Log file path')
    return parser.parse_args()


def setup_log_file(filename):
    log.basicConfig(filename=filename, level=log.INFO)

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
        return date + path.suffix
    else:
        return None


def prompt_proceed(msg='Proceed? (y/n)', exit=True):
    if input(msg + ' ') != 'y':
        if exit:
            sys.exit(0)
        return False
    return True


def rename_files(files_and_new_names: list, base_dir, new_dir='restructured', failed_dir='failed'):
    new_dir = base_dir/Path(new_dir)
    failed_dir = new_dir/Path(failed_dir)
    try:
        new_dir.mkdir()
        failed_dir.mkdir()
    except FileExistsError:
        pass

    for file, new_name in tqdm(files_and_new_names):
        if new_name:
            directory = new_dir/Path(new_name[:4])
            if not directory.is_dir():
                directory.mkdir()
            try:
                copy(file, directory)
            except SameFileError:
                log.info(f'copy for file {file} failed since it was already in the destination folder {directory}')
                continue
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

    selected = []
    for prefix, suffix in product(prefices, suffices):
        selected.extend(args.dir.glob(f'**/{prefix}*{suffix}'))

    # filter out directories
    selected = list(filter(lambda f: not f.is_dir(), selected))

    # exclude all files whose path matches any in args.exclude
    if args.exclude:
        selected = list(filter(lambda img: not any([ex in str(img.parent.resolve()) for ex in args.exclude]), selected))

    files_and_new_names = list(zip(selected, map(get_new_name, selected)))
    print(f'Found {len(files_and_new_names)} files that match your parameters. Would you like to see them?')
    preview = prompt_proceed(exit=False)
    if preview:
        print('[old name]\t[new name]')
        for old, new in files_and_new_names:
            print(f'{old}\t{new}')
    prompt_proceed('Proceed renaming selected files? (y/n) ')
    rename_files(files_and_new_names, args.dir)
