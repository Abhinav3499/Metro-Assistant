import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List

class MetroSchedule:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.gtfs_path = os.path.join(self.base_path, 'gtfs')
        self.load_schedule_data()
    
    def load_schedule_data(self):
        """Load GTFS schedule data"""
        try:
            self.stops = pd.read_csv(os.path.join(self.gtfs_path, 'stops.txt'))
            self.trips = pd.read_csv(os.path.join(self.gtfs_path, 'trips.txt'))
            self.stop_times = pd.read_csv(os.path.join(self.gtfs_path, 'stop_times.txt'))
            self.routes = pd.read_csv(os.path.join(self.gtfs_path, 'routes.txt'))
            self.calendar = pd.read_csv(os.path.join(self.gtfs_path, 'calendar.txt'))
        except Exception as e:
            print(f"Error loading schedule data: {e}")
    
    def get_station_schedule(self, station_name: str, time_of_day: str = "current") -> Dict:
        """Get schedule for a specific station"""
        # Find station
        station_matches = self.stops[self.stops['stop_name'].str.contains(station_name, case=False, na=False)]
        
        if station_matches.empty:
            return {"error": f"Station '{station_name}' not found"}
        
        station_id = station_matches.iloc[0]['stop_id']
        
        # Get current time or specified time
        if time_of_day == "current":
            current_time = datetime.now().time()
        else:
            # Parse time string (e.g., "14:30")
            try:
                current_time = datetime.strptime(time_of_day, "%H:%M").time()
            except:
                current_time = datetime.now().time()
        
        # Get next trains
        next_trains = self.get_next_trains(station_id, current_time)
        
        return {
            "station_name": station_matches.iloc[0]['stop_name'],
            "current_time": current_time.strftime("%H:%M"),
            "next_trains": next_trains,
            "operating_hours": "5:30 AM - 11:30 PM",
            "peak_hours": "8:00 AM - 11:00 AM, 5:00 PM - 8:00 PM"
        }
    
    def get_next_trains(self, station_id: str, current_time, limit: int = 5) -> List[Dict]:
        """Get next trains arriving at a station"""
        # Get stop times for this station
        station_times = self.stop_times[self.stop_times['stop_id'] == station_id]
        
        if station_times.empty:
            return []
        
        # Merge with trip and route information
        merged = station_times.merge(self.trips, on='trip_id').merge(self.routes, on='route_id')
        
        # Convert arrival times to datetime for comparison
        merged['arrival_time'] = pd.to_datetime(merged['arrival_time'], format='%H:%M:%S').dt.time
        
        # Filter for trains after current time
        future_trains = merged[merged['arrival_time'] > current_time]
        
        # Sort by arrival time and take next few
        next_trains = future_trains.sort_values('arrival_time').head(limit)
        
        trains = []
        for _, train in next_trains.iterrows():
            trains.append({
                'line': train['route_short_name'],
                'direction': train['trip_headsign'] if pd.notna(train['trip_headsign']) else 'Unknown',
                'arrival_time': train['arrival_time'].strftime('%H:%M'),
                'platform': train.get('platform_code', 'TBD')
            })
        
        return trains
    
    def get_route_schedule(self, from_station: str, to_station: str) -> Dict:
        """Get schedule for a specific route"""
        # Find stations
        from_matches = self.stops[self.stops['stop_name'].str.contains(from_station, case=False, na=False)]
        to_matches = self.stops[self.stops['stop_name'].str.contains(to_station, case=False, na=False)]
        
        if from_matches.empty or to_matches.empty:
            return {"error": "One or both stations not found"}
        
        from_id = from_matches.iloc[0]['stop_id']
        to_id = to_matches.iloc[0]['stop_id']
        
        # Get current time
        current_time = datetime.now().time()
        
        # Find direct routes between stations
        route_info = self.find_direct_route(from_id, to_id, current_time)
        
        return {
            "from_station": from_matches.iloc[0]['stop_name'],
            "to_station": to_matches.iloc[0]['stop_name'],
            "route_info": route_info,
            "estimated_duration": "20-45 minutes",
            "frequency": "Every 3-5 minutes during peak hours"
        }
    
    def find_direct_route(self, from_id: str, to_id: str, current_time) -> List[Dict]:
        """Find direct routes between two stations"""
        # Get all trips that pass through both stations
        from_times = self.stop_times[self.stop_times['stop_id'] == from_id]
        to_times = self.stop_times[self.stop_times['stop_id'] == to_id]
        
        # Find common trips
        common_trips = set(from_times['trip_id']).intersection(set(to_times['trip_id']))
        
        routes = []
        for trip_id in list(common_trips)[:3]:  # Limit to 3 routes
            trip_info = self.trips[self.trips['trip_id'] == trip_id].iloc[0]
            route_info = self.routes[self.routes['route_id'] == trip_info['route_id']].iloc[0]
            
            # Get departure and arrival times
            from_time = from_times[from_times['trip_id'] == trip_id]['departure_time'].iloc[0]
            to_time = to_times[to_times['trip_id'] == trip_id]['arrival_time'].iloc[0]
            
            routes.append({
                'line': route_info['route_short_name'],
                'line_name': route_info['route_long_name'],
                'departure_time': from_time,
                'arrival_time': to_time,
                'duration': self.calculate_duration(from_time, to_time)
            })
        
        return routes
    
    def calculate_duration(self, departure_time: str, arrival_time: str) -> str:
        """Calculate duration between two times"""
        try:
            dep = datetime.strptime(departure_time, '%H:%M:%S')
            arr = datetime.strptime(arrival_time, '%H:%M:%S')
            
            # Handle overnight trips
            if arr < dep:
                arr += timedelta(days=1)
            
            duration = arr - dep
            minutes = int(duration.total_seconds() / 60)
            
            if minutes < 60:
                return f"{minutes} minutes"
            else:
                hours = minutes // 60
                mins = minutes % 60
                return f"{hours}h {mins}m"
        except:
            return "Unknown"

def get_schedule(from_station: str = "", to_station: str = "") -> Dict:
    """Main function to get schedule information"""
    schedule = MetroSchedule()
    
    if from_station and to_station:
        return schedule.get_route_schedule(from_station, to_station)
    elif from_station:
        return schedule.get_station_schedule(from_station)
    else:
        return {"error": "Please specify at least one station"} 