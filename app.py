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

app = Flask(__name__)
app.config.from_object(config)

# Initialize database
init_db()

# Initialize scraper
scraper = AIContentScraper()

@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")

@app.route("/api/scrape", methods=["POST"])
def scrape():
    """API endpoint to scrape a URL."""
    data = request.get_json()
    url = data.get("url")
    
    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400
    
    result = scraper.scrape_and_save(url)
    return jsonify(result)

@app.route("/api/scrape-multiple", methods=["POST"])
def scrape_multiple():
    """API endpoint to scrape multiple URLs."""
    data = request.get_json()
    urls = data.get("urls", [])
    
    if not urls:
        return jsonify({"success": False, "message": "URLs are required"}), 400
    
    results = scraper.scrape_multiple(urls)
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

if __name__ == "__main__":
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
