#!/usr/bin/env python3
import pyexiv2
import concurrent.futures
import countries
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
    parser.add_argument('--organize-by-location', action='store_true', help='Reorganize files such that photos/videos are grouped by country of origin.')
    parser.add_argument('--add-location-tag', action='store_true', help='Add country of origin as an EXIF user comment tag')
    return parser.parse_args()


def setup_args(args):
    assert args.out.parent != args.dir, 'Output directory should not be put inside the input directory'
    if args.log:
        setup_log_file(args.log)

    global out_dir, failed_dir, prefices, suffices, exclude, delete_after_copy, organize_by_location, add_location_tag
    delete_after_copy = args.delete_after_copy
    out_dir = create_dir(args.out)
    failed_dir = create_dir(out_dir/'failed')
    suffices = []
    prefices = args.prefix
    add_location_tag = args.add_location_tag
    organize_by_location = args.organize_by_location
    for suf in args.suffix:
        suffices.extend([suf.lower(), suf.upper()])
    exclude = args.exclude


def setup_log_file(filename):
    log.basicConfig(filename=filename, level=log.INFO, format='%(asctime)s %(message)s')


def parse_key_from_metadata(path:Path, keys:list) -> str:
    metadata = get_json(path)[0]

    for key in keys:
        if key in metadata:
            return str(metadata[key])
    raise KeyError


def run_parse_funcs(parse_funcs: list, errors: tuple):
    for func in parse_funcs:
        try:
            return func()
        except errors:
            pass
    return None


def parse_coordinate(degrees: str) -> float:
     def is_number(w):
         try:
             float(w)
             return True
         except ValueError:
             return False

     def degree_to_dec(deg_min_sec: tuple) -> float: 
         assert len(deg_min_sec) == 3
         deg, minute, second = map(float, deg_min_sec)
         return deg + minute/60 + second/3600

     words = degrees.split(' ')
     words = list(map(lambda w: re.sub('[^0-9\.]', '', w), words)) 
     nums = list(filter(is_number, words)) 
     latitude, longitude = nums[0:3], nums[3:]

     return list(map(degree_to_dec, (latitude, longitude)))


def get_country(path: Path) -> str:
    metadata_keys = [
        'Composite:GPSPosition'
    ]

    parse_funcs = [
        lambda: parse_coordinate(parse_key_from_metadata(path, metadata_keys))
    ]
    
    coords = run_parse_funcs(parse_funcs, (AssertionError, KeyError))

    if not coords:
        return 'Unknown location'

    cc = countries.CountryChecker('TM_WORLD_BORDERS-0.3.shp')
    return str(cc.getCountry(countries.Point(coords[0], coords[1])))


def get_date(path: Path) -> str:
    metadata_keys = [
        'EXIF:DateTimeOriginal',
        'MakerNotes:DateTimeOriginal',
        'QuickTime:CreateDate'
    ]

    parse_funcs = [
        lambda: parse_key_from_metadata(path, metadata_keys),
    ]

    return run_parse_funcs(parse_funcs, (KeyError, ValueError, OverflowError))


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


def add_exif_tag(path:Path, value:str, key:str='Exif.Photo.Usercomment') -> None:
    metadata = pyexiv2.ImageMetadata(path)
    metadata.read()
    metadata[key] = value
    metadata.write()


def copy_and_rename_file(filepath:str):
    f = Path(filepath)
    if sifted_by_arguments(f):
        return

    new_name = get_new_name(f)

    if new_name:
        year = new_name[:4]
        if organize_by_location:
            country = get_country(f)
            year_dir = create_dir(out_dir/year)
            target_dir = year_dir/country
        else:
            target_dir = out_dir/year
    else:
        subdir_name = str(f.parent.resolve()).replace('/','_')
        target_dir = failed_dir/(subdir_name)
        new_name = f.name

    target_dir = create_dir(target_dir)

    conflict_name = get_conflict_name(f, target_dir, new_name)
    if conflict_name:
        new_name = conflict_name
    else:
        maybe_delete_file(f)
        return

    copy(f, target_dir)
    copied_file = target_dir/f.name
    copied_file.rename(target_dir/new_name)
    copied_file = target_dir/new_name
    log.info(f'copy {f.resolve()} -> {(target_dir/new_name).resolve()}')
    maybe_delete_file(f)
    if add_location_tag and country != 'Unknown location':
        add_exif_tag(copied_file, country)


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
        #executor.map(copy_and_rename_file, files)
    list(map(copy_and_rename_file, files))
    log.info('end of main')
