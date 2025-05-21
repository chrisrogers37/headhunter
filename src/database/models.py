from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, UUID, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Create database engine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/headhunter")
engine = create_engine(DATABASE_URL)

# Create base class for models
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    description = Column(Text)
    url = Column(String, unique=True)
    date_posted = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Job(title='{self.title}', company='{self.company}')>"

class IndeedJob(Base):
    __tablename__ = "indeed_jobs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(String, unique=True)  # Indeed's unique job ID
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    description = Column(Text)
    url = Column(String, unique=True)
    date_posted = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Indeed-specific fields
    salary = Column(String)  # Raw salary text
    job_type = Column(String)  # Full-time, Part-time, etc.
    company_rating = Column(String)  # Company rating if available
    company_reviews_count = Column(String)  # Number of company reviews
    company_website = Column(String)  # Company website if available
    benefits = Column(JSON)  # JSON array of benefits
    raw_data = Column(JSON)  # Store complete raw data for future processing
    
    def __repr__(self):
        return f"<IndeedJob(title='{self.title}', company='{self.company}')>"

class StackOverflowJob(Base):
    __tablename__ = "stackoverflow_jobs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(String)  # Stack Overflow's internal job ID
    title = Column(String)
    company = Column(String)
    location = Column(String)
    description = Column(String)
    url = Column(String)
    date_posted = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    salary_range = Column(String, nullable=True)
    job_type = Column(String, nullable=True)  # Full-time, Contract, etc.
    experience_level = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)  # Store job tags/technologies
    company_size = Column(String, nullable=True)
    company_industry = Column(String, nullable=True)
    remote_work = Column(Boolean, nullable=True)
    raw_data = Column(JSON)  # Store complete raw data for future processing

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 