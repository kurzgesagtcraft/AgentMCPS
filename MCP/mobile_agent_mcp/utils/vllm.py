import requests
import base64
import os

class MLLMWrapper:
    def __init__(self, api_key, base_url, model):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def predict_mm(self, prompt, image_paths):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        content = [{"type": "text", "text": prompt}]
        for path in image_paths:
            base64_image = self.encode_image(path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            })

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 1024
        }

        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            output = result['choices'][0]['message']['content']
            return output, result['choices'][0]['message'], True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return "", None, False