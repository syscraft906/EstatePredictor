# Technical Implementation Guide

Detailed technical documentation for the Bang Gia Dat price guide system.

## Table of Contents

1. [Architecture](#architecture)
2. [Data Flow](#data-flow)
3. [Implementation Details](#implementation-details)
4. [Web Scraping Strategy](#web-scraping-strategy)
5. [Data Normalization](#data-normalization)
6. [Feature Engineering](#feature-engineering)
7. [Performance Optimization](#performance-optimization)
8. [Error Handling](#error-handling)
9. [Testing](#testing)
10. [Deployment](#deployment)

## Architecture

### Component Overview

```
Web Sources
  │
  ├─► GulandScraper
  ├─► BatdongSanScraper
  ├─► MeeylandScraper
  └─► OneHousingScraper
         │
         ▼
    PriceNormalizer
         │
         ▼
    PriceGuideEntry
         │
         ▼
    PriceGuideDatabase
         │
         ▼
    PriceGuideAnalyzer ◄─► LocationMarketAnalysis
         │
         ▼
    PriceGuideQualityAssessor
         │
         ▼
    PriceGuideMLPipeline
         │
         ▼
    ML Features
```

### Design Patterns

#### 1. **Strategy Pattern** (Scrapers)
Each website has a different structure. Using strategy pattern allows:
- Pluggable scrapers for different sources
- Easy addition of new sources
- Source-specific parsing logic isolated

```python
class BaseScraper(ABC):
    @abstractmethod
    def source_name(self) -> str:
        pass
    
    @abstractmethod
    def scrape(self) -> List[PriceGuideEntry]:
        pass
```

#### 2. **Repository Pattern** (PriceGuideDatabase)
Centralized data access with:
- In-memory storage
- Multiple indices for fast queries
- Export to different formats

```python
class PriceGuideDatabase:
    def __init__(self):
        self.entries = {}  # Primary storage
        self.index_by_location = {}  # Query index
        self.index_by_source = {}  # Query index
```

#### 3. **Factory Pattern** (PriceGuideScraper)
Orchestrates all scrapers:
- Creates scraper instances
- Manages scraping workflow
- Aggregates results

```python
class PriceGuideScraper:
    def __init__(self):
        self.scrapers = [
            GulandScraper(),
            BatdongSanScraper(),
            # ...
        ]
```

## Data Flow

### Scraping Flow

```
1. URL Request
   └─► Fetch HTML (with retries)
       └─► Parse HTML (BeautifulSoup)
           └─► Extract Price Data
               └─► Normalize Prices (PriceNormalizer)
                   └─► Create PriceGuideEntry
                       └─► Add to Database
```

### Analysis Flow

```
1. Load Database
   └─► Group by Location + PropertyType
       └─► Calculate Statistics
           ├─► Price stats (min/max/mean/median/std)
           ├─► Trend detection
           └─► Confidence calculation
               └─► LocationMarketAnalysis
                   └─► Quality Assessment
```

### Feature Extraction Flow

```
1. Load Listing Data
   └─► Normalize Location
       └─► Find Nearest Price Guide
           ├─► Extract Price Features
           ├─► Extract Trend Features
           ├─► Extract Confidence Features
           └─► Extract Location Features
               └─► ML Feature Vector
```

## Implementation Details

### Location Matching Algorithm

Vietnamese location naming is complex:
- Multiple alias formats (Hà Nội vs Ha Noi vs Hanoi)
- District codes (Quận 1 vs District 1)
- Ward variations

**Solution**: Hierarchical fuzzy matching

```python
def calculate_location_distance(loc1: Location, loc2: Location) -> int:
    # Returns: 0 (same street) to 999 (different province)
    # Used to find best matching price guide
    
    # Distance levels:
    # 0: Same street (most specific)
    # 1: Same ward
    # 2: Same district
    # 3: Same province (least specific)
    # 999: Different province (no match)
```

### Price Normalization

Vietnamese price formats vary across sources:

```
"3 tỷ"              → 3,000,000,000 VND (billion)
"3,000 triệu"       → 3,000,000,000 VND (million)
"3000 triệu"        → 3,000,000,000 VND (no comma)
"3 tỷ 5 triệu"      → 3,500,000,000 VND (combined)
"55 triệu/m²"       → 55,000,000 VND/m²
```

**Solution**: Regex pattern matching with unit conversion

```python
class PriceNormalizer:
    PRICE_PATTERNS = [
        (r'(\d+(?:[.,]\d+)?)\s*tỷ', 'billion'),
        (r'(\d+(?:[.,]\d+)?)\s*triệu', 'million'),
        (r'(\d+(?:[.,]\d+)?)\s*nghìn', 'thousand'),
    ]
    
    @staticmethod
    def clean_number(text: str) -> float:
        # Remove symbols, parse magnitude, convert to VND
        pass
```

### Confidence Scoring

Confidence reflects data reliability:

```python
confidence = (
    (source_diversity / 3.0) * 0.4 +  # Multiple sources good
    (data_quantity / 10.0) * 0.3 +     # More data points good
    (sample_size / 100.0) * 0.3        # Larger sample good
) * 0.9 + 0.1  # Min confidence 10%
```

## Web Scraping Strategy

### Rate Limiting

Respectful scraping requires rate limits:

```python
class ScraperConfig:
    rate_limit_delay: float = 1.0  # 1 second between requests
    timeout: int = 10  # 10 second request timeout
    max_retries: int = 3  # 3 retry attempts
    retry_delay: float = 2.0  # 2 seconds between retries
```

### Error Handling

```python
def fetch_page(self, url: str, retries: int = 0) -> Optional[str]:
    try:
        response = self.session.get(url, timeout=self.config.timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        if retries < self.config.max_retries:
            time.sleep(self.config.retry_delay)
            return self.fetch_page(url, retries + 1)
        logger.error(f"Failed to fetch {url}: {e}")
        return None
```

### Cloudflare Protection

Many Vietnamese real estate sites use Cloudflare. Solutions:

1. **User-Agent Rotation**
   ```python
   headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
   }
   ```

2. **Session Persistence**
   ```python
   self.session = requests.Session()
   # Maintains cookies and connection pool
   ```

3. **Headless Browser** (if needed)
   ```python
   # Use Selenium/Playwright for JavaScript-rendered content
   # Slower but handles Cloudflare/JavaScript
   ```

## Data Normalization

### Price Range Normalization

Outlier detection and removal:

```python
def normalize_prices(entries: List[PriceGuideEntry]) -> List[PriceGuideEntry]:
    # Calculate median price for location/type
    median_prices = {}
    for entry in entries:
        key = f"{entry.location}_{entry.property_type}"
        prices = [e.price_range.average_price for e in entries if key == ...]
        median_prices[key] = median(prices)
    
    # Flag outliers (±50% from median)
    for entry in entries:
        key = ...
        if entry.price_range.average_price < median_prices[key] * 0.5:
            entry.notes = "[OUTLIER_DETECTED]"
```

### Location Normalization

Standardize location names:

```python
PROVINCE_ALIASES = {
    'hà nội': 'Hà Nội',
    'hanoi': 'Hà Nội',
    'ho chi minh': 'TP. Hồ Chí Minh',
    'sài gòn': 'TP. Hồ Chí Minh',
}

normalized = Location(
    province=PROVINCE_ALIASES.get(raw_province.lower(), raw_province),
    district=district,
    ward=ward,
)
```

## Feature Engineering

### Feature Categories

#### 1. Price Deviation Features

```python
# Absolute deviation
deviation = ((listing_price - guide_price) / guide_price) * 100

# Normalized to [-1, 1] range
normalized_deviation = deviation / 100

# Binary flags
is_overpriced = 1.0 if deviation > 10 else 0.0
is_underpriced = 1.0 if deviation < -10 else 0.0
```

#### 2. Trend Features

```python
# Direction
trend_signal = 1.0 if trend == 'up' else -1.0 if trend == 'down' else 0.0

# Strength (normalized)
trend_strength = min(abs(change_percent) / 20, 1.0)

# Velocity (rate of change)
days_old = (now - date_recorded).days
velocity = trend_strength / max(days_old / 30, 1)  # Per month
```

#### 3. Confidence Features

```python
# Source diversity (0 to 3 sources)
source_diversity = min(num_sources / 3, 1.0)

# Data freshness (90 day decay)
days_old = (now - latest_date).days
freshness = max(1.0 - (days_old / 90), 0.0)

# Data quantity (target 10 entries)
quantity = min(num_entries / 10, 1.0)

# Combined confidence
confidence = (diversity * 0.33 + freshness * 0.33 + quantity * 0.34)
```

## Performance Optimization

### Indexing Strategy

```python
class PriceGuideDatabase:
    def __init__(self):
        # Primary: O(1) lookup
        self.entries = {}  # id -> entry
        
        # Secondary indices: O(1) list access
        self.index_by_location = {}  # location_string -> [entry_ids]
        self.index_by_source = {}  # source -> [entry_ids]
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_location_analysis(location_key: str):
    # Expensive computation
    # Result cached for repeated calls
    pass
```

### Batch Processing

```python
# Instead of:
for listing in listings:
    features = extract_features(listing)  # Slow

# Do this:
features_list = pipeline.prepare_features(listings)  # Fast
```

### Memory Management

```python
# For large datasets, use generators
def entries_by_location(location):
    for entry_id in self.index_by_location[location]:
        yield self.entries[entry_id]  # Lazy evaluation
```

## Error Handling

### Validation

```python
@dataclass
class PriceGuideEntry:
    def __post_init__(self):
        # Validate data
        if self.price_range:
            assert self.price_range.min_price <= self.price_range.max_price
            self.price_range.calculate_average()
        
        if self.price_per_m2:
            assert self.price_per_m2.min_price_per_m2 <= self.price_per_m2.max_price_per_m2
            self.price_per_m2.calculate_average()
```

### Graceful Degradation

```python
def extract_features(listing: Dict) -> Dict[str, float]:
    try:
        # Try to get price guide
        price_guide = find_nearest_guide(listing)
        if price_guide:
            return extract_with_guide(listing, price_guide)
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Return neutral features if error
    return get_null_features()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Parsing row from table")
logger.info("Successfully scraped 150 entries from guland.vn")
logger.warning("Price data not found, using default")
logger.error("Failed to connect to website: connection timeout")
```

## Testing

### Unit Tests

```python
def test_price_normalization():
    assert PriceNormalizer.clean_number("3 tỷ") == 3e9
    assert PriceNormalizer.clean_number("55 triệu/m²") == 55e6
    assert PriceNormalizer.clean_number("1,500 nghìn") == 1.5e6

def test_location_matching():
    loc1 = Location(province="Hà Nội", district="Q1")
    loc2 = Location(province="Hà Nội", district="Q1")
    assert calculate_location_distance(loc1, loc2) == 2  # Same district

def test_confidence_calculation():
    entry = PriceGuideEntry(..., confidence_score=0.85)
    assert 0 <= entry.confidence_score <= 1
```

### Integration Tests

```python
def test_scrape_and_store():
    scraper = PriceGuideScraper()
    database = scraper.scrape_source("guland.vn")
    assert len(database.entries) > 0
    
    # Test retrieval
    entries = database.find_by_source("guland.vn")
    assert all(e.source == "guland.vn" for e in entries)

def test_ml_pipeline():
    pipeline = PriceGuideMLPipeline(database)
    listing = {
        'location': Location(...),
        'property_type': PropertyType.RESIDENTIAL_APARTMENT,
        'price': 5e9,
    }
    features = pipeline.feature_extractor.extract_features(listing)
    assert len(features) == 14  # Expected number of features
    assert all(isinstance(v, (int, float)) for v in features.values())
```

## Deployment

### Production Setup

```python
# config.py
SCRAPER_CONFIG = ScraperConfig(
    timeout=15,
    max_retries=5,
    rate_limit_delay=2.0,  # More respectful
)

UPDATE_SCHEDULE = {
    'guland.vn': 'weekly',
    'batdongsan.com.vn': 'daily',
    'meeyland.com': 'weekly',
    'onehousing.vn': 'monthly',
}

STORAGE = {
    'format': 'json',
    'location': '/data/price_guides/',
    'compression': 'gzip',
}
```

### Scheduled Updates

```python
# Using APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=2)  # 2 AM daily
def update_price_guides():
    scraper = PriceGuideScraper()
    database = scraper.scrape_all()
    database.to_json('/data/price_guides/latest.json.gz')
    logger.info("Price guides updated")

scheduler.start()
```

### Monitoring

```python
def monitor_quality():
    assessment = PriceGuideQualityAssessor.assess_database(database)
    
    if assessment['average_quality_score'] < 70:
        logger.warning("Data quality below threshold")
        send_alert("Price guide quality degraded")
    
    if assessment['total_issues'] > 100:
        logger.warning("Too many data issues detected")
        send_alert("Price guide has many quality issues")
    
    return assessment
```

---

**Version**: 1.0.0
**Last Updated**: March 17, 2026
