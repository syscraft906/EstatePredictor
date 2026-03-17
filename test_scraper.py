"""
Unit Tests for Estate Crawler
Tests key functionality including parsing, database operations, and exports
"""

import unittest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from config import DATABASE_PATH
from database import EstateDatabase
from scraper import OneHousingScraper, GulandScraper, BatDongSanScraper, BaseScraper
from data_export import DataExporter


class TestBaseScraper(unittest.TestCase):
    """Test BaseScraper functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_db = EstateDatabase(database_path=':memory:')
        self.domain_config = {
            'url': 'https://example.com',
            'search_url': 'https://example.com/search',
            'priority': 1,
            'scraper_type': 'beautifulsoup',
            'enabled': True,
        }
    
    def test_parse_price_valid(self):
        """Test price parsing with valid inputs"""
        scraper = OneHousingScraper(self.domain_config, self.test_db)
        
        # Test VND format
        self.assertEqual(scraper.parse_price("1.500.000 đ"), 1500000)
        self.assertEqual(scraper.parse_price("2,500,000"), 2500000)
        self.assertEqual(scraper.parse_price("1000000"), 1000000)
    
    def test_parse_price_invalid(self):
        """Test price parsing with invalid inputs"""
        scraper = OneHousingScraper(self.domain_config, self.test_db)
        
        self.assertIsNone(scraper.parse_price(None))
        self.assertIsNone(scraper.parse_price(""))
        self.assertIsNone(scraper.parse_price("abc"))
    
    def test_parse_area_valid(self):
        """Test area parsing with valid inputs"""
        scraper = OneHousingScraper(self.domain_config, self.test_db)
        
        self.assertEqual(scraper.parse_area("100 m2"), 100.0)
        self.assertEqual(scraper.parse_area("50,5 m²"), 50.5)
        self.assertEqual(scraper.parse_area("150.25"), 150.25)
    
    def test_parse_area_invalid(self):
        """Test area parsing with invalid inputs"""
        scraper = OneHousingScraper(self.domain_config, self.test_db)
        
        self.assertIsNone(scraper.parse_area(None))
        self.assertIsNone(scraper.parse_area(""))
    
    def test_extract_amenities(self):
        """Test amenity extraction from text"""
        scraper = OneHousingScraper(self.domain_config, self.test_db)
        
        text = "Căn hộ có máy lạnh, wifi, bảo vệ 24/7"
        amenities = scraper.extract_amenities(text)
        
        self.assertIn('air_conditioning', amenities)
        self.assertIn('wifi', amenities)
        self.assertIn('security', amenities)
    
    def test_extract_amenities_empty(self):
        """Test amenity extraction with empty text"""
        scraper = OneHousingScraper(self.domain_config, self.test_db)
        
        amenities = scraper.extract_amenities("")
        self.assertEqual(amenities, [])


class TestDatabase(unittest.TestCase):
    """Test Database operations"""
    
    def setUp(self):
        """Set up test database"""
        self.db = EstateDatabase(database_path=':memory:')
    
    def test_database_initialization(self):
        """Test database is properly initialized"""
        self.assertIsNotNone(self.db)
    
    def test_insert_property(self):
        """Test property insertion"""
        property_data = {
            'property_id': 'test-001',
            'source_domain': 'example.com',
            'source_url': 'https://example.com/property-001',
            'title': 'Test Property',
            'description': 'Test description with máy lạnh',
            'price_vnd': 1500000,
            'price_original': '1.500.000 đ',
            'location_address': '123 Main St',
            'province': 'Ho Chi Minh',
            'area_sqm': 50.0,
            'bedrooms': 2,
            'bathrooms': 1,
            'amenities': ['wifi', 'air_conditioning'],
        }
        
        result = self.db.insert_property(property_data)
        self.assertIsNotNone(result)
    
    def test_duplicate_detection(self):
        """Test duplicate detection"""
        property_data = {
            'property_id': 'test-dup-001',
            'source_domain': 'example.com',
            'source_url': 'https://example.com/property-dup',
            'title': 'Test Property',
            'price_vnd': 1500000,
        }
        
        # Insert first
        result1 = self.db.insert_property(property_data)
        self.assertIsNotNone(result1)
        
        # Try to insert duplicate
        result2 = self.db.insert_property(property_data)
        self.assertIsNone(result2)
    
    def test_insert_multiple_properties(self):
        """Test inserting multiple properties"""
        properties = [
            {
                'property_id': f'test-multi-{i}',
                'source_domain': 'example.com',
                'source_url': f'https://example.com/property-{i}',
                'title': f'Test Property {i}',
                'price_vnd': 1500000 + i * 100000,
            }
            for i in range(3)
        ]
        
        total, added, duplicates = self.db.insert_multiple_properties(properties)
        
        self.assertEqual(total, 3)
        self.assertEqual(added, 3)
        self.assertEqual(duplicates, 0)
    
    def test_get_properties(self):
        """Test retrieving properties"""
        # Insert test data
        for i in range(5):
            self.db.insert_property({
                'property_id': f'test-get-{i}',
                'source_domain': 'example.com',
                'source_url': f'https://example.com/prop-{i}',
                'title': f'Property {i}',
                'province': 'Ho Chi Minh' if i % 2 == 0 else 'Ha Noi',
                'price_vnd': 1000000 + i * 100000,
            })
        
        # Get all
        all_props = self.db.get_properties(limit=100)
        self.assertEqual(len(all_props), 5)
        
        # Get filtered
        hcm_props = self.db.get_properties(province='Ho Chi Minh')
        self.assertEqual(len(hcm_props), 3)
    
    def test_validate_property_data(self):
        """Test data validation"""
        data = {
            'price_vnd': 1500000,
            'area_sqm': 50.0,
            'bedrooms': 2,
            'title': '  Test  ',
        }
        
        validated = self.db.validate_property_data(data)
        
        self.assertEqual(validated['price_vnd'], 1500000)
        self.assertEqual(validated['area_sqm'], 50.0)
        self.assertEqual(validated['title'], 'Test')
    
    def test_validate_invalid_price(self):
        """Test validation rejects invalid prices"""
        data = {
            'price_vnd': 999999999999999,  # Too high
        }
        
        validated = self.db.validate_property_data(data)
        self.assertIsNone(validated['price_vnd'])
    
    def test_database_stats(self):
        """Test getting database statistics"""
        # Insert some test data
        for i in range(3):
            self.db.insert_property({
                'property_id': f'stat-test-{i}',
                'source_domain': 'example.com',
                'source_url': f'https://example.com/stat-{i}',
                'title': f'Stat Test {i}',
                'price_vnd': 1000000 + i * 100000,
                'area_sqm': 50.0 + i * 10,
                'bedrooms': 1 + i,
                'province': 'Ho Chi Minh',
            })
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_properties'], 3)
        self.assertIsNotNone(stats['avg_price_vnd'])
        self.assertIsNotNone(stats['avg_area_sqm'])
        self.assertIsNotNone(stats['avg_bedrooms'])


class TestDataExporter(unittest.TestCase):
    """Test Data Export functionality"""
    
    def setUp(self):
        """Set up test exporter and database"""
        self.test_db = EstateDatabase(database_path=':memory:')
        self.exporter = DataExporter(self.test_db)
        
        # Insert test data
        for i in range(5):
            self.test_db.insert_property({
                'property_id': f'export-test-{i}',
                'source_domain': 'example.com',
                'source_url': f'https://example.com/export-{i}',
                'title': f'Export Test {i}',
                'price_vnd': 1000000 + i * 100000,
                'area_sqm': 50.0 + i * 10,
                'bedrooms': 1 + i,
                'province': 'Ho Chi Minh',
            })
    
    def test_export_to_csv(self):
        """Test CSV export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.exporter.export_dir = Path(tmpdir)
            
            result = self.exporter.export_to_csv('test.csv')
            
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(result))
    
    def test_export_to_json(self):
        """Test JSON export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.exporter.export_dir = Path(tmpdir)
            
            result = self.exporter.export_to_json('test.json')
            
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(result))
    
    def test_export_statistics(self):
        """Test statistics export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.exporter.export_dir = Path(tmpdir)
            
            result = self.exporter.export_statistics('stats.json')
            
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(result))
    
    def test_prepare_property_for_export(self):
        """Test property preparation for export"""
        prop = {
            'property_id': 'test-prep',
            'source_domain': 'example.com',
            'amenities': '["wifi", "ac"]',
            'price_vnd': 1000000,
        }
        
        prepared = DataExporter._prepare_property_for_export(prop)
        
        self.assertEqual(prepared['property_id'], 'test-prep')
        self.assertIsNotNone(prepared['amenities'])


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete workflow: parse -> store -> export"""
        db = EstateDatabase(database_path=':memory:')
        scraper = OneHousingScraper({
            'url': 'https://example.com',
            'search_url': 'https://example.com/search',
        }, db)
        
        # Create test properties
        properties = []
        for i in range(3):
            prop = {
                'property_id': f'workflow-{i}',
                'source_domain': 'example.com',
                'source_url': f'https://example.com/prop-{i}',
                'title': f'Workflow Test {i}',
                'description': f'Căn hộ có máy lạnh và wifi',
                'price_vnd': 1000000 + i * 100000,
                'area_sqm': 50.0 + i * 10,
                'bedrooms': 1 + i,
                'province': 'Ho Chi Minh',
            }
            prop['amenities'] = scraper.extract_amenities(prop['description'])
            properties.append(prop)
        
        # Store properties
        total, added, duplicates = db.insert_multiple_properties(properties)
        self.assertEqual(added, 3)
        
        # Export
        exporter = DataExporter(db)
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter.export_dir = Path(tmpdir)
            
            csv_result = exporter.export_to_csv()
            json_result = exporter.export_to_json()
            
            self.assertIsNotNone(csv_result)
            self.assertIsNotNone(json_result)
            self.assertTrue(os.path.exists(csv_result))
            self.assertTrue(os.path.exists(json_result))


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBaseScraper))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestDataExporter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
