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
    parser.add_argument('--exclude',            type=str,   nargs='+',      default=[],                                                         help='Exclude paths containing any of these strings')
    parser.add_argument('--suffix',             type=str,   nargs='+',      default=['.avi', '.png', '.jpg', '.jpeg', '.raw', '.mov', '.mp4'],  help='Filter on file name suffix')
    parser.add_argument('--prefix',             type=str,   nargs='+',      default=[''],                                                       help='Filter on file name prefix')
    parser.add_argument('--out',                type=Path,  required=True,  default='./restructured',                                           help='Output  directory path')
    parser.add_argument('--dir',                type=Path,  required=True,                                                                      help='Input directory path')
    parser.add_argument('--log',                type=Path,                                                                                      help='Log file path')
    parser.add_argument('--delete-after-copy',  action='store_true',                                                                            help='Delete the original file after it has been copied and renamed OR skipped. BACKUP your input before doing this.')
    return parser.parse_args()


def setup_args(args):
    assert args.out.parent != args.dir, 'Output directory should not be put inside the input directory'
    if args.log:
        setup_log_file(args.log)

    global out_dir, failed_dir, prefices, suffices, exclude, delete_after_copy
    delete_after_copy = args.delete_after_copy
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


def sifted_by_arguments(file: Path) -> bool:
    if file.is_dir():
        return True
    if not any(file.name.startswith(prefix) for prefix in prefices):
        return True
    if not any(file.name.endswith(suffix) for suffix in suffices):
        return True
    if any([ex in str(file.resolve()) for ex in exclude]):
        return True
    return False


def maybe_delete_file(file:Path):
    if delete_after_copy:
        file.unlink()
        log.info(f'delete {file.resolve()}')


def get_conflict_name(file:Path, target_dir:Path, new_name:str):
    i = 1
    name, extension = splitext(new_name)
    while (target_dir/new_name).exists():
        if not files_equal((target_dir/new_name), file):
            new_name = f'{name}_conflict{i}{extension}'
            i += 1
        else:
            log.info(f'skip {file.resolve()} - duplicate of {(target_dir/new_name).resolve()}')
            return None
    return new_name



def copy_and_rename_file(filepath:str):
    file = Path(filepath)
    if sifted_by_arguments(file):
        return

    new_name = get_new_name(file)

    if new_name:
        year = new_name[:4]
        target_dir = out_dir/Path(year)
    else:
        subdir_name = str(file.parent.resolve()).replace('/','_')
        target_dir = failed_dir/(subdir_name)
        new_name = file.name

    target_dir = create_dir(target_dir)

    conflict_name = get_conflict_name(file, target_dir, new_name)
    if conflict_name:
        new_name = conflict_name
    else:
        maybe_delete_file(file)
        return

    copy(file, target_dir)
    copied_file = target_dir/file.name
    copied_file.rename(target_dir/new_name)
    log.info(f'copy {file.resolve()} -> {(target_dir/new_name).resolve()}')
    maybe_delete_file(file)


if __name__ == "__main__":
    args = get_args()
    setup_args(args)
    print(f'Selecting files that start with any of {prefices} and end with any of {suffices}')
    if args.exclude:
        print(f'Ignoring all files in directories {exclude}')
    prompt_proceed()
    if delete_after_copy:
        prompt_proceed('You have chosen to delete your input files after they processed. You are advised to have a backup of your input data when doing this. Are you sure you want to proceed? (y/n)')

    with concurrent.futures.ProcessPoolExecutor() as executor:
        files = glob.iglob(f'{args.dir}/**/*', recursive=True)
        executor.map(copy_and_rename_file, files)
    log.info('end of main')
