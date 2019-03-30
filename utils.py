#!/usr/bin/env python3
import sys
import logging as log
from pathlib import Path
from os.path import splitext
from pyexifinfo import get_json


def prompt_proceed(msg='Proceed? (y/n)'):
    if input(f'{msg} ') != 'y':
        sys.exit(0)


def files_equal(f1: Path, f2: Path) -> bool:
    return open(f1, 'rb').read() == open(f2, 'rb').read()


def create_dir(directory: Path) -> Path:
    try:
        directory.mkdir()
    except FileExistsError:
        pass


def setup_log_file(filename):
    log.basicConfig(filename=filename, level=log.INFO, format='%(asctime)s %(message)s')


def parse_date_from_metadata(path: Path, keys: list) -> str:
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

    try:
        return parse_date_from_metadata(path, metadata_keys)
    except (KeyError, ValueError, OverflowError):
        pass
    return None


def get_new_name(f: Path) -> str:
    date = get_date(f)
    if date:
        date = date.replace(' ', '_')
        date = date.replace(':', '.')
        return date + f.suffix.lower()


def ignore_file(f: Path, args) -> bool:
    if f.is_dir():
        return True
    if not any(f.name.startswith(prefix) for prefix in args.prefix):
        return True
    if not any(f.name.endswith(suffix) for suffix in args.suffix):
        return True
    if any([ex in str(f.resolve()) for ex in args.exclude]):
        return True
    return False


def maybe_delete_file(f: Path, args):
    if args.delete:
        f.unlink()
        log.info(f'delete {f.resolve()}')


def get_unique_name(f: Path, target_dir: Path, new_name: str) -> (str, bool):
    """
    Returns a unique name for the file, to prevent overwriting.
    Raises FileExistsError if file with same name and content already exists in target_dir
    """
    i = 1
    name, extension = splitext(new_name)
    while (target_dir/new_name).exists():
        if not files_equal((target_dir/new_name), f):
            new_name = f'{name}_conflict{i}{extension}'
            i += 1
        else:
            log.info(f'skip {f.resolve()} - duplicate of {(target_dir/new_name).resolve()}')
            raise FileExistsError
    return new_name
