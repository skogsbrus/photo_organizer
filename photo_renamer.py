#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path
import exifread
from itertools import product

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix',     type=str, nargs='+', default=['.jpg', '.raw'], help='Suffix (file ending) which the affected files must end with')
    parser.add_argument('--prefix',     type=str, nargs='+', default=[''], help='Prefix which the affected files must begin with')
    parser.add_argument('--dir',        type=Path, required=True, help='Directory path')
    parser.add_argument('--exclude',    type=str, nargs='+', help='Ignore paths matching')
    return parser.parse_args()


def get_exif_tag(path: Path, tag:str='Image DateTime'):
    try:
        with open(path, 'rb') as img:
            tags = exifread.process_file(img)
        date = str(tags[tag])
        date = date.replace(' ', '_')
        date = date.replace(':', '.')
    except KeyError:
        return None
    return Path(date + path.suffix)

if __name__ == "__main__":
    args = get_args()
    suffices = []
    prefices = args.prefix
    for suf in args.suffix:
        suffices.append(suf.lower())
        suffices.append(suf.upper())
    print(f'Selecting files that start with any of {args.prefix} and end with any of {suffices}')
    if args.exclude:
        print(f'Ignoring all files in directories {args.exclude}')
    proceed = input('Proceed? (y/n) ')
    if proceed != 'y':
        sys.exit(0)
    selected = []
    for prefix, suffix in product(prefices, suffices):
        selected.extend(args.dir.glob(f'**/{prefix}*{suffix}'))
    selected = list(filter(lambda f: not f.is_dir(), selected))
    if args.exclude:
        selected = list(filter(lambda img: not any([ex in str(img.parent.resolve()) for ex in args.exclude]), selected))
    tups = list(zip(selected, map(get_exif_tag, selected)))
    for old, new in tups:
        if new:
            print(f'renaming {old} -> {new}')
            old.rename(new)
        else:
            pass
            print(f'no date found for {old}')
