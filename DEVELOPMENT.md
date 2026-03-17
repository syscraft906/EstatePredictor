# Development Guide - Estate Crawler

This guide is for developers who want to extend and improve the Estate Crawler.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Main Entry (main.py)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Scraper     │  │  Scheduler   │  │  Exporter    │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                  │                   │
│  ┌──────▼──────────────────▼──────────────────▼─────┐            │
│  │         Database (SQLite)                        │            │
│  │  - Properties Table                             │            │
│  │  - Crawl Logs Table                             │            │
│  │  - Duplicate Hashes Table                       │            │
│  └────────────────────────────────────────────────┘            │
│                                                                   │
│  External:                                                       │
│  ┌─────────────────────────────────────────────────┐            │
│  │  Vietnamese Real Estate Websites                │            │
│  │  (onehousing, guland, batdongsan, etc.)        │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure & Responsibilities

### Core Files

**config.py**
- Centralized configuration management
- Domain definitions with URL patterns
- Province/amenity definitions
- Database schema constants
- Add new domains by updating `PRIORITY_DOMAINS` dict

**database.py**
- SQLite ORM implementation
- CRUD operations for properties
- Duplicate detection using hashes
- Statistics and queries
- Extend with new query methods as needed

**scraper.py**
- Abstract `BaseScraper` class for all scrapers
- Domain-specific scraper implementations:
  - `OneHousingScraper`
  - `GulandScraper`
  - `BatDongSanScraper`
- `ScraperFactory` for creating scrapers
- `MultiDomainScraper` orchestrator
- Add new scrapers by extending `BaseScraper`

**scheduler.py**
- APScheduler integration
- Scheduled job management
- Automatic execution at intervals
- `CrawlerScheduler` main class

**data_export.py**
- Multi-format export (CSV, JSON, Parquet)
- ML dataset preparation
- Statistics export
- Extend with new export formats

**test_scraper.py**
- Unit tests for all components
- Test database operations
- Test scraper parsing
- Test export functionality

## Adding a New Scraper

### Step 1: Analyze Target Website

```python
# tools/analyze_site.py
import requests
from bs4 import BeautifulSoup

url = "https://newsite.vn/search"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find property containers
properties = soup.find_all('div', class_='property-item')
print(f"Found {len(properties)} properties")

# Analyze first property structure
if properties:
    print(properties[0].prettify()[:500])
```

### Step 2: Create Scraper Class

In `scraper.py`, add:

```python
class NewSiteScraper(BaseScraper):
    """Scraper for newsite.vn"""
    
    def scrape_listings(self) -> List[Dict]:
        """Scrape listings"""
        listings = []
        try:
            url = self.domain_config['search_url']
            soup = self.fetch_page(url)
            
            if not soup:
                return listings
            
            # Find properties (adjust selector based on site structure)
            property_items = soup.find_all('div', class_='property-card')
            
            logger.info(f"Found {len(property_items)} on NewSite")
            
            for item in property_items:
                prop = self.parse_property(item)
                if prop:
                    listings.append(prop)
            
            return listings
        except Exception as e:
            logger.error(f"Error scraping NewSite: {e}")
            return listings
    
    def parse_property(self, item) -> Optional[Dict]:
        """Parse property from listing item"""
        try:
            # Extract data using CSS selectors
            title = item.find('h2').text.strip() if item.find('h2') else None
            url = item.find('a')['href'] if item.find('a') else None
            price_str = item.find('span', class_='price').text if item.find('span', class_='price') else None
            
            return {
                'property_id': self._extract_id(url) if url else None,
                'source_domain': 'newsite.vn',
                'source_url': urljoin(self.domain_config['url'], url) if url else None,
                'title': title,
                'price_vnd': self.parse_price(price_str),
                'description': item.find('p', class_='desc').text if item.find('p', class_='desc') else None,
                # ... other fields
            }
        except Exception as e:
            logger.debug(f"Error parsing NewSite property: {e}")
            return None
    
    @staticmethod
    def _extract_id(url: str) -> Optional[str]:
        """Extract property ID from URL"""
        try:
            # Implement based on URL pattern
            return urlparse(url).path.split('/')[-1]
        except:
            return None
```

### Step 3: Register in Config

In `config.py`, add to `PRIORITY_DOMAINS`:

```python
'newsite': {
    'url': 'https://newsite.vn',
    'search_url': 'https://newsite.vn/can-ban',
    'priority': 12,
    'scraper_type': 'beautifulsoup',  # or 'selenium'
    'enabled': True,
}
```

### Step 4: Register in Factory

In `scraper.py`, update `ScraperFactory`:

```python
SCRAPER_MAP = {
    'onehousing': OneHousingScraper,
    'guland': GulandScraper,
    'batdongsan': BatDongSanScraper,
    'newsite': NewSiteScraper,  # Add here
}
```

### Step 5: Add Unit Test

In `test_scraper.py`, add:

```python
class TestNewSiteScraper(unittest.TestCase):
    """Tests for NewSite scraper"""
    
    def setUp(self):
        self.test_db = EstateDatabase(database_path=':memory:')
        self.domain_config = {
            'url': 'https://newsite.vn',
            'search_url': 'https://newsite.vn/can-ban',
        }
        self.scraper = NewSiteScraper(self.domain_config, self.test_db)
    
    def test_parse_property(self):
        # Test property parsing
        pass
    
    def test_scrape_listings(self):
        # Test listing scraping
        pass
```

### Step 6: Test

```bash
python test_scraper.py TestNewSiteScraper
```

## Handling JavaScript-Heavy Sites

For sites requiring JavaScript rendering (like BatDongSan), use Selenium:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

class JSScraper(BaseScraper):
    
    def __init__(self, domain_config, database):
        super().__init__(domain_config, database)
        self.driver = webdriver.Chrome()  # Configure as needed
    
    def scrape_listings(self):
        try:
            self.driver.get(self.domain_config['search_url'])
            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements(By.CLASS_NAME, "property-item")
            )
            
            items = self.driver.find_elements(By.CLASS_NAME, "property-item")
            
            listings = []
            for item in items:
                prop = self.parse_property(item)
                if prop:
                    listings.append(prop)
            
            return listings
        finally:
            self.driver.quit()
```

## Database Queries

### Custom Queries

Add methods to `EstateDatabase`:

```python
def get_properties_by_price_range(self, min_price: int, max_price: int):
    """Get properties in price range"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT * FROM {TABLE_PROPERTIES}
            WHERE price_vnd BETWEEN ? AND ?
            ORDER BY price_vnd DESC
        ''', (min_price, max_price))
        return [dict(row) for row in cursor.fetchall()]

def get_price_per_sqm_stats(self, province: str):
    """Get price per sqm statistics"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT 
                AVG(price_vnd / area_sqm) as avg_price_per_sqm,
                MIN(price_vnd / area_sqm) as min_price_per_sqm,
                MAX(price_vnd / area_sqm) as max_price_per_sqm
            FROM {TABLE_PROPERTIES}
            WHERE province = ? AND price_vnd IS NOT NULL AND area_sqm IS NOT NULL
        ''', (province,))
        return cursor.fetchone()
```

## Adding Export Formats

Add new export format to `data_export.py`:

```python
def export_to_xml(self, filename: str = None) -> Optional[str]:
    """Export data to XML format"""
    try:
        if filename is None:
            filename = f"estate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        
        filepath = self.export_dir / filename
        
        properties = self.database.get_properties(limit=1000000)
        
        # Use xml.etree.ElementTree or similar
        import xml.etree.ElementTree as ET
        
        root = ET.Element('properties')
        root.attrib['count'] = str(len(properties))
        
        for prop in properties:
            prop_elem = ET.SubElement(root, 'property')
            # ... populate XML structure
        
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Exported to XML: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error exporting to XML: {e}")
        return None
```

## Performance Optimization

### Batch Processing

```python
def insert_batch(self, properties: List[Dict], batch_size: int = 1000):
    """Insert properties in batches for better performance"""
    for i in range(0, len(properties), batch_size):
        batch = properties[i:i+batch_size]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Batch insert logic
            conn.commit()
```

### Query Optimization

```python
# Add database indexes in init_database():
cursor.execute(f'''
    CREATE INDEX IF NOT EXISTS idx_price_province 
    ON {TABLE_PROPERTIES}(province, price_vnd)
''')
```

### Concurrent Scraping

```python
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

class ConcurrentScraper:
    def __init__(self, num_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.lock = Lock()
    
    def scrape_concurrent(self):
        futures = []
        for domain_key, domain_config in PRIORITY_DOMAINS.items():
            future = self.executor.submit(self.scrape_domain, domain_key, domain_config)
            futures.append(future)
        
        results = [f.result() for f in futures]
        return results
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect HTML

```python
# In scraper, save raw HTML for inspection
with open('debug_page.html', 'w') as f:
    f.write(soup.prettify())
```

### Database Inspection

```python
import sqlite3

conn = sqlite3.connect('data/estate_crawler.db')
cursor = conn.cursor()

# Inspect schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())

# Quick query
cursor.execute("SELECT COUNT(*) FROM properties")
print(cursor.fetchone())
```

## Code Style

Follow PEP 8:

```bash
# Format code
black *.py

# Check style
flake8 *.py

# Type checking
mypy scraper.py
```

## Testing Strategy

```bash
# Run specific test
pytest test_scraper.py::TestDatabase::test_insert_property -v

# Run with coverage
pytest --cov=. test_scraper.py

# Run integration tests only
pytest test_scraper.py::TestIntegration -v
```

## Deployment Checklist

- [ ] All tests pass: `python test_scraper.py`
- [ ] Code formatted: `black *.py`
- [ ] No style issues: `flake8 *.py`
- [ ] Environment file configured: `.env` present
- [ ] Database initialized: `python main.py init`
- [ ] Single scrape test: `python main.py scrape`
- [ ] Export test: `python main.py export --format all`
- [ ] Docker image builds: `docker build .`
- [ ] Documentation updated

## Common Issues & Solutions

### Website Returns 403 Forbidden
**Problem**: Server blocking requests
**Solution**:
1. Add delays in config
2. Rotate user agents
3. Use proxy service

### Selector Not Finding Elements
**Problem**: Website HTML structure changed
**Solution**:
1. Use browser dev tools to find new selectors
2. Update CSS/XPath selectors in scraper
3. Add fallback selectors

### Database Lock Errors
**Problem**: Multiple processes accessing DB simultaneously
**Solution**:
1. Use connection pooling
2. Implement queue-based processing
3. Use WAL mode: `conn.execute('PRAGMA journal_mode=WAL')`

### Memory Usage Growing
**Problem**: Objects not released
**Solution**:
1. Use generators instead of lists for large datasets
2. Clear cache periodically
3. Use `del` for large objects after use

---

For questions or issues, check the main README.md or create an issue in the repository.
