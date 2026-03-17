"""
ML Integration Module

Integrates bang gia dat (price guide) data with the EstatePredictor ML model.

Features:
- Feature engineering from price guide data
- Mapping between listings and price guides
- Price deviation features
- Market heat features
- Location-based price benchmarking
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import math

from price_guide_schema import (
    Location, PropertyType, PriceGuideEntry, PriceGuideDatabase
)
from price_guide_analyzer import PriceGuideAnalyzer


logger = logging.getLogger(__name__)


class LocationMatcher:
    """Match listing locations to price guide locations"""
    
    # Vietnamese location mappings for normalization
    PROVINCE_ALIASES = {
        'hà nội': 'Hà Nội',
        'hanoi': 'Hà Nội',
        'ho chi minh': 'TP. Hồ Chí Minh',
        'hồ chí minh': 'TP. Hồ Chí Minh',
        'tphcm': 'TP. Hồ Chí Minh',
        'sài gòn': 'TP. Hồ Chí Minh',
    }
    
    @staticmethod
    def normalize_location(location: Location) -> Location:
        """Normalize location names to standard format"""
        normalized_province = LocationMatcher.PROVINCE_ALIASES.get(
            location.province.lower(),
            location.province
        )
        
        return Location(
            province=normalized_province,
            district=location.district,
            ward=location.ward,
            street=location.street,
        )
    
    @staticmethod
    def calculate_location_distance(loc1: Location, loc2: Location) -> int:
        """Calculate 'distance' between two locations (lower = closer)
        
        Returns:
            - 0: Same street
            - 1: Same ward
            - 2: Same district
            - 3: Same province
            - 999: Different province
        """
        if loc1.province.lower() != loc2.province.lower():
            return 999
        
        if loc1.street and loc2.street and loc1.street.lower() == loc2.street.lower():
            return 0
        
        if loc1.ward and loc2.ward and loc1.ward.lower() == loc2.ward.lower():
            return 1
        
        if loc1.district and loc2.district and loc1.district.lower() == loc2.district.lower():
            return 2
        
        return 3
    
    @staticmethod
    def find_nearest_price_guide(location: Location, property_type: PropertyType,
                                 database: PriceGuideDatabase) -> Optional[PriceGuideEntry]:
        """Find the nearest/most specific price guide entry for a location"""
        
        normalized = LocationMatcher.normalize_location(location)
        
        # Try to find exact or closest match
        best_match = None
        best_distance = 999
        
        for entry in database.entries.values():
            if entry.property_type != property_type:
                continue
            
            distance = LocationMatcher.calculate_location_distance(normalized, entry.location)
            
            if distance < best_distance:
                best_distance = distance
                best_match = entry
        
        return best_match


class PriceGuideFeatureExtractor:
    """Extract ML features from price guide data"""
    
    def __init__(self, database: PriceGuideDatabase, analyzer: PriceGuideAnalyzer):
        self.database = database
        self.analyzer = analyzer
    
    def extract_features(self, listing: Dict[str, Any]) -> Dict[str, float]:
        """Extract all price guide features for a listing
        
        Args:
            listing: Dictionary with listing data (must contain:
                    'location' (Location), 'property_type' (PropertyType), 'price' (float))
        
        Returns:
            Dictionary of features: {
                'guide_price': reference price,
                'price_deviation_percent': deviation from guide,
                'price_per_m2_deviation': deviation in unit price,
                'market_trend_signal': trend indicator (-1, 0, 1),
                'confidence_score': reliability of features,
                'market_heat': activity level (0-1),
                'location_specificity': data specificity level (0-1),
                ...
            }
        """
        features = {}
        
        try:
            location = listing.get('location')
            property_type = listing.get('property_type')
            listing_price = listing.get('price')
            
            if not all([location, property_type, listing_price]):
                return self._get_null_features()
            
            # Find nearest price guide
            price_guide = LocationMatcher.find_nearest_price_guide(
                location, property_type, self.database
            )
            
            if price_guide:
                features.update(self._extract_price_features(listing, price_guide))
                features.update(self._extract_trend_features(location, property_type))
                features.update(self._extract_confidence_features(location, property_type))
            else:
                features.update(self._get_null_features())
            
            # Add location-based features
            features.update(self._extract_location_features(location))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return self._get_null_features()
    
    def _extract_price_features(self, listing: Dict[str, Any],
                               price_guide: PriceGuideEntry) -> Dict[str, float]:
        """Extract price-related features"""
        features = {}
        
        listing_price = listing.get('price', 0)
        
        # Reference price from guide
        if price_guide.price_range:
            guide_avg_price = price_guide.price_range.average_price
            features['guide_price'] = guide_avg_price
            
            # Price deviation
            if guide_avg_price > 0:
                deviation = ((listing_price - guide_avg_price) / guide_avg_price) * 100
                features['price_deviation_percent'] = deviation
                features['is_overpriced'] = 1.0 if deviation > 10 else 0.0
                features['is_underpriced'] = 1.0 if deviation < -10 else 0.0
        
        # Price per m² features
        if price_guide.price_per_m2:
            listing_size = listing.get('size_sqm', 0)
            if listing_size > 0:
                listing_price_per_m2 = listing_price / listing_size
                guide_price_per_m2 = price_guide.price_per_m2.average_price_per_m2
                
                features['listing_price_per_m2'] = listing_price_per_m2
                features['guide_price_per_m2'] = guide_price_per_m2
                
                if guide_price_per_m2 > 0:
                    features['price_per_m2_deviation'] = (
                        (listing_price_per_m2 - guide_price_per_m2) / guide_price_per_m2
                    ) * 100
        
        return features
    
    def _extract_trend_features(self, location: Location,
                               property_type: PropertyType) -> Dict[str, float]:
        """Extract market trend features"""
        features = {}
        
        # Get trend data
        trend_data = self.analyzer.get_price_trends(location, property_type)
        
        if trend_data:
            # Trend direction signal
            trend_map = {'up': 1.0, 'down': -1.0, 'stable': 0.0}
            features['market_trend_signal'] = trend_map.get(trend_data['trend'], 0.0)
            
            # Trend strength
            change_pct = trend_data.get('change_percent', 0)
            features['trend_strength'] = min(abs(change_pct) / 20, 1.0)  # Normalize to 0-1
            
            # Recent activity (based on data points)
            data_points = trend_data.get('data_points', 0)
            features['market_activity'] = min(data_points / 10, 1.0)  # Normalize to 0-1
        else:
            features['market_trend_signal'] = 0.0
            features['trend_strength'] = 0.0
            features['market_activity'] = 0.0
        
        return features
    
    def _extract_confidence_features(self, location: Location,
                                    property_type: PropertyType) -> Dict[str, float]:
        """Extract confidence/reliability features"""
        features = {}
        
        entries = self.database.find_by_location(location)
        matching = [e for e in entries if e.property_type == property_type]
        
        if matching:
            # Source diversity
            sources = set(e.source for e in matching)
            features['source_diversity'] = min(len(sources) / 3, 1.0)
            
            # Data freshness
            from datetime import datetime, timedelta
            latest = max(e.date_recorded for e in matching)
            days_old = (datetime.now() - latest).days
            freshness = max(1.0 - (days_old / 90), 0.0)  # Max 90 days
            features['data_freshness'] = freshness
            
            # Data quantity
            features['data_quantity'] = min(len(matching) / 10, 1.0)
            
            # Average confidence
            avg_confidence = sum(e.confidence_score for e in matching) / len(matching)
            features['guide_confidence'] = avg_confidence
        else:
            features['source_diversity'] = 0.0
            features['data_freshness'] = 0.0
            features['data_quantity'] = 0.0
            features['guide_confidence'] = 0.0
        
        return features
    
    def _extract_location_features(self, location: Location) -> Dict[str, float]:
        """Extract location-specific features"""
        features = {}
        
        # Location specificity (how detailed the location data is)
        if location.street:
            specificity = 1.0
        elif location.ward:
            specificity = 0.7
        elif location.district:
            specificity = 0.5
        else:
            specificity = 0.2
        
        features['location_specificity'] = specificity
        
        # Market heat (based on entry count in location)
        all_entries = self.database.find_by_location(location)
        features['market_heat'] = min(len(all_entries) / 20, 1.0)
        
        return features
    
    @staticmethod
    def _get_null_features() -> Dict[str, float]:
        """Return neutral features when no price guide data available"""
        return {
            'guide_price': 0.0,
            'price_deviation_percent': 0.0,
            'price_per_m2_deviation': 0.0,
            'market_trend_signal': 0.0,
            'trend_strength': 0.0,
            'market_activity': 0.0,
            'source_diversity': 0.0,
            'data_freshness': 0.0,
            'data_quantity': 0.0,
            'guide_confidence': 0.0,
            'location_specificity': 0.0,
            'market_heat': 0.0,
            'is_overpriced': 0.0,
            'is_underpriced': 0.0,
        }


class PriceGuideMLPipeline:
    """Complete pipeline for integrating price guides into ML model"""
    
    def __init__(self, database: PriceGuideDatabase):
        self.database = database
        self.analyzer = PriceGuideAnalyzer(database)
        self.feature_extractor = PriceGuideFeatureExtractor(database, self.analyzer)
    
    def prepare_features(self, listings: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """Prepare features for all listings"""
        features_list = []
        
        for listing in listings:
            features = self.feature_extractor.extract_features(listing)
            features_list.append(features)
        
        return features_list
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return [
            'guide_price',
            'price_deviation_percent',
            'price_per_m2_deviation',
            'market_trend_signal',
            'trend_strength',
            'market_activity',
            'source_diversity',
            'data_freshness',
            'data_quantity',
            'guide_confidence',
            'location_specificity',
            'market_heat',
            'is_overpriced',
            'is_underpriced',
        ]


if __name__ == "__main__":
    # Example usage
    from price_guide_scraper import PriceGuideScraper
    from price_guide_schema import PropertyType
    
    # Initialize
    scraper = PriceGuideScraper()
    database = scraper.scrape_all()
    
    pipeline = PriceGuideMLPipeline(database)
    
    # Example listing
    example_listing = {
        'location': Location(
            province='Hà Nội',
            district='Hoàn Kiếm',
            ward='Tràng Tiền'
        ),
        'property_type': PropertyType.RESIDENTIAL_APARTMENT,
        'price': 5e9,  # 5 billion VND
        'size_sqm': 100,
    }
    
    features = pipeline.feature_extractor.extract_features(example_listing)
    print("Extracted Features:")
    for name, value in features.items():
        print(f"  {name}: {value}")
