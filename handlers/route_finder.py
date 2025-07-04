import pandas as pd
from collections import defaultdict
import os
import math
from typing import Dict, List, Tuple

BASE = os.path.dirname(os.path.dirname(__file__))
GTFS = os.path.join(BASE, 'gtfs')

stops = pd.read_csv(os.path.join(GTFS, 'stops.txt'))
trips = pd.read_csv(os.path.join(GTFS, 'trips.txt'))
stop_times = pd.read_csv(os.path.join(GTFS, 'stop_times.txt'))
routes = pd.read_csv(os.path.join(GTFS, 'routes.txt'))

def build_graph():
    """Build a graph representation of the metro network"""
    stop_to_routes = defaultdict(set)
    merged = stop_times.merge(trips, on='trip_id').sort_values(['trip_id', 'stop_sequence'])
    
    for _, row in merged.iterrows():
        stop_to_routes[row['stop_id']].add(row['route_id'])
    
    return stop_to_routes

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def calculate_fare(from_station: str, to_station: str) -> Dict:
    """Calculate fare between two stations"""
    # Find stations
    from_matches = stops[stops['stop_name'].str.contains(from_station, case=False, na=False)]
    to_matches = stops[stops['stop_name'].str.contains(to_station, case=False, na=False)]
    
    if from_matches.empty or to_matches.empty:
        return {"error": "Station not found"}
    
    from_station = from_matches.iloc[0]
    to_station = to_matches.iloc[0]
    
    # Calculate distance
    distance = calculate_distance(
        from_station['stop_lat'], from_station['stop_lon'],
        to_station['stop_lat'], to_station['stop_lon']
    )
    
    # Delhi Metro fare structure (simplified)
    if distance <= 2:
        fare = 10
    elif distance <= 5:
        fare = 20
    elif distance <= 12:
        fare = 30
    elif distance <= 21:
        fare = 40
    elif distance <= 32:
        fare = 50
    else:
        fare = 60
    
    return {
        "distance_km": round(distance, 1),
        "fare": fare,
        "smart_card_discount": round(fare * 0.1, 0),
        "final_fare": round(fare * 0.9, 0),
        "currency": "₹"
    }

def find_route(user_query: str) -> Dict:
    """Find route between stations mentioned in the query"""
    from handlers.llm import extract_stations
    start, end = extract_stations(user_query)
    
    if not start or not end:
        return {'steps': [], 'fare': 0, 'error': 'Could not identify stations'}
    
    stop_to_routes = build_graph()
    start_ids = stops[stops['stop_name'].str.contains(start, case=False, na=False)]['stop_id']
    end_ids = stops[stops['stop_name'].str.contains(end, case=False, na=False)]['stop_id']
    
    if start_ids.empty or end_ids.empty:
        return {'steps': [], 'fare': 0, 'error': 'Stations not found'}
    
    routes_found = []
    
    for s in start_ids:
        for e in end_ids:
            common = stop_to_routes[s].intersection(stop_to_routes[e])
            if common:
                for r in common:
                    route_info = routes.loc[routes['route_id']==r]
                    if not route_info.empty:
                        routes_found.append({
                            'from': start,
                            'to': end,
                            'via': route_info.iloc[0]['route_long_name'],
                            'line': route_info.iloc[0]['route_short_name'],
                            'platform_from': stops.loc[stops['stop_id']==s, 'stop_code'].iloc[0],
                            'platform_to': stops.loc[stops['stop_id']==e, 'stop_code'].iloc[0],
                            'direction': 'Both directions',
                            'estimated_time': '20-45 minutes',
                            'frequency': 'Every 3-5 minutes'
                        })
                break
    
    # Calculate fare
    fare_info = calculate_fare(start, end)
    
    return {
        'steps': routes_found,
        'fare_info': fare_info,
        'total_routes': len(routes_found)
    }

def find_multiple_routes(from_station: str, to_station: str, max_routes: int = 3) -> Dict:
    """Find multiple route options between two stations"""
    # Find stations
    from_matches = stops[stops['stop_name'].str.contains(from_station, case=False, na=False)]
    to_matches = stops[stops['stop_name'].str.contains(to_station, case=False, na=False)]
    
    if from_matches.empty or to_matches.empty:
        return {"error": "Stations not found"}
    
    from_id = from_matches.iloc[0]['stop_id']
    to_id = to_matches.iloc[0]['stop_id']
    
    # Get all possible routes
    all_routes = []
    
    # Direct routes
    direct_routes = find_direct_routes(from_id, to_id)
    all_routes.extend(direct_routes)
    
    # Routes with one interchange
    interchange_routes = find_interchange_routes(from_id, to_id)
    all_routes.extend(interchange_routes)
    
    # Sort by estimated time and take top routes
    all_routes.sort(key=lambda x: x.get('estimated_minutes', 999))
    
    return {
        'from_station': from_matches.iloc[0]['stop_name'],
        'to_station': to_matches.iloc[0]['stop_name'],
        'routes': all_routes[:max_routes],
        'fare_info': calculate_fare(from_station, to_station)
    }

def find_direct_routes(from_id: str, to_id: str) -> List[Dict]:
    """Find direct routes between two stations"""
    # Get all trips that pass through both stations
    from_times = stop_times[stop_times['stop_id'] == from_id]
    to_times = stop_times[stop_times['stop_id'] == to_id]
    
    # Find common trips
    common_trips = set(from_times['trip_id']).intersection(set(to_times['trip_id']))
    
    routes = []
    for trip_id in list(common_trips)[:2]:  # Limit to 2 direct routes
        trip_info = trips[trips['trip_id'] == trip_id].iloc[0]
        route_info = routes.loc[routes['route_id'] == trip_info['route_id']].iloc[0]
        
        # Get departure and arrival times
        from_time = from_times[from_times['trip_id'] == trip_id]['departure_time'].iloc[0]
        to_time = to_times[to_times['trip_id'] == trip_id]['arrival_time'].iloc[0]
        
        routes.append({
            'type': 'Direct',
            'line': route_info['route_short_name'],
            'line_name': route_info['route_long_name'],
            'departure_time': from_time,
            'arrival_time': to_time,
            'estimated_minutes': calculate_time_difference(from_time, to_time),
            'interchanges': 0,
            'route_type': 'Direct'
        })
    
    return routes

def find_interchange_routes(from_id: str, to_id: str) -> List[Dict]:
    """Find routes with one interchange"""
    # This is a simplified version - in reality, you'd need a more complex algorithm
    # to find optimal interchange points
    
    routes = []
    
    # Get all routes from source station
    from_times = stop_times[stop_times['stop_id'] == from_id]
    from_routes = from_times.merge(trips, on='trip_id').merge(routes, on='route_id')
    
    # Get all routes to destination station
    to_times = stop_times[stop_times['stop_id'] == to_id]
    to_routes = to_times.merge(trips, on='trip_id').merge(routes, on='route_id')
    
    # Find common interchange stations (simplified)
    interchange_stations = find_common_stations(from_routes, to_routes)
    
    for station in interchange_stations[:2]:  # Limit to 2 interchange routes
        routes.append({
            'type': 'Interchange',
            'interchange_station': station['name'],
            'first_line': station['first_line'],
            'second_line': station['second_line'],
            'estimated_minutes': station['estimated_time'],
            'interchanges': 1,
            'route_type': 'Interchange'
        })
    
    return routes

def find_common_stations(from_routes: pd.DataFrame, to_routes: pd.DataFrame) -> List[Dict]:
    """Find common stations that can serve as interchange points"""
    # This is a simplified implementation
    # In reality, you'd need to analyze the actual network topology
    
    common_stations = []
    
    # Get unique stations from both route sets
    from_stations = set(from_routes['stop_id'].unique())
    to_stations = set(to_routes['stop_id'].unique())
    
    # Find intersection
    interchange_stations = from_stations.intersection(to_stations)
    
    for station_id in list(interchange_stations)[:3]:  # Limit to 3 interchange points
        station_info = stops[stops['stop_id'] == station_id].iloc[0]
        
        common_stations.append({
            'name': station_info['stop_name'],
            'first_line': from_routes[from_routes['stop_id'] == station_id]['route_short_name'].iloc[0],
            'second_line': to_routes[to_routes['stop_id'] == station_id]['route_short_name'].iloc[0],
            'estimated_time': 30  # Simplified estimate
        })
    
    return common_stations

def calculate_time_difference(time1: str, time2: str) -> int:
    """Calculate time difference in minutes"""
    try:
        from datetime import datetime
        t1 = datetime.strptime(time1, '%H:%M:%S')
        t2 = datetime.strptime(time2, '%H:%M:%S')
        
        # Handle overnight trips
        if t2 < t1:
            t2 = datetime.combine(t2.date() + timedelta(days=1), t2.time())
        
        diff = t2 - t1
        return int(diff.total_seconds() / 60)
    except:
        return 30  # Default estimate

def get_route_summary(route_data: Dict) -> str:
    """Generate a human-readable summary of the route"""
    if not route_data.get('steps'):
        return "No route found"
    
    steps = route_data['steps']
    fare_info = route_data.get('fare_info', {})
    
    summary = f"Route from {steps[0]['from']} to {steps[0]['to']}:\n"
    summary += f"• Take {steps[0]['line']} line ({steps[0]['via']})\n"
    summary += f"• Estimated time: {steps[0]['estimated_time']}\n"
    summary += f"• Fare: ₹{fare_info.get('fare', 0)} (₹{fare_info.get('final_fare', 0)} with smart card)\n"
    summary += f"• Frequency: {steps[0]['frequency']}"
    
    return summary
