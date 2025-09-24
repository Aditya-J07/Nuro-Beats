import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
import routes  # Import routes to register them

# Export the Flask app for Vercel (this is the WSGI entry point)
application = app

if __name__ == "__main__":
    app.run(debug=True)