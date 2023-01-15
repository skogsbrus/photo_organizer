#!/usr/bin/env python3

import sys
import argparse
import logging as log
import glob
from pathlib import Path
from shutil import copy
from os.path import splitext
from pyexifinfo import get_json
from threading import Thread, Lock
import subprocess


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--exclude',
        type=str,
        nargs='+',
        default=[],
        help='Exclude paths containing any of these strings. Case sensitive.'
    )
    parser.add_argument(
        '--suffix',
        type=str,
        nargs='+',
        default=['.avi', '.png', '.jpg', '.jpeg', '.raw', '.mov', '.mp4', '.flv', '.mkv'],
        help='Filter on file name suffix. Case insensitive.'
    )
    parser.add_argument(
        '--prefix',
        type=str,
        nargs='+',
        default=[''],
        help='Filter on file name prefix. Case insensitive.'
    )
    parser.add_argument(
        '--out',
        type=str,
        required=True,
        default='./restructured',
        help='Output  directory path'
    )
    parser.add_argument(
        '--dir',
        type=str,
        required=True,
        help='Input directory path'
    )
    parser.add_argument(
        '--log',
        type=str,
        help='Log file path'
    )
    parser.add_argument(
        '--nbr-threads',
        type=int,
        default=4,
        help='Number of threads to run concurrently'
    )
    parser.add_argument(
        '--delete-after-copy',
        action='store_true',
        help=(
                'Delete the original file after it'
                ' has been copied and renamed OR skipped.'
                ' BACKUP your input before doing this.'
             )
    )
    parser.add_argument(
        '--silent',
        action='store_true',
    )
    return parser.parse_args()


def setup_args(args):
    for p in Path(args.out).resolve().parents:
        print(p.resolve())
        assert p != Path(args.dir), 'Output dir can not be inside the input dir'
    if args.log:
        setup_log_file(args.log)

    global out_dir, failed_dir, prefices, suffices, exclude, delete_after_copy
    delete_after_copy = args.delete_after_copy
    out_dir = create_dir(Path(args.out))
    failed_dir = create_dir(Path(out_dir/'failed'))
    suffices = []
    prefices = args.prefix
    suffices = args.suffix
    exclude = args.exclude


def setup_log_file(filename):
    log.basicConfig(filename=filename, level=log.INFO, format='%(asctime)s %(message)s')


def parse_date_from_metadata(path: str, keys: list) -> str:
    metadata = get_json(path)[0]

    for key in keys:
        if key in metadata:
            return str(metadata[key])
    raise KeyError


def get_date(path: str) -> str:
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


def get_new_name(fp: str) -> str:
    date = get_date(fp)
    _, ext = splitext(fp)
    if date:
        date = date.replace(' ', '_')
        date = date.replace(':', '.')
        return date + ext.lower()


def prompt_proceed(msg='Proceed? (y/n)'):
    if input(msg + ' ') != 'y':
        sys.exit(0)


def create_dir(directory: Path) -> Path:
    try:
        directory.mkdir()
    except FileExistsError:
        pass
    return directory


def files_equal(fp1: str, fp2: str, chunk_sz=2**24) -> bool:
    with open(fp1, 'rb') as f1:
        with open(fp2, 'rb') as f2:
            while True:

                try:
                    mut_global.acquire()
                    chunk1 = f1.read(chunk_sz)
                    chunk2 = f2.read(chunk_sz)
                finally:
                    mut_global.release()

                f1.seek(chunk_sz, 1)
                f2.seek(chunk_sz, 1)
                if chunk1 != chunk2:
                    result = False
                    break
                if not chunk1 or not chunk2:
                    assert not chunk1 and not chunk2
                    result = True
                    break
    return result


def sifted_by_arguments(f: str) -> bool:
    f_path = Path(f)
    filename = f_path.name.lower()
    if f_path.is_dir():
        return True
    if not any(filename.startswith(prefix.lower()) for prefix in prefices):
        return True
    if not any(filename.endswith(suffix.lower()) for suffix in suffices):
        return True
    if any([ex in str(f_path.resolve()) for ex in exclude]):
        return True
    return False


def maybe_delete_file(f_str: str):
    if delete_after_copy:
        Path(f_str).unlink()
        log.info('delete {}'.format(f_str))


def get_conflict_name(f: str, target_dir: str, new_name: str):
    i = 1
    t_path = Path(target_dir)
    name, extension = splitext(new_name)
    while (t_path/new_name).exists():
        if not files_equal(str(t_path/new_name), f):
            new_name = '{}_conflict{}{}'.format(name, i, extension)
            i += 1
        else:
            log.info('skip {} - duplicate of {}'.format(f,
                                                        str((t_path/new_name).resolve())))
            return None
    return new_name


def copy_and_rename_file(src_str: str):
    src_path = Path(src_str)
    if sifted_by_arguments(src_path):
        return

    new_name = get_new_name(src_str)

    if new_name:
        year = new_name[:4]
        dest_path = Path(out_dir)/year
    else:
        subdir_name = str(src_path.parent.resolve()).replace('/', '_')
        dest_path = failed_dir/(subdir_name)
        new_name = src_path.name

    dest_path = create_dir(dest_path)
    dest_str = str(dest_path.resolve())

    conflict_name = get_conflict_name(src_str, dest_str, new_name)
    if conflict_name:
        new_name = conflict_name
    else:
        maybe_delete_file(src_str)
        return

    try:
        mut_global.acquire()
        copy(src_str, dest_str)
    finally:
        mut_global.release()

    copied_file = dest_path/src_path.name
    copied_file.rename(dest_path/new_name)
    log.info('copy {} -> {}'.format(src_str, str((dest_path/new_name).resolve())))
    maybe_delete_file(src_str)


class Copier(Thread):
    index = 0

    def __init__(self, run_func=copy_and_rename_file):
        self.func = run_func
        self.index = Copier.index
        Copier.index += 1
        super(Copier, self).__init__()

    def run(self):
        global err_global
        while True:
            mut_global.acquire()
            err = err_global
            try:
                filepath = files_global.__next__()
            except StopIteration:
                return
            finally:
                mut_global.release()

            # exit if any thread failed
            if err:
                err_msg = "Thread {} returning: global error was set".format(self.index)
                log.warning(err_msg)
                return

            # catch all errors and set global error if they occur
            try:
                self.func(filepath)
            except Exception as e:
                mut_global.acquire()
                err_global = True
                mut_global.release()
                err_msg = "Thread {} raised an exception: ".format(self.index)
                log.warning(err_msg, exc_info=e)


if __name__ == "__main__":
    args = get_args()
    mut_global = Lock()  # used for thread safety and disk writes
    err_global = False
    setup_args(args)
    print(args)
    if not args.silent:
        print('Selecting files that start with any of {}'.format(prefices),
              'and end with any of {}'.format(suffices))
        if args.exclude:
            print('Ignoring all files that have any of {} in their paths'.format(exclude))
        prompt_proceed()
        if delete_after_copy:
            prompt_proceed((
                'You have chosen to delete your input files after they processed.'
                'You are advised to have a backup of your input data when doing this.'
                'Are you sure you want to proceed? (y/n)'
            ))

    files_global = glob.iglob('{}/**/*'.format(args.dir), recursive=True)
    threads = []
    for _ in range(args.nbr_threads):
        threads.append(Copier())

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    log.info("End of main")
