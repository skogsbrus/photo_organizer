#!/usr/bin/env python3

import concurrent.futures
import sys
import argparse
import logging as log
import glob
from pathlib import Path
from shutil import copy, SameFileError
import re
from os.path import splitext
from pyexifinfo import get_json

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exclude',    type=str,   nargs='+',                                                                          help='Exclude paths containing any of these strings')
    parser.add_argument('--suffix',     type=str,   nargs='+',      default=['.avi', '.png', '.jpg', '.jpeg', '.raw', '.mov', '.mp4'],  help='Filter on file name suffix')
    parser.add_argument('--prefix',     type=str,   nargs='+',      default=[''],                                                       help='Filter on file name prefix')
    parser.add_argument('--out',        type=Path,  required=True,  default='./restructured',                                           help='Output  directory path')
    parser.add_argument('--dir',        type=Path,  required=True,                                                                      help='Input directory path')
    parser.add_argument('--log',        type=Path,                                                                                      help='Log file path')
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


def parse_date_from_metadata(path:Path, keys:list) -> str:
    metadata = get_json(path)[0]

    for key in keys:
        if key in metadata:
            return str(metadata[key])
    raise KeyError


def get_date(path: Path) -> str:
    metadata_keys = [
        'EXIF:DateTimeOriginal',
        'MakerNotes:DateTimeOriginal',
        'QuickTime:CreateDate'
    ]

    parse_funcs = [
        lambda: parse_date_from_metadata(path, metadata_keys),
    ]

    for func in parse_funcs:
        try:
            return func()
        except (KeyError, ValueError, OverflowError):
            pass
    return None


def get_new_name(file: Path) -> str:
    date = get_date(file)
    if date:
        date = date.replace(' ', '_')
        date = date.replace(':', '.')
        return date + file.suffix.lower()


def prompt_proceed(msg='Proceed? (y/n)'):
    if input(msg + ' ') != 'y':
        sys.exit(0)


def create_dir(directory:Path) -> Path:
    try:
        directory.mkdir()
    except FileExistsError:
        pass
    return directory


def files_equal(f1:Path, f2:Path) -> bool:
    return open(f1, 'rb').read() == open(f2, 'rb').read()


def copy_and_rename_file(filepath=str):
    file = Path(filepath)
    if file.is_dir():
        return
    if not any(file.name.startswith(prefix) for prefix in prefices):
        return
    if not any(file.name.endswith(suffix) for suffix in suffices):
        return
    if any([ex in str(file.resolve()) for ex in args.exclude]):
        return

    new_name = get_new_name(file)

    if new_name:
        year = new_name[:4]
        target_directory = out_dir/Path(year)
    else:
        subfolder_name = str(file.parent.resolve()).replace('/','_')
        target_directory = failed_dir/(subfolder_name)
        new_name = file.name

    if not target_directory.is_dir():
        target_directory.mkdir()

    # check if duplicate file already exists in target directory
    if (target_directory/new_name).exists():
        if not files_equal(target_directory/new_name, file):
            new_filename, extension = splitext(new_name)
            i = 1
            while (target_directory/new_name).exists():
                new_name = f'{new_filename}_collision{i}{extension}'
                i += 1
        else:
            log.info(f'skip {file.resolve()} - duplicate of {(target_directory/new_name).resolve()}')
            return

    copy(file, target_directory)
    if file.name != new_name:
        copied_file = target_directory/file.name
        copied_file.rename(target_directory/new_name)
    log.info(f'copy {file.resolve()} -> {(target_directory/new_name).resolve()}')


if __name__ == "__main__":
    args = get_args()
    setup_args(args)
    print(f'Selecting files that start with any of {prefices} and end with any of {suffices}')
    if args.exclude:
        print(f'Ignoring all files in directories {exclude}')
    prompt_proceed()

    with concurrent.futures.ProcessPoolExecutor() as executor:
        files = glob.iglob(f'{args.dir}/**/*', recursive=True)
        executor.map(copy_and_rename_file, files)
    log.info('end of main')
