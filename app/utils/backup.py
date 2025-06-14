"""
Backup utilities for database and file backups
"""

import os
import datetime
import shutil
import zipfile
from flask import current_app

def create_backup():
    """Create a database backup and return the backup file path"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"arshafa_backup_{timestamp}.zip"
    backup_path = os.path.join(current_app.config['BACKUP_FOLDER'], backup_filename)
    
    # Create zip file
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add database file
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            zipf.write(db_path, os.path.basename(db_path))
        
        # Add uploaded files
        for root, _, files in os.walk(current_app.config['UPLOAD_FOLDER']):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
                zipf.write(file_path, os.path.join('uploads', arcname))
    
    return backup_path