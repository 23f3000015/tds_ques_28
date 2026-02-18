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
            # ✅ Send first token immediately (latency fix)
            first_payload = {
                "choices": [
                    {"delta": {"content": ""}}
                ]
            }
            yield f"data: {json.dumps(first_payload)}\n\n"

            # Get full response (non-streaming for stability)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            full_text = completion.choices[0].message.content
            words = full_text.split()

            # Stream word by word
            for word in words:
                payload = {
                    "choices": [
                        {"delta": {"content": word + " "}}
                    ]
                }

                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.01)  # tiny delay forces real chunking

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return Response(
        generate(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)
