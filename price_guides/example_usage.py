"""
Complete Examples: Using Bang Gia Dat Price Guide System

Demonstrates all major features and workflows.
"""

import logging
from datetime import datetime
from price_guide_schema import Location, PropertyType, PriceGuideDatabase
from price_guide_scraper import PriceGuideScraper, ScraperConfig
from price_guide_analyzer import PriceGuideAnalyzer, PriceGuideQualityAssessor
from ml_integration import PriceGuideMLPipeline

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_scraping():
    """Example 1: Basic scraping of price guides"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Price Guide Scraping")
    print("="*60)
    
    # Initialize scraper with custom config
    config = ScraperConfig(
        timeout=10,
        max_retries=3,
        rate_limit_delay=1.0,
    )
    
    scraper = PriceGuideScraper(config)
    
    # Scrape all sources
    print("\nScraping price guides from all sources...")
    database = scraper.scrape_all()
    
    print(f"\n✓ Total entries scraped: {len(database.entries)}")
    print(f"✓ Unique sources: {len(database.index_by_source)}")
    print(f"✓ Unique locations: {len(database.index_by_location)}")
    
    # Show source breakdown
    print("\nBreakdown by source:")
    for source, entry_ids in database.index_by_source.items():
        print(f"  {source}: {len(entry_ids)} entries")
    
    return database


def example_2_scrape_single_source(database=None):
    """Example 2: Scrape a single specific source"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Scrape Single Source")
    print("="*60)
    
    scraper = PriceGuideScraper()
    
    # Scrape only guland.vn
    print("\nScraping guland.vn only...")
    guland_database = scraper.scrape_source("guland.vn")
    
    guland_entries = guland_database.find_by_source("guland.vn")
    print(f"✓ Scraped {len(guland_entries)} entries from guland.vn")
    
    return guland_database


def example_3_export_data(database):
    """Example 3: Export data to different formats"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Export Price Guide Data")
    print("="*60)
    
    if not database.entries:
        print("No data to export. Skipping...")
        return
    
    # Export to CSV
    csv_file = "/tmp/bang_gia_dat.csv"
    print(f"\nExporting to CSV: {csv_file}")
    database.to_csv(csv_file)
    print("✓ CSV export complete")
    
    # Export to JSON
    json_file = "/tmp/bang_gia_dat.json"
    print(f"Exporting to JSON: {json_file}")
    database.to_json(json_file)
    print("✓ JSON export complete")


def example_4_analyze_prices(database):
    """Example 4: Analyze price guides"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Price Guide Analysis")
    print("="*60)
    
    if not database.entries:
        print("No data to analyze. Skipping...")
        return
    
    # Create analyzer
    analyzer = PriceGuideAnalyzer(database)
    
    # Analyze all entries
    print("\nAnalyzing all price guide entries...")
    analyses = analyzer.analyze_all()
    
    print(f"✓ Completed analysis for {len(analyses)} location/type combinations")
    
    # Show some results
    print("\nSample analyses:")
    for i, (key, analysis) in enumerate(list(analyses.items())[:3]):
        print(f"\n  {i+1}. {analysis.location.to_string()}")
        print(f"     Property Type: {analysis.property_type.value}")
        print(f"     Total Entries: {analysis.total_entries}")
        print(f"     Sources: {analysis.unique_sources}")
        
        if analysis.price_stats:
            print(f"     Price Range: {analysis.price_stats.min_price:,.0f} - {analysis.price_stats.max_price:,.0f}")
            print(f"     Average: {analysis.price_stats.mean_price:,.0f} VND")
        
        if analysis.avg_trend:
            print(f"     Trend: {analysis.avg_trend}")
    
    return analyzer


def example_5_market_report(analyzer):
    """Example 5: Generate market report for a location"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Market Report Generation")
    print("="*60)
    
    # Define target location
    location = Location(
        province="Hà Nội",
        district="Hoàn Kiếm"
    )
    
    print(f"\nGenerating market report for: {location.to_string()}")
    
    # Get report
    report = analyzer.get_market_report(location)
    
    if 'error' in report:
        print(f"✗ Error: {report['error']}")
        return
    
    print(f"\n✓ Total entries: {report['total_entries']}")
    print(f"✓ Unique sources: {report['unique_sources']}")
    print(f"✓ Last updated: {report['last_updated']}")
    
    print(f"\nPrice by property type:")
    for prop_type, data in report['property_types'].items():
        print(f"\n  {prop_type}:")
        print(f"    Count: {data['count']}")
        if data['avg_price']:
            print(f"    Average: {data['avg_price']:,.0f} VND")
            print(f"    Range: {data['min_price']:,.0f} - {data['max_price']:,.0f} VND")
        print(f"    Sources: {', '.join(data['sources'])}")


def example_6_price_trends(analyzer):
    """Example 6: Analyze price trends"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Price Trend Analysis")
    print("="*60)
    
    location = Location(
        province="TP. Hồ Chí Minh",
        district="Quận 1"
    )
    
    property_type = PropertyType.RESIDENTIAL_APARTMENT
    
    print(f"\nAnalyzing trends for: {location.to_string()} - {property_type.value}")
    
    # Get trend data
    trends = analyzer.get_price_trends(location, property_type, days=365)
    
    if trends:
        print(f"\n✓ Trend Data:")
        print(f"  Period: {trends['start_date']} to {trends['end_date']}")
        print(f"  Start Price: {trends['start_price']:,.0f} VND")
        print(f"  End Price: {trends['end_price']:,.0f} VND")
        print(f"  Change: {trends['change_percent']:.2f}%")
        print(f"  Trend: {trends['trend'].upper()}")
        print(f"  Data Points: {trends['data_points']}")
    else:
        print("✗ No trend data available for this location")


def example_7_price_deviation(analyzer):
    """Example 7: Calculate price deviation from guide"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Price Deviation Analysis")
    print("="*60)
    
    # Example listing
    location = Location(
        province="Hà Nội",
        district="Hoàn Kiếm",
        ward="Tràng Tiền"
    )
    
    property_type = PropertyType.RESIDENTIAL_APARTMENT
    listing_price = 5.5e9  # 5.5 billion VND
    
    print(f"\nAnalyzing listing:")
    print(f"  Location: {location.to_string()}")
    print(f"  Type: {property_type.value}")
    print(f"  Listing Price: {listing_price:,.0f} VND")
    
    # Calculate deviation
    deviation = analyzer.calculate_price_deviation(
        location=location,
        property_type=property_type,
        listing_price=listing_price,
    )
    
    if deviation:
        print(f"\n✓ Analysis Result:")
        print(f"  Guide Price: {deviation['guide_price']:,.0f} VND")
        print(f"  Deviation: {deviation['deviation_percent']:.2f}%")
        print(f"  Status: {'OVERPRICED' if deviation['is_overpriced'] else 'UNDERPRICED' if deviation['is_underpriced'] else 'FAIR'}")
        print(f"  Matching Entries: {deviation['matching_entries']}")
    else:
        print("✗ No price guide data found for this location")


def example_8_data_quality(database):
    """Example 8: Assess data quality"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Data Quality Assessment")
    print("="*60)
    
    if not database.entries:
        print("No data to assess. Skipping...")
        return
    
    # Assess database
    assessment = PriceGuideQualityAssessor.assess_database(database)
    
    print(f"\n✓ Overall Assessment:")
    print(f"  Total Entries: {assessment['total_entries']}")
    print(f"  Average Quality Score: {assessment['average_quality_score']:.1f}/100")
    print(f"  Quality Rating: {assessment['quality_rating']}")
    print(f"  Total Issues: {assessment['total_issues']}")
    print(f"  Issues per Entry: {assessment['issues_per_entry']:.2f}")
    
    print(f"\n✓ By Source:")
    for source, count in assessment['sources_breakdown'].items():
        print(f"  {source}: {count} entries")
    
    # Show sample quality assessments
    print(f"\n✓ Sample Entry Quality:")
    for entry in list(database.entries.values())[:3]:
        entry_assessment = PriceGuideQualityAssessor.assess_entry(entry)
        print(f"\n  {entry.source} ({entry.location.to_string()}):")
        print(f"    Quality Score: {entry_assessment['quality_score']:.1f}")
        print(f"    Recommendation: {entry_assessment['recommended_use']}")
        if entry_assessment['issues']:
            print(f"    Issues: {', '.join(entry_assessment['issues'][:2])}")


def example_9_ml_features(database):
    """Example 9: Extract ML features from price guides"""
    print("\n" + "="*60)
    print("EXAMPLE 9: ML Feature Extraction")
    print("="*60)
    
    if not database.entries:
        print("No data for feature extraction. Skipping...")
        return
    
    # Create pipeline
    pipeline = PriceGuideMLPipeline(database)
    
    # Example listing
    listing = {
        'location': Location(
            province='Hà Nội',
            district='Hoàn Kiếm',
            ward='Tràng Tiền'
        ),
        'property_type': PropertyType.RESIDENTIAL_APARTMENT,
        'price': 5.5e9,
        'size_sqm': 100,
    }
    
    print(f"\nExtracting features for listing:")
    print(f"  Location: {listing['location'].to_string()}")
    print(f"  Price: {listing['price']:,.0f} VND")
    print(f"  Size: {listing['size_sqm']} m²")
    
    # Extract features
    features = pipeline.feature_extractor.extract_features(listing)
    
    print(f"\n✓ Extracted {len(features)} features:")
    
    # Group by category
    price_features = {
        'guide_price', 'price_deviation_percent', 'price_per_m2_deviation',
        'is_overpriced', 'is_underpriced'
    }
    
    trend_features = {
        'market_trend_signal', 'trend_strength', 'market_activity'
    }
    
    quality_features = {
        'source_diversity', 'data_freshness', 'data_quantity', 'guide_confidence'
    }
    
    location_features = {'location_specificity', 'market_heat'}
    
    print("\nPrice Features:")
    for feature in price_features:
        value = features.get(feature, 0)
        if isinstance(value, float):
            print(f"  {feature}: {value:.4f}")
        else:
            print(f"  {feature}: {value:,.0f}")
    
    print("\nTrend Features:")
    for feature in trend_features:
        print(f"  {feature}: {features.get(feature, 0):.4f}")
    
    print("\nQuality Features:")
    for feature in quality_features:
        print(f"  {feature}: {features.get(feature, 0):.4f}")
    
    print("\nLocation Features:")
    for feature in location_features:
        print(f"  {feature}: {features.get(feature, 0):.4f}")


def example_10_batch_processing(database):
    """Example 10: Batch feature extraction for multiple listings"""
    print("\n" + "="*60)
    print("EXAMPLE 10: Batch Processing")
    print("="*60)
    
    if not database.entries:
        print("No data for batch processing. Skipping...")
        return
    
    # Create pipeline
    pipeline = PriceGuideMLPipeline(database)
    
    # Example listings
    listings = [
        {
            'location': Location(province='Hà Nội', district='Hoàn Kiếm'),
            'property_type': PropertyType.RESIDENTIAL_APARTMENT,
            'price': 5e9,
            'size_sqm': 100,
        },
        {
            'location': Location(province='TP. Hồ Chí Minh', district='Quận 1'),
            'property_type': PropertyType.RESIDENTIAL_APARTMENT,
            'price': 10e9,
            'size_sqm': 120,
        },
        {
            'location': Location(province='Đà Nẵng', district='Hải Châu'),
            'property_type': PropertyType.RESIDENTIAL_HOUSE,
            'price': 3e9,
            'size_sqm': 150,
        },
    ]
    
    print(f"\nProcessing {len(listings)} listings...")
    
    # Batch process
    features_list = pipeline.prepare_features(listings)
    
    print(f"✓ Successfully extracted features for {len(features_list)} listings")
    
    # Show summary
    print(f"\nFeature Summary:")
    print(f"  Price Deviation Range: {min(f.get('price_deviation_percent', 0) for f in features_list):.1f}% to {max(f.get('price_deviation_percent', 0) for f in features_list):.1f}%")
    print(f"  Market Trend Signals: {sum(1 for f in features_list if f.get('market_trend_signal', 0) > 0)} up, {sum(1 for f in features_list if f.get('market_trend_signal', 0) < 0)} down")
    print(f"  Average Confidence: {sum(f.get('guide_confidence', 0) for f in features_list) / len(features_list):.3f}")


def example_11_identify_gaps(analyzer):
    """Example 11: Identify data gaps"""
    print("\n" + "="*60)
    print("EXAMPLE 11: Data Gap Identification")
    print("="*60)
    
    # Identify gaps
    print("\nScanning for data gaps...")
    gaps = analyzer.identify_market_gaps()
    
    if gaps:
        print(f"✓ Found {len(gaps)} locations with data quality issues:\n")
        for i, gap in enumerate(gaps[:5], 1):
            print(f"  {i}. {gap['location']} ({gap['property_type']})")
            print(f"     Issue: {gap['reason']}")
            print(f"     Entries: {gap['entries']}\n")
    else:
        print("✓ No significant data gaps found")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("BANG GIA DAT SYSTEM - COMPLETE EXAMPLES")
    print("="*60)
    
    try:
        # Example 1: Basic scraping
        database = example_1_basic_scraping()
        
        # Example 2: Single source
        # example_2_scrape_single_source(database)
        
        # Example 3: Export data
        example_3_export_data(database)
        
        if len(database.entries) > 0:
            # Example 4: Analyze prices
            analyzer = example_4_analyze_prices(database)
            
            # Example 5: Market report
            example_5_market_report(analyzer)
            
            # Example 6: Price trends
            example_6_price_trends(analyzer)
            
            # Example 7: Price deviation
            example_7_price_deviation(analyzer)
            
            # Example 8: Data quality
            example_8_data_quality(database)
            
            # Example 9: ML features
            example_9_ml_features(database)
            
            # Example 10: Batch processing
            example_10_batch_processing(database)
            
            # Example 11: Gap identification
            example_11_identify_gaps(analyzer)
        
        print("\n" + "="*60)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
