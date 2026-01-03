"""Flask web application for AI training materials scraper."""
from flask import Flask, render_template, request, jsonify, send_file
import json
from io import BytesIO
import config
from models import init_db
from scraper import (
    AIContentScraper,
    get_all_content,
    get_content_by_id,
    delete_content,
    get_statistics,
)
from auto_gather import get_auto_gatherer, discover_related_urls
from ai_helper import get_ai_helper
from settings_manager import get_settings_manager
from image_scraper import get_image_scraper
from code_scraper import get_code_scraper
from export_manager import get_exporter

app = Flask(__name__)
app.config.from_object(config)

# Initialize database
init_db()

# Initialize settings manager
settings_mgr = get_settings_manager()

# Initialize AI helper
ai_helper = get_ai_helper(settings_mgr.get_openrouter_key())

# Initialize scraper with AI if enabled
use_ai = settings_mgr.is_ai_enabled()
scraper = AIContentScraper(use_ai=use_ai, ai_helper=ai_helper if use_ai else None)

# Initialize specialized scrapers
image_scraper = get_image_scraper()
code_scraper = get_code_scraper()

# Initialize exporter
exporter = get_exporter()

# Initialize auto gatherer
auto_gatherer = get_auto_gatherer()

@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")

@app.route("/settings")
def settings_page():
    """Settings page."""
    return render_template("settings.html")

@app.route("/api/scrape", methods=["POST"])
def scrape():
    """API endpoint to scrape a URL."""
    data = request.get_json()
    url = data.get("url")
    
    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400
    
    # Reinitialize scraper with current AI settings
    use_ai = settings_mgr.is_ai_enabled()
    ai_helper_instance = get_ai_helper(settings_mgr.get_openrouter_key())
    scraper_instance = AIContentScraper(use_ai=use_ai, ai_helper=ai_helper_instance if use_ai else None)
    
    result = scraper_instance.scrape_and_save(url, source_type="manual")
    return jsonify(result)

@app.route("/api/scrape-multiple", methods=["POST"])
def scrape_multiple():
    """API endpoint to scrape multiple URLs."""
    data = request.get_json()
    urls = data.get("urls", [])
    
    if not urls:
        return jsonify({"success": False, "message": "URLs are required"}), 400
    
    results = scraper.scrape_multiple(urls, source_type="manual")
    return jsonify({"results": results})

@app.route("/api/content", methods=["GET"])
def get_content():
    """Get all scraped content."""
    content = get_all_content()
    return jsonify({"content": content})

@app.route("/api/content/<int:content_id>", methods=["GET"])
def get_single_content(content_id):
    """Get specific content by ID."""
    content = get_content_by_id(content_id)
    if content:
        return jsonify({"content": content})
    return jsonify({"error": "Content not found"}), 404

@app.route("/api/content/<int:content_id>", methods=["DELETE"])
def delete_single_content(content_id):
    """Delete content by ID."""
    if delete_content(content_id):
        return jsonify({"success": True, "message": "Content deleted"})
    return jsonify({"success": False, "message": "Content not found"}), 404

@app.route("/api/statistics", methods=["GET"])
def statistics():
    """Get scraping statistics."""
    stats = get_statistics()
    return jsonify(stats)

@app.route("/api/export", methods=["GET"])
def export_data():
    """Export all data as JSON."""
    content = get_all_content()
    
    # Create JSON file in memory
    json_data = json.dumps(content, indent=2)
    buffer = BytesIO()
    buffer.write(json_data.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name='scraped_data.json'
    )

# Auto-gathering endpoints

@app.route("/api/auto-gather/status", methods=["GET"])
def auto_gather_status():
    """Get auto-gather status."""
    status = auto_gatherer.get_status()
    return jsonify(status)

@app.route("/api/auto-gather/start", methods=["POST"])
def auto_gather_start():
    """Start automatic gathering."""
    success = auto_gatherer.start()
    if success:
        return jsonify({"success": True, "message": "Auto-gathering started"})
    return jsonify({"success": False, "message": "Already running"})

@app.route("/api/auto-gather/stop", methods=["POST"])
def auto_gather_stop():
    """Stop automatic gathering."""
    success = auto_gatherer.stop()
    if success:
        return jsonify({"success": True, "message": "Auto-gathering stopped"})
    return jsonify({"success": False, "message": "Not running"})

@app.route("/api/auto-gather/scrape-now", methods=["POST"])
def auto_gather_scrape_now():
    """Manually trigger auto-gathering."""
    result = auto_gatherer.scrape_now()
    return jsonify(result)

@app.route("/api/auto-gather/sources", methods=["GET"])
def auto_gather_get_sources():
    """Get auto-gathering sources."""
    sources = auto_gatherer.get_sources()
    return jsonify({"sources": sources})

@app.route("/api/auto-gather/sources", methods=["POST"])
def auto_gather_add_source():
    """Add a source to auto-gathering."""
    data = request.get_json()
    url = data.get("url")
    
    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400
    
    auto_gatherer.add_source(url)
    return jsonify({"success": True, "message": "Source added"})

@app.route("/api/auto-gather/sources/<path:url>", methods=["DELETE"])
def auto_gather_remove_source(url):
    """Remove a source from auto-gathering."""
    auto_gatherer.remove_source(url)
    return jsonify({"success": True, "message": "Source removed"})

@app.route("/api/discover-urls", methods=["POST"])
def discover_urls():
    """Discover related URLs from base URLs."""
    data = request.get_json()
    base_urls = data.get("urls", [])
    
    if not base_urls:
        return jsonify({"success": False, "message": "Base URLs required"}), 400
    
    discovered = discover_related_urls(base_urls)
    return jsonify({"success": True, "urls": discovered})

# Settings endpoints

@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get current settings."""
    return jsonify(settings_mgr.get_all())

@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Update settings."""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    # Update settings
    settings_mgr.update_multiple(data)
    
    # Reinitialize AI helper if API key changed
    if "openrouter_api_key" in data:
        global ai_helper
        ai_helper = get_ai_helper(data["openrouter_api_key"])
    
    return jsonify({"success": True, "message": "Settings updated"})

# AI-powered endpoints

@app.route("/api/ai/suggest-urls", methods=["POST"])
def ai_suggest_urls():
    """Use AI to suggest URLs for a topic."""
    data = request.get_json()
    topic = data.get("topic")
    count = data.get("count", 10)
    
    if not topic:
        return jsonify({"success": False, "message": "Topic is required"}), 400
    
    ai = get_ai_helper(settings_mgr.get_openrouter_key())
    if not ai.is_configured():
        return jsonify({"success": False, "message": "AI not configured. Please add OpenRouter API key in settings."}), 400
    
    urls = ai.suggest_ai_urls(topic, count)
    return jsonify({"success": True, "urls": urls})

@app.route("/api/ai/related-queries", methods=["POST"])
def ai_related_queries():
    """Use AI to suggest related search queries."""
    data = request.get_json()
    topic = data.get("topic")
    
    if not topic:
        return jsonify({"success": False, "message": "Topic is required"}), 400
    
    ai = get_ai_helper(settings_mgr.get_openrouter_key())
    if not ai.is_configured():
        return jsonify({"success": False, "message": "AI not configured"}), 400
    
    queries = ai.suggest_related_queries(topic)
    return jsonify({"success": True, "queries": queries})

@app.route("/api/ai/status", methods=["GET"])
def ai_status():
    """Get AI configuration status."""
    ai = get_ai_helper(settings_mgr.get_openrouter_key())
    return jsonify({
        "configured": ai.is_configured(),
        "enabled": settings_mgr.is_ai_enabled()
    })

# Specialized scraper endpoints

@app.route("/api/scrape/images", methods=["POST"])
def scrape_images():
    """Scrape URL specifically for images."""
    data = request.get_json()
    url = data.get("url")
    min_images = data.get("min_images", 5)
    
    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400
    
    result = image_scraper.scrape_images(url, min_images)
    if "error" not in result:
        save_result = image_scraper.save_to_db(result)
        return jsonify(save_result)
    
    return jsonify({"success": False, "message": result["error"]})

@app.route("/api/scrape/code", methods=["POST"])
def scrape_code():
    """Scrape URL specifically for code."""
    data = request.get_json()
    url = data.get("url")
    min_snippets = data.get("min_snippets", 3)
    
    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400
    
    result = code_scraper.scrape_code(url, min_snippets)
    if "error" not in result:
        save_result = code_scraper.save_to_db(result)
        return jsonify(save_result)
    
    return jsonify({"success": False, "message": result["error"]})

# Enhanced export endpoints

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Export data as CSV."""
    content_type = request.args.get("content_type")
    min_quality = request.args.get("min_quality", type=float)
    
    csv_data = exporter.export_csv(content_type, min_quality)
    buffer = BytesIO(csv_data)
    
    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'scraped_data_{content_type or "all"}.csv'
    )

@app.route("/api/export/images", methods=["GET"])
def export_images():
    """Export only image data."""
    min_quality = request.args.get("min_quality", type=float)
    
    image_data = exporter.export_images_only(min_quality)
    return jsonify(image_data)

@app.route("/api/export/code", methods=["GET"])
def export_code():
    """Export only code snippets."""
    language = request.args.get("language")
    min_quality = request.args.get("min_quality", type=float)
    
    code_data = exporter.export_code_only(language, min_quality)
    return jsonify(code_data)

@app.route("/api/export/by-type", methods=["GET"])
def export_by_type():
    """Export data grouped by content type."""
    data = exporter.export_by_content_type()
    return jsonify(data)

@app.route("/api/export/training", methods=["GET"])
def export_training():
    """Export data in training-ready format."""
    content_type = request.args.get("content_type")
    
    training_data = exporter.export_training_dataset(content_type)
    
    # Return as downloadable JSON
    json_str = json.dumps(training_data, indent=2)
    buffer = BytesIO(json_str.encode('utf-8'))
    
    return send_file(
        buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'training_data_{content_type or "all"}.json'
    )

@app.route("/api/export/filtered", methods=["GET"])
def export_filtered():
    """Export filtered data as JSON."""
    content_type = request.args.get("content_type")
    min_quality = request.args.get("min_quality", type=float)
    format_type = request.args.get("format", "json")  # json or csv
    
    if format_type == "csv":
        csv_data = exporter.export_csv(content_type, min_quality)
        buffer = BytesIO(csv_data)
        return send_file(
            buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'filtered_data.csv'
        )
    else:
        json_data = exporter.export_json(content_type, min_quality)
        buffer = BytesIO(json_data)
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'filtered_data.json'
        )

if __name__ == "__main__":
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
