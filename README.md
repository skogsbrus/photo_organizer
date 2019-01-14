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

Executing `./photo_organizer.py --dir ~/Pictures/photo_organizer_test/ --out ./test --log log.txt` gives the following.

### Before

```
├── photo_organizer_test
│   ├── 121010_m_uy543_012_by_wright_usmc_d5hr70h.jpg
│   ├── 3_times_a_day_by_hersley_dvzs8y.jpg
│   ├── an_odd_couple_by_driftermanifesto_d4y9ql7.jpg
│   ├── band_of_brothers_by_combatcamera09_d5a3pch.jpg
│   ├── baskunchak_by_alexmaker34_d3co5p2.jpg
│   ├── good_morning_vietnam___lampions_in_hue_by_rikitza_dc1xbja.jpg
│   ├── have_a_seat_by_ulivonboedefeld_d29qnz3.jpg
│   ├── hoi_an_people___xii_by_inayatshah_davrdz5.jpg
│   ├── ied_detection_dog_by_militaryphotos_d55rz1x.jpg
│   └── smiles_by_digitalgrace_d1llmdg.jpg
```

### After

```
└── test
    ├── 2006
    │   └── 2006.12.19_17.59.15.jpg
    ├── 2007
    │   └── 2007.04.13_07.51.30.jpg
    ├── 2009
    │   └── 2009.09.17_01.45.58.jpg
    ├── 2011
    │   └── 2011.03.27_12.04.52.jpg
    ├── 2012
    │   ├── 2012.01.04_16.39.13.jpg
    │   ├── 2012.03.18_11.27.36.jpg
    │   ├── 2012.07.22_20.54.54.jpg
    │   └── 2012.10.10_10.23.01.jpg
    ├── 2014
    │   └── 2014.01.06_03.34.56.jpg
    ├── 2018
    │   └── 2018.01.18_06.15.46.jpg
    └── failed
```
