# Headhunter

A robust job scraping toolkit that collects job listings from Stack Overflow Jobs with anti-detection measures and comprehensive monitoring, designed for resume-to-job matching using vector databases.

## Features

- **Job Scraping**
  - Stack Overflow Jobs integration
  - Anti-detection measures
  - Comprehensive monitoring
  - Metrics tracking

- **Anti-Detection Measures**
  - Intelligent request timing
  - Browser automation
  - Request management
  - Location-based access

- **Comprehensive Monitoring**
  - Real-time scraping metrics
  - Success/failure tracking
  - Performance monitoring
  - Error logging
  - Metrics stored in both JSON and PostgreSQL

- **Data Storage**
  - PostgreSQL database integration
  - Structured job data models
  - Raw HTML storage for debugging
  - Metrics history tracking

## Project Structure

```
headhunter/
├── src/
│   ├── scrapers/           # Platform-specific scrapers
│   │   ├── stackoverflow_scraper.py
│   │   ├── indeed_scraper.py      # Development only
│   │   └── linkedin_scraper.py    # Development only
│   ├── database/          # Database models and utilities
│   │   └── models.py
│   ├── utils/             # Shared utilities
│   │   ├── monitoring.py
│   │   └── rate_limiter.py
│   └── scripts/           # Executable scripts
│       ├── run_stackoverflow_scraper.py
│       ├── run_indeed_scraper.py      # Development only
│       └── run_linkedin_scraper.py    # Development only
├── tests/                 # Unit tests
│   ├── test_stackoverflow_scraper.py
│   └── test_indeed_scraper.py        # Development only
├── metrics/              # Scraping metrics JSON files
├── setup.py             # Package configuration
└── requirements.txt     # Project dependencies
```

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/headhunter.git
   cd headhunter
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Set up PostgreSQL database**
   - Create a database named `headhunter`
   - Create a `.env` file (do not commit this file to version control):
     ```
     DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<database>
     ```
   - Add `.env` to your `.gitignore` file

5. **Install Playwright browsers**
   ```bash
   playwright install
   ```

## Usage

### Running the Scraper

Run the Stack Overflow Jobs scraper:

```bash
python -m src.scripts.run_stackoverflow_scraper
```

### Viewing Results

- Job listings are stored in the PostgreSQL database
- Scraping metrics are saved in both:
  - JSON files in the `metrics/` directory
  - `scraping_metrics` table in the database

### Running Tests

```bash
python -m unittest tests/test_stackoverflow_scraper.py
```

## Development-Only Features

The following features are marked for future development but not part of the current roadmap:
- Indeed scraper (requires significant anti-bot measures)
- LinkedIn scraper (requires significant anti-bot measures)
- Multi-platform support
- Platform-specific data models

## Security Notes

- Never commit `.env` files containing real credentials
- Keep your database credentials secure
- Be mindful of rate limits and terms of service
- Consider using environment variables for sensitive configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
