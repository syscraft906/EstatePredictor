"""
Data Export Module
Exports collected data to CSV, JSON, and Parquet formats for analysis and ML training
"""

import csv
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

from config import DATA_DIR, CSV_DELIMITER, JSON_INDENT, EXPORT_FORMATS
from database import EstateDatabase

logger = logging.getLogger(__name__)


class DataExporter:
    """Handles data export to various formats"""
    
    def __init__(self, database: EstateDatabase = None):
        """Initialize exporter"""
        self.database = database or EstateDatabase()
        self.export_dir = Path(DATA_DIR) / 'processed'
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_csv(self, filename: str = None, **filters) -> Optional[str]:
        """Export data to CSV format"""
        try:
            if filename is None:
                filename = f"estate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            filepath = self.export_dir / filename
            
            # Get all properties (without limit for export)
            properties = self.database.get_properties(limit=1000000, **filters)
            
            if not properties:
                logger.warning("No properties to export")
                return None
            
            # Prepare data for CSV
            csv_data = []
            for prop in properties:
                csv_data.append(self._prepare_property_for_export(prop))
            
            # Write to CSV
            if csv_data:
                keys = csv_data[0].keys()
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys, delimiter=CSV_DELIMITER)
                    writer.writeheader()
                    writer.writerows(csv_data)
                
                logger.info(f"Exported {len(csv_data)} properties to CSV: {filepath}")
                return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def export_to_json(self, filename: str = None, **filters) -> Optional[str]:
        """Export data to JSON format"""
        try:
            if filename is None:
                filename = f"estate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            filepath = self.export_dir / filename
            
            # Get all properties
            properties = self.database.get_properties(limit=1000000, **filters)
            
            if not properties:
                logger.warning("No properties to export")
                return None
            
            # Prepare data
            json_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_records': len(properties),
                    'filters': filters,
                },
                'properties': [
                    self._prepare_property_for_export(prop)
                    for prop in properties
                ]
            }
            
            # Write to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=JSON_INDENT)
            
            logger.info(f"Exported {len(properties)} properties to JSON: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return None
    
    def export_to_parquet(self, filename: str = None, **filters) -> Optional[str]:
        """Export data to Parquet format for ML training"""
        if not HAS_PANDAS:
            logger.error("Pandas not available. Install pandas and pyarrow for parquet export")
            return None
        
        try:
            if filename is None:
                filename = f"estate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            
            filepath = self.export_dir / filename
            
            # Get all properties
            properties = self.database.get_properties(limit=1000000, **filters)
            
            if not properties:
                logger.warning("No properties to export")
                return None
            
            # Convert to DataFrame
            df_data = [self._prepare_property_for_export(prop) for prop in properties]
            df = pd.DataFrame(df_data)
            
            # Data type conversions for parquet
            df['price_vnd'] = pd.to_numeric(df['price_vnd'], errors='coerce')
            df['area_sqm'] = pd.to_numeric(df['area_sqm'], errors='coerce')
            df['bedrooms'] = pd.to_numeric(df['bedrooms'], errors='coerce')
            df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')
            df['images_count'] = pd.to_numeric(df['images_count'], errors='coerce')
            
            # Save to parquet
            df.to_parquet(filepath, index=False)
            
            logger.info(f"Exported {len(df)} properties to Parquet: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting to Parquet: {e}")
            return None
    
    def export_all_formats(self, prefix: str = None, **filters) -> Dict[str, Optional[str]]:
        """Export data to all available formats"""
        if prefix is None:
            prefix = f"estate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        results = {
            'csv': self.export_to_csv(f"{prefix}.csv", **filters),
            'json': self.export_to_json(f"{prefix}.json", **filters),
        }
        
        # Try parquet if pandas is available
        if HAS_PANDAS:
            results['parquet'] = self.export_to_parquet(f"{prefix}.parquet", **filters)
        
        return results
    
    def export_by_province(self, province: str) -> Dict[str, Optional[str]]:
        """Export data for specific province"""
        prefix = f"estate_data_{province}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_all_formats(prefix=prefix, province=province)
    
    def export_ml_dataset(self, filename: str = None, test_split: float = 0.2) -> Optional[str]:
        """Export data specifically prepared for ML training"""
        if not HAS_PANDAS:
            logger.error("Pandas required for ML dataset export")
            return None
        
        try:
            if filename is None:
                filename = f"estate_ml_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            
            filepath = self.export_dir / filename
            
            # Get all properties
            properties = self.database.get_properties(limit=1000000)
            
            if not properties:
                logger.warning("No properties to export")
                return None
            
            # Prepare ML dataset
            ml_data = []
            for prop in properties:
                if prop.get('price_vnd') and prop.get('area_sqm'):  # Only include with price and area
                    ml_data.append({
                        'property_id': prop.get('property_id'),
                        'property_type': prop.get('property_type'),
                        'price_vnd': float(prop['price_vnd']) if prop.get('price_vnd') else None,
                        'area_sqm': float(prop['area_sqm']) if prop.get('area_sqm') else None,
                        'bedrooms': int(prop['bedrooms']) if prop.get('bedrooms') else None,
                        'bathrooms': int(prop['bathrooms']) if prop.get('bathrooms') else None,
                        'province': prop.get('province'),
                        'district': prop.get('district'),
                        'amenity_count': len(prop.get('amenities', [])) if isinstance(prop.get('amenities'), list) else 0,
                        'images_count': int(prop.get('images_count', 0)) if prop.get('images_count') else 0,
                    })
            
            if ml_data:
                df = pd.DataFrame(ml_data)
                
                # Remove rows with NaN in critical columns
                df = df.dropna(subset=['price_vnd', 'area_sqm', 'province'])
                
                # Create price per sqm feature
                df['price_per_sqm'] = df['price_vnd'] / df['area_sqm']
                
                # Save to parquet
                df.to_parquet(filepath, index=False)
                
                logger.info(f"Exported {len(df)} properties to ML dataset: {filepath}")
                logger.info(f"Features: {list(df.columns)}")
                logger.info(f"Shape: {df.shape}")
                
                return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting ML dataset: {e}")
            return None
    
    def export_statistics(self, filename: str = None) -> Optional[str]:
        """Export database statistics"""
        try:
            if filename is None:
                filename = f"estate_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            filepath = self.export_dir / filename
            
            stats = self.database.get_stats()
            
            # Additional statistics
            all_properties = self.database.get_properties(limit=1000000)
            
            if all_properties:
                prices = [p['price_vnd'] for p in all_properties if p.get('price_vnd')]
                areas = [p['area_sqm'] for p in all_properties if p.get('area_sqm')]
                
                if prices:
                    stats['min_price'] = min(prices)
                    stats['max_price'] = max(prices)
                    stats['median_price'] = sorted(prices)[len(prices) // 2]
                
                if areas:
                    stats['min_area'] = min(areas)
                    stats['max_area'] = max(areas)
                    stats['median_area'] = sorted(areas)[len(areas) // 2]
            
            stats['export_date'] = datetime.now().isoformat()
            
            # Write statistics
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=JSON_INDENT)
            
            logger.info(f"Exported statistics to: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}")
            return None
    
    @staticmethod
    def _prepare_property_for_export(prop: Dict) -> Dict:
        """Prepare property data for export"""
        # Handle amenities
        amenities = prop.get('amenities')
        if isinstance(amenities, str):
            try:
                amenities = json.loads(amenities)
            except:
                amenities = []
        
        return {
            'property_id': prop.get('property_id'),
            'source_domain': prop.get('source_domain'),
            'source_url': prop.get('source_url'),
            'property_type': prop.get('property_type'),
            'title': prop.get('title'),
            'description': prop.get('description'),
            'price_vnd': prop.get('price_vnd'),
            'price_original': prop.get('price_original'),
            'location_address': prop.get('location_address'),
            'province': prop.get('province'),
            'district': prop.get('district'),
            'ward': prop.get('ward'),
            'area_sqm': prop.get('area_sqm'),
            'bedrooms': prop.get('bedrooms'),
            'bathrooms': prop.get('bathrooms'),
            'amenities': json.dumps(amenities) if amenities else '',
            'images_count': prop.get('images_count'),
            'listing_date': prop.get('listing_date'),
            'contact_name': prop.get('contact_name'),
            'contact_phone': prop.get('contact_phone'),
            'contact_email': prop.get('contact_email'),
            'is_active': prop.get('is_active'),
            'crawl_date': prop.get('crawl_date'),
        }


def export_all():
    """Export all data to all formats"""
    exporter = DataExporter()
    
    logger.info("Starting data export...")
    
    results = exporter.export_all_formats()
    exporter.export_statistics()
    
    if HAS_PANDAS:
        exporter.export_ml_dataset()
    
    logger.info("Data export completed")
    print("Export Results:")
    for format_type, filepath in results.items():
        if filepath:
            print(f"  {format_type}: {filepath}")


if __name__ == '__main__':
    # Test exporter
    logging.basicConfig(level=logging.INFO)
    exporter = DataExporter()
    
    print("Available export formats:", EXPORT_FORMATS)
    print("\nExporting data...")
    
    results = exporter.export_all_formats()
    print("\nExport Results:")
    for format_type, filepath in results.items():
        if filepath:
            print(f"  {format_type}: {filepath}")
        else:
            print(f"  {format_type}: Failed")
    
    # Export statistics
    stats_file = exporter.export_statistics()
    if stats_file:
        print(f"\nStatistics exported to: {stats_file}")
