import os
import base64
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

image_path = r"C:\Users\vedaa\OneDrive\Desktop\day-zero\universal-images\acne.jpg"
image_file = open(image_path, "rb").read()
encoded_image = base64.b64encode(image_file).decode("utf-8")

client = Groq()
model = "llama-3.2-90b-vision-preview"   # Updated model name (check current available models)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is the diagnosis?"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
            ]
        }
    ],
    model=model,
)

print(chat_completion.choices[0].message.content)