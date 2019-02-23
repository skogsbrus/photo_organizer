#!/usr/bin/env python3
import argparse
import glob
import logging as log
from shutil import copy
import concurrent.futures
from utils import setup_log_file, create_dir, ignore_file, get_new_name, \
        get_unique_name, maybe_delete_file, prompt_proceed
from pathlib import Path


def setup_args(args):
    assert args.dir not in args.out.parents, \
        'Output directory can not be inside the input directory'
    if args.log:
        setup_log_file(args.log)
    create_dir(args.out)
    create_dir(args.fail)
    suffices = []
    for suf in args.suffix:
        suffices.extend([suf.lower(), suf.upper()])
    args.suffix = suffices
    del suffices


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--exclude',
        type=str,
        nargs='+',
        default=[],
        help='Exclude paths containing any of these strings'
    )
    parser.add_argument(
        '--suffix',
        type=str,
        nargs='+',
        default=['.avi', '.png', '.jpg', '.jpeg', '.raw', '.mov', '.mp4'],
        help='Filter on file name suffix'
    )
    parser.add_argument(
        '--prefix',
        type=str,
        nargs='+',
        default=[''],
        help='Filter on file name prefix'
    )
    parser.add_argument(
        '--out',
        type=Path,
        required=True,
        help='Output  directory path'
    )
    parser.add_argument(
        '--fail',
        type=Path,
        required=True,
        help='Output fail directory path'
    )
    parser.add_argument(
        '--dir',
        type=Path,
        required=True,
        help='Input directory path'
    )
    parser.add_argument(
        '--log',
        type=Path,
        help='Log file path'
    )
    parser.add_argument(
        '--delete',
        action='store_true',
        help=(
                'Delete the original file after it'
                ' has been copied and renamed OR skipped.'
                ' BACKUP your input before doing this.'
             )
    )
    return parser.parse_args()


def copy_and_rename_file(filepath: str, args: argparse.Namespace):
    f = Path(filepath)
    if ignore_file(f, args):
        return

    new_name = get_new_name(f)

    if new_name:
        year = new_name[:4]
        target_dir = args.out/Path(year)
    else:
        subdir_name = str(f.parent.resolve()).replace('/', '_')
        target_dir = args.fail/(subdir_name)
        new_name = f.name

    create_dir(target_dir)

    try:
        new_name = get_unique_name(f, target_dir, new_name)
    except FileExistsError:
        maybe_delete_file(f, args)
        return

    copy(f, target_dir)
    copied_file = target_dir/f.name
    copied_file.rename(target_dir/new_name)
    if args.log:
        log.info(f'copy {f.resolve()} -> {(target_dir/new_name).resolve()}')
    maybe_delete_file(f, args)


if __name__ == "__main__":
    args = get_args()
    setup_args(args)
    if args.delete:
        prompt_proceed((
            'You have chosen to delete your input files after they processed.'
            'You are advised to have a backup of your input data when doing this.'
            'Are you sure you want to proceed? (y/n)'
        ))

    def cp_rename(file_and_args):
        copy_and_rename_file(*file_and_args)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        files = glob.iglob(f'{args.dir}/**/*', recursive=True)
        map_args = ((f, args) for f in files)
        executor.map(cp_rename, map_args)
    if args.log:
        log.info('end of main')
