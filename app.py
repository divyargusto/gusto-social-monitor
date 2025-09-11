#!/usr/bin/env python3
"""
Main entry point for Gusto Social Media Monitor Flask App
This file is required for hosting platforms like Render, Railway, etc.
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
