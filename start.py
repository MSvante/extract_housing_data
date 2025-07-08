#!/usr/bin/env python3
"""
Housing Data System Startup Script
Unified script to start different components of the housing data system
"""

import sys
import subprocess
import argparse
import os
import venv
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    return True

def setup_virtual_environment():
    """Create and setup virtual environment if it doesn't exist."""
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return get_venv_python(venv_path)
    
    print("🔧 Creating virtual environment...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created successfully")
        return get_venv_python(venv_path)
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return None

def get_venv_python(venv_path):
    """Get the Python executable path from virtual environment."""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        return venv_path / "bin" / "python"

def check_dependencies(python_executable):
    """Check if required dependencies are installed."""
    project_root = Path(__file__).parent
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print("⚠️  No requirements.txt found")
        return True
    
    print("🔍 Checking installed packages...")
    
    # Check if key packages are installed
    key_packages = ["pandas", "streamlit", "requests", "beautifulsoup4", "duckdb"]
    missing_packages = []
    
    for package in key_packages:
        try:
            result = subprocess.run([
                str(python_executable), "-c", f"import {package}; print('{package} installed')"
            ], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                missing_packages.append(package)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_packages.append(package)
    
    if missing_packages:
        print(f"📦 Installing missing packages: {', '.join(missing_packages)}")
        return install_dependencies(python_executable, requirements_file)
    else:
        print("✅ All key dependencies are installed")
        return True

def install_dependencies(python_executable, requirements_file):
    """Install dependencies from requirements.txt."""
    print("📦 Installing dependencies...")
    try:
        result = subprocess.run([
            str(python_executable), "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories for the project."""
    project_root = Path(__file__).parent
    directories = ["data", "logs"]
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {dir_name}")
        else:
            print(f"✅ Directory exists: {dir_name}")

def setup_project():
    """Complete project setup including virtual environment and dependencies."""
    print("🏠 Housing Data System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup virtual environment
    venv_python = setup_virtual_environment()
    if not venv_python:
        return False
    
    # Check and install dependencies
    if not check_dependencies(venv_python):
        return False
    
    # Create necessary directories
    create_directories()
    
    print("✅ Project setup completed successfully!")
    print("=" * 50)
    return venv_python

def run_pipeline(python_executable=None):
    """Run the data extraction and transformation pipeline."""
    if python_executable is None:
        python_executable = sys.executable
    
    print("🔄 Starting housing data pipeline...")
    result = subprocess.run([
        str(python_executable), 
        str(Path(__file__).parent / "pipeline" / "run_pipeline.py")
    ])
    return result.returncode == 0

def start_app(python_executable=None):
    """Start the Streamlit web application."""
    if python_executable is None:
        python_executable = sys.executable
        
    print("🚀 Starting Streamlit web application...")
    subprocess.run([
        str(python_executable), "-m", "streamlit", "run", 
        str(Path(__file__).parent / "app" / "app_local.py"),
        "--server.headless=false"
    ])

def start_scheduler(python_executable=None):
    """Start the automated scheduler."""
    if python_executable is None:
        python_executable = sys.executable
        
    print("⏰ Starting automated scheduler...")
    subprocess.run([
        str(python_executable),
        str(Path(__file__).parent / "scripts" / "scheduler.py")
    ])

def run_full_setup(python_executable=None):
    """Run pipeline once, then start the app."""
    print("🎯 Running full setup: Pipeline + App")
    success = run_pipeline(python_executable)
    if success:
        print("✅ Pipeline completed successfully!")
        print("🚀 Starting web application...")
        start_app(python_executable)
    else:
        print("❌ Pipeline failed!")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Housing Data System Control")
    parser.add_argument(
        "command", 
        choices=["pipeline", "app", "scheduler", "full", "setup"],
        help="Command to run: setup (setup environment), pipeline (run once), app (start webapp), scheduler (automated), full (pipeline + app)"
    )
    parser.add_argument(
        "--skip-setup", 
        action="store_true",
        help="Skip the automatic setup and use system Python"
    )
    
    args = parser.parse_args()
    
    # Handle setup command separately
    if args.command == "setup":
        setup_project()
        return
    
    # Determine which Python executable to use
    python_executable = sys.executable
    if not args.skip_setup:
        # Try to setup/verify environment
        venv_python = setup_project()
        if venv_python and venv_python.exists():
            python_executable = venv_python
        else:
            print("⚠️  Setup failed, falling back to system Python")
    
    print("\n🏠 Housing Data System")
    print("=" * 50)
    
    if args.command == "pipeline":
        success = run_pipeline(python_executable)
        sys.exit(0 if success else 1)
    elif args.command == "app":
        start_app(python_executable)
    elif args.command == "scheduler":
        start_scheduler(python_executable)
    elif args.command == "full":
        run_full_setup(python_executable)

if __name__ == "__main__":
    main()
