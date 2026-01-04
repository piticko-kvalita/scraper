"""Database models for storing scraped content."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config

Base = declarative_base()

class ScrapedContent(Base):
    """Model for storing scraped AI training materials."""
    __tablename__ = "scraped_content"
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    content_type = Column(String(100))  # article, documentation, tutorial, image, video, code, dataset
    scraped_at = Column(DateTime, default=datetime.utcnow)
    word_count = Column(Integer, default=0)
    
    # Media and resources
    images = Column(JSON)  # List of image URLs
    videos = Column(JSON)  # List of video URLs
    code_snippets = Column(JSON)  # List of code blocks
    
    # Quality metrics
    quality_score = Column(Float, default=0.0)  # 0.0 to 1.0
    is_valid = Column(Boolean, default=True)  # False if filtered as bad data
    
    # Auto-gathering metadata
    source_type = Column(String(50), default="manual")  # manual, auto, scheduled
    
    def __repr__(self):
        return f"<ScrapedContent(title='{self.title}', url='{self.url}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "content": self.content[:500] if self.content else None,  # Preview
            "content_type": self.content_type,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "word_count": self.word_count,
            "images": self.images or [],
            "videos": self.videos or [],
            "code_snippets": self.code_snippets or [],
            "quality_score": self.quality_score,
            "is_valid": self.is_valid,
            "source_type": self.source_type,
        }

# Database initialization
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

def init_db():
    """Initialize the database."""
    Base.metadata.create_all(engine)

def get_session():
    """Get a database session."""
    return Session()
