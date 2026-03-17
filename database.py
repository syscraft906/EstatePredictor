"""
SQLite Database Management
Handles schema creation, ORM operations, and data persistence
"""

import sqlite3
import logging
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

from config import (
    DATABASE_PATH, TABLE_PROPERTIES, TABLE_CRAWL_LOG, TABLE_DUPLICATE_HASHES,
    VALID_BEDROOMS, VALID_BATHROOMS, MIN_PRICE, MAX_PRICE, MIN_AREA, MAX_AREA
)

logger = logging.getLogger(__name__)


class EstateDatabase:
    """Database manager for real estate property data"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Create all necessary tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Properties table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {TABLE_PROPERTIES} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id TEXT UNIQUE,
                    source_domain TEXT NOT NULL,
                    source_url TEXT UNIQUE NOT NULL,
                    property_type TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    price_vnd INTEGER,
                    price_original TEXT,
                    location_address TEXT,
                    province TEXT,
                    district TEXT,
                    ward TEXT,
                    area_sqm REAL,
                    bedrooms INTEGER,
                    bathrooms INTEGER,
                    amenities TEXT,
                    images_count INTEGER DEFAULT 0,
                    listing_date TEXT,
                    last_updated TEXT,
                    contact_name TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    crawl_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_province ON {TABLE_PROPERTIES}(province)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_domain ON {TABLE_PROPERTIES}(source_domain)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_type ON {TABLE_PROPERTIES}(property_type)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_price ON {TABLE_PROPERTIES}(price_vnd)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_area ON {TABLE_PROPERTIES}(area_sqm)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_crawl_date ON {TABLE_PROPERTIES}(crawl_date)')
            
            # Crawl logs table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {TABLE_CRAWL_LOG} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    status TEXT,
                    records_crawled INTEGER DEFAULT 0,
                    records_added INTEGER DEFAULT 0,
                    records_updated INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    error_messages TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds REAL
                )
            ''')
            
            # Duplicate hashes table (for deduplication)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {TABLE_DUPLICATE_HASHES} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_hash TEXT UNIQUE NOT NULL,
                    property_id TEXT,
                    source_url TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("Database initialized successfully")
    
    def insert_property(self, property_data: Dict) -> Optional[int]:
        """
        Insert a property record into the database
        Returns: row_id if successful, None otherwise
        """
        try:
            # Validate required fields
            if not property_data.get('source_url') or not property_data.get('title'):
                logger.warning("Missing required fields in property data")
                return None
            
            # Generate property hash for deduplication
            prop_hash = self.generate_property_hash(property_data)
            
            # Check if already exists (duplicate)
            if self.is_duplicate(prop_hash):
                logger.debug(f"Duplicate property detected: {property_data.get('source_url')}")
                return None
            
            # Validate data
            property_data = self.validate_property_data(property_data)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare data
                amenities_json = json.dumps(property_data.get('amenities', []))
                
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {TABLE_PROPERTIES} (
                        property_id, source_domain, source_url, property_type,
                        title, description, price_vnd, price_original,
                        location_address, province, district, ward,
                        area_sqm, bedrooms, bathrooms, amenities,
                        images_count, listing_date, contact_name,
                        contact_phone, contact_email, is_active,
                        crawl_date, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    property_data.get('property_id'),
                    property_data.get('source_domain'),
                    property_data.get('source_url'),
                    property_data.get('property_type'),
                    property_data.get('title'),
                    property_data.get('description'),
                    property_data.get('price_vnd'),
                    property_data.get('price_original'),
                    property_data.get('location_address'),
                    property_data.get('province'),
                    property_data.get('district'),
                    property_data.get('ward'),
                    property_data.get('area_sqm'),
                    property_data.get('bedrooms'),
                    property_data.get('bathrooms'),
                    amenities_json,
                    property_data.get('images_count', 0),
                    property_data.get('listing_date'),
                    property_data.get('contact_name'),
                    property_data.get('contact_phone'),
                    property_data.get('contact_email'),
                    1,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                row_id = cursor.lastrowid

                # Store hash inside the same connection (avoids "database is locked")
                cursor.execute(f'''
                    INSERT OR IGNORE INTO {TABLE_DUPLICATE_HASHES}
                    (property_hash, property_id, source_url)
                    VALUES (?, ?, ?)
                ''', (prop_hash, property_data.get('property_id'), property_data.get('source_url')))
                
                logger.info(f"Property inserted: {property_data.get('source_url')}")
                return row_id
        
        except Exception as e:
            logger.error(f"Error inserting property: {e}")
            return None
    
    def insert_multiple_properties(self, properties: List[Dict]) -> Tuple[int, int, int]:
        """
        Insert multiple properties efficiently
        Returns: (total, added, duplicates)
        """
        added = 0
        duplicates = 0
        
        for prop in properties:
            result = self.insert_property(prop)
            if result:
                added += 1
            else:
                duplicates += 1
        
        return len(properties), added, duplicates
    
    def validate_property_data(self, data: Dict) -> Dict:
        """Validate and clean property data"""
        try:
            # Price validation
            if data.get('price_vnd'):
                price = int(data['price_vnd'])
                if price < MIN_PRICE or price > MAX_PRICE:
                    data['price_vnd'] = None
            
            # Area validation
            if data.get('area_sqm'):
                area = float(data['area_sqm'])
                if area < MIN_AREA or area > MAX_AREA:
                    data['area_sqm'] = None
            
            # Bedrooms validation
            if data.get('bedrooms'):
                if data['bedrooms'] not in VALID_BEDROOMS:
                    data['bedrooms'] = None
            
            # Bathrooms validation
            if data.get('bathrooms'):
                if data['bathrooms'] not in VALID_BATHROOMS:
                    data['bathrooms'] = None
            
            # Strip whitespace from strings
            for key in ['title', 'description', 'location_address', 'province', 'district']:
                if isinstance(data.get(key), str):
                    data[key] = data[key].strip()
            
            return data
        except Exception as e:
            logger.error(f"Error validating property data: {e}")
            return data
    
    @staticmethod
    def generate_property_hash(property_data: Dict) -> str:
        """Generate hash for property deduplication"""
        # Use URL + property_id as base for hash
        hash_input = f"{property_data.get('source_url', '')}{property_data.get('property_id', '')}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def is_duplicate(self, prop_hash: str) -> bool:
        """Check if property already exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT id FROM {TABLE_DUPLICATE_HASHES} WHERE property_hash = ?', (prop_hash,))
            return cursor.fetchone() is not None
    
    def store_hash(self, prop_hash: str, property_id: Optional[str], source_url: Optional[str]):
        """Store property hash for deduplication"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT OR IGNORE INTO {TABLE_DUPLICATE_HASHES}
                    (property_hash, property_id, source_url)
                    VALUES (?, ?, ?)
                ''', (prop_hash, property_id, source_url))
        except Exception as e:
            logger.error(f"Error storing hash: {e}")
    
    def log_crawl(self, domain: str, status: str, records_crawled: int = 0,
                  records_added: int = 0, records_updated: int = 0,
                  errors: int = 0, error_messages: str = None,
                  duration_seconds: float = None):
        """Log crawl operation"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT INTO {TABLE_CRAWL_LOG}
                    (domain, status, records_crawled, records_added, records_updated, 
                     errors, error_messages, end_time, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    domain, status, records_crawled, records_added, records_updated,
                    errors, error_messages, datetime.now().isoformat(), duration_seconds
                ))
                logger.info(f"Crawl logged for {domain}: {records_added} added, {records_updated} updated")
        except Exception as e:
            logger.error(f"Error logging crawl: {e}")
    
    def get_properties(self, limit: int = 100, offset: int = 0, **filters) -> List[Dict]:
        """Retrieve properties with optional filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f'SELECT * FROM {TABLE_PROPERTIES} WHERE 1=1'
                params = []
                
                if filters.get('province'):
                    query += ' AND province = ?'
                    params.append(filters['province'])
                
                if filters.get('property_type'):
                    query += ' AND property_type = ?'
                    params.append(filters['property_type'])
                
                if filters.get('min_price'):
                    query += ' AND price_vnd >= ?'
                    params.append(filters['min_price'])
                
                if filters.get('max_price'):
                    query += ' AND price_vnd <= ?'
                    params.append(filters['max_price'])
                
                query += ' ORDER BY crawl_date DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving properties: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f'SELECT COUNT(*) as total FROM {TABLE_PROPERTIES}')
                total = cursor.fetchone()['total']
                
                cursor.execute(f'SELECT COUNT(DISTINCT province) as provinces FROM {TABLE_PROPERTIES}')
                provinces = cursor.fetchone()['provinces']
                
                cursor.execute(f'SELECT COUNT(DISTINCT source_domain) as domains FROM {TABLE_PROPERTIES}')
                domains = cursor.fetchone()['domains']
                
                cursor.execute(f'''
                    SELECT 
                        AVG(price_vnd) as avg_price,
                        AVG(area_sqm) as avg_area,
                        AVG(bedrooms) as avg_bedrooms
                    FROM {TABLE_PROPERTIES}
                    WHERE price_vnd IS NOT NULL
                ''')
                stats_row = cursor.fetchone()
                
                return {
                    'total_properties': total,
                    'unique_provinces': provinces,
                    'unique_domains': domains,
                    'avg_price_vnd': stats_row['avg_price'],
                    'avg_area_sqm': stats_row['avg_area'],
                    'avg_bedrooms': stats_row['avg_bedrooms']
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


# Convenience functions
def get_database() -> EstateDatabase:
    """Get database instance"""
    return EstateDatabase()


if __name__ == '__main__':
    # Test database initialization
    logging.basicConfig(level=logging.INFO)
    db = EstateDatabase()
    print("Database initialized successfully")
    print(f"Database path: {db.db_path}")
