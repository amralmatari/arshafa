#!/usr/bin/env python3
"""
Arshafa Document Management System
Installation Script
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def create_virtual_environment():
    """Create virtual environment"""
    if os.path.exists('venv'):
        print("📁 Virtual environment already exists")
        return True
    
    return run_command('python -m venv venv', 'Creating virtual environment')

def activate_virtual_environment():
    """Get activation command for virtual environment"""
    if os.name == 'nt':  # Windows
        return 'venv\\Scripts\\activate'
    else:  # Linux/Mac
        return 'source venv/bin/activate'

def install_dependencies():
    """Install Python dependencies"""
    pip_cmd = 'venv\\Scripts\\pip' if os.name == 'nt' else 'venv/bin/pip'
    return run_command(f'{pip_cmd} install -r requirements.txt', 'Installing dependencies')

def setup_environment_file():
    """Setup environment configuration file"""
    if os.path.exists('.env'):
        print("📁 Environment file already exists")
        return True
    
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("✅ Environment file created from template")
        print("⚠️  Please edit .env file with your configuration")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'app/static/uploads',
        'backups',
        'search_index',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def setup_database():
    """Setup database and run migrations"""
    flask_cmd = 'venv\\Scripts\\flask' if os.name == 'nt' else 'venv/bin/flask'
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = 'run.py'
    
    commands = [
        (f'{flask_cmd} db init', 'Initializing database migrations'),
        (f'{flask_cmd} db migrate -m "Initial migration"', 'Creating initial migration'),
        (f'{flask_cmd} db upgrade', 'Applying database migrations'),
        (f'{flask_cmd} init-db', 'Initializing default data')
    ]
    
    for command, description in commands:
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, env=env)
            print(f"✅ {description} completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  {description} failed (this might be normal): {e.stderr}")
    
    return True

def print_success_message():
    """Print installation success message"""
    activation_cmd = activate_virtual_environment()
    
    print("\n" + "="*60)
    print("🎉 Arshafa Document Management System installed successfully!")
    print("="*60)
    print("\n📋 Next steps:")
    print(f"1. Activate virtual environment: {activation_cmd}")
    print("2. Edit .env file with your configuration")
    print("3. Run the application: python run.py")
    print("\n🔑 Default login credentials:")
    print("   Admin: admin / admin123")
    print("   User:  user / user123")
    print("   Viewer: viewer / viewer123")
    print("\n🌐 Application will be available at: http://localhost:5000")
    print("\n📚 For more information, see README.md")
    print("="*60)

def main():
    """Main installation function"""
    print("🚀 Installing Arshafa Document Management System")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment file
    if not setup_environment_file():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("⚠️  Database setup had issues, but installation can continue")
    
    # Print success message
    print_success_message()

if __name__ == '__main__':
    main()
