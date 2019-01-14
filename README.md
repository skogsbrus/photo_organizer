# photo_organizer

Organize your photos by date.

## Installation

### exiftool

You need [exiftool](https://en.wikipedia.org/wiki/ExifTool) installed in order to read metadata from photos/videos.

On Ubuntu/Debian et al. you can install it with:

```
sudo apt install exiftool
```

For other distributions or platforms, please refer to [these instructions](https://web.mit.edu/jhawk/mnt/cgs/Image-ExifTool-6.99/html/install.html).

### photo_organizer

```
git clone https://github.com/johan-andersson01/photo_organizer.git
cd photo_organizer
pipenv shell && pipenv install
```

## Usage

`photo_organizer` will currently reorganize your photos/videos to directories named by year, inside  of which the files are named by the complete date the photo/video was taken/shot.

There are future plans to also incorporate the geographical location of the photo/video in the file structure; probably as subdirectories for each year.

```
usage: photo_organizer.py [-h] [--exclude EXCLUDE [EXCLUDE ...]]
                          [--suffix SUFFIX [SUFFIX ...]]
                          [--prefix PREFIX [PREFIX ...]] --out OUT --dir DIR
                          [--log LOG] [--delete-after-copy]

optional arguments:
  -h, --help            show this help message and exit
  --exclude EXCLUDE [EXCLUDE ...]
                        Exclude paths containing any of these strings
  --suffix SUFFIX [SUFFIX ...]
                        Filter on file name suffix
  --prefix PREFIX [PREFIX ...]
                        Filter on file name prefix
  --out OUT             Output directory path
  --dir DIR             Input directory path
  --log LOG             Log file path
  --delete-after-copy   Delete the original file after it has been copied and
                        renamed OR skipped. BACKUP your input before doing
                        this.
```

## Go from an unorganized mess of photos to something cleaner

![unorganized](https://www.teambonding.com/wp-content/uploads/2013/10/unorganized.jpg)

:arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down::arrow_down:


![organized](http://www.sweetcaptcha.com/wp-content/uploads/2018/03/organized.jpg)
