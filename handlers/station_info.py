import pandas as pd
import os
from typing import Dict, List

class StationInfo:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.gtfs_path = os.path.join(self.base_path, 'gtfs')
        self.load_station_data()
    
    def load_station_data(self):
        """Load station data from GTFS"""
        try:
            self.stops = pd.read_csv(os.path.join(self.gtfs_path, 'stops.txt'))
            self.routes = pd.read_csv(os.path.join(self.gtfs_path, 'routes.txt'))
            self.trips = pd.read_csv(os.path.join(self.gtfs_path, 'trips.txt'))
            self.stop_times = pd.read_csv(os.path.join(self.gtfs_path, 'stop_times.txt'))
        except Exception as e:
            print(f"Error loading station data: {e}")
    
    def get_station_details(self, station_name: str) -> Dict:
        """Get detailed information about a station"""
        # Find station
        station_matches = self.stops[self.stops['stop_name'].str.contains(station_name, case=False, na=False)]
        
        if station_matches.empty:
            return {"error": f"Station '{station_name}' not found"}
        
        station = station_matches.iloc[0]
        station_id = station['stop_id']
        
        # Get station information
        station_info = {
            "name": station['stop_name'],
            "code": station['stop_code'],
            "description": station.get('stop_desc', 'Delhi Metro Station'),
            "location": {
                "latitude": station['stop_lat'],
                "longitude": station['stop_lon']
            },
            "facilities": self.get_station_facilities(station['stop_name']),
            "connections": self.get_station_connections(station_id),
            "lines": self.get_station_lines(station_id),
            "accessibility": self.get_accessibility_info(station['stop_name']),
            "operating_hours": "5:30 AM - 11:30 PM",
            "last_train": "11:30 PM",
            "first_train": "5:30 AM"
        }
        
        return station_info
    
    def get_station_facilities(self, station_name: str) -> List[str]:
        """Get facilities available at the station"""
        # This would typically come from a separate facilities database
        # For now, providing common facilities
        common_facilities = [
            "Ticket Counter",
            "Smart Card Recharge",
            "Security Check",
            "Platform Display",
            "Public Address System",
            "Drinking Water",
            "Restrooms"
        ]
        
        # Add specific facilities based on station name
        if "airport" in station_name.lower():
            common_facilities.extend(["Airport Shuttle", "Baggage Handling"])
        elif "mall" in station_name.lower() or "market" in station_name.lower():
            common_facilities.extend(["Shopping Center Access", "Food Court"])
        elif "hospital" in station_name.lower():
            common_facilities.extend(["Medical Emergency", "Ambulance Access"])
        
        return common_facilities
    
    def get_station_connections(self, station_id: str) -> List[Dict]:
        """Get connecting stations and lines"""
        # Get all trips that stop at this station
        station_trips = self.stop_times[self.stop_times['stop_id'] == station_id]
        
        if station_trips.empty:
            return []
        
        # Get route information for these trips
        trip_routes = station_trips.merge(self.trips, on='trip_id').merge(self.routes, on='route_id')
        
        # Get unique routes
        unique_routes = trip_routes[['route_id', 'route_short_name', 'route_long_name']].drop_duplicates()
        
        connections = []
        for _, route in unique_routes.iterrows():
            connections.append({
                'line': route['route_short_name'],
                'line_name': route['route_long_name'],
                'direction': 'Both directions'
            })
        
        return connections
    
    def get_station_lines(self, station_id: str) -> List[str]:
        """Get metro lines that serve this station"""
        station_trips = self.stop_times[self.stop_times['stop_id'] == station_id]
        
        if station_trips.empty:
            return []
        
        trip_routes = station_trips.merge(self.trips, on='trip_id').merge(self.routes, on='route_id')
        unique_lines = trip_routes['route_short_name'].unique().tolist()
        
        return unique_lines
    
    def get_accessibility_info(self, station_name: str) -> Dict:
        """Get accessibility information for the station"""
        # This would typically come from accessibility database
        accessibility = {
            "wheelchair_accessible": True,
            "elevator": True,
            "escalator": True,
            "ramp_access": True,
            "tactile_path": True,
            "audio_signals": True,
            "visual_signals": True
        }
        
        # Some stations might have limited accessibility
        if "old" in station_name.lower() or "heritage" in station_name.lower():
            accessibility["wheelchair_accessible"] = False
            accessibility["elevator"] = False
        
        return accessibility
    
    def get_nearby_stations(self, station_name: str, radius_km: float = 2.0) -> List[Dict]:
        """Get nearby stations within specified radius"""
        # Find the target station
        station_matches = self.stops[self.stops['stop_name'].str.contains(station_name, case=False, na=False)]
        
        if station_matches.empty:
            return []
        
        target_station = station_matches.iloc[0]
        target_lat = target_station['stop_lat']
        target_lon = target_station['stop_lon']
        
        # Calculate distances to other stations
        nearby_stations = []
        for _, station in self.stops.iterrows():
            if station['stop_id'] != target_station['stop_id']:
                distance = self.calculate_distance(
                    target_lat, target_lon,
                    station['stop_lat'], station['stop_lon']
                )
                
                if distance <= radius_km:
                    nearby_stations.append({
                        'name': station['stop_name'],
                        'code': station['stop_code'],
                        'distance': f"{distance:.1f} km",
                        'lines': self.get_station_lines(station['stop_id'])
                    })
        
        # Sort by distance
        nearby_stations.sort(key=lambda x: float(x['distance'].split()[0]))
        return nearby_stations[:5]  # Return top 5 nearby stations
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math
        
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
    
    def get_station_statistics(self, station_name: str) -> Dict:
        """Get usage statistics for a station"""
        # This would typically come from usage analytics
        # For now, providing sample statistics
        stats = {
            "daily_passengers": "15,000 - 25,000",
            "peak_hour_traffic": "2,000 - 3,500",
            "platform_capacity": "High",
            "crowding_level": "Moderate",
            "cleanliness_rating": "4.2/5",
            "safety_rating": "4.5/5"
        }
        
        # Adjust based on station characteristics
        if "airport" in station_name.lower():
            stats["daily_passengers"] = "8,000 - 12,000"
            stats["peak_hour_traffic"] = "1,500 - 2,500"
        elif "mall" in station_name.lower() or "market" in station_name.lower():
            stats["daily_passengers"] = "20,000 - 35,000"
            stats["peak_hour_traffic"] = "3,000 - 5,000"
        
        return stats

def get_station_details(station_name: str) -> Dict:
    """Main function to get station details"""
    station_info = StationInfo()
    return station_info.get_station_details(station_name) 