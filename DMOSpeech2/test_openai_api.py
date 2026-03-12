import requests
import json

def test_speech():
    url = "http://localhost:8000/v1/audio/speech"
    payload = {
        "model": "f5-tts",
        "input": "你好，这是一段测试文本，用于验证 OpenAI 兼容接口是否工作正常。",
        "voice": "default",
        "response_format": "wav"
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            with open("test_output.wav", "wb") as f:
                f.write(response.content)
            print("Successfully synthesized audio! Saved to test_output.wav")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Failed to connect: {e}")

def test_models():
    url = "http://localhost:8000/api/models"
    print(f"Sending request to {url}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Available models/voices:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_models()
    test_speech()