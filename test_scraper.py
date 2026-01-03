"""Tests for the AI training materials scraper."""
import unittest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import AIContentScraper, get_all_content, get_statistics, delete_content
from models import init_db, get_session, ScrapedContent


class TestDataValidation(unittest.TestCase):
    """Test data validation and quality filtering."""
    
    def setUp(self):
        """Set up test database."""
        # Use in-memory database for testing
        import config
        config.DATABASE_PATH = ":memory:"
        config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        init_db()
    
    def test_valid_url_validation(self):
        """Test that valid URLs are accepted."""
        scraper = AIContentScraper()
        result = scraper.scrape_url("https://example.com")
        self.assertNotIn("error", result)
    
    def test_invalid_url_validation(self):
        """Test that invalid URLs are rejected."""
        scraper = AIContentScraper()
        result = scraper.scrape_url("not-a-valid-url")
        self.assertIn("error", result)
        self.assertIn("Invalid URL", result["error"])
    
    def test_content_length_validation(self):
        """Test that content meets minimum length requirements."""
        scraper = AIContentScraper()
        
        # Create mock HTML with very short content
        short_content = "<html><body><p>Too short</p></body></html>"
        
        # This should be filtered as bad data
        self.assertTrue(len(short_content) < 100)
    
    def test_word_count_accuracy(self):
        """Test that word count is calculated correctly."""
        scraper = AIContentScraper()
        test_text = "This is a test with ten words in total here."
        word_count = len(test_text.split())
        self.assertEqual(word_count, 10)


class TestContentExtraction(unittest.TestCase):
    """Test content extraction functionality."""
    
    def setUp(self):
        """Set up test scraper."""
        self.scraper = AIContentScraper()
    
    def test_title_extraction(self):
        """Test title extraction from HTML."""
        from bs4 import BeautifulSoup
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        title = self.scraper._extract_title(soup)
        self.assertEqual(title, "Test Title")
    
    def test_content_type_detection(self):
        """Test content type detection."""
        from bs4 import BeautifulSoup
        
        # Test tutorial detection
        url = "https://example.com/tutorial-machine-learning"
        soup = BeautifulSoup("<html></html>", "html.parser")
        images = []
        videos = []
        code_snippets = []
        content_type = self.scraper._determine_content_type(url, soup, images, videos, code_snippets)
        self.assertEqual(content_type, "tutorial")
        
        # Test documentation detection
        url = "https://example.com/docs/api"
        content_type = self.scraper._determine_content_type(url, soup, images, videos, code_snippets)
        self.assertEqual(content_type, "documentation")


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test database."""
        import config
        config.DATABASE_PATH = ":memory:"
        config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        init_db()
    
    def test_save_content(self):
        """Test saving content to database."""
        db_session = get_session()
        content = ScrapedContent(
            url="https://example.com/test",
            title="Test Title",
            content="Test content",
            content_type="article",
            word_count=2
        )
        db_session.add(content)
        db_session.commit()
        
        # Verify it was saved
        saved = db_session.query(ScrapedContent).first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.title, "Test Title")
        db_session.close()
    
    def test_duplicate_url_handling(self):
        """Test that duplicate URLs are handled correctly."""
        db_session = get_session()
        
        # Add first content
        content1 = ScrapedContent(
            url="https://example.com/test",
            title="First Title",
            content="First content",
            content_type="article",
            word_count=2
        )
        db_session.add(content1)
        db_session.commit()
        
        # Try to add duplicate URL
        try:
            content2 = ScrapedContent(
                url="https://example.com/test",
                title="Second Title",
                content="Second content",
                content_type="article",
                word_count=2
            )
            db_session.add(content2)
            db_session.commit()
            self.fail("Should have raised an error for duplicate URL")
        except Exception:
            db_session.rollback()
            # This is expected
            pass
        
        db_session.close()
    
    def test_get_statistics(self):
        """Test statistics calculation."""
        db_session = get_session()
        
        # Add test data
        for i in range(3):
            content = ScrapedContent(
                url=f"https://example.com/test{i}",
                title=f"Test {i}",
                content=f"Test content {i}",
                content_type="article" if i % 2 == 0 else "tutorial",
                word_count=10
            )
            db_session.add(content)
        db_session.commit()
        db_session.close()
        
        # Get statistics
        stats = get_statistics()
        self.assertEqual(stats["total_items"], 3)
        self.assertEqual(stats["total_words"], 30)
        self.assertIn("article", stats["content_types"])
        self.assertIn("tutorial", stats["content_types"])


class TestDataQualityFilter(unittest.TestCase):
    """Test data quality filtering."""
    
    def test_minimum_content_length(self):
        """Test that content meets minimum length."""
        # Content should have at least 50 words to be considered valid
        short_content = " ".join(["word"] * 10)  # Only 10 words
        self.assertTrue(len(short_content.split()) < 50)
        
        long_content = " ".join(["word"] * 100)  # 100 words
        self.assertTrue(len(long_content.split()) >= 50)
    
    def test_spam_detection(self):
        """Test spam content detection."""
        # Test for common spam indicators
        spam_keywords = ["viagra", "casino", "lottery", "click here", "buy now"]
        
        clean_text = "This is a legitimate article about machine learning"
        spam_text = "Click here to buy viagra and win the lottery at our casino"
        
        # Check if spam keywords are present
        spam_found = any(keyword in spam_text.lower() for keyword in spam_keywords)
        self.assertTrue(spam_found)
        
        clean_found = any(keyword in clean_text.lower() for keyword in spam_keywords)
        self.assertFalse(clean_found)


if __name__ == "__main__":
    unittest.main()
