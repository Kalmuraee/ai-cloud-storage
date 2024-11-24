"""
Performance testing configuration using Locust.
"""
from locust import HttpUser, task, between
import json
import random

class AICloudStorageUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login at start of test."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def upload_file(self):
        """Test file upload performance."""
        files = {
            'file': ('test.txt', 'Test content for performance testing', 'text/plain')
        }
        self.client.post(
            "/api/v1/storage/upload",
            files=files,
            headers=self.headers
        )
    
    @task(5)
    def search_files(self):
        """Test search performance."""
        queries = ["test", "document", "important", "meeting", "report"]
        self.client.get(
            f"/api/v1/search?q={random.choice(queries)}",
            headers=self.headers
        )
    
    @task(2)
    def process_file(self):
        """Test AI processing performance."""
        self.client.post(
            "/api/v1/ai/process",
            json={"file_id": "test_file_id", "operations": ["summarize", "analyze"]},
            headers=self.headers
        )
    
    @task(4)
    def vector_search(self):
        """Test vector search performance."""
        self.client.post(
            "/api/v1/search/semantic",
            json={"query": "important documents about machine learning"},
            headers=self.headers
        )
    
    @task(1)
    def batch_process(self):
        """Test batch processing performance."""
        self.client.post(
            "/api/v1/ai/batch-process",
            json={
                "file_ids": ["id1", "id2", "id3"],
                "operations": ["summarize"]
            },
            headers=self.headers
        )
