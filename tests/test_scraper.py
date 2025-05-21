from scrapers.linkedin_scraper import LinkedInScraper
import json
from datetime import datetime
from database.models import SessionLocal, Job

def main():
    # Initialize the scraper
    scraper = LinkedInScraper(headless=True)
    
    # Test parameters
    search_term = "python developer"
    location = "United States"
    max_pages = 2
    max_jobs = 10
    
    print(f"Starting scrape for '{search_term}' in {location}")
    print(f"Max pages: {max_pages}, Max jobs: {max_jobs}")
    print("-" * 50)
    
    # Run the scraper
    jobs = scraper.scrape_jobs(
        search_term=search_term,
        location=location,
        max_pages=max_pages,
        max_jobs=max_jobs
    )
    
    # Print results
    print(f"\nScraped {len(jobs)} jobs")
    for job in jobs:
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Posted: {job['date_posted']}")
        print("-" * 50)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"jobs_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    print(f"\nResults saved to {filename}")
    
    # Verify database entries
    db = SessionLocal()
    try:
        db_jobs = db.query(Job).all()
        print(f"\nFound {len(db_jobs)} jobs in database")
        for job in db_jobs:
            print(f"\nTitle: {job.title}")
            print(f"Company: {job.company}")
            print(f"Location: {job.location}")
            print(f"Posted: {job.date_posted}")
            print("-" * 50)
    finally:
        db.close()

if __name__ == "__main__":
    main() 