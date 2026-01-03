"""Database models for storing scraped content."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
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
    content_type = Column(String(100))  # article, documentation, tutorial, etc.
    scraped_at = Column(DateTime, default=datetime.utcnow)
    word_count = Column(Integer, default=0)
    
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
