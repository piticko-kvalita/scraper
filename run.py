#!/usr/bin/env python3
"""
Quick start script for AI Training Materials Scraper.
Run this script to start the scraper web application.
"""
import subprocess
import sys
import os

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        import requests
        import bs4
        import sqlalchemy
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("\n📦 Installing dependencies...")
        return False

def install_dependencies():
    """Install required dependencies."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def initialize_database():
    """Initialize the database."""
    try:
        from models import init_db
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

def start_application():
    """Start the Flask application."""
    print("\n" + "="*60)
    print("🤖 Starting AI Training Materials Scraper...")
    print("="*60)
    print("\n📍 Application will be available at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        sys.exit(0)

def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("🤖 AI Training Materials Scraper - Quick Start")
    print("="*60 + "\n")
    
    # Check Python version
    check_python_version()
    
    # Check and install dependencies
    if not check_dependencies():
        install_dependencies()
    
    # Initialize database
    initialize_database()
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()
