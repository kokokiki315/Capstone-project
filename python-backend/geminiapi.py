import os, requests, json, base64

api_key = os.getenv("OPENROUTER_API_KEY")
file_path = "screenshot_person0.jpg"

with open(file_path, "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode("utf-8")

image_data_url = f"data:image/jpeg;base64,{img_base64}"

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this CCTV image in detail:"},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ],
    },
)

response_data = response.json()

try:
    # Extract the model text
    content = response_data["choices"][0]["message"]["content"].strip()
    print(content)
except KeyError:
    print("Error: Unexpected response format")
    print(response_data)