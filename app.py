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
            # Get full response first (non-streaming)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            full_text = completion.choices[0].message.content

            # Split into words to force multiple chunks
            words = full_text.split()

            for word in words:
                payload = {
                    "choices": [
                        {
                            "delta": {
                                "content": word + " "
                            }
                        }
                    ]
                }

                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.02)  # Force progressive streaming

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
