"""
Main Web Scraper for Vietnamese Real Estate
Handles multi-domain scraping with BeautifulSoup and Selenium support
"""

import logging
import requests
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from config import (
    PRIORITY_DOMAINS, SECONDARY_DOMAINS, USER_AGENTS, REQUEST_TIMEOUT,
    RETRY_ATTEMPTS, RETRY_DELAY, RATE_LIMIT_DELAY, AMENITY_KEYWORDS,
    LOG_LEVEL, LOG_DIR, LOG_FILE_NAME
)
from database import EstateDatabase

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/{LOG_FILE_NAME}'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, domain_config: Dict, database: EstateDatabase):
        """Initialize scraper with domain config"""
        self.domain_config = domain_config
        self.database = database
        self.domain_name = list(PRIORITY_DOMAINS.keys())[
            list([v.get('url') for v in PRIORITY_DOMAINS.values()]).index(domain_config['url'])
        ] if domain_config['url'] in [v.get('url') for v in PRIORITY_DOMAINS.values()] else 'unknown'
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        return session
    
    def _get_with_retry(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Get URL with retry logic"""
        for attempt in range(RETRY_ATTEMPTS):
            try:
                time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
                response = self.session.get(url, timeout=REQUEST_TIMEOUT, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS} failed for {url}: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Failed to fetch {url} after {RETRY_ATTEMPTS} attempts")
                    return None
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        response = self._get_with_retry(url)
        if response:
            return BeautifulSoup(response.content, 'html.parser')
        return None
    
    @abstractmethod
    def scrape_listings(self) -> List[Dict]:
        """Scrape listings from the domain"""
        pass
    
    @abstractmethod
    def parse_property(self, item: any) -> Optional[Dict]:
        """Parse a property item"""
        pass
    
    def extract_amenities(self, text: str) -> List[str]:
        """Extract amenities from text"""
        amenities = []
        if not text:
            return amenities
        
        text_lower = text.lower()
        for amenity, keywords in AMENITY_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                amenities.append(amenity)
        
        return amenities
    
    def parse_price(self, price_str: str) -> Optional[int]:
        """Parse price string to integer VND"""
        if not price_str:
            return None
        
        try:
            price_str = price_str.lower().strip()
            
            # Remove non-numeric characters except . and ,
            clean_price = ''.join(c for c in price_str if c.isdigit() or c in '.,')
            
            # Handle different separators
            if ',' in clean_price and '.' in clean_price:
                # Determine which is thousands and which is decimal
                if clean_price.rindex(',') > clean_price.rindex('.'):
                    clean_price = clean_price.replace('.', '').replace(',', '')
                else:
                    clean_price = clean_price.replace(',', '').replace('.', '')
            elif ',' in clean_price:
                clean_price = clean_price.replace(',', '')
            elif '.' in clean_price:
                clean_price = clean_price.replace('.', '')
            
            price = int(clean_price) if clean_price else None
            
            # If price is in billions/millions, it's likely VND
            return price if price and price < 100000000000 else None
        except Exception as e:
            logger.debug(f"Error parsing price '{price_str}': {e}")
            return None
    
    def parse_area(self, area_str: str) -> Optional[float]:
        """Parse area string to float in square meters"""
        if not area_str:
            return None
        
        try:
            area_str = area_str.lower().strip()
            # Extract numbers
            clean_area = ''.join(c for c in area_str if c.isdigit() or c in '.,')
            
            if ',' in clean_area and '.' in clean_area:
                if clean_area.rindex(',') > clean_area.rindex('.'):
                    clean_area = clean_area.replace('.', '').replace(',', '.')
                else:
                    clean_area = clean_area.replace(',', '')
            else:
                clean_area = clean_area.replace(',', '.')
            
            return float(clean_area) if clean_area else None
        except Exception as e:
            logger.debug(f"Error parsing area '{area_str}': {e}")
            return None


class OneHousingScraper(BaseScraper):
    """Scraper for onehousing.vn"""
    
    def scrape_listings(self) -> List[Dict]:
        """Scrape listings from OneHousing"""
        listings = []
        try:
            url = self.domain_config['search_url']
            soup = self.fetch_page(url)
            
            if not soup:
                return listings
            
            # Find property listing containers (adjust selector as needed)
            property_items = soup.find_all('div', class_='property-item')
            
            logger.info(f"Found {len(property_items)} properties on OneHousing")
            
            for item in property_items:
                prop = self.parse_property(item)
                if prop:
                    listings.append(prop)
            
            return listings
        except Exception as e:
            logger.error(f"Error scraping OneHousing: {e}")
            return listings
    
    def parse_property(self, item) -> Optional[Dict]:
        """Parse property from OneHousing listing item"""
        try:
            # Extract basic info
            title_elem = item.find('h2', class_='property-title')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # URL
            link_elem = item.find('a', class_='property-link')
            url = urljoin(self.domain_config['url'], link_elem['href']) if link_elem else None
            
            # Price
            price_elem = item.find('span', class_='property-price')
            price_str = price_elem.get_text(strip=True) if price_elem else None
            price = self.parse_price(price_str) if price_str else None
            
            # Location
            location_elem = item.find('span', class_='property-location')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Area
            area_elem = item.find('span', class_='property-area')
            area_str = area_elem.get_text(strip=True) if area_elem else None
            area = self.parse_area(area_str) if area_str else None
            
            # Description (for amenities)
            desc_elem = item.find('p', class_='property-description')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            return {
                'property_id': self._extract_id_from_url(url) if url else None,
                'source_domain': 'onehousing.vn',
                'source_url': url,
                'title': title,
                'description': description,
                'price_vnd': price,
                'price_original': price_str,
                'location_address': location,
                'area_sqm': area,
                'amenities': self.extract_amenities(description or ''),
                'listing_date': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"Error parsing OneHousing property: {e}")
            return None
    
    @staticmethod
    def _extract_id_from_url(url: str) -> Optional[str]:
        """Extract property ID from URL"""
        try:
            # Extract ID from URL path (adjust based on actual URL structure)
            parts = urlparse(url).path.split('/')
            return parts[-1] if parts else None
        except:
            return None


class GulandScraper(BaseScraper):
    """Scraper for guland.vn"""
    
    def scrape_listings(self) -> List[Dict]:
        """Scrape listings from Guland"""
        listings = []
        try:
            url = self.domain_config['search_url']
            soup = self.fetch_page(url)
            
            if not soup:
                return listings
            
            # Find property containers (adjust selector)
            property_items = soup.find_all('div', class_='product-item')
            
            logger.info(f"Found {len(property_items)} properties on Guland")
            
            for item in property_items:
                prop = self.parse_property(item)
                if prop:
                    listings.append(prop)
            
            return listings
        except Exception as e:
            logger.error(f"Error scraping Guland: {e}")
            return listings
    
    def parse_property(self, item) -> Optional[Dict]:
        """Parse property from Guland listing"""
        try:
            # Title
            title_elem = item.find('h3', class_='product-title')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # URL
            link_elem = item.find('a', class_='product-link')
            url = urljoin(self.domain_config['url'], link_elem['href']) if link_elem else None
            
            # Price
            price_elem = item.find('span', class_='product-price')
            price_str = price_elem.get_text(strip=True) if price_elem else None
            price = self.parse_price(price_str) if price_str else None
            
            # Location
            location_elem = item.find('span', class_='product-location')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Area
            area_elem = item.find('span', class_='product-area')
            area_str = area_elem.get_text(strip=True) if area_elem else None
            area = self.parse_area(area_str) if area_str else None
            
            # Description
            desc_elem = item.find('p', class_='product-description')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            return {
                'property_id': self._extract_id_from_url(url) if url else None,
                'source_domain': 'guland.vn',
                'source_url': url,
                'title': title,
                'description': description,
                'price_vnd': price,
                'price_original': price_str,
                'location_address': location,
                'area_sqm': area,
                'amenities': self.extract_amenities(description or ''),
                'listing_date': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"Error parsing Guland property: {e}")
            return None
    
    @staticmethod
    def _extract_id_from_url(url: str) -> Optional[str]:
        """Extract property ID from URL"""
        try:
            parts = urlparse(url).path.split('/')
            return parts[-1] if parts else None
        except:
            return None


class BatDongSanScraper(BaseScraper):
    """Scraper for batdongsan.com.vn"""
    
    def scrape_listings(self) -> List[Dict]:
        """Scrape listings from BatDongSan"""
        listings = []
        try:
            url = self.domain_config['search_url']
            soup = self.fetch_page(url)
            
            if not soup:
                return listings
            
            # BatDongSan uses different selectors
            property_items = soup.find_all('div', class_=['item-info', 'js-listing-item'])
            
            if not property_items:
                property_items = soup.find_all('div', {'data-id': True})
            
            logger.info(f"Found {len(property_items)} properties on BatDongSan")
            
            for item in property_items:
                prop = self.parse_property(item)
                if prop:
                    listings.append(prop)
            
            return listings
        except Exception as e:
            logger.error(f"Error scraping BatDongSan: {e}")
            return listings
    
    def parse_property(self, item) -> Optional[Dict]:
        """Parse property from BatDongSan"""
        try:
            # Title
            title_elem = item.find('h2', class_='item-title')
            if not title_elem:
                title_elem = item.find('a')
            
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # URL
            url = title_elem.get('href') if title_elem and title_elem.name == 'a' else None
            if url:
                url = urljoin(self.domain_config['url'], url)
            
            # Price
            price_elem = item.find('span', class_='item-price')
            price_str = price_elem.get_text(strip=True) if price_elem else None
            price = self.parse_price(price_str) if price_str else None
            
            # Location
            location_elem = item.find('span', class_='item-location')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Area
            area_elem = item.find('span', class_='item-area')
            area_str = area_elem.get_text(strip=True) if area_elem else None
            area = self.parse_area(area_str) if area_str else None
            
            # Description
            desc_elem = item.find('div', class_='item-description')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            return {
                'property_id': item.get('data-id') or (self._extract_id_from_url(url) if url else None),
                'source_domain': 'batdongsan.com.vn',
                'source_url': url,
                'title': title,
                'description': description,
                'price_vnd': price,
                'price_original': price_str,
                'location_address': location,
                'area_sqm': area,
                'amenities': self.extract_amenities(description or ''),
                'listing_date': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"Error parsing BatDongSan property: {e}")
            return None
    
    @staticmethod
    def _extract_id_from_url(url: str) -> Optional[str]:
        """Extract property ID from URL"""
        try:
            parts = urlparse(url).path.split('-')
            # BatDongSan uses ID at the end
            return parts[-1].split('/')[0] if parts else None
        except:
            return None


class ScraperFactory:
    """Factory to create appropriate scraper for domain"""
    
    SCRAPER_MAP = {
        'onehousing': OneHousingScraper,
        'guland': GulandScraper,
        'batdongsan': BatDongSanScraper,
        # Add more scrapers here as implemented
    }
    
    @classmethod
    def create_scraper(cls, domain_key: str, domain_config: Dict, database: EstateDatabase) -> Optional[BaseScraper]:
        """Create scraper instance for domain"""
        scraper_class = cls.SCRAPER_MAP.get(domain_key)
        
        if scraper_class:
            return scraper_class(domain_config, database)
        else:
            logger.warning(f"No scraper implementation for {domain_key}")
            return None


class MultiDomainScraper:
    """Orchestrates scraping across multiple domains"""
    
    def __init__(self):
        """Initialize multi-domain scraper"""
        self.database = EstateDatabase()
    
    def scrape_all(self, domains: Dict = None) -> Dict:
        """Scrape all enabled domains"""
        if domains is None:
            domains = PRIORITY_DOMAINS
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'domains': {},
            'total_records': 0,
            'total_added': 0,
        }
        
        for domain_key, domain_config in domains.items():
            if not domain_config.get('enabled', True):
                logger.info(f"Skipping disabled domain: {domain_key}")
                continue
            
            logger.info(f"Starting scrape for {domain_key}")
            start_time = time.time()
            
            try:
                scraper = ScraperFactory.create_scraper(domain_key, domain_config, self.database)
                
                if not scraper:
                    logger.warning(f"Could not create scraper for {domain_key}")
                    continue
                
                # Scrape listings
                listings = scraper.scrape_listings()
                
                # Insert to database
                total, added, duplicates = self.database.insert_multiple_properties(listings)
                
                duration = time.time() - start_time
                
                # Log results
                self.database.log_crawl(
                    domain=domain_key,
                    status='success' if added > 0 else 'no_data',
                    records_crawled=total,
                    records_added=added,
                    errors=duplicates,
                    duration_seconds=duration
                )
                
                results['domains'][domain_key] = {
                    'total': total,
                    'added': added,
                    'duplicates': duplicates,
                    'duration_seconds': duration,
                }
                
                results['total_records'] += total
                results['total_added'] += added
                
                logger.info(f"Completed {domain_key}: {added} added, {duplicates} duplicates in {duration:.2f}s")
            
            except Exception as e:
                logger.error(f"Error scraping {domain_key}: {e}", exc_info=True)
                self.database.log_crawl(
                    domain=domain_key,
                    status='error',
                    errors=1,
                    error_messages=str(e),
                    duration_seconds=time.time() - start_time
                )
        
        return results


if __name__ == '__main__':
    # Test scraper
    logging.info("Starting multi-domain scraper")
    scraper = MultiDomainScraper()
    
    # Scrape only first 3 priority domains for testing
    test_domains = {k: v for k, v in list(PRIORITY_DOMAINS.items())[:3]}
    results = scraper.scrape_all(test_domains)
    
    logger.info(f"Scraping completed: {results}")
    print(f"\nResults: {results}")
