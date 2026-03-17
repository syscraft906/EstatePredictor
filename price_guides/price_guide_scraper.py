"""
Bang Gia Dat Scraper

Extracts price guide data from Vietnamese real estate websites:
- guland.vn/bang-gia-dat
- batdongsan.com.vn
- meeyland.com
- onehousing.vn

This module provides:
1. Source-specific scrapers for each website
2. Common parsing utilities for price normalization
3. Error handling and data validation
4. Rate limiting and respectful scraping
"""

import re
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import time

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import requests
except ImportError:
    requests = None

from price_guide_schema import (
    PriceGuideEntry, Location, PriceRange, PricePerM2,
    PropertyType, LocationLevel, PriceGuideDatabase
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuration for web scrapers"""
    timeout: int = 10
    max_retries: int = 3
    retry_delay: float = 2.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    rate_limit_delay: float = 1.0  # Seconds between requests


class PriceNormalizer:
    """Normalize and convert price data across sources"""
    
    # Vietnamese number format patterns
    PRICE_PATTERNS = [
        (r'(\d+(?:[.,]\d+)?)\s*tỷ', 'billion'),  # tỷ (billion)
        (r'(\d+(?:[.,]\d+)?)\s*triệu', 'million'),  # triệu (million)
        (r'(\d+(?:[.,]\d+)?)\s*nghìn', 'thousand'),  # nghìn (thousand)
        (r'(\d+(?:[.,]\d+)?)\s*đ', 'vnd'),  # đ or VND
        (r'(\d+(?:[.,]\d+)?)', 'number'),  # plain number
    ]
    
    @staticmethod
    def clean_number(text: str) -> float:
        """Clean and parse Vietnamese number format"""
        text = text.strip().lower()
        
        # Remove common currency symbols and text
        text = re.sub(r'[vnd$€₫]', '', text)
        text = re.sub(r'\s+', '', text)
        
        # Try each pattern
        for pattern, unit in PriceNormalizer.PRICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1).replace(',', '.')
                num = float(num_str)
                
                if unit == 'billion':
                    return num * 1e9
                elif unit == 'million':
                    return num * 1e6
                elif unit == 'thousand':
                    return num * 1e3
                elif unit == 'vnd':
                    return num
                else:
                    return num
        
        raise ValueError(f"Could not parse price: {text}")
    
    @staticmethod
    def parse_price_range(min_text: str, max_text: str) -> PriceRange:
        """Parse price range from text"""
        min_price = PriceNormalizer.clean_number(min_text)
        max_price = PriceNormalizer.clean_number(max_text)
        return PriceRange(min_price=min_price, max_price=max_price)
    
    @staticmethod
    def parse_price_per_m2(min_text: str, max_text: str) -> PricePerM2:
        """Parse price per m² from text"""
        min_price = PriceNormalizer.clean_number(min_text)
        max_price = PriceNormalizer.clean_number(max_text)
        return PricePerM2(min_price_per_m2=min_price, max_price_per_m2=max_price)


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, config: ScraperConfig = None):
        self.config = config or ScraperConfig()
        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': self.config.user_agent})
    
    @abstractmethod
    def source_name(self) -> str:
        """Get source name"""
        pass
    
    @abstractmethod
    def scrape(self) -> List[PriceGuideEntry]:
        """Main scraping method"""
        pass
    
    def fetch_page(self, url: str, retries: int = 0) -> Optional[str]:
        """Fetch a web page with retry logic"""
        if not self.session:
            logger.error("requests library not available")
            return None
        
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            time.sleep(self.config.rate_limit_delay)
            return response.text
        except Exception as e:
            if retries < self.config.max_retries:
                logger.warning(f"Failed to fetch {url}, retrying... ({retries + 1}/{self.config.max_retries})")
                time.sleep(self.config.retry_delay)
                return self.fetch_page(url, retries + 1)
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """Parse HTML content"""
        if not BeautifulSoup:
            logger.error("BeautifulSoup not available")
            return None
        return BeautifulSoup(html, 'html.parser')


class GulandScraper(BaseScraper):
    """Scraper for guland.vn/bang-gia-dat"""
    
    def source_name(self) -> str:
        return "guland.vn"
    
    def scrape(self) -> List[PriceGuideEntry]:
        """Scrape bang gia dat from guland.vn
        
        Expected structure (based on typical Vietnamese real estate sites):
        - Table/cards organized by location (province > district)
        - Columns: Location, Property Type, Min Price, Max Price, Price/m²
        - Date last updated
        """
        entries = []
        url = "https://guland.vn/bang-gia-dat"
        
        html = self.fetch_page(url)
        if not html:
            return entries
        
        soup = self.parse_html(html)
        if not soup:
            return entries
        
        try:
            # Look for price guide tables - structure varies by site
            # This is a template based on common Vietnamese real estate patterns
            tables = soup.find_all(['table', 'div'], class_=re.compile(r'(price|bang|gia|dat)', re.I))
            
            for table in tables:
                rows = table.find_all(['tr', 'div'], class_=re.compile(r'(row|item)', re.I))
                
                for row in rows:
                    try:
                        entry = self._parse_row(row)
                        if entry:
                            entries.append(entry)
                    except Exception as e:
                        logger.debug(f"Error parsing row: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error scraping guland.vn: {e}")
        
        return entries
    
    def _parse_row(self, row) -> Optional[PriceGuideEntry]:
        """Parse a single price guide row"""
        # This is a template - actual structure needs inspection
        cells = row.find_all(['td', 'div', 'span'])
        if len(cells) < 5:
            return None
        
        # Extract location
        location_text = cells[0].get_text(strip=True)
        location = self._parse_location(location_text)
        
        # Extract property type
        prop_type_text = cells[1].get_text(strip=True)
        property_type = self._parse_property_type(prop_type_text)
        
        # Extract prices
        min_price_text = cells[2].get_text(strip=True)
        max_price_text = cells[3].get_text(strip=True)
        
        try:
            price_range = PriceNormalizer.parse_price_range(min_price_text, max_price_text)
        except ValueError:
            return None
        
        # Create entry
        entry = PriceGuideEntry(
            id=f"guland_{location.province}_{location.district or 'all'}_{property_type.value}_{datetime.now().strftime('%Y%m%d')}",
            source=self.source_name(),
            location=location,
            property_type=property_type,
            price_range=price_range,
            source_url="https://guland.vn/bang-gia-dat",
        )
        
        return entry
    
    @staticmethod
    def _parse_location(text: str) -> Location:
        """Parse location from text"""
        # Split by common delimiters
        parts = [p.strip() for p in re.split(r'[,-]', text)]
        
        province = parts[0] if len(parts) > 0 else "Unknown"
        district = parts[1] if len(parts) > 1 else None
        ward = parts[2] if len(parts) > 2 else None
        
        return Location(province=province, district=district, ward=ward)
    
    @staticmethod
    def _parse_property_type(text: str) -> PropertyType:
        """Detect property type from text"""
        text = text.lower()
        
        if 'căn hộ' in text or 'apartment' in text:
            return PropertyType.RESIDENTIAL_APARTMENT
        elif 'nhà riêng' in text or 'house' in text:
            return PropertyType.RESIDENTIAL_HOUSE
        elif 'đất' in text or 'land' in text:
            return PropertyType.RESIDENTIAL_LAND
        elif 'office' in text or 'văn phòng' in text:
            return PropertyType.COMMERCIAL_OFFICE
        elif 'bán lẻ' in text or 'retail' in text:
            return PropertyType.COMMERCIAL_RETAIL
        else:
            return PropertyType.RESIDENTIAL_HOUSE


class BatdongSanScraper(BaseScraper):
    """Scraper for batdongsan.com.vn"""
    
    def source_name(self) -> str:
        return "batdongsan.com.vn"
    
    def scrape(self) -> List[PriceGuideEntry]:
        """Scrape price guides from batdongsan.com.vn"""
        entries = []
        # batdongsan.com.vn typically has price info embedded in listing pages
        # Would need to aggregate from multiple listing searches by location
        
        # Example locations to scrape
        locations = [
            ("Ha Noi", "Hoang Kiem"),
            ("Ha Noi", "Ba Dinh"),
            ("Ho Chi Minh", "District 1"),
            ("Ho Chi Minh", "District 3"),
        ]
        
        for province, district in locations:
            try:
                entries.extend(self._scrape_location(province, district))
            except Exception as e:
                logger.error(f"Error scraping {province}/{district}: {e}")
        
        return entries
    
    def _scrape_location(self, province: str, district: str) -> List[PriceGuideEntry]:
        """Scrape a specific location on batdongsan"""
        # This would construct a search URL and aggregate price data from listings
        entries = []
        # Implementation depends on actual website structure
        return entries


class MeeylandScraper(BaseScraper):
    """Scraper for meeyland.com"""
    
    def source_name(self) -> str:
        return "meeyland.com"
    
    def scrape(self) -> List[PriceGuideEntry]:
        """Scrape price guides from meeyland.com"""
        entries = []
        url = "https://meeyland.com/gia-dat"  # Estimated URL
        
        html = self.fetch_page(url)
        if not html:
            return entries
        
        # Parse and extract price guide data
        soup = self.parse_html(html)
        if not soup:
            return entries
        
        # Implementation based on actual website structure
        return entries


class OneHousingScraper(BaseScraper):
    """Scraper for onehousing.vn"""
    
    def source_name(self) -> str:
        return "onehousing.vn"
    
    def scrape(self) -> List[PriceGuideEntry]:
        """Scrape price guides from onehousing.vn"""
        entries = []
        url = "https://onehousing.vn/thong-tin-thi-truong"  # Estimated URL
        
        html = self.fetch_page(url)
        if not html:
            return entries
        
        soup = self.parse_html(html)
        if not soup:
            return entries
        
        # Implementation based on actual website structure
        return entries


class PriceGuideScraper:
    """Main scraper orchestrator for all sources"""
    
    def __init__(self, config: ScraperConfig = None):
        self.config = config or ScraperConfig()
        self.scrapers = [
            GulandScraper(config),
            BatdongSanScraper(config),
            MeeylandScraper(config),
            OneHousingScraper(config),
        ]
        self.database = PriceGuideDatabase()
    
    def scrape_all(self) -> PriceGuideDatabase:
        """Scrape all sources and return populated database"""
        for scraper in self.scrapers:
            logger.info(f"Scraping {scraper.source_name()}...")
            try:
                entries = scraper.scrape()
                for entry in entries:
                    self.database.add_entry(entry)
                logger.info(f"Successfully scraped {len(entries)} entries from {scraper.source_name()}")
            except Exception as e:
                logger.error(f"Error scraping {scraper.source_name()}: {e}")
        
        return self.database
    
    def scrape_source(self, source_name: str) -> PriceGuideDatabase:
        """Scrape a specific source"""
        for scraper in self.scrapers:
            if scraper.source_name().lower() == source_name.lower():
                logger.info(f"Scraping {source_name}...")
                entries = scraper.scrape()
                for entry in entries:
                    self.database.add_entry(entry)
                return self.database
        
        logger.error(f"Scraper for {source_name} not found")
        return self.database


if __name__ == "__main__":
    # Example usage
    scraper = PriceGuideScraper()
    database = scraper.scrape_all()
    
    # Export results
    database.to_csv("/tmp/bang_gia_dat.csv")
    database.to_json("/tmp/bang_gia_dat.json")
    
    logger.info(f"Scraped {len(database.entries)} total entries")
