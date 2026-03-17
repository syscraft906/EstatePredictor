"""
Bang Gia Dat (Price Guide) Database Schema

This module defines the data structures for storing and managing Vietnamese real estate
price guides from multiple sources (guland.vn, batdongsan.com.vn, meeyland.com, etc.)

Price Guide Data typically includes:
- Location hierarchy (Province -> District -> Ward -> Street)
- Price ranges (min, max, average)
- Price per square meter (m²)
- Property types (residential, commercial, land, etc.)
- Temporal data (last updated, historical trends)
- Source information
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import json


class PropertyType(Enum):
    """Property types commonly tracked in Vietnamese real estate price guides"""
    RESIDENTIAL_APARTMENT = "apartment"
    RESIDENTIAL_HOUSE = "house"
    RESIDENTIAL_LAND = "land"
    COMMERCIAL_OFFICE = "office"
    COMMERCIAL_RETAIL = "retail"
    COMMERCIAL_LAND = "commercial_land"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"


class PriceUnit(Enum):
    """Currency and measurement units"""
    VND = "vnd"  # Vietnamese Dong
    USD = "usd"
    PER_M2 = "per_m2"
    PER_LOT = "per_lot"


class LocationLevel(Enum):
    """Hierarchical location levels in Vietnam"""
    PROVINCE = "province"
    DISTRICT = "district"
    WARD = "ward"
    STREET = "street"
    NEIGHBORHOOD = "neighborhood"


@dataclass
class Location:
    """Hierarchical location representation"""
    province: str  # e.g., "Hà Nội", "TP. Hồ Chí Minh"
    district: Optional[str] = None  # e.g., "Hoàn Kiếm", "Quận 1"
    ward: Optional[str] = None  # e.g., "Tràng Tiền", "Bến Nghé"
    street: Optional[str] = None  # e.g., "Phố Cổ", "Nguyễn Huệ"
    neighborhood: Optional[str] = None  # e.g., "Bến Vân Đồn"
    
    def get_level(self) -> LocationLevel:
        """Determine the detail level of this location"""
        if self.street:
            return LocationLevel.STREET
        elif self.neighborhood:
            return LocationLevel.NEIGHBORHOOD
        elif self.ward:
            return LocationLevel.WARD
        elif self.district:
            return LocationLevel.DISTRICT
        return LocationLevel.PROVINCE
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_string(self) -> str:
        """Get full location string"""
        parts = [self.province]
        if self.district:
            parts.append(self.district)
        if self.ward:
            parts.append(self.ward)
        if self.street:
            parts.append(self.street)
        return ", ".join(parts)


@dataclass
class PriceRange:
    """Price range with min, max, and average values"""
    min_price: float  # Minimum price in VND
    max_price: float  # Maximum price in VND
    average_price: Optional[float] = None  # Average price in VND
    
    def calculate_average(self):
        """Calculate average if not provided"""
        if self.average_price is None:
            self.average_price = (self.min_price + self.max_price) / 2
        return self.average_price
    
    def get_range_string(self, format_billions=True) -> str:
        """Get human-readable price range"""
        if format_billions:
            min_str = f"{self.min_price / 1e9:.1f}B"
            max_str = f"{self.max_price / 1e9:.1f}B"
        else:
            min_str = f"{self.min_price:,.0f}"
            max_str = f"{self.max_price:,.0f}"
        return f"{min_str} - {max_str} VND"


@dataclass
class PricePerM2:
    """Price per square meter data"""
    min_price_per_m2: float  # VND/m²
    max_price_per_m2: float  # VND/m²
    average_price_per_m2: Optional[float] = None
    
    def calculate_average(self):
        """Calculate average if not provided"""
        if self.average_price_per_m2 is None:
            self.average_price_per_m2 = (self.min_price_per_m2 + self.max_price_per_m2) / 2
        return self.average_price_per_m2


@dataclass
class PriceGuideEntry:
    """Single price guide entry from a real estate website
    
    This represents a price guide point for a specific location,
    property type, and time period.
    """
    # Identifiers
    id: str  # Unique ID (source_province_district_property_type_date)
    source: str  # Source website (e.g., "guland.vn", "batdongsan.com.vn")
    
    # Location
    location: Location
    
    # Property details
    property_type: PropertyType
    property_size_range: Optional[tuple] = None  # (min_sqm, max_sqm)
    
    # Pricing
    price_range: Optional[PriceRange] = None
    price_per_m2: Optional[PricePerM2] = None
    
    # Temporal
    date_recorded: datetime = field(default_factory=datetime.now)
    date_updated: Optional[datetime] = None
    effective_date: Optional[datetime] = None  # When this price is valid from
    
    # Quality metrics
    sample_size: Optional[int] = None  # Number of listings used for calculation
    confidence_score: Optional[float] = field(default=0.7)  # 0.0-1.0, reliability estimate
    
    # Additional metadata
    currency: PriceUnit = PriceUnit.VND
    price_trend: Optional[str] = None  # "up", "down", "stable"
    trend_percentage: Optional[float] = None  # YoY change percentage
    notes: Optional[str] = None
    source_url: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize data"""
        if self.price_range:
            self.price_range.calculate_average()
        if self.price_per_m2:
            self.price_per_m2.calculate_average()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "source": self.source,
            "location": self.location.to_dict(),
            "property_type": self.property_type.value,
            "price_range": {
                "min": self.price_range.min_price,
                "max": self.price_range.max_price,
                "avg": self.price_range.average_price,
            } if self.price_range else None,
            "price_per_m2": {
                "min": self.price_per_m2.min_price_per_m2,
                "max": self.price_per_m2.max_price_per_m2,
                "avg": self.price_per_m2.average_price_per_m2,
            } if self.price_per_m2 else None,
            "date_recorded": self.date_recorded.isoformat(),
            "date_updated": self.date_updated.isoformat() if self.date_updated else None,
            "sample_size": self.sample_size,
            "confidence_score": self.confidence_score,
            "price_trend": self.price_trend,
            "trend_percentage": self.trend_percentage,
            "notes": self.notes,
            "source_url": self.source_url,
        }


@dataclass
class HistoricalPriceData:
    """Historical pricing data for trend analysis"""
    location: Location
    property_type: PropertyType
    price_history: List[Dict[str, Any]] = field(default_factory=list)  # List of {date, price} dicts
    
    def add_price_point(self, date: datetime, price: float, price_per_m2: Optional[float] = None):
        """Add a historical price point"""
        self.price_history.append({
            "date": date.isoformat(),
            "price": price,
            "price_per_m2": price_per_m2,
        })
    
    def get_trend(self) -> Optional[str]:
        """Calculate price trend from history"""
        if len(self.price_history) < 2:
            return None
        
        prices = [p["price"] for p in self.price_history]
        first_price = prices[0]
        last_price = prices[-1]
        change = ((last_price - first_price) / first_price) * 100
        
        if change > 5:
            return "up"
        elif change < -5:
            return "down"
        return "stable"


class PriceGuideDatabase:
    """In-memory database for price guide entries with query capabilities"""
    
    def __init__(self):
        self.entries: Dict[str, PriceGuideEntry] = {}
        self.index_by_location: Dict[str, List[str]] = {}  # location_string -> [entry_ids]
        self.index_by_source: Dict[str, List[str]] = {}  # source -> [entry_ids]
    
    def add_entry(self, entry: PriceGuideEntry):
        """Add an entry to the database"""
        self.entries[entry.id] = entry
        
        # Update location index
        loc_key = entry.location.to_string()
        if loc_key not in self.index_by_location:
            self.index_by_location[loc_key] = []
        self.index_by_location[loc_key].append(entry.id)
        
        # Update source index
        if entry.source not in self.index_by_source:
            self.index_by_source[entry.source] = []
        self.index_by_source[entry.source].append(entry.id)
    
    def find_by_location(self, location: Location) -> List[PriceGuideEntry]:
        """Find entries matching a location"""
        loc_key = location.to_string()
        entry_ids = self.index_by_location.get(loc_key, [])
        return [self.entries[eid] for eid in entry_ids]
    
    def find_by_source(self, source: str) -> List[PriceGuideEntry]:
        """Find all entries from a specific source"""
        entry_ids = self.index_by_source.get(source, [])
        return [self.entries[eid] for eid in entry_ids]
    
    def find_nearest_location(self, location: Location, property_type: PropertyType) -> Optional[PriceGuideEntry]:
        """Find the nearest/most specific price guide for a location"""
        # Try exact location match first
        matches = self.find_by_location(location)
        exact_matches = [e for e in matches if e.property_type == property_type]
        
        if exact_matches:
            # Return most recently updated
            return max(exact_matches, key=lambda e: e.date_updated or e.date_recorded)
        
        # Try progressively less specific locations
        if location.street:
            # Try without street
            location.street = None
            return self.find_nearest_location(location, property_type)
        
        return None
    
    def to_csv(self, filename: str):
        """Export database to CSV format"""
        import csv
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'source', 'province', 'district', 'ward', 'street',
                'property_type', 'min_price', 'max_price', 'avg_price',
                'min_price_per_m2', 'max_price_per_m2', 'avg_price_per_m2',
                'date_recorded', 'sample_size', 'confidence_score', 'price_trend'
            ])
            writer.writeheader()
            
            for entry in self.entries.values():
                row = {
                    'id': entry.id,
                    'source': entry.source,
                    **entry.location.to_dict(),
                    'property_type': entry.property_type.value,
                    'min_price': entry.price_range.min_price if entry.price_range else None,
                    'max_price': entry.price_range.max_price if entry.price_range else None,
                    'avg_price': entry.price_range.average_price if entry.price_range else None,
                    'min_price_per_m2': entry.price_per_m2.min_price_per_m2 if entry.price_per_m2 else None,
                    'max_price_per_m2': entry.price_per_m2.max_price_per_m2 if entry.price_per_m2 else None,
                    'avg_price_per_m2': entry.price_per_m2.average_price_per_m2 if entry.price_per_m2 else None,
                    'date_recorded': entry.date_recorded.isoformat(),
                    'sample_size': entry.sample_size,
                    'confidence_score': entry.confidence_score,
                    'price_trend': entry.price_trend,
                }
                writer.writerow(row)
    
    def to_json(self, filename: str):
        """Export database to JSON format"""
        data = [entry.to_dict() for entry in self.entries.values()]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
