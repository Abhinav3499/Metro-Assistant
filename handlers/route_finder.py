import pandas as pd
from collections import defaultdict
import os

BASE = os.path.dirname(os.path.dirname(__file__))
GTFS = os.path.join(BASE, 'gtfs')

stops = pd.read_csv(os.path.join(GTFS, 'stops.txt'))
trips = pd.read_csv(os.path.join(GTFS, 'trips.txt'))
stop_times = pd.read_csv(os.path.join(GTFS, 'stop_times.txt'))
routes = pd.read_csv(os.path.join(GTFS, 'routes.txt'))

def build_graph():
    stop_to_routes = defaultdict(set)
    merged = stop_times.merge(trips, on='trip_id').sort_values(['trip_id', 'stop_sequence'])
    for _, row in merged.iterrows():
        stop_to_routes[row['stop_id']].add(row['route_id'])
    return stop_to_routes

def find_route(user_query):
    from handlers.llm import extract_stations
    start, end = extract_stations(user_query)
    if not start or not end:
        return {'steps': [], 'fare': 0}
    stop_to_routes = build_graph()
    start_ids = stops[stops['stop_name'].str.contains(start, case=False, na=False)]['stop_id']
    end_ids = stops[stops['stop_name'].str.contains(end, case=False, na=False)]['stop_id']
    steps = []
    for s in start_ids:
        for e in end_ids:
            common = stop_to_routes[s].intersection(stop_to_routes[e])
            if common:
                for r in common:
                    steps.append({
                        'from': start,
                        'to': end,
                        'via': routes.loc[routes['route_id']==r, 'route_long_name'].iloc[0],
                        'platform_from': stops.loc[stops['stop_id']==s, 'stop_code'].iloc[0],
                        'platform_to': stops.loc[stops['stop_id']==e, 'stop_code'].iloc[0],
                        'direction': 'up/down'
                    })
                break
    fare = 30 if steps else 0
    return {'steps': steps, 'fare': fare}
