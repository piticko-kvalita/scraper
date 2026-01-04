# AI Training Materials Scraper 🤖

A modern web application for scraping and organizing AI training materials from across the web. Features a clean, responsive UI and powerful scraping capabilities.

## Features

- 🌐 **Web Scraping**: Extract content from any URL with intelligent content detection
- 📊 **Statistics Dashboard**: Real-time statistics on scraped content
- 🎨 **Clean UI**: Modern, responsive interface built with vanilla JavaScript
- 💾 **Data Storage**: SQLite database for efficient content management
- 📤 **Export Functionality**: Export scraped data as JSON
- 🔍 **Content Classification**: Automatic categorization (articles, tutorials, documentation, etc.)
- ⚡ **Bulk Scraping**: Scrape multiple URLs at once with rate limiting
- 🎯 **Default Sources**: Quick-start with pre-configured AI training material sources

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/piticko-kvalita/scraper.git
cd scraper
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

The easiest way to get started:

```bash
python run.py
```

This script will:
- Check your Python version
- Install dependencies if needed
- Initialize the database
- Start the web server

### Manual Setup

Alternatively, you can run the application manually:

#### Running the Application

Start the web server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Using the Web Interface

1. **Scrape a Single URL**:
   - Enter a URL in the input field
   - Click "Scrape" button
   - View the scraped content in the content list

2. **Scrape Default Sources**:
   - Click "Scrape Default Sources" to scrape pre-configured AI training materials from Wikipedia

3. **Bulk Scraping**:
   - Click "Bulk Scrape"
   - Enter multiple URLs (one per line)
   - Click "Scrape All"

4. **View Content**:
   - Click on any content item to view full details
   - See title, content type, word count, and full text

5. **Export Data**:
   - Click "Export JSON" to download all scraped content

### Programmatic Usage

You can also use the scraper in your Python code. See `example.py` for examples:

```python
from scraper import AIContentScraper
from models import init_db

init_db()
scraper = AIContentScraper()

# Scrape a URL
result = scraper.scrape_and_save("https://example.com/article")
print(result)
```

### API Endpoints

The application provides a RESTful API:

- `POST /api/scrape` - Scrape a single URL
  ```json
  {"url": "https://example.com"}
  ```

- `POST /api/scrape-multiple` - Scrape multiple URLs
  ```json
  {"urls": ["https://example1.com", "https://example2.com"]}
  ```

- `GET /api/content` - Get all scraped content

- `GET /api/content/<id>` - Get specific content by ID

- `DELETE /api/content/<id>` - Delete content by ID

- `GET /api/statistics` - Get scraping statistics

- `GET /api/export` - Export all data as JSON

## Configuration

Edit `config.py` to customize:

- `DATABASE_PATH`: Location of SQLite database
- `USER_AGENT`: User agent string for web requests
- `REQUEST_TIMEOUT`: Timeout for web requests (seconds)
- `RATE_LIMIT_DELAY`: Delay between bulk requests (seconds)
- `DEFAULT_SOURCES`: List of default URLs to scrape

## Project Structure

```
scraper/
├── app.py              # Flask web application
├── scraper.py          # Core scraping functionality
├── models.py           # Database models
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── run.py              # Quick start script
├── example.py          # Programmatic usage examples
├── templates/
│   └── index.html      # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css   # Stylesheet
│   └── js/
│       └── app.js      # Frontend JavaScript
└── README.md           # This file
```

## Technologies Used

- **Backend**: Flask, SQLAlchemy, BeautifulSoup4, Requests
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: SQLite
- **Web Scraping**: BeautifulSoup4, lxml

## Features in Detail

### Intelligent Content Extraction

The scraper automatically:
- Detects and extracts page titles
- Identifies main content areas
- Removes navigation, footers, and scripts
- Cleans up whitespace and formatting
- Calculates word counts

### Content Classification

Automatically categorizes content as:
- **Tutorial**: Guides and how-to articles
- **Documentation**: Technical documentation
- **Article**: Blog posts and articles
- **Wiki**: Wikipedia and wiki pages
- **General**: Other content types

### Data Management

- Prevents duplicate scraping of the same URL
- Updates existing content when re-scraped
- Stores metadata (title, URL, content type, word count, timestamp)
- Provides efficient querying and retrieval

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
## 🌐 Universal AI Materials Scraper

The **Universal Scraper** extracts ALL types of materials needed for AI training in a single operation!

### Supported Material Types (12 Total)

1. **📝 Text/NLP** - Articles, documentation, blog posts for language models
2. **🖼️ Images** - Photos, diagrams, illustrations for computer vision
3. **🎥 Videos** - Video files and embeds for video understanding AI
4. **🎵 Audio** - Audio files (MP3, WAV, etc.) for speech/music AI
5. **💻 Code** - Code snippets in 15+ languages for code generation AI
6. **📊 Datasets** - CSV, JSON, Excel files for direct ML training
7. **📄 PDFs** - Documents for document AI and OCR
8. **📋 Tables** - HTML tables for tabular data AI
9. **❓ Q&A Pairs** - Question-answer pairs for chatbot training
10. **💬 Dialogues** - Conversations for dialogue AI
11. **📜 Transcripts** - Video/audio transcripts for NLU
12. **🏷️ Annotations** - Pre-labeled data for supervised learning

### Quick Start

```bash
# Via Web UI
python run.py
# Click "🌐 Universal Scraper (All Materials)"
# Enter URL and scrape!

# Via Python
from universal_scraper import get_universal_scraper

scraper = get_universal_scraper()
materials = scraper.scrape_all_materials("https://example.com")
scraper.save_to_db(materials)

# Via API
curl -X POST http://localhost:5000/api/scrape/universal \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### See Complete Guide

For detailed information about all material types, use cases, and training formats:
👉 **[AI Materials Guide](AI_MATERIALS_GUIDE.md)**

### What Makes This Complete?

✅ Covers **all major AI domains**: Language, Vision, Speech, Code, Data, Documents, Conversations
✅ Extracts **12 distinct material types** in one operation
✅ Calculates **richness score** based on material diversity
✅ Exports in **training-ready formats**
✅ Shows which material types were found
✅ No manual configuration needed

### AI Use Cases Covered

- 🗣️ **Language Models** (GPT, BERT): Text, Q&A, dialogues
- 👁️ **Computer Vision** (CNN, YOLO): Images, videos, annotations
- 🎵 **Speech AI** (Whisper, TTS): Audio, transcripts
- 💻 **Code AI** (Codex, CodeLlama): Code snippets, documentation
- 📊 **Data Science AI** (TabNet): Tables, datasets
- 📄 **Document AI** (LayoutLM): PDFs, structured documents
- 💬 **Conversational AI** (ChatGPT): Dialogues, Q&A
- 🌐 **Multimodal AI** (CLIP, Flamingo): Images+text, videos+transcripts

