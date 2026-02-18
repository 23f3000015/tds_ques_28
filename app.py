from flask import Flask, request, Response
from flask_cors import CORS
from openai import OpenAI
import os
import json
import time

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key=os.getenv("AIPIPE_TOKEN"),
    base_url="https://api.aipipe.org/v1"
)

@app.route("/stream", methods=["POST"])
def stream():
    data = request.get_json()
    prompt = data.get("prompt", "")

    def generate():
        try:
            # 🔥 1. Immediate first chunk (latency fix)
            first = {
                "choices": [{"delta": {"content": ""}}]
            }
            yield f"data: {json.dumps(first)}\n\n"

            # 🔥 2. Padding to force proxy flush
            yield ":" + (" " * 2048) + "\n\n"

            # 🔥 3. Get full completion
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            text = completion.choices[0].message.content

            # 🔥 4. Stream character by character
            for char in text:
                payload = {
                    "choices": [{"delta": {"content": char}}]
                }

                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.005)

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return Response(
        generate(),
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)
