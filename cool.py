#!/usr/bin/env python3

import argparse
import itertools
import json
import requests

from datetime import date
from enum import Enum

import numpy as np
import pandas as pd

from dateutil.parser import parse

from tzlocal import get_localzone

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
    parser.add_argument('--min-temperature', default=17.0, type=float, help='min target temperature')
    parser.add_argument('--max-temperature', default=21.0, type=float, help='max target temperature')
    return parser.parse_args()

def make_api_request(url, date, lat, lon):
    payload = {'date': date, 'lat': lat, 'lon': lon}
    r = requests.get(url, params=payload)
    return r.json()

class Sign(Enum):
    NEGATIVE = -1
    ZERO = 0
    POSITIVE = 1

def zero_crossing(data):
    signs = []
    for x in data:
        if x > 0:
            signs.append(Sign.POSITIVE)
        elif x == 0:
            signs.append(Sign.ZERO)
        else:
            signs.append(Sign.NEGATIVE)

    crosspoints = []
    directions = []
    last_nonzero = Sign.ZERO
    for i, (l, r) in enumerate(itertools.pairwise(signs)):
        if l == Sign.NEGATIVE and r == Sign.POSITIVE:
            crosspoints.append((data.index[i], Sign.POSITIVE))
        elif l == Sign.POSITIVE and r == Sign.NEGATIVE:
            crosspoints.append((data.index[i], Sign.NEGATIVE))
        elif l == Sign.ZERO:
            if last_nonzero == Sign.ZERO and r == Sign.POSITIVE:
                crosspoints.append((data.index[i], Sign.POSITIVE))
            elif last_nonzero == Sign.ZERO and r == Sign.NEGATIVE:
                crosspoints.append((data.index[i], Sign.NEGATIVE))
            elif last_nonzero == Sign.NEGATIVE and r == Sign.POSITIVE:
                crosspoints.append((data.index[i], Sign.POSITIVE))
            elif last_nonzero == Sign.POSITIVE and r == Sign.NEGATIVE:
                crosspoints.append((data.index[i], Sign.NEGATIVE))
        if l != Sign.ZERO:
            last_nonzero = l

    print(crosspoints)
    return crosspoints

def calculate_crosspoints(df, temperature):
    zeroed_temperature = df['temperature'] - temperature
    print(zeroed_temperature)
    return zero_crossing(zeroed_temperature)

def build_dataframe(json_data):
    columns = (
      "cloud_cover",
      "condition",
      "dew_point",
      "icon",
      "precipitation",
      "pressure_msl",
      "relative_humidity",
      "source_id",
      "sunshine",
      "temperature",
      "visibility",
      "wind_direction",
      "wind_gust_direction",
      "wind_gust_speed",
      "wind_speed",
    )

    data = {}
    for column in columns:
        data[column] = [x[column] for x in json_data['weather']]

    timestamps = [parse(x['timestamp']) for x in json_data['weather']]

    return pd.DataFrame(data, index=timestamps)


def main(args):
    data = make_api_request(args.url, args.date, args.lat, args.lon)
    df = build_dataframe(data)
    calculate_crosspoints(df, args.min_temperature)
    calculate_crosspoints(df, args.max_temperature)


if __name__ == '__main__':
    main(get_args())