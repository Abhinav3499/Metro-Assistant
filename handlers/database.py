import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

class MetroDatabase:
    def __init__(self, db_path: str = "metro_assistant.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_query TEXT,
                assistant_response TEXT,
                route_data TEXT,
                language TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processing_time REAL
            )
        ''')
        
        # Create user_preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                session_id TEXT PRIMARY KEY,
                preferred_language TEXT DEFAULT 'en',
                frequent_stations TEXT,
                accessibility_needs TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create station_favorites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS station_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                station_name TEXT,
                station_code TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create route_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                from_station TEXT,
                to_station TEXT,
                route_data TEXT,
                search_count INTEGER DEFAULT 1,
                first_searched DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_searched DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, session_id: str, user_query: str, assistant_response: str, 
                         route_data: Dict = None, language: str = 'en', processing_time: float = 0.0):
        """Save a conversation interaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conversation_id = str(uuid.uuid4())
        route_json = json.dumps(route_data) if route_data else None
        
        cursor.execute('''
            INSERT INTO conversations (id, session_id, user_query, assistant_response, route_data, language, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (conversation_id, session_id, user_query, assistant_response, route_json, language, processing_time))
        
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_query, assistant_response, route_data, language, timestamp, processing_time
            FROM conversations 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'user_query': row[0],
                'assistant_response': row[1],
                'route_data': json.loads(row[2]) if row[2] else None,
                'language': row[3],
                'timestamp': row[4],
                'processing_time': row[5]
            })
        
        return history
    
    def save_user_preferences(self, session_id: str, preferences: Dict):
        """Save or update user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences 
            (session_id, preferred_language, frequent_stations, accessibility_needs, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            session_id,
            preferences.get('language', 'en'),
            json.dumps(preferences.get('frequent_stations', [])),
            json.dumps(preferences.get('accessibility_needs', []))
        ))
        
        conn.commit()
        conn.close()
    
    def get_user_preferences(self, session_id: str) -> Dict:
        """Get user preferences for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preferred_language, frequent_stations, accessibility_needs
            FROM user_preferences 
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'language': row[0],
                'frequent_stations': json.loads(row[1]) if row[1] else [],
                'accessibility_needs': json.loads(row[2]) if row[2] else []
            }
        
        return {'language': 'en', 'frequent_stations': [], 'accessibility_needs': []}
    
    def add_station_favorite(self, session_id: str, station_name: str, station_code: str = None):
        """Add a station to user's favorites"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO station_favorites (session_id, station_name, station_code)
            VALUES (?, ?, ?)
        ''', (session_id, station_name, station_code))
        
        conn.commit()
        conn.close()
    
    def get_station_favorites(self, session_id: str) -> List[Dict]:
        """Get user's favorite stations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT station_name, station_code, added_at
            FROM station_favorites 
            WHERE session_id = ?
            ORDER BY added_at DESC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'name': row[0], 'code': row[1], 'added_at': row[2]} for row in rows]
    
    def save_route_search(self, session_id: str, from_station: str, to_station: str, route_data: Dict):
        """Save a route search for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if this route was searched before
        cursor.execute('''
            SELECT id, search_count FROM route_history 
            WHERE session_id = ? AND from_station = ? AND to_station = ?
        ''', (session_id, from_station, to_station))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE route_history 
                SET search_count = search_count + 1, last_searched = CURRENT_TIMESTAMP, route_data = ?
                WHERE id = ?
            ''', (json.dumps(route_data), existing[0]))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO route_history (session_id, from_station, to_station, route_data)
                VALUES (?, ?, ?, ?)
            ''', (session_id, from_station, to_station, json.dumps(route_data)))
        
        conn.commit()
        conn.close()
    
    def get_popular_routes(self, limit: int = 10) -> List[Dict]:
        """Get most frequently searched routes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT from_station, to_station, SUM(search_count) as total_searches
            FROM route_history 
            GROUP BY from_station, to_station
            ORDER BY total_searches DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'from': row[0], 'to': row[1], 'searches': row[2]} for row in rows]
    
    def get_user_insights(self, session_id: str) -> Dict:
        """Get insights about user's metro usage patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total conversations
        cursor.execute('SELECT COUNT(*) FROM conversations WHERE session_id = ?', (session_id,))
        total_conversations = cursor.fetchone()[0]
        
        # Get favorite stations
        cursor.execute('''
            SELECT station_name, COUNT(*) as visit_count
            FROM station_favorites 
            WHERE session_id = ?
            GROUP BY station_name
            ORDER BY visit_count DESC
            LIMIT 5
        ''', (session_id,))
        favorite_stations = [{'name': row[0], 'visits': row[1]} for row in cursor.fetchall()]
        
        # Get most searched routes
        cursor.execute('''
            SELECT from_station, to_station, SUM(search_count) as total_searches
            FROM route_history 
            WHERE session_id = ?
            GROUP BY from_station, to_station
            ORDER BY total_searches DESC
            LIMIT 5
        ''', (session_id,))
        frequent_routes = [{'from': row[0], 'to': row[1], 'searches': row[2]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_conversations': total_conversations,
            'favorite_stations': favorite_stations,
            'frequent_routes': frequent_routes
        }

# Global database instance
db = MetroDatabase() 