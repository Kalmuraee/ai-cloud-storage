"""Test configuration settings."""

import os
from pathlib import Path

# API endpoints
API_PREFIX = "/api/v1"
AUTH_TOKEN = f"{API_PREFIX}/auth/token"  # Changed from /login to /token
STORAGE_UPLOAD = f"{API_PREFIX}/storage/upload"
STORAGE_DOWNLOAD = f"{API_PREFIX}/storage/download"
STORAGE_LIST = f"{API_PREFIX}/storage/list"
STORAGE_DUPLICATES = f"{API_PREFIX}/storage/duplicates"
STORAGE_METADATA = f"{API_PREFIX}/storage/metadata"

# Test configuration
TEST_HOST = "http://localhost:8000"
TEST_USER = "test@example.com"
TEST_USERNAME = "testuser"  # Added username field
TEST_PASSWORD = "TestPassword123"  # Added uppercase letter

# Test file paths
TEST_FILES_DIR = Path(__file__).parent / "test_files"
TEST_FILES_DIR.mkdir(exist_ok=True)

# Create test files if they don't exist
SAMPLE_TEXT = TEST_FILES_DIR / "sample.txt"
if not SAMPLE_TEXT.exists():
    with open(SAMPLE_TEXT, "w") as f:
        f.write("This is a sample text file for testing.")

SAMPLE_IMAGE = TEST_FILES_DIR / "sample.jpg"
if not SAMPLE_IMAGE.exists():
    # Create a simple binary file as a placeholder
    with open(SAMPLE_IMAGE, "wb") as f:
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C")  # JPEG header
