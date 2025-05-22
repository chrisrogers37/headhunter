import unittest
import sys
import os
import logging
from datetime import datetime
import json
import time
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.stackoverflow_scraper import StackOverflowScraper
from database.models import StackOverflowJob, SessionLocal
from utils.rate_limiter import RateLimiter
from utils.monitoring import ScraperMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestStackOverflowScraper(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.scraper = StackOverflowScraper(headless=False)
        self.test_search_term = "Data Scientist"
        self.test_location = "New York, NY"
        self.max_pages = 2
        self.max_jobs = 10

    def tearDown(self):
        """Clean up after tests."""
        if self.scraper.browser:
            self.scraper.browser.close()
        if self.scraper.playwright:
            self.scraper.playwright.stop()

    def test_scraper_initialization(self):
        """Test if the scraper initializes correctly."""
        self.assertIsNotNone(self.scraper)
        self.assertEqual(self.scraper.base_url, "https://stackoverflowjobs.com")
        self.assertFalse(self.scraper.headless)
        self.assertIsInstance(self.scraper.rate_limiter, RateLimiter)
        self.assertIsInstance(self.scraper.monitor, ScraperMonitor)

    def test_basic_scraping(self):
        """Test basic scraping functionality."""
        jobs = self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=self.max_pages,
            max_jobs=self.max_jobs
        )
        
        self.assertIsInstance(jobs, list)
        self.assertLessEqual(len(jobs), self.max_jobs)
        
        if jobs:
            job = jobs[0]
            self.assertIn('title', job)
            self.assertIn('company', job)
            self.assertIn('location', job)
            self.assertIn('description', job)
            self.assertIn('url', job)
            self.assertIn('date_posted', job)
            self.assertIn('raw_data', job)

    def test_database_saving(self):
        """Test if jobs are saved to the database correctly."""
        # First, clear existing test data
        db = SessionLocal()
        db.query(StackOverflowJob).delete()
        db.commit()
        
        # Scrape some jobs
        jobs = self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=1,
            max_jobs=5
        )
        
        # Check if jobs were saved to database
        saved_jobs = db.query(StackOverflowJob).all()
        self.assertLessEqual(len(saved_jobs), 5)
        
        if saved_jobs:
            job = saved_jobs[0]
            self.assertIsNotNone(job.id)
            self.assertIsNotNone(job.job_id)
            self.assertIsNotNone(job.title)
            self.assertIsNotNone(job.company)
            self.assertIsNotNone(job.location)
            self.assertIsNotNone(job.description)
            self.assertIsNotNone(job.url)
            self.assertIsNotNone(job.date_posted)
            self.assertIsNotNone(job.raw_data)
        
        db.close()

    def test_error_handling(self):
        """Test error handling with invalid inputs."""
        # Test with invalid search term
        jobs = self.scraper.scrape_jobs(
            search_term="",  # Empty search term
            location=self.test_location,
            max_pages=1,
            max_jobs=5
        )
        self.assertIsInstance(jobs, list)
        
        # Test with invalid location
        jobs = self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location="",  # Empty location
            max_pages=1,
            max_jobs=5
        )
        self.assertIsInstance(jobs, list)

    def test_rate_limiting(self):
        """Test if rate limiting is working."""
        start_time = datetime.now()
        
        jobs = self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=2,
            max_jobs=10
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Check if scraping took at least 2 seconds (due to rate limiting)
        self.assertGreaterEqual(duration, 2)
        
        # Check if rate limiter is tracking requests
        self.assertGreater(self.scraper.rate_limiter.request_timestamps, 0)

    def test_monitoring(self):
        """Test if monitoring is working correctly."""
        jobs = self.scraper.scrape_jobs(
            search_term=self.test_search_term,
            location=self.test_location,
            max_pages=1,
            max_jobs=5
        )
        
        # Check if metrics were recorded
        metrics = self.scraper.monitor.metrics
        self.assertIsNotNone(metrics.start_time)
        self.assertIsNotNone(metrics.end_time)
        self.assertGreaterEqual(metrics.total_jobs_found, 0)
        self.assertGreaterEqual(metrics.total_jobs_scraped, 0)
        self.assertGreaterEqual(metrics.total_jobs_saved, 0)
        
        # Check if metrics file was created
        metrics_dir = Path("metrics")
        self.assertTrue(metrics_dir.exists())
        metrics_files = list(metrics_dir.glob("stackoverflow_scraper_*.json"))
        self.assertGreater(len(metrics_files), 0)

    def test_rate_limiter_adaptive_delay(self):
        """Test if rate limiter adapts to failures."""
        # Simulate some failures
        self.scraper.rate_limiter.record_failure()
        self.scraper.rate_limiter.record_failure()
        self.scraper.rate_limiter.record_failure()
        
        # Check if burst mode is activated
        self.assertTrue(self.scraper.rate_limiter.burst_mode)
        
        # Record a success
        self.scraper.rate_limiter.record_success()
        
        # Check if burst mode is deactivated
        self.assertFalse(self.scraper.rate_limiter.burst_mode)
        
        # Check if consecutive failures are reset
        self.assertEqual(self.scraper.rate_limiter.consecutive_failures, 0)

if __name__ == '__main__':
    unittest.main() 