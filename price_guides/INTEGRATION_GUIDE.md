# Bang Gia Dat (Price Guide) Integration Guide

## Overview

This guide explains how to integrate "bang gia dat" (Vietnamese real estate price guides) with the EstatePredictor ML model.

## What is Bang Gia Dat?

**Bang gia dat** (literally "price list for land") refers to standardized price guides published by Vietnamese real estate websites showing typical market prices by location, property type, and other characteristics.

Key characteristics:
- **Location-based**: Organized by Province → District → Ward → Street
- **Property-typed**: Separate guides for apartments, houses, land, commercial, etc.
- **Regular updates**: Typically updated monthly or quarterly
- **Market reference**: Reflects average/median market prices in each area

## Data Sources

The system extracts data from:

1. **guland.vn/bang-gia-dat** - Primary source for price guides
   - Comprehensive coverage by location
   - Regular updates (monthly)
   - Price ranges and per-m² pricing

2. **batdongsan.com.vn** - Largest Vietnamese real estate portal
   - Aggregated from millions of listings
   - Covers all property types
   - Historical price tracking

3. **meeyland.com** - Real estate data platform
   - Market analysis reports
   - Price trends
   - Location-based segmentation

4. **onehousing.vn** - Real estate news and data
   - Market reports
   - Price indices
   - Trend analysis

## Architecture

```
┌─────────────────────────────────────────────┐
│ Price Guide Extraction                      │
├─────────────────────────────────────────────┤
│ price_guide_scraper.py                      │
│ - GulandScraper                             │
│ - BatdongSanScraper                         │
│ - MeeylandScraper                           │
│ - OneHousingScraper                         │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Data Storage & Schema                       │
├─────────────────────────────────────────────┤
│ price_guide_schema.py                       │
│ - PriceGuideEntry                           │
│ - Location hierarchy                        │
│ - PriceGuideDatabase                        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Analysis & Quality Assessment               │
├─────────────────────────────────────────────┤
│ price_guide_analyzer.py                     │
│ - PriceGuideAnalyzer                        │
│ - Trend detection                           │
│ - Quality assessment                        │
│ - Normalization                             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ ML Integration                              │
├─────────────────────────────────────────────┤
│ ml_integration.py                           │
│ - LocationMatcher                           │
│ - PriceGuideFeatureExtractor                │
│ - Feature engineering                       │
│ - Price benchmarking                        │
└─────────────────────────────────────────────┘
```

## Data Schema

### Location Hierarchy

```python
Location(
    province="Hà Nội",          # Required
    district="Hoàn Kiếm",       # Optional
    ward="Tràng Tiền",          # Optional
    street="Phố Cổ",            # Optional
    neighborhood="Bến Vân Đồn"  # Optional
)
```

### Price Guide Entry

```python
PriceGuideEntry(
    id="guland_ha_noi_hoan_kiem_apartment_20260317",
    source="guland.vn",
    location=Location(...),
    property_type=PropertyType.RESIDENTIAL_APARTMENT,
    
    # Pricing data
    price_range=PriceRange(
        min_price=3e9,      # 3 billion VND
        max_price=8e9,      # 8 billion VND
        average_price=5.5e9 # Calculated
    ),
    price_per_m2=PricePerM2(
        min_price_per_m2=30e6,      # 30M VND/m²
        max_price_per_m2=80e6,      # 80M VND/m²
        average_price_per_m2=55e6   # 55M VND/m²
    ),
    
    # Metadata
    date_recorded=datetime(2026, 3, 17),
    sample_size=150,
    confidence_score=0.85,
    price_trend="up",
    trend_percentage=5.2,
)
```

## Usage Examples

### 1. Scraping Price Guides

```python
from price_guide_scraper import PriceGuideScraper

# Initialize scraper
scraper = PriceGuideScraper()

# Scrape all sources
database = scraper.scrape_all()

# Or scrape specific source
database = scraper.scrape_source("guland.vn")

# Export results
database.to_csv("bang_gia_dat.csv")
database.to_json("bang_gia_dat.json")
```

### 2. Analyzing Price Guides

```python
from price_guide_analyzer import PriceGuideAnalyzer

# Create analyzer
analyzer = PriceGuideAnalyzer(database)

# Analyze all entries
analyses = analyzer.analyze_all()

# Get market report for location
location = Location(province="Hà Nội", district="Hoàn Kiếm")
report = analyzer.get_market_report(location)
print(report)

# Analyze price trends
trends = analyzer.get_price_trends(location, PropertyType.RESIDENTIAL_APARTMENT)
print(f"12-month trend: {trends['trend']} ({trends['change_percent']:.1f}%)")

# Calculate price deviation for a listing
deviation = analyzer.calculate_price_deviation(
    location=Location(...),
    property_type=PropertyType.RESIDENTIAL_APARTMENT,
    listing_price=5e9
)
print(f"Listing is {deviation['deviation_percent']:.1f}% from guide price")
```

### 3. Extracting ML Features

```python
from ml_integration import PriceGuideMLPipeline
from price_guide_schema import Location, PropertyType

# Initialize pipeline
pipeline = PriceGuideMLPipeline(database)

# Example listing
listing = {
    'location': Location(
        province='Hà Nội',
        district='Hoàn Kiếm',
        ward='Tràng Tiền'
    ),
    'property_type': PropertyType.RESIDENTIAL_APARTMENT,
    'price': 5e9,
    'size_sqm': 100,
}

# Extract features
features = pipeline.feature_extractor.extract_features(listing)

# Process multiple listings
all_listings = [listing1, listing2, listing3, ...]
all_features = pipeline.prepare_features(all_listings)
```

### 4. Integration with ML Model

```python
import pandas as pd
from ml_integration import PriceGuideMLPipeline

# Prepare price guide features
pipeline = PriceGuideMLPipeline(database)
listings_data = [...]  # Your listing data
features = pipeline.prepare_features(listings_data)

# Convert to DataFrame
features_df = pd.DataFrame(features)

# Combine with other features from your listings
X = pd.concat([your_existing_features, features_df], axis=1)

# Train your ML model
model.fit(X, y)
```

## Extracted Features

The price guide integration adds these features to your ML model:

### Price Features
- **guide_price**: Reference price from price guide (VND)
- **price_deviation_percent**: How much listing price deviates from guide (%)
- **price_per_m2_deviation**: Unit price deviation from guide (%)
- **is_overpriced**: Binary flag if listing is >10% above guide
- **is_underpriced**: Binary flag if listing is >10% below guide

### Market Trend Features
- **market_trend_signal**: Trend direction (-1=down, 0=stable, 1=up)
- **trend_strength**: Magnitude of trend (0-1)
- **market_activity**: Activity level in location (0-1)

### Data Quality Features
- **source_diversity**: Number of sources reporting this price (0-1)
- **data_freshness**: How recent the price guide data is (0-1)
- **data_quantity**: Number of data points available (0-1)
- **guide_confidence**: Overall reliability score (0-1)

### Location Features
- **location_specificity**: How detailed the location data is (0-1)
- **market_heat**: Market activity in this location (0-1)

## Data Freshness & Updates

Price guides should be updated regularly:

- **Refresh frequency**: Weekly to monthly
- **Data retention**: Keep historical data for trend analysis
- **Quality threshold**: Filter entries with confidence < 0.5

```python
# Schedule regular updates
from datetime import datetime, timedelta

last_update = datetime.now()
update_interval = timedelta(weeks=2)  # Update every 2 weeks

if datetime.now() - last_update > update_interval:
    scraper = PriceGuideScraper()
    new_database = scraper.scrape_all()
    # Merge with historical data
    # ...
```

## Handling Different Data Quality

The system provides confidence scoring:

```python
# Filter by confidence level
high_confidence = [e for e in database.entries.values() 
                   if e.confidence_score >= 0.8]

medium_confidence = [e for e in database.entries.values() 
                     if 0.6 <= e.confidence_score < 0.8]

# Use confidence in weighted analysis
from statistics import mean
avg_price = sum(e.price_range.average_price * e.confidence_score 
                for e in entries) / sum(e.confidence_score for e in entries)
```

## Troubleshooting

### No Data for Location

If price guides aren't found for a location:

1. Check location spelling/format
2. Try broader location (ward → district → province)
3. Check if location is supported by sources
4. Look for data gaps using `analyzer.identify_market_gaps()`

```python
gaps = analyzer.identify_market_gaps()
print("Locations with limited data:")
for gap in gaps:
    print(f"  {gap['location']}: {gap['reason']}")
```

### Outlier Prices

The analyzer automatically detects outliers:

```python
normalized = analyzer.normalize_prices(entries)
outliers = [e for e in normalized if 'OUTLIER_DETECTED' in (e.notes or '')]
```

### Missing Price per m²

If `price_per_m2` is None, you can estimate from `price_range` and listing size:

```python
if entry.price_per_m2 is None and listing.get('size_sqm'):
    estimated_price_per_m2 = (
        entry.price_range.average_price / listing['size_sqm']
    )
```

## Performance Considerations

### Memory Usage
- Store database in cache for repeated queries
- Use indices for fast lookups by location/source

### Query Optimization
```python
# Fast: Use database indices
entries = database.find_by_location(location)

# Slower: Loop through all entries
entries = [e for e in database.entries.values() ...]
```

### Feature Extraction Speed
```python
# Cache analyzer results
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_location_features(location_key):
    # ... expensive computation
    pass
```

## Integration Checklist

- [ ] Install dependencies: `pip install requests beautifulsoup4`
- [ ] Import required modules
- [ ] Initialize PriceGuideScraper
- [ ] Scrape initial data: `database = scraper.scrape_all()`
- [ ] Create PriceGuideMLPipeline
- [ ] Test feature extraction on sample listings
- [ ] Integrate features into existing ML pipeline
- [ ] Add price guide refresh to data update schedule
- [ ] Monitor data quality metrics
- [ ] Set up logging for scraping errors

## References

- Vietnamese Real Estate Market: https://guland.vn
- Market Data Providers: batdongsan.com.vn, meeyland.com
- Feature Engineering Best Practices: See `price_guide_analyzer.py`

## Support

For issues or feature requests:
1. Check existing price guide entries with `database.find_by_location()`
2. Review quality assessment: `PriceGuideQualityAssessor.assess_database(database)`
3. Analyze gaps: `analyzer.identify_market_gaps()`
