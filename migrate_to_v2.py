#!/usr/bin/env python3
"""
TravelNet Portal v2.0 Migration Script

This script helps migrate from the old monolithic structure to the new
modular architecture while preserving existing configurations.
"""

import os
import shutil
import sys
from pathlib import Path

def main():
    """Main migration function"""
    print("TravelNet Portal v2.0 Migration Script")
    print("=" * 50)
    
    # Check if old app.py exists
    old_app = Path("app.py")
    if old_app.exists():
        print("✓ Found old app.py file")
        
        # Backup old file
        backup_path = Path("app_v1_backup.py")
        shutil.copy2(old_app, backup_path)
        print(f"✓ Backed up old app.py to {backup_path}")
        
        # Remove old app.py
        old_app.unlink()
        print("✓ Removed old app.py")
    else:
        print("ℹ No old app.py found - migration may already be complete")
    
    # Check if new structure exists
    app_dir = Path("app")
    if app_dir.exists():
        print("✓ New modular structure detected")
    else:
        print("✗ New modular structure not found")
        print("Please ensure you have the new app/ directory structure")
        return False
    
    # Update systemd service file if it exists
    service_files = [
        Path("/etc/systemd/system/travelnet.service"),
        Path("/opt/travelnet/travelnet.service")
    ]
    
    for service_file in service_files:
        if service_file.exists():
            print(f"✓ Found service file: {service_file}")
            update_service_file(service_file)
    
    # Update any startup scripts
    startup_scripts = [
        Path("start.sh"),
        Path("/opt/travelnet/start.sh")
    ]
    
    for script in startup_scripts:
        if script.exists():
            print(f"✓ Found startup script: {script}")
            update_startup_script(script)
    
    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Test the new application: python run.py")
    print("2. Update any custom scripts to use 'python run.py' instead of 'python app.py'")
    print("3. Restart the systemd service if applicable")
    print("4. Review the new API documentation at /api/v1/docs")
    
    return True

def update_service_file(service_file):
    """Update systemd service file to use new entry point"""
    try:
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Replace old app.py with run.py
        updated_content = content.replace('app.py', 'run.py')
        
        if updated_content != content:
            # Backup original
            backup_file = service_file.with_suffix('.service.backup')
            shutil.copy2(service_file, backup_file)
            
            # Write updated content
            with open(service_file, 'w') as f:
                f.write(updated_content)
            
            print(f"  ✓ Updated service file (backup: {backup_file})")
        else:
            print(f"  ℹ Service file already up to date")
            
    except Exception as e:
        print(f"  ✗ Error updating service file: {e}")

def update_startup_script(script_file):
    """Update startup script to use new entry point"""
    try:
        with open(script_file, 'r') as f:
            content = f.read()
        
        # Replace old app.py with run.py
        updated_content = content.replace('python app.py', 'python run.py')
        updated_content = updated_content.replace('python3 app.py', 'python3 run.py')
        
        if updated_content != content:
            # Backup original
            backup_file = script_file.with_suffix('.sh.backup')
            shutil.copy2(script_file, backup_file)
            
            # Write updated content
            with open(script_file, 'w') as f:
                f.write(updated_content)
            
            print(f"  ✓ Updated startup script (backup: {backup_file})")
        else:
            print(f"  ℹ Startup script already up to date")
            
    except Exception as e:
        print(f"  ✗ Error updating startup script: {e}")

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)