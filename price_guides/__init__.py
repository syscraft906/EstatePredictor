"""
Bang Gia Dat (Price Guide) Module

Vietnamese real estate price guide extraction, analysis, and ML integration.

Example usage:
    from price_guides.price_guide_scraper import PriceGuideScraper
    from price_guides.ml_integration import PriceGuideMLPipeline
    
    # Scrape price guides
    scraper = PriceGuideScraper()
    database = scraper.scrape_all()
    
    # Extract ML features
    pipeline = PriceGuideMLPipeline(database)
    features = pipeline.prepare_features(listings)
"""

from .price_guide_schema import (
    PriceGuideEntry,
    Location,
    LocationLevel,
    PropertyType,
    PriceRange,
    PricePerM2,
    PriceGuideDatabase,
    HistoricalPriceData,
)

from .price_guide_scraper import (
    PriceGuideScraper,
    ScraperConfig,
    PriceNormalizer,
    BaseScraper,
    GulandScraper,
    BatdongSanScraper,
    MeeylandScraper,
    OneHousingScraper,
)

from .price_guide_analyzer import (
    PriceGuideAnalyzer,
    LocationMarketAnalysis,
    PriceStatistics,
    PriceGuideQualityAssessor,
)

from .ml_integration import (
    PriceGuideMLPipeline,
    PriceGuideFeatureExtractor,
    LocationMatcher,
)

__version__ = "1.0.0"
__author__ = "EstatePredictor"

__all__ = [
    # Schema
    "PriceGuideEntry",
    "Location",
    "LocationLevel",
    "PropertyType",
    "PriceRange",
    "PricePerM2",
    "PriceGuideDatabase",
    "HistoricalPriceData",
    
    # Scraping
    "PriceGuideScraper",
    "ScraperConfig",
    "PriceNormalizer",
    "BaseScraper",
    "GulandScraper",
    "BatdongSanScraper",
    "MeeylandScraper",
    "OneHousingScraper",
    
    # Analysis
    "PriceGuideAnalyzer",
    "LocationMarketAnalysis",
    "PriceStatistics",
    "PriceGuideQualityAssessor",
    
    # ML Integration
    "PriceGuideMLPipeline",
    "PriceGuideFeatureExtractor",
    "LocationMatcher",
]
