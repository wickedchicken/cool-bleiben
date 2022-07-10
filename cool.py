#!/usr/bin/env python3

import argparse
import json
import requests

from datetime import date

import numpy as np

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', 
        default='https://api.brightsky.dev/weather',
                    help='URL to access weather data from')
    parser.add_argument('--date', 
        default=date.today().isoformat(),
                    help='date to get the weather of')

    parser.add_argument('lat', type=float, help='latitude')
    parser.add_argument('lon', type=float, help='longitude')
    return parser.parse_args()


def make_api_request(url, date, lat, lon):
    payload = {'date': date, 'lat': lat, 'lon': lon}
    r = requests.get(url, params=payload)
    print(json.dumps(r.json()))

def main(args):
    make_api_request(args.url, args.date, args.lat, args.lon)

if __name__ == '__main__':
    main(get_args())