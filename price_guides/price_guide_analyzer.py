"""
Bang Gia Dat Analyzer

Analyzes, normalizes, and generates insights from price guide data.

Features:
- Price normalization across sources
- Trend detection and analysis
- Market segmentation
- Price deviation calculation
- Quality assessment
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass
from statistics import mean, median, stdev

from price_guide_schema import (
    PriceGuideEntry, Location, PropertyType, LocationLevel,
    PriceRange, PricePerM2, PriceGuideDatabase
)


logger = logging.getLogger(__name__)


@dataclass
class PriceStatistics:
    """Statistical summary of prices"""
    count: int
    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    std_dev: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'count': self.count,
            'min': self.min_price,
            'max': self.max_price,
            'mean': self.mean_price,
            'median': self.median_price,
            'std_dev': self.std_dev,
        }


@dataclass
class LocationMarketAnalysis:
    """Market analysis for a specific location"""
    location: Location
    property_type: PropertyType
    
    # Price data
    total_entries: int
    price_stats: Optional[PriceStatistics] = None
    price_per_m2_stats: Optional[PriceStatistics] = None
    
    # Source diversity
    sources: List[str] = None
    unique_sources: int = 0
    
    # Trends
    avg_trend: Optional[str] = None  # "up", "down", "stable"
    avg_trend_percentage: Optional[float] = None
    
    # Confidence
    overall_confidence: float = 0.7
    source_confidence: float = 0.7  # Based on source diversity
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
    
    def update_confidence(self):
        """Calculate overall confidence based on data quality"""
        # More sources = higher confidence
        source_weight = min(self.unique_sources / 3.0, 1.0)  # Max at 3 sources
        
        # More data points = higher confidence
        data_weight = min(self.total_entries / 10.0, 1.0)  # Max at 10 entries
        
        # Combine
        self.source_confidence = source_weight * 0.7 + 0.3
        self.overall_confidence = (source_weight + data_weight) / 2 * 0.9 + 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'location': self.location.to_dict(),
            'property_type': self.property_type.value,
            'total_entries': self.total_entries,
            'price_stats': self.price_stats.to_dict() if self.price_stats else None,
            'price_per_m2_stats': self.price_per_m2_stats.to_dict() if self.price_per_m2_stats else None,
            'sources': list(set(self.sources)),
            'unique_sources': self.unique_sources,
            'trend': self.avg_trend,
            'trend_percentage': self.avg_trend_percentage,
            'confidence': self.overall_confidence,
        }


class PriceGuideAnalyzer:
    """Analyzes price guide data"""
    
    def __init__(self, database: PriceGuideDatabase):
        self.database = database
        self.analyses: Dict[str, LocationMarketAnalysis] = {}
    
    def analyze_all(self) -> Dict[str, LocationMarketAnalysis]:
        """Analyze all entries in database"""
        # Group by location and property type
        groups = self._group_entries()
        
        for key, entries in groups.items():
            analysis = self._analyze_group(entries)
            self.analyses[key] = analysis
        
        return self.analyses
    
    def _group_entries(self) -> Dict[str, List[PriceGuideEntry]]:
        """Group entries by location and property type"""
        groups = {}
        
        for entry in self.database.entries.values():
            loc_str = entry.location.to_string()
            key = f"{loc_str}_{entry.property_type.value}"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(entry)
        
        return groups
    
    def _analyze_group(self, entries: List[PriceGuideEntry]) -> LocationMarketAnalysis:
        """Analyze a group of entries"""
        if not entries:
            return None
        
        # Get representative location and type
        location = entries[0].location
        property_type = entries[0].property_type
        sources = [e.source for e in entries]
        
        # Analyze prices
        prices = [e.price_range.average_price for e in entries if e.price_range]
        prices_per_m2 = [e.price_per_m2.average_price_per_m2 for e in entries if e.price_per_m2]
        
        price_stats = self._calculate_stats(prices) if prices else None
        price_per_m2_stats = self._calculate_stats(prices_per_m2) if prices_per_m2 else None
        
        # Analyze trends
        trends = [e.price_trend for e in entries if e.price_trend]
        trend_percentages = [e.trend_percentage for e in entries if e.trend_percentage]
        
        avg_trend = self._determine_trend(trends)
        avg_trend_percentage = mean(trend_percentages) if trend_percentages else None
        
        # Create analysis
        analysis = LocationMarketAnalysis(
            location=location,
            property_type=property_type,
            total_entries=len(entries),
            price_stats=price_stats,
            price_per_m2_stats=price_per_m2_stats,
            sources=sources,
            unique_sources=len(set(sources)),
            avg_trend=avg_trend,
            avg_trend_percentage=avg_trend_percentage,
        )
        
        analysis.update_confidence()
        return analysis
    
    @staticmethod
    def _calculate_stats(values: List[float]) -> Optional[PriceStatistics]:
        """Calculate statistics for a list of values"""
        if not values:
            return None
        
        values.sort()
        std = stdev(values) if len(values) > 1 else None
        
        return PriceStatistics(
            count=len(values),
            min_price=min(values),
            max_price=max(values),
            mean_price=mean(values),
            median_price=median(values),
            std_dev=std,
        )
    
    @staticmethod
    def _determine_trend(trends: List[str]) -> Optional[str]:
        """Determine overall trend from list of trend indicators"""
        if not trends:
            return None
        
        up_count = trends.count('up')
        down_count = trends.count('down')
        
        if up_count > down_count * 1.5:
            return 'up'
        elif down_count > up_count * 1.5:
            return 'down'
        return 'stable'
    
    def normalize_prices(self, entries: List[PriceGuideEntry]) -> List[PriceGuideEntry]:
        """Normalize prices across different sources"""
        # Calculate median price for each location/type across sources
        groups = {}
        for entry in entries:
            key = f"{entry.location.to_string()}_{entry.property_type.value}"
            if key not in groups:
                groups[key] = []
            if entry.price_range:
                groups[key].append(entry.price_range.average_price)
        
        # Adjust outliers and normalize
        normalized_entries = []
        for entry in entries:
            key = f"{entry.location.to_string()}_{entry.property_type.value}"
            median_price = median(groups[key]) if groups[key] else None
            
            if median_price and entry.price_range:
                # Adjust if too far from median (±50%)
                avg_price = entry.price_range.average_price
                if avg_price < median_price * 0.5 or avg_price > median_price * 1.5:
                    # Mark as outlier but keep data
                    entry.notes = f"{entry.notes or ''} [OUTLIER_DETECTED]".strip()
            
            normalized_entries.append(entry)
        
        return normalized_entries
    
    def calculate_price_deviation(self, location: Location, property_type: PropertyType,
                                 listing_price: float) -> Optional[Dict[str, Any]]:
        """Calculate price deviation between listing and price guide"""
        
        # Find matching price guide entries
        entries = self.database.find_by_location(location)
        matching = [e for e in entries if e.property_type == property_type]
        
        if not matching:
            return None
        
        # Calculate average from price guides
        guide_prices = [e.price_range.average_price for e in matching if e.price_range]
        if not guide_prices:
            return None
        
        avg_guide_price = mean(guide_prices)
        deviation = ((listing_price - avg_guide_price) / avg_guide_price) * 100
        
        return {
            'guide_price': avg_guide_price,
            'listing_price': listing_price,
            'deviation_percent': deviation,
            'is_overpriced': deviation > 10,
            'is_underpriced': deviation < -10,
            'matching_entries': len(matching),
        }
    
    def get_price_trends(self, location: Location, property_type: PropertyType,
                        days: int = 365) -> Optional[Dict[str, Any]]:
        """Get price trends for a location over time"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        entries = self.database.find_by_location(location)
        matching = [e for e in entries
                   if e.property_type == property_type and
                   e.date_recorded >= cutoff_date]
        
        if not matching:
            return None
        
        # Sort by date
        matching.sort(key=lambda e: e.date_recorded)
        
        prices = [e.price_range.average_price for e in matching if e.price_range]
        if len(prices) < 2:
            return None
        
        first_price = prices[0]
        last_price = prices[-1]
        change_percent = ((last_price - first_price) / first_price) * 100
        
        return {
            'start_date': matching[0].date_recorded.isoformat(),
            'end_date': matching[-1].date_recorded.isoformat(),
            'start_price': first_price,
            'end_price': last_price,
            'change_percent': change_percent,
            'data_points': len(prices),
            'trend': 'up' if change_percent > 0 else 'down',
        }
    
    def get_market_report(self, location: Location) -> Dict[str, Any]:
        """Generate a market report for a location"""
        
        entries = self.database.find_by_location(location)
        if not entries:
            return {'error': 'No data found for this location'}
        
        # Group by property type
        by_type = {}
        for entry in entries:
            if entry.property_type not in by_type:
                by_type[entry.property_type] = []
            by_type[entry.property_type].append(entry)
        
        property_reports = {}
        for prop_type, type_entries in by_type.items():
            prices = [e.price_range.average_price for e in type_entries if e.price_range]
            property_reports[prop_type.value] = {
                'count': len(type_entries),
                'avg_price': mean(prices) if prices else None,
                'min_price': min(prices) if prices else None,
                'max_price': max(prices) if prices else None,
                'sources': list(set(e.source for e in type_entries)),
            }
        
        return {
            'location': location.to_dict(),
            'total_entries': len(entries),
            'unique_sources': len(set(e.source for e in entries)),
            'property_types': property_reports,
            'last_updated': max(e.date_recorded for e in entries).isoformat(),
        }
    
    def identify_market_gaps(self) -> List[Dict[str, Any]]:
        """Identify locations and property types with limited data"""
        
        gaps = []
        groups = self._group_entries()
        
        for key, entries in groups.items():
            # Low confidence indicators
            if len(entries) < 2:  # Only one source
                location = entries[0].location
                prop_type = entries[0].property_type
                gaps.append({
                    'location': location.to_string(),
                    'property_type': prop_type.value,
                    'reason': 'Single source only',
                    'entries': len(entries),
                })
            
            # Missing price per m² data
            if not any(e.price_per_m2 for e in entries):
                gaps.append({
                    'location': entries[0].location.to_string(),
                    'property_type': entries[0].property_type.value,
                    'reason': 'No price per m² data',
                    'entries': len(entries),
                })
        
        return gaps


class PriceGuideQualityAssessor:
    """Assess quality and reliability of price guide data"""
    
    @staticmethod
    def assess_entry(entry: PriceGuideEntry) -> Dict[str, Any]:
        """Assess quality of a single entry"""
        
        issues = []
        score = 100
        
        # Check for required fields
        if not entry.price_range and not entry.price_per_m2:
            issues.append("No price data provided")
            score -= 30
        
        # Check date freshness
        days_old = (datetime.now() - entry.date_recorded).days
        if days_old > 90:
            issues.append(f"Data is {days_old} days old")
            score -= min(days_old // 30 * 10, 30)
        
        # Check confidence
        if entry.confidence_score < 0.5:
            issues.append("Low confidence score")
            score -= 10
        
        # Check sample size
        if entry.sample_size and entry.sample_size < 5:
            issues.append("Small sample size")
            score -= 5
        
        return {
            'entry_id': entry.id,
            'quality_score': max(score, 0),
            'issues': issues,
            'recommended_use': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low',
        }
    
    @staticmethod
    def assess_database(database: PriceGuideDatabase) -> Dict[str, Any]:
        """Assess overall database quality"""
        
        total_entries = len(database.entries)
        total_quality = 0
        issue_count = 0
        
        for entry in database.entries.values():
            assessment = PriceGuideQualityAssessor.assess_entry(entry)
            total_quality += assessment['quality_score']
            issue_count += len(assessment['issues'])
        
        avg_quality = total_quality / total_entries if total_entries > 0 else 0
        
        return {
            'total_entries': total_entries,
            'unique_sources': len(database.index_by_source),
            'average_quality_score': avg_quality,
            'total_issues': issue_count,
            'issues_per_entry': issue_count / total_entries if total_entries > 0 else 0,
            'quality_rating': 'High' if avg_quality >= 80 else 'Medium' if avg_quality >= 60 else 'Low',
            'sources_breakdown': {source: len(ids) for source, ids in database.index_by_source.items()},
        }


if __name__ == "__main__":
    # Example usage
    from price_guide_scraper import PriceGuideScraper
    
    scraper = PriceGuideScraper()
    database = scraper.scrape_all()
    
    analyzer = PriceGuideAnalyzer(database)
    analyses = analyzer.analyze_all()
    
    quality_assessment = PriceGuideQualityAssessor.assess_database(database)
    print("Database Quality Assessment:")
    print(quality_assessment)
