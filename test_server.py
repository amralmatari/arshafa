#!/usr/bin/env python3
"""
Test server with debug output
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    print("✓ App imported successfully")
    
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    print("✓ App created successfully")
    
    print("Starting server on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
