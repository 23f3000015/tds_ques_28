from flask import Flask, request, Response, stream_with_context
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

    @stream_with_context
    def generate():
        try:
            # ✅ Immediate first chunk
            yield 'data: {"choices":[{"delta":{"content":""}}]}\n\n'
            time.sleep(0.05)

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            text = completion.choices[0].message.content

            # 🔥 Split into 200-character chunks
            chunk_size = 200
            for i in range(0, len(text), chunk_size):
                part = text[i:i+chunk_size]

                payload = {
                    "choices": [
                        {"delta": {"content": part}}
                    ]
                }

                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.02)  # force separate network flush

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f'data: {{"error":"{str(e)}"}}\n\n'

    return Response(
        generate(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        },
        direct_passthrough=True
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)
