"""
API guidelines as of 2019-03-30

- 1 request per second maximum
- Valid HTTP header or user agent
- Display attribution
- Single thread, one machine
- Cached results
"""

"""
API:
https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=-34.44076&lon=-58.70521
"""

import urllib.request
import json
import sys
import argparse
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', type=str, required=True, help='Enter your email (required by Nomatim API)')
    parser.add_argument('--input_dir', type=Path, help='Input directory of photos you want organized by location')
    return parser.parse_args()


def get_location(lat, lon, email, user_agent='https://github.com/johan-andersson01/photo_organizer'):
    base_url= 'https://nominatim.openstreetmap.org/reverse?format=jsonv2'
    url = f'{base_url}&lat={lat}&lon={lon}&email={email}'
    header = {'User-Agent': user_agent}
    request = urllib.request.Request(url=url, headers=header)

    with urllib.request.urlopen(request) as response:
        # TODO: urllib error handling
        json_response = json.loads(response.read())
        try:
            results = json_response['address']
        except KeyError:
            sys.exit()
    return f"{results['town']}, {results['country']}"


def find_addresses(args):
    # TODO: glob args.input_dir
    coords = [(-34.4, -58.7)]
    for lat, lon in coords:
        print(get_location(lat, lon, args.email))


if __name__ == "__main__":
    args = get_args()
    find_addresses(args)
