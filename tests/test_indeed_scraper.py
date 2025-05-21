import unittest
import sys
import os
from datetime import datetime
import json

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.indeed_scraper import IndeedScraper
from database.models import IndeedJob, SessionLocal

class TestIndeedScraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment before running tests."""
        cls.scraper = IndeedScraper(headless=True)
        cls.test_search_term = "python developer"
        cls.test_location = "United States"
        
    def setUp(self):
        """Set up before each test."""
        # Clear the database before each test
        db = SessionLocal()
        db.query(IndeedJob).delete()
        db.commit()
        db.close()
        
    def test_scraper_initialization(self):
        """Test if scraper initializes correctly."""
        self.assertIsNotNone(self.scraper)
        self.assertTrue(self.scraper.headless)
        
    def test_basic_scraping(self):
        """Test basic scraping functionality."""
        # Scrape a small number of jobs
        jobs = self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=1,
            max_jobs=2
        )
        
        # Verify jobs were scraped
        self.assertIsInstance(jobs, list)
        self.assertLessEqual(len(jobs), 2)
        
        if jobs:
            # Verify job data structure
            job = jobs[0]
            self.assertIn('id', job)
            self.assertIn('title', job)
            self.assertIn('company', job)
            self.assertIn('location', job)
            self.assertIn('description', job)
            self.assertIn('url', job)
            self.assertIn('date_posted', job)
            self.assertIn('scraped_at', job)
            
            # Verify Indeed-specific fields
            self.assertIn('job_id', job)
            self.assertIn('salary', job)
            self.assertIn('job_type', job)
            self.assertIn('company_rating', job)
            self.assertIn('company_reviews_count', job)
            self.assertIn('company_website', job)
            self.assertIn('benefits', job)
            self.assertIn('raw_data', job)
            
    def test_database_saving(self):
        """Test if jobs are being saved to the database."""
        # Scrape one job
        self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=1,
            max_jobs=1
        )
        
        # Verify job was saved to database
        db = SessionLocal()
        saved_jobs = db.query(IndeedJob).all()
        db.close()
        
        self.assertGreater(len(saved_jobs), 0)
        if saved_jobs:
            job = saved_jobs[0]
            self.assertIsInstance(job, IndeedJob)
            self.assertIsNotNone(job.id)
            self.assertIsNotNone(job.title)
            self.assertIsNotNone(job.company)
            
    def test_raw_data_storage(self):
        """Test if raw data is being stored correctly."""
        # Scrape one job
        self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=1,
            max_jobs=1
        )
        
        # Verify raw data
        db = SessionLocal()
        job = db.query(IndeedJob).first()
        db.close()
        
        if job:
            raw_data = json.loads(job.raw_data)
            self.assertIn('html', raw_data)
            self.assertIn('metadata', raw_data)
            self.assertIn('scraped_at', raw_data['metadata'])
            self.assertIn('url', raw_data['metadata'])
            self.assertIn('title', raw_data['metadata'])
            self.assertIn('company', raw_data['metadata'])
            
    def test_error_handling(self):
        """Test error handling with invalid search terms."""
        # Test with empty search term
        jobs = self.scraper.scrape_jobs(
            search_term="",
            location=self.test_location,
            max_pages=1,
            max_jobs=1
        )
        self.assertIsInstance(jobs, list)
        
        # Test with invalid location
        jobs = self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location="InvalidLocation123",
            max_pages=1,
            max_jobs=1
        )
        self.assertIsInstance(jobs, list)
        
    def test_rate_limiting(self):
        """Test if rate limiting is working."""
        import time
        start_time = time.time()
        
        # Scrape multiple pages
        self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=2,
            max_jobs=4
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify that scraping took at least 8 seconds (2 pages * 4 seconds minimum delay)
        self.assertGreaterEqual(duration, 8)

if __name__ == '__main__':
    unittest.main() 