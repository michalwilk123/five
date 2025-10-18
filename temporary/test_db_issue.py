#!/usr/bin/env python3
"""Test script to isolate database setup issue"""
from pathlib import Path
import tempfile
import shutil

from five_cli.db_models import db

def test_generate_mapping_issue():
    """Reproduce the database setup issue"""
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / 'test.db'

    try:
        print(f"Testing database setup at {db_path}")
        print(f"DB provider before bind: {db.provider}")
        print(f"DB schema before bind: {db.schema}")

        # This is what connect() does
        db.bind(provider='sqlite', filename=str(db_path), create_db=True)
        print(f"DB bound successfully")
        print(f"DB provider after bind: {db.provider}")

        # This should fail with "no such table: Commit" if check_tables=True (default)
        print("\nCalling generate_mapping(create_tables=False)...")
        db.generate_mapping(create_tables=False)
        print("SUCCESS: generate_mapping(create_tables=False) completed")

        print(f"\nDB schema after first mapping: {db.schema}")

        # This would fail with "Mapping was already generated"
        print("\nCalling generate_mapping(create_tables=True)...")
        db.generate_mapping(create_tables=True)
        print("SUCCESS: generate_mapping(create_tables=True) completed")

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
    test_generate_mapping_issue()
