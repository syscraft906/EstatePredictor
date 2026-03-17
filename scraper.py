"""
Vietnam Real Estate Scraper — powered by crawl4ai
Stealth browser crawling to bypass anti-bot protection
"""

import asyncio
import json
import logging
import os
import re
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

warnings.filterwarnings("ignore")

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from config import (
    LOG_DIR, LOG_FILE_NAME, LOG_LEVEL,
    RETRY_ATTEMPTS as MAX_RETRIES,
    RATE_LIMIT_DELAY as REQUEST_DELAY,
)
from database import EstateDatabase, get_database

MAX_PAGES_PER_DOMAIN = 2  # URLs per domain per run

# ── Logging ───────────────────────────────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{LOG_DIR}/{LOG_FILE_NAME}"),
    ],
)
logger = logging.getLogger("scraper")

# ── Browser config (stealth) ──────────────────────────────────────────────────
BROWSER_CONFIG = BrowserConfig(
    browser_type="chromium",
    headless=True,
    verbose=False,
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ],
)

# ── Per-site CSS schemas ──────────────────────────────────────────────────────
SITE_CONFIGS: Dict[str, Dict] = {
    # alonhadat: confirmed live selectors from HTML inspection
    "alonhadat": {
        "urls": [
            "https://alonhadat.com.vn/can-ban-nha-dat",
            "https://alonhadat.com.vn/can-ban-nha-dat/trang--2",
        ],
        "schema": {
            "name": "properties",
            "baseSelector": "article.property-item",
            "fields": [
                {"name": "title",    "selector": "h3.property-title",   "type": "text"},
                {"name": "price",    "selector": "span.price strong",    "type": "text"},
                {"name": "area",     "selector": "span.square",          "type": "text"},
                {"name": "location", "selector": "span.address",         "type": "text"},
                {"name": "url",      "selector": "a.link",               "type": "attribute", "attribute": "href"},
            ],
        },
    },
    # batdongsan: confirmed live selectors from HTML inspection
    "batdongsan": {
        "urls": [
            "https://batdongsan.com.vn/nha-dat-ban",
            "https://batdongsan.com.vn/can-ho-chung-cu",
        ],
        "schema": {
            "name": "properties",
            "baseSelector": "div.js__card",
            "fields": [
                {"name": "title",    "selector": "span.js__card-title",        "type": "text"},
                {"name": "price",    "selector": "span.re__card-config-price",  "type": "text"},
                {"name": "area",     "selector": "span.re__card-config-area",   "type": "text"},
                {"name": "location", "selector": "div.re__card-location span",  "type": "text"},
                {"name": "url",      "selector": "a.js__product-link-for-product-id",
                                     "type": "attribute", "attribute": "href"},
            ],
        },
    },
    # NOTE: meeyland.com — times out (server blocks headless), removed for now
    # NOTE: nha.vn       — ERR_ADDRESS_UNREACHABLE (domain down), removed for now
}


# ── Result ────────────────────────────────────────────────────────────────────
@dataclass
class ScrapeResult:
    domain: str
    added: int = 0
    duplicates: int = 0
    errors: int = 0
    duration: float = 0.0


# ── Scraper ───────────────────────────────────────────────────────────────────
class Crawl4AIScraper:
    def __init__(self, db: EstateDatabase):
        self.db = db

    async def scrape_domain(self, domain_key: str) -> ScrapeResult:
        cfg = SITE_CONFIGS.get(domain_key)
        if not cfg:
            logger.warning(f"No config for: {domain_key}")
            return ScrapeResult(domain=domain_key, errors=1)

        result = ScrapeResult(domain=domain_key)
        start = datetime.now()

        extraction = JsonCssExtractionStrategy(cfg["schema"], verbose=False)
        run_cfg = CrawlerRunConfig(
            extraction_strategy=extraction,
            cache_mode=CacheMode.BYPASS,
            wait_until="networkidle",
            page_timeout=30000,
            simulate_user=True,
            magic=True,
            remove_overlay_elements=True,
        )

        async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
            for url in cfg["urls"][:MAX_PAGES_PER_DOMAIN]:
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        logger.info(f"[{domain_key}] {url} (attempt {attempt}/{MAX_RETRIES})")
                        res = await crawler.arun(url=url, config=run_cfg)

                        if not res.success:
                            logger.warning(f"[{domain_key}] Error: {res.error_message}")
                            await asyncio.sleep(REQUEST_DELAY * attempt)
                            continue

                        raw = res.extracted_content
                        if not raw:
                            logger.warning(f"[{domain_key}] Empty extraction from {url}")
                            break

                        items = json.loads(raw) if isinstance(raw, str) else raw
                        if isinstance(items, dict):
                            items = items.get("properties", [])

                        added, dupes, _ = self.db.insert_multiple_properties(
                            [_to_db_dict(item, domain_key, url) for item in items if item.get("title")]
                        )
                        result.added += added
                        result.duplicates += dupes
                        logger.info(f"[{domain_key}] Done: +{added} new, {dupes} dupes")
                        break

                    except Exception as e:
                        logger.error(f"[{domain_key}] Attempt {attempt} exception: {e}")
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(REQUEST_DELAY * attempt)
                        else:
                            result.errors += 1

                await asyncio.sleep(REQUEST_DELAY)

        result.duration = (datetime.now() - start).total_seconds()
        self.db.log_crawl(
            domain=domain_key,
            status="success" if result.errors == 0 else "partial",
            records_crawled=result.added + result.duplicates,
            records_added=result.added,
            records_updated=0,
        )
        return result


# ── Multi-domain orchestrator ─────────────────────────────────────────────────
class MultiDomainScraper:
    def __init__(self):
        self.db = get_database()
        self.scraper = Crawl4AIScraper(self.db)

    def scrape_all(self) -> Dict:
        return asyncio.run(self._run())

    async def _run(self) -> Dict:
        domains = list(SITE_CONFIGS.keys())
        logger.info(f"Scraping {len(domains)} domains via crawl4ai")
        results = {}
        for domain in domains:
            results[domain] = await self.scraper.scrape_domain(domain)
        return self._summary(results)

    def _summary(self, results: Dict[str, ScrapeResult]) -> Dict:
        total_added = sum(r.added for r in results.values())
        total_dupes = sum(r.duplicates for r in results.values())
        s = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_added": total_added,
            "total_duplicates": total_dupes,
            "domains": {
                k: {"added": v.added, "duplicates": v.duplicates,
                    "errors": v.errors, "duration_s": round(v.duration, 2)}
                for k, v in results.items()
            },
        }
        print("\n" + "=" * 72)
        print("SCRAPE RESULTS")
        print("=" * 72)
        print(f"Timestamp  : {s['timestamp']}")
        print(f"Total new  : {total_added}")
        print(f"Duplicates : {total_dupes}")
        print("-" * 72)
        for domain, d in s["domains"].items():
            icon = "✓" if d["errors"] == 0 else "✗"
            print(f"{icon} {domain:<18} | +{d['added']:>4} new | {d['duplicates']:>4} dupes | {d['errors']} err | {d['duration_s']:>5.1f}s")
        print("=" * 72 + "\n")
        return s


# ── Helpers ───────────────────────────────────────────────────────────────────
def _clean(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    return re.sub(r"\s+", " ", str(val)).strip() or None


def _infer_type(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["căn hộ", "chung cư", "apartment", "cc"]):
        return "apartment"
    if any(k in t for k in ["đất", "land", "lô đất"]):
        return "land"
    if any(k in t for k in ["villa", "biệt thự"]):
        return "villa"
    if any(k in t for k in ["nhà phố", "townhouse"]):
        return "townhouse"
    return "house"


def _to_db_dict(item: Dict, domain: str, source_url: str) -> Dict:
    title = _clean(item.get("title")) or ""
    url = item.get("url") or ""
    if url and not url.startswith("http"):
        base = "/".join(source_url.split("/")[:3])  # e.g. https://alonhadat.com.vn
        url = base + "/" + url.lstrip("/")
    return {
        "title": title,
        "price": _clean(item.get("price")),
        "area": _clean(item.get("area")),
        "address": _clean(item.get("location")),
        "source_domain": domain,
        "source_url": url or source_url,
        "property_type": _infer_type(title),
        "scraped_at": datetime.utcnow().isoformat(),
    }
