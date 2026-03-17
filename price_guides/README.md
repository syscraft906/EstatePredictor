# Bang Gia Dat - Vietnamese Real Estate Price Guide System

Complete system for extracting, analyzing, and integrating Vietnamese real estate price guides with EstatePredictor ML models.

## What is Bang Gia Dat?

**Bang gia dat** (price list) refers to standardized price reference guides published by Vietnamese real estate websites. These guides show:

- Standard market prices by location
- Prices by property type (apartments, houses, land, etc.)
- Price ranges (min, max, average)
- Unit prices (price per m²)
- Market trends (up, down, stable)
- Historical pricing data

## Quick Start

### Installation

```bash
pip install requests beautifulsoup4 pandas
```

### Basic Usage

```python
from price_guides import PriceGuideScraper, PriceGuideMLPipeline

# 1. Scrape price guides
scraper = PriceGuideScraper()
database = scraper.scrape_all()

# 2. Create ML pipeline
pipeline = PriceGuideMLPipeline(database)

# 3. Extract features for listings
features = pipeline.prepare_features(your_listings)

# 4. Use features in ML model
X = combine_with_other_features(features)
model.fit(X, y)
```

## Features

### Data Extraction
- ✅ Multi-source scraping (guland.vn, batdongsan.com.vn, meeyland.com, onehousing.vn)
- ✅ Automatic price normalization
- ✅ Location hierarchy support
- ✅ Property type classification
- ✅ Trend detection

### Analysis
- ✅ Price statistics (mean, median, std dev)
- ✅ Market trend analysis
- ✅ Price deviation calculation
- ✅ Quality assessment
- ✅ Gap identification

### ML Integration
- ✅ Automated feature extraction
- ✅ Location matching
- ✅ Price benchmarking
- ✅ Confidence scoring
- ✅ Market heat calculation

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  price_guides/                                       │
│  ├── __init__.py              # Package init         │
│  ├── README.md                # This file            │
│  ├── INTEGRATION_GUIDE.md     # ML integration docs  │
│  │                                                   │
│  ├── price_guide_schema.py    # Data structures      │
│  │   ├── Location              # Hierarchical loc    │
│  │   ├── PriceRange            # Price data          │
│  │   ├── PricePerM2            # Unit pricing        │
│  │   ├── PriceGuideEntry       # Single guide entry  │
│  │   └── PriceGuideDatabase    # Storage & queries   │
│  │                                                   │
│  ├── price_guide_scraper.py  # Web scraping         │
│  │   ├── PriceNormalizer      # Price parsing       │
│  │   ├── BaseScraper          # Base class          │
│  │   ├── GulandScraper        # guland.vn           │
│  │   ├── BatdongSanScraper    # batdongsan.com.vn   │
│  │   ├── MeeylandScraper      # meeyland.com        │
│  │   ├── OneHousingScraper    # onehousing.vn       │
│  │   └── PriceGuideScraper    # Main orchestrator   │
│  │                                                   │
│  ├── price_guide_analyzer.py # Analysis tools       │
│  │   ├── PriceGuideAnalyzer   # Statistics          │
│  │   ├── LocationMarketAnalysis # Market analysis    │
│  │   └── PriceGuideQualityAssessor # Quality check   │
│  │                                                   │
│  ├── ml_integration.py        # ML feature extract   │
│  │   ├── LocationMatcher      # Location normalizat │
│  │   ├── PriceGuideFeatureExtractor # Features      │
│  │   └── PriceGuideMLPipeline # Complete pipeline   │
│  │                                                   │
│  ├── example_bang_gia_dat.csv # Sample data        │
│  └── TECHNICAL_GUIDE.md       # Implementation doc  │
└──────────────────────────────────────────────────────┘
```

## Extracted Features

The system generates 14 ML-ready features for each listing:

### Price Features (5)
- `guide_price`: Reference price from guides
- `price_deviation_percent`: How much listing differs from guide
- `price_per_m2_deviation`: Unit price deviation
- `is_overpriced`: Binary flag (>10% above guide)
- `is_underpriced`: Binary flag (>10% below guide)

### Market Features (3)
- `market_trend_signal`: Direction of price trend (-1/0/1)
- `trend_strength`: Magnitude of trend (0-1)
- `market_activity`: Market activity level (0-1)

### Data Quality Features (4)
- `source_diversity`: Number of sources (0-1)
- `data_freshness`: Age of data (0-1)
- `data_quantity`: Number of data points (0-1)
- `guide_confidence`: Overall reliability (0-1)

### Location Features (2)
- `location_specificity`: Detail level of location (0-1)
- `market_heat`: Activity in location (0-1)

## Data Sources

### 1. guland.vn
- **URL**: https://guland.vn/bang-gia-dat
- **Coverage**: All provinces and districts
- **Update Frequency**: Monthly
- **Data Types**: Price ranges, price per m², trends

### 2. batdongsan.com.vn
- **URL**: https://batdongsan.com.vn (aggregated from listings)
- **Coverage**: Nationwide, all property types
- **Update Frequency**: Real-time
- **Data Types**: Market statistics, average prices

### 3. meeyland.com
- **URL**: https://meeyland.com
- **Coverage**: Major cities
- **Update Frequency**: Weekly
- **Data Types**: Price guides, market reports, trends

### 4. onehousing.vn
- **URL**: https://onehousing.vn
- **Coverage**: Major markets
- **Update Frequency**: Monthly
- **Data Types**: Market analysis, price indices

## Data Schema

### Location Hierarchy

```python
Location(
    province="Hà Nội",          # Required: "Hà Nội", "TP. Hồ Chí Minh", etc.
    district="Hoàn Kiếm",       # Optional: "Hoàn Kiếm", "Quận 1", etc.
    ward="Tràng Tiền",          # Optional: "Tràng Tiền", "Bến Nghé", etc.
    street="Phố Cổ",            # Optional: Street/area name
    neighborhood="Bến Vân Đồn"  # Optional: Neighborhood name
)
```

### Price Guide Entry

```python
PriceGuideEntry(
    id="guland_ha_noi_hoan_kiem_apartment_20260317",
    source="guland.vn",
    location=Location(...),
    property_type=PropertyType.RESIDENTIAL_APARTMENT,
    
    # Pricing
    price_range=PriceRange(3e9, 8e9),  # Min, Max
    price_per_m2=PricePerM2(30e6, 80e6),  # VND/m²
    
    # Metadata
    date_recorded=datetime.now(),
    sample_size=150,
    confidence_score=0.85,
    price_trend="up",
    trend_percentage=5.2,
)
```

## Usage Examples

### Example 1: Scrape and Export

```python
from price_guides import PriceGuideScraper

scraper = PriceGuideScraper()
database = scraper.scrape_all()

# Export to CSV
database.to_csv("bang_gia_dat.csv")

# Export to JSON
database.to_json("bang_gia_dat.json")

print(f"Scraped {len(database.entries)} entries")
```

### Example 2: Analyze Market

```python
from price_guides import PriceGuideAnalyzer, Location

analyzer = PriceGuideAnalyzer(database)

# Get market report
location = Location(province="Hà Nội", district="Hoàn Kiếm")
report = analyzer.get_market_report(location)

print(f"Average apartment price: {report['property_types']['apartment']['avg_price']:,.0f} VND")
print(f"Price range: {report['property_types']['apartment']['min_price']:,.0f} - {report['property_types']['apartment']['max_price']:,.0f}")
```

### Example 3: Extract ML Features

```python
from price_guides import PriceGuideMLPipeline, Location, PropertyType

pipeline = PriceGuideMLPipeline(database)

listing = {
    'location': Location(province='Hà Nội', district='Hoàn Kiếm'),
    'property_type': PropertyType.RESIDENTIAL_APARTMENT,
    'price': 5e9,
    'size_sqm': 100,
}

features = pipeline.feature_extractor.extract_features(listing)

print("Extracted Features:")
for name, value in features.items():
    print(f"  {name}: {value}")
```

### Example 4: Calculate Price Deviation

```python
from price_guides import PriceGuideAnalyzer, Location, PropertyType

analyzer = PriceGuideAnalyzer(database)

location = Location(province="Hà Nội", district="Hoàn Kiếm")
deviation = analyzer.calculate_price_deviation(
    location=location,
    property_type=PropertyType.RESIDENTIAL_APARTMENT,
    listing_price=5.5e9,  # 5.5 billion VND
)

print(f"Guide price: {deviation['guide_price']:,.0f} VND")
print(f"Deviation: {deviation['deviation_percent']:.1f}%")
print(f"Overpriced: {deviation['is_overpriced']}")
```

### Example 5: Monitor Data Quality

```python
from price_guides import PriceGuideQualityAssessor

quality_report = PriceGuideQualityAssessor.assess_database(database)

print(f"Total entries: {quality_report['total_entries']}")
print(f"Average quality: {quality_report['average_quality_score']:.1f}/100")
print(f"Quality rating: {quality_report['quality_rating']}")
print(f"Issues: {quality_report['total_issues']}")
```

## Integration with EstatePredictor

### Step 1: Prepare Data

```python
from price_guides import PriceGuideScraper, PriceGuideMLPipeline
import pandas as pd

# Scrape and prepare
scraper = PriceGuideScraper()
database = scraper.scrape_all()
pipeline = PriceGuideMLPipeline(database)
```

### Step 2: Extract Features

```python
# Load your listings
listings = pd.read_csv('listings.csv').to_dict('records')

# Extract features
price_guide_features = pipeline.prepare_features(listings)
features_df = pd.DataFrame(price_guide_features)
```

### Step 3: Combine with Existing Features

```python
# Load existing features
existing_features = pd.read_csv('existing_features.csv')

# Combine
X = pd.concat([existing_features, features_df], axis=1)
y = pd.read_csv('target.csv')

# Train model
model.fit(X, y)
```

## Performance Tips

1. **Cache Results**: Store database in memory for repeated queries
2. **Use Indices**: Leverage built-in location/source indices
3. **Batch Processing**: Extract features in batches for large datasets
4. **Update Schedule**: Refresh price guides weekly/monthly

## Troubleshooting

### No Data Found

```python
# Check location format
from price_guides import LocationMatcher

normalized = LocationMatcher.normalize_location(your_location)
entries = database.find_by_location(normalized)
```

### Low Quality Data

```python
# Filter by confidence
high_confidence = [e for e in database.entries.values() 
                   if e.confidence_score >= 0.8]
```

### Missing Price per m²

```python
# Estimate from price and size
if entry.price_per_m2 is None and listing_size > 0:
    estimated = entry.price_range.average_price / listing_size
```

## File Manifest

| File | Purpose |
|------|---------|
| `__init__.py` | Package initialization |
| `price_guide_schema.py` | Data structures (Location, PriceGuideEntry, etc.) |
| `price_guide_scraper.py` | Web scraping from multiple sources |
| `price_guide_analyzer.py` | Price analysis, trends, quality assessment |
| `ml_integration.py` | ML feature extraction and pipeline |
| `INTEGRATION_GUIDE.md` | Detailed integration documentation |
| `README.md` | This file |
| `TECHNICAL_GUIDE.md` | Implementation details |
| `example_bang_gia_dat.csv` | Sample extracted data |

## Dependencies

```
requests>=2.28.0          # HTTP requests
beautifulsoup4>=4.11.0    # HTML parsing
pandas>=1.3.0             # Data manipulation (optional)
numpy>=1.21.0             # Numerical operations (optional)
```

## License

Part of EstatePredictor project.

## Contributing

To add support for new price guide sources:

1. Create a new scraper class extending `BaseScraper`
2. Implement `scrape()` method
3. Add to `PriceGuideScraper.scrapers` list
4. Test with sample data

## References

- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - ML integration details
- [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - Implementation documentation
- [example_bang_gia_dat.csv](example_bang_gia_dat.csv) - Sample data

## Support

For issues:
1. Check data quality: `PriceGuideQualityAssessor.assess_database()`
2. Identify gaps: `analyzer.identify_market_gaps()`
3. Verify location format: Use `LocationMatcher.normalize_location()`

---

**Last Updated**: March 17, 2026
**Version**: 1.0.0
