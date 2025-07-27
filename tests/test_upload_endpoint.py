import io
import os
import shutil
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, UploadFile, File, Form
from server.server import app, getDestination

# Create a temp directory for storing uploaded files
TEST_DEST_DIR = Path("test_destination")
TEST_FILE_CONTENT = b"Hello, this is a test file!"

# Override the dependency to use our test directory
app.dependency_overrides[getDestination] = lambda: str(TEST_DEST_DIR)

client = TestClient(app)
# Fixture t o set up and remove the test environment
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Create clean test directory
    if TEST_DEST_DIR.exists():
        shutil.rmtree(TEST_DEST_DIR)
    TEST_DEST_DIR.mkdir(parents=True)
    # Yield to allow the test to run
    yield
    # Teardown: Clean up test directory
    shutil.rmtree(TEST_DEST_DIR)

'''
 Test case to test the upload file endpoint
 This will upload a file to the server and check if it is saved correctly.
'''
def test_upload_file_success():
    file_name = "test.txt"
    sub_path = "test_folder/test.txt"
    # Create a file-like object to simulate an uploaded file with io.BytesIO
    # In our FastAPI implementation we ignore MIME type (file.content_type), but we specify it here for completeness
    # This is allowed as we use the UploadFile type - which provide file.content_type but does not require it
    files = {
        "file": ("test.txt", io.BytesIO(TEST_FILE_CONTENT), "text/plain")
    }
    data = {
        "subPath": sub_path
    }

    response = client.post("/uploadfile", files=files, data=data)
    
    assert response.status_code == 200
    assert f"File '{file_name}' uploaded successfully" in response.json()["message"]

    # Verify file is actually written to disk
    uploaded_file_path = TEST_DEST_DIR / sub_path
    # Ensure the file and directory exists
    assert uploaded_file_path.exists()
    # Ensure the content is correct
    with open(uploaded_file_path, "rb") as f:
        assert f.read() == TEST_FILE_CONTENT
