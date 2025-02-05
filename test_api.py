import requests
import json

BASE_URL = "http://localhost:10000"

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Erro: {str(e)}")

def test_login():
    try:
        data = {
            "username": "seu_email@exemplo.com",
            "password": "sua_senha"
        }
        response = requests.post(f"{BASE_URL}/login", data=data)
        print(f"Login: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    test_health()
    test_login() 