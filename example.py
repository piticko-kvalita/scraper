"""
Example: Using the scraper programmatically
This demonstrates how to use the scraper module directly in Python code.
"""

from scraper import AIContentScraper, get_all_content, get_statistics
from models import init_db

# Initialize database (only needed once)
init_db()

# Create scraper instance
scraper = AIContentScraper()

# Example 1: Scrape a single URL
print("Example 1: Scraping a single URL")
print("-" * 50)
result = scraper.scrape_and_save("https://example.com/ai-article")
if result["success"]:
    print(f"✅ Success: {result['message']}")
    print(f"   Title: {result['data']['title']}")
    print(f"   Words: {result['data']['word_count']}")
else:
    print(f"❌ Error: {result['message']}")

# Example 2: Scrape multiple URLs
print("\n\nExample 2: Scraping multiple URLs")
print("-" * 50)
urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]
results = scraper.scrape_multiple(urls, delay=2)
success_count = sum(1 for r in results if r["success"])
print(f"✅ Successfully scraped {success_count} of {len(urls)} URLs")

# Example 3: Get all scraped content
print("\n\nExample 3: Retrieving all content")
print("-" * 50)
all_content = get_all_content()
print(f"Total items in database: {len(all_content)}")
for item in all_content[:3]:  # Show first 3
    print(f"  - {item['title']} ({item['word_count']} words)")

# Example 4: Get statistics
print("\n\nExample 4: Getting statistics")
print("-" * 50)
stats = get_statistics()
print(f"Total items: {stats['total_items']}")
print(f"Total words: {stats['total_words']}")
print(f"Content types: {stats['content_types']}")
