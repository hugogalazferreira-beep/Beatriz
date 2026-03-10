import requests
import time
import subprocess
import os

def test_backend():
    print("Starting FastAPI server...")
    # Start the server in the background
    process = subprocess.Popen(["uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"])

    # Wait for the server to start (increased wait time)
    for i in range(10):
        try:
            requests.get("http://127.0.0.1:8000/", timeout=1)
            print("Server is up!")
            break
        except requests.exceptions.ConnectionError:
            print(f"Waiting for server... ({i+1}/10)")
            time.sleep(1)

    try:
        # Test root endpoint
        print("Testing root endpoint...")
        response = requests.get("http://127.0.0.1:8000/")
        print(f"Root response: {response.json()}")
        assert response.status_code == 200

        # Test static file serving
        print("Testing static file serving...")
        response = requests.get("http://127.0.0.1:8000/static/widget.js")
        assert response.status_code == 200
        print("Static file serving works!")

        # Note: We can't easily test the /api/chat endpoint without real API keys
        print("Testing chat endpoint (expecting error due to missing Gemini API key)...")
        response = requests.post("http://127.0.0.1:8000/api/chat", json={"message": "Olá"})
        print(f"Chat response (expected error): {response.status_code}")
        assert response.status_code in [500, 422]

    finally:
        print("Stopping FastAPI server...")
        process.terminate()

if __name__ == "__main__":
    test_backend()
