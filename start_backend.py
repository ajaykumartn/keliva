"""
Startup script for KeLiva backend
Run this from the project root directory
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add backend directory to Python path for relative imports
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# Change to backend directory for relative file paths
os.chdir(backend_path)

# Now import and run the backend
from main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting KeLiva Backend Server...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path includes: {project_root}")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
