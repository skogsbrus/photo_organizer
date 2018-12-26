#!/usr/bin/env python3

import argparse
from pathlib import Path
import glob
from PIL import Image

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix', type=str, default='.jpg', help='Suffix (file ending) which the affected files must end with')
    parser.add_argument('--prefix', type=str, default='', help='Prefix which the affected files must begin with')
    parser.add_argument('--dir', type=Path, help='Directory path')
    parser.add_argument('--exclude', type=Path, help='Ignore this path')
    return parser.parse_args()


def get_date_taken(path: Path):
    try:
        temp = Image.open(path)._getexif()[36867]
        temp = temp.replace(' ', '_')
        temp = temp.replace(':', '.')
    except TypeError:
        return None
    except KeyError:
        return None
    except OSError:
        return None
    return Path(temp + path.suffix)

if __name__ == "__main__":
    args = get_args()
    patterns = ('*' + args.suffix.lower(), '*' + args.suffix.upper())
    print(patterns)
    selected = []
    for imgs in patterns:
        selected.extend(glob.glob(imgs))
    selected = map(Path, selected)
    selected = list(filter(lambda f: not f.is_dir(), selected))
    tups = list(zip(selected, map(get_date_taken, selected)))
    for old, new in tups:
        if new:
            print(f'renaming {old} -> {new}')
            old.rename(new)
        else:
            print(f'no date found for {old}')
