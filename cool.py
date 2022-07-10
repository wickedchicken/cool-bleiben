#!/usr/bin/env python3

import argparse
import itertools
import json
import requests

from datetime import date
from enum import Enum, auto

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

class Action(Enum):
    OPEN = auto()
    CLOSE = auto()

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

    return crosspoints

def calculate_crosspoints(df, temperature, cooling):
    zeroed_temperature = df['temperature'] - temperature
    crossings = zero_crossing(zeroed_temperature)
    if cooling:
        def window_func(crossing):
            if crossing == Sign.POSITIVE:
                return Action.CLOSE
            else:
                return Action.OPEN
    else:
        def window_func(crossing):
            if crossing == Sign.NEGATIVE:
                return Action.CLOSE
            else:
                return Action.OPEN

    return [(x[0], window_func(x[1])) for x in crossings]



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

def build_crosspoints(df, min_temperature, max_temperature):
    mean_temp = df['temperature'].mean()
    crosspoints = []

    if mean_temp > min_temperature:
        crosspoints.extend(calculate_crosspoints(df, max_temperature, True))
    if mean_temp < max_temperature:
        crosspoints.extend(calculate_crosspoints(df, min_temperature, False))
    crosspoints.sort(key=lambda x: x[0])
    return crosspoints

def assume_start(df, min_temperature, max_temperature):
    if df['temperature'].empty:
        return Action.CLOSE

    if df['temperature'][0] > max_temperature:
        return Action.CLOSE
    if df['temperature'][0] < min_temperature:
        return Action.CLOSE
    return Action.OPEN

def print_actions(date, assumed_start, crosspoints):
    local_tz = get_localzone()
    print(f'On {date}: (all times are in {local_tz} time)')
    if assumed_start == Action.CLOSE:
        print('Assuming window starts closed.')
    else:
        print('Assuming window starts opened.')

    if not crosspoints:
        print('There is nothing to do.')


    for crosspoint in crosspoints:
        if crosspoint[1] == Action.OPEN:
            action = 'open the window.'
        else:
            action = 'close the window.'
        local_time = crosspoint[0].to_pydatetime().astimezone(local_tz).strftime("%H:%M")

        print(f'Around {local_time} {action}')



def main(args):
    data = make_api_request(args.url, args.date, args.lat, args.lon)
    df = build_dataframe(data)

    assumed_start = assume_start(df, args.min_temperature, args.max_temperature)
    crosspoints = build_crosspoints(df, args.min_temperature, args.max_temperature)

    print_actions(args.date, assumed_start, crosspoints)


if __name__ == '__main__':
    main(get_args())