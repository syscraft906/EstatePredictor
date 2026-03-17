"""
Configuration for Vietnam Real Estate Web Crawler
Contains domain settings, provinces, and scraper parameters
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===========================
# SCRAPER SETTINGS
# ===========================

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', '/root/clawd/EstatePredictor/data/estate_crawler.db')
LOG_DIR = os.getenv('LOG_DIR', '/root/clawd/EstatePredictor/logs')
DATA_DIR = os.getenv('DATA_DIR', '/root/clawd/EstatePredictor/data')

# Request settings
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', 3))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 5))
RATE_LIMIT_DELAY = int(os.getenv('RATE_LIMIT_DELAY', 2))

# Scheduler settings
SCHEDULER_ENABLED = os.getenv('SCHEDULER_ENABLED', 'True').lower() == 'true'
SCHEDULER_INTERVAL_HOURS = int(os.getenv('SCHEDULER_INTERVAL_HOURS', 48))

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE_NAME = 'estate_crawler.log'

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
]

# ===========================
# PRIORITY DOMAINS (1-11)
# ===========================

PRIORITY_DOMAINS = {
    'onehousing': {
        'url': 'https://onehousing.vn',
        'search_url': 'https://onehousing.vn/nha-tro-phong-tro',
        'priority': 1,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'guland': {
        'url': 'https://guland.vn',
        'search_url': 'https://guland.vn/nha-dat-ban',
        'priority': 2,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'batdongsan': {
        'url': 'https://batdongsan.com.vn',
        'search_url': 'https://batdongsan.com.vn/nha-cho-thue',
        'priority': 3,
        'scraper_type': 'selenium',  # JavaScript-heavy
        'enabled': True,
    },
    'chotot': {
        'url': 'https://nha.chotot.com',
        'search_url': 'https://nha.chotot.com/ho-chi-minh/mua-ban-nha-dat',
        'priority': 4,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'meeyland': {
        'url': 'https://meeyland.com',
        'search_url': 'https://meeyland.com/nha-dat',
        'priority': 5,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'ihouzz': {
        'url': 'https://ihouzz.com',
        'search_url': 'https://ihouzz.com/vi/ban-nha-dat',
        'priority': 6,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'nhadat888': {
        'url': 'https://nhadat888.vn',
        'search_url': 'https://nhadat888.vn/tin-nha-dat',
        'priority': 7,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'cenhomes': {
        'url': 'https://cenhomes.vn',
        'search_url': 'https://cenhomes.vn/nha-dat',
        'priority': 8,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'kiembatdongsan': {
        'url': 'https://kiembatdongsannhanh.com',
        'search_url': 'https://kiembatdongsannhanh.com/tim-mua-nha-dat',
        'priority': 9,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'alonhadat': {
        'url': 'https://alonhadat.com.vn',
        'search_url': 'https://alonhadat.com.vn/bat-dong-san',
        'priority': 10,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
    'hoozing': {
        'url': 'https://hoozing.com',
        'search_url': 'https://hoozing.com/nha-dat',
        'priority': 11,
        'scraper_type': 'beautifulsoup',
        'enabled': True,
    },
}

# Additional secondary domains for expansion
SECONDARY_DOMAINS = {
    'phongtro123': {
        'url': 'https://phongtro123.com',
        'search_url': 'https://phongtro123.com',
        'priority': 12,
        'scraper_type': 'beautifulsoup',
        'enabled': False,
    },
    'nhachot': {
        'url': 'https://nhachot.vn',
        'search_url': 'https://nhachot.vn',
        'priority': 13,
        'scraper_type': 'beautifulsoup',
        'enabled': False,
    },
    'muabannhadat': {
        'url': 'https://muabannhadat.vn',
        'search_url': 'https://muabannhadat.vn',
        'priority': 14,
        'scraper_type': 'beautifulsoup',
        'enabled': False,
    },
}

# ===========================
# VIETNAMESE PROVINCES (63)
# ===========================

VIETNAMESE_PROVINCES = {
    'AG': {'name': 'An Giang', 'region': 'Mekong Delta'},
    'BL': {'name': 'Bạc Liêu', 'region': 'Mekong Delta'},
    'BA': {'name': 'Bắc Kạn', 'region': 'North East'},
    'BG': {'name': 'Bắc Giang', 'region': 'North East'},
    'BN': {'name': 'Bắc Ninh', 'region': 'North East'},
    'BT': {'name': 'Bình Thuận', 'region': 'South Central Coast'},
    'BD': {'name': 'Bình Dương', 'region': 'South East'},
    'BR': {'name': 'Bình Phước', 'region': 'South East'},
    'BH': {'name': 'Bình Định', 'region': 'South Central Coast'},
    'CM': {'name': 'Cà Mau', 'region': 'Mekong Delta'},
    'CT': {'name': 'Cao Bằng', 'region': 'North East'},
    'ĐN': {'name': 'Đà Nẵng', 'region': 'South Central Coast'},
    'ĐL': {'name': 'Đắk Lắk', 'region': 'Central Highlands'},
    'ĐM': {'name': 'Đắk Nông', 'region': 'Central Highlands'},
    'ĐB': {'name': 'Điện Biên', 'region': 'North West'},
    'DT': {'name': 'Đồng Tháp', 'region': 'Mekong Delta'},
    'GA': {'name': 'Gia Lai', 'region': 'Central Highlands'},
    'HG': {'name': 'Hà Giang', 'region': 'North East'},
    'HN': {'name': 'Hà Nội', 'region': 'Red River Delta'},
    'HT': {'name': 'Hà Tĩnh', 'region': 'North Central'},
    'HP': {'name': 'Hải Phòng', 'region': 'Red River Delta'},
    'HN': {'name': 'Hậu Giang', 'region': 'Mekong Delta'},
    'HB': {'name': 'Hoà Bình', 'region': 'North West'},
    'HC': {'name': 'Hồ Chí Minh', 'region': 'South East'},
    'HD': {'name': 'Hưng Yên', 'region': 'Red River Delta'},
    'KH': {'name': 'Khánh Hòa', 'region': 'South Central Coast'},
    'KG': {'name': 'Kiên Giang', 'region': 'Mekong Delta'},
    'KT': {'name': 'Kon Tum', 'region': 'Central Highlands'},
    'LÂ': {'name': 'Lâm Đồng', 'region': 'Central Highlands'},
    'LS': {'name': 'Lạng Sơn', 'region': 'North East'},
    'LÃO': {'name': 'Lào Cai', 'region': 'North West'},
    'LD': {'name': 'Long An', 'region': 'Mekong Delta'},
    'ND': {'name': 'Nam Định', 'region': 'Red River Delta'},
    'NA': {'name': 'Nghệ An', 'region': 'North Central'},
    'NĐ': {'name': 'Ninh Dương', 'region': 'South Central Coast'},
    'NT': {'name': 'Ninh Thuận', 'region': 'South Central Coast'},
    'PT': {'name': 'Phú Thọ', 'region': 'Red River Delta'},
    'PY': {'name': 'Phú Yên', 'region': 'South Central Coast'},
    'QB': {'name': 'Quảng Bình', 'region': 'North Central'},
    'QN': {'name': 'Quảng Ngãi', 'region': 'South Central Coast'},
    'QT': {'name': 'Quảng Trị', 'region': 'North Central'},
    'QH': {'name': 'Quảng Ninh', 'region': 'North East'},
    'SG': {'name': 'Sóc Trăng', 'region': 'Mekong Delta'},
    'ST': {'name': 'Sơn La', 'region': 'North West'},
    'TG': {'name': 'Tây Giang', 'region': 'South Central Coast'},
    'TN': {'name': 'Tây Ninh', 'region': 'South East'},
    'TB': {'name': 'Thanh Bình', 'region': 'Mekong Delta'},
    'TH': {'name': 'Thanh Hóa', 'region': 'North Central'},
    'TT': {'name': 'Thừa Thiên-Huế', 'region': 'North Central'},
    'TĐ': {'name': 'Tiền Giang', 'region': 'Mekong Delta'},
    'TG': {'name': 'Tuyên Quang', 'region': 'North East'},
    'VB': {'name': 'Vĩnh Long', 'region': 'Mekong Delta'},
    'VP': {'name': 'Vĩnh Phúc', 'region': 'Red River Delta'},
    'YB': {'name': 'Yên Bái', 'region': 'North West'},
}

# Simplified province list with common names
PROVINCE_NAMES = {
    'ho_chi_minh': {'name': 'Hồ Chí Minh', 'code': 'HC'},
    'ha_noi': {'name': 'Hà Nội', 'code': 'HN'},
    'hai_phong': {'name': 'Hải Phòng', 'code': 'HP'},
    'binh_duong': {'name': 'Bình Dương', 'code': 'BD'},
    'dong_nai': {'name': 'Đồng Nai', 'code': 'DN'},
    'ba_ria_vung_tau': {'name': 'Bà Rịa-Vũng Tàu', 'code': 'BR'},
    'da_nang': {'name': 'Đà Nẵng', 'code': 'ĐN'},
    'can_tho': {'name': 'Cần Thơ', 'code': 'CT'},
}

# ===========================
# PROPERTY TYPES
# ===========================

PROPERTY_TYPES = ['apartment', 'house', 'land', 'townhouse', 'villa', 'penthouse']

# ===========================
# FEATURE KEYWORDS (for amenity extraction)
# ===========================

AMENITY_KEYWORDS = {
    'air_conditioning': ['máy lạnh', 'điều hòa', 'ac', 'air con'],
    'wifi': ['wifi', 'internet', 'wlan'],
    'parking': ['bãi đỗ xe', 'chỗ để xe', 'tầng hầm', 'garage'],
    'gym': ['phòng tập', 'gym', 'thể dục'],
    'pool': ['bể bơi', 'hồ bơi', 'swimming pool'],
    'garden': ['vườn', 'sân vườn', 'cây xanh'],
    'kitchen': ['bếp', 'nhà bếp', 'kitchen'],
    'balcony': ['ban công', 'balcony'],
    'security': ['bảo vệ', 'an ninh', '24/7', 'cổng kiểm soát'],
    'furnished': ['nội thất', 'đầy đủ nội thất', 'furniture'],
    'elevator': ['thang máy', 'lift'],
    'washing_machine': ['máy giặt', 'washing'],
    'tv': ['tivi', 'tv', 'smart tv'],
    'refrigerator': ['tủ lạnh', 'fridge', 'refrigerator'],
}

# ===========================
# EXPORT SETTINGS
# ===========================

EXPORT_FORMATS = ['csv', 'json', 'parquet']  # parquet for ML training
CSV_DELIMITER = ','
JSON_INDENT = 2

# ===========================
# DATABASE SCHEMA SETTINGS
# ===========================

TABLE_PROPERTIES = 'properties'
TABLE_CRAWL_LOG = 'crawl_logs'
TABLE_DUPLICATE_HASHES = 'duplicate_hashes'

# Data validation
MIN_PRICE = 100000  # VND
MAX_PRICE = 100000000000  # VND (100B VND)
MIN_AREA = 10  # sq meters
MAX_AREA = 100000  # sq meters
VALID_BEDROOMS = range(0, 20)  # 0-19 bedrooms
VALID_BATHROOMS = range(0, 20)  # 0-19 bathrooms

# ===========================
# DISPLAY SETTINGS
# ===========================

CONSOLE_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
FILE_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
