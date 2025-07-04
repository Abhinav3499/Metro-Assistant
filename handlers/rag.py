import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from typing import List, Dict, Any
import pickle
from handlers.llm import clean_text_for_tts

class MetroRAG:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.gtfs_path = os.path.join(self.base_path, 'gtfs')
        self.knowledge_base = []
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.vectors = None
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """Load and process GTFS data into searchable knowledge base"""
        try:
            # Load GTFS files
            stops = pd.read_csv(os.path.join(self.gtfs_path, 'stops.txt'))
            routes = pd.read_csv(os.path.join(self.gtfs_path, 'routes.txt'))
            trips = pd.read_csv(os.path.join(self.gtfs_path, 'trips.txt'))
            stop_times = pd.read_csv(os.path.join(self.gtfs_path, 'stop_times.txt'))
            
            # Create station knowledge entries
            for _, stop in stops.iterrows():
                self.knowledge_base.append({
                    'type': 'station',
                    'content': f"Station: {stop['stop_name']} (Code: {stop['stop_code']}) - {stop['stop_desc'] if pd.notna(stop['stop_desc']) else 'Delhi Metro Station'}",
                    'metadata': {
                        'stop_id': stop['stop_id'],
                        'stop_name': stop['stop_name'],
                        'stop_code': stop['stop_code'],
                        'latitude': stop['stop_lat'],
                        'longitude': stop['stop_lon']
                    }
                })
            
            # Create route knowledge entries
            for _, route in routes.iterrows():
                self.knowledge_base.append({
                    'type': 'route',
                    'content': f"Route: {route['route_long_name']} (Line {route['route_short_name']}) - {route['route_desc'] if pd.notna(route['route_desc']) else 'Delhi Metro Line'}",
                    'metadata': {
                        'route_id': route['route_id'],
                        'route_name': route['route_long_name'],
                        'route_short': route['route_short_name']
                    }
                })
            
            # Create fare and timing knowledge
            self.knowledge_base.extend([
                {
                    'type': 'fare',
                    'content': "Delhi Metro fare structure: Minimum fare ₹10, Maximum fare ₹60. Smart card users get 10% discount.",
                    'metadata': {'category': 'pricing'}
                },
                {
                    'type': 'timing',
                    'content': "Delhi Metro operating hours: 5:30 AM to 11:30 PM. Peak hours: 8-11 AM and 5-8 PM.",
                    'metadata': {'category': 'schedule'}
                },
                {
                    'type': 'general',
                    'content': "Delhi Metro has 8 color-coded lines: Red, Yellow, Blue, Green, Violet, Pink, Magenta, and Grey lines.",
                    'metadata': {'category': 'lines'}
                }
            ])
            
            # Vectorize knowledge base
            texts = [entry['content'] for entry in self.knowledge_base]
            self.vectors = self.vectorizer.fit_transform(texts)
            
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search knowledge base for relevant information"""
        if self.vectors is None:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.vectors).flatten()
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                results.append({
                    'content': self.knowledge_base[idx]['content'],
                    'metadata': self.knowledge_base[idx]['metadata'],
                    'type': self.knowledge_base[idx]['type'],
                    'similarity': float(similarities[idx])
                })
        
        return results
    
    def get_route_info(self, from_station: str, to_station: str) -> Dict:
        """Get specific route information between two stations"""
        # Search for stations
        from_results = self.search(from_station, top_k=3)
        to_results = self.search(to_station, top_k=3)
        
        route_info = {
            'from_station': from_results[0] if from_results else None,
            'to_station': to_results[0] if to_results else None,
            'route_steps': [],
            'estimated_time': 0,
            'fare': 0
        }
        
        # Calculate basic fare and time estimates
        if route_info['from_station'] and route_info['to_station']:
            # Simple fare calculation (can be enhanced with actual fare data)
            route_info['fare'] = 20  # Base fare
            route_info['estimated_time'] = 30  # Base time in minutes
        
        return route_info
    
    def get_station_details(self, station_name: str) -> Dict:
        """Get detailed information about a specific station"""
        results = self.search(station_name, top_k=5)
        
        station_info = {
            'name': station_name,
            'details': [],
            'facilities': [],
            'connections': []
        }
        
        for result in results:
            if result['type'] == 'station':
                station_info['details'].append(result['content'])
                if 'metadata' in result and 'latitude' in result['metadata']:
                    station_info['location'] = {
                        'lat': result['metadata']['latitude'],
                        'lng': result['metadata']['longitude']
                    }
        
        return station_info

def enhance_response_with_rag(query: str, base_response: str) -> str:
    """Enhance LLM response with RAG-retrieved information"""
    rag = MetroRAG()
    relevant_info = rag.search(query, top_k=3)
    
    # If no relevant info found, just return cleaned base response
    if not relevant_info:
        return clean_text_for_tts(base_response)
    
    # Check if the base response already contains the information we want to add
    base_response_lower = base_response.lower()
    
    # Filter out redundant information
    useful_info = []
    for info in relevant_info:
        info_content = info['content'].lower()
        
        # Skip if this information is already mentioned in the base response
        if any(keyword in base_response_lower for keyword in ['fare', 'timing', 'operating hours', 'lines']):
            if any(keyword in info_content for keyword in ['fare', 'timing', 'operating hours', 'lines']):
                continue
        
        # Skip generic station information that doesn't add value
        if 'station:' in info_content and 'delhi metro station' in info_content:
            continue
            
        # Only add information that's actually useful and not redundant
        if info['similarity'] > 0.3:  # Higher threshold for relevance
            useful_info.append(info)
    
    # If no useful additional info, just return the base response
    if not useful_info:
        return clean_text_for_tts(base_response)
    
    # Only add additional information if it's truly valuable
    if len(useful_info) > 0:
        enhanced_response = base_response + "\n\nAdditional Information:\n"
        for info in useful_info[:2]:  # Limit to 2 most relevant items
            enhanced_response += f"• {info['content']}\n"
        
        return clean_text_for_tts(enhanced_response)
    
    return clean_text_for_tts(base_response) 