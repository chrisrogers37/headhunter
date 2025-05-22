import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass, field
import json
import os
from database.models import ScrapingMetrics, SessionLocal

logger = logging.getLogger(__name__)

@dataclass
class ScrapingMetricsData:
    """Data class to store scraping metrics."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_jobs_found: int = 0
    total_jobs_scraped: int = 0
    total_jobs_saved: int = 0
    failed_jobs: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0.0
    errors: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_jobs_found': self.total_jobs_found,
            'total_jobs_scraped': self.total_jobs_scraped,
            'total_jobs_saved': self.total_jobs_saved,
            'failed_jobs': self.failed_jobs,
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'total_duration': self.total_duration,
            'success_rate': (self.total_jobs_scraped / self.total_jobs_found * 100) if self.total_jobs_found > 0 else 0,
            'errors': self.errors
        }

class ScraperMonitor:
    def __init__(self, scraper_name: str):
        """
        Initialize the scraper monitor.
        
        Args:
            scraper_name: Name of the scraper being monitored
        """
        self.scraper_name = scraper_name
        self.metrics = ScrapingMetricsData()
        self.start_time = time.time()
        
    def record_job_found(self):
        """Record that a job was found."""
        self.metrics.total_jobs_found += 1
        
    def record_job_scraped(self):
        """Record that a job was successfully scraped."""
        self.metrics.total_jobs_scraped += 1
        
    def record_job_saved(self):
        """Record that a job was successfully saved to the database."""
        self.metrics.total_jobs_saved += 1
        
    def record_job_failed(self, error: Exception):
        """Record a failed job scrape."""
        self.metrics.failed_jobs += 1
        self.metrics.errors.append({
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error)
        })
        
    def record_request(self, success: bool = True):
        """Record a request attempt."""
        self.metrics.total_requests += 1
        if not success:
            self.metrics.failed_requests += 1
            
    def finish(self):
        """Mark the scraping session as complete and calculate final metrics."""
        self.metrics.end_time = datetime.now()
        self.metrics.total_duration = time.time() - self.start_time
        
    def save_metrics(self, directory: str = "metrics"):
        """Save metrics to both JSON file and database."""
        self.finish()
        metrics_dict = self.metrics.to_dict()
        
        # Save to JSON file
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{directory}/{self.scraper_name}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(metrics_dict, f, indent=2)
            
        logger.info(f"Saved metrics to {filename}")
        
        # Save to database
        try:
            db = SessionLocal()
            db_metrics = ScrapingMetrics(
                scraper_name=self.scraper_name,
                start_time=self.metrics.start_time,
                end_time=self.metrics.end_time,
                total_jobs_found=self.metrics.total_jobs_found,
                total_jobs_scraped=self.metrics.total_jobs_scraped,
                total_jobs_saved=self.metrics.total_jobs_saved,
                failed_jobs=self.metrics.failed_jobs,
                total_requests=self.metrics.total_requests,
                failed_requests=self.metrics.failed_requests,
                total_duration=self.metrics.total_duration,
                success_rate=metrics_dict['success_rate'],
                errors=self.metrics.errors
            )
            db.add(db_metrics)
            db.commit()
            logger.info(f"Saved metrics to database with ID: {db_metrics.id}")
        except Exception as e:
            logger.error(f"Error saving metrics to database: {str(e)}")
            db.rollback()
        finally:
            db.close()
            
    def log_summary(self):
        """Log a summary of the scraping session."""
        self.finish()
        metrics = self.metrics.to_dict()
        
        logger.info(f"\nScraping Summary for {self.scraper_name}:")
        logger.info(f"Duration: {metrics['total_duration']:.2f} seconds")
        logger.info(f"Jobs Found: {metrics['total_jobs_found']}")
        logger.info(f"Jobs Scraped: {metrics['total_jobs_scraped']}")
        logger.info(f"Jobs Saved: {metrics['total_jobs_saved']}")
        logger.info(f"Failed Jobs: {metrics['failed_jobs']}")
        logger.info(f"Success Rate: {metrics['success_rate']:.1f}%")
        logger.info(f"Total Requests: {metrics['total_requests']}")
        logger.info(f"Failed Requests: {metrics['failed_requests']}")
        
        if metrics['errors']:
            logger.warning(f"Encountered {len(metrics['errors'])} errors during scraping") 