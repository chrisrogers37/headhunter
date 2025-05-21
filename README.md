# Headhunter

A robust, cloud-ready job scraping and analysis tool for tracking and analyzing job postings across multiple platforms, with a focus on Stack Overflow Jobs.

## Project Overview
Headhunter is designed to automate the collection, structuring, and analysis of job postings. It supports scraping job data, storing it in a PostgreSQL database, and providing tools for analysis and API access. The project is engineered for both local and cloud deployment, with a focus on reliability, scalability, and maintainability.

## Key Features
- Scrape job postings from Stack Overflow Jobs (all fields, including full descriptions)
- Store structured job data in PostgreSQL (local or managed cloud instance)
- Robust, anti-bot scraping with Playwright
- Tracks job posting changes over time
- Analysis tools and REST API (planned)
- Cloud-ready: supports deployment on remote servers and integration with managed databases
- Monitoring, logging, and debugging tools

## Current Status
- Stack Overflow scraper reliably extracts all fields, including job descriptions
- Database schema and models are production-ready
- Local and cloud deployment roadmap in progress
- Codebase is clean, robust, and well-documented
- See `ROADMAP.md` for detailed progress and next steps

## Roadmap Highlights
- [x] Local scraping and database integration
- [x] Robust field extraction and error handling
- [ ] Cloud deployment and remote database integration
- [ ] Full pagination support for Stack Overflow Jobs
- [ ] API and analysis tools

## Setup Instructions
### Local Development
1. **Clone the repository and create a virtual environment:**
   ```bash
   git clone <repo-url>
   cd headhunter
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Playwright browsers:**
   ```bash
   python3 -m playwright install chromium
   ```
4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```
5. **Initialize the database:**
   ```bash
   python3 src/database/init_db.py
   ```

### Remote/Cloud Deployment (Planned)
- Provision a cloud server (e.g., AWS EC2, DigitalOcean Droplet, GCP Compute Engine)
- Set up a managed PostgreSQL instance (e.g., AWS RDS, Supabase, Neon)
- Configure secure connectivity between the scraper and the database
- Deploy the code and run the scraper as a service or scheduled job
- See `ROADMAP.md` for detailed steps and best practices

## Usage
- **Run the scraper:**
  ```bash
  python3 src/scrapers/stackoverflow_scraper.py
  ```
- **Inspect the database:**
  Use a PostgreSQL client or run:
  ```bash
  PYTHONPATH=src python3 -c "from database.models import SessionLocal, StackOverflowJob; db = SessionLocal(); jobs = db.query(StackOverflowJob).all(); print(f'Found {len(jobs)} jobs'); [print(f'{job.title} at {job.company} | {job.location}\n{(job.description[:200] if job.description else 'No description') + '...'}\n---') for job in jobs]; db.close()"
  ```
- **API and analysis tools:** (coming soon)

## Best Practices & Learnings
- Use robust selectors and wait for dynamic content
- Save HTML snapshots for debugging
- Separate scraping, data processing, and analysis logic
- Plan for cloud deployment and secure data pipelines

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License - see LICENSE file for details
