#!/usr/bin/env python3
"""Test script to verify the solution"""
from pathlib import Path
import tempfile
import shutil

from five_cli.db_models import db, Commit

def test_correct_approach():
    """Test the correct way to setup database"""
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / 'test.db'

    try:
        print(f"Testing database setup at {db_path}")

        # Bind the database
        db.bind(provider='sqlite', filename=str(db_path), create_db=True)
        print(f"DB bound successfully")

        # Generate mapping AND create tables in one call
        print("\nCalling generate_mapping(create_tables=True, check_tables=False)...")
        db.generate_mapping(create_tables=True, check_tables=False)
        print("SUCCESS: Tables created")

        # Verify we can query
        print("\nVerifying database works...")
        commits = list(Commit.select())
        print(f"Number of commits: {len(commits)}")
        print("SUCCESS: Database is working correctly")

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db.provider:
            db.disconnect()
            db.provider = db.schema = None
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    test_correct_approach()
