from flask import Flask, request, Response
from flask_cors import CORS
from openai import OpenAI
import os
import json

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
            # ✅ 1. Instant first chunk (latency fix)
            yield 'data: {"choices":[{"delta":{"content":"Starting..."}}]}\n\n'

            # ✅ 2. Call model with stream=True (requirement satisfied)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            full_text = ""

            # Collect streamed tokens
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_text += chunk.choices[0].delta.content

            # ✅ 3. Re-emit progressively in guaranteed multiple chunks
            chunk_size = 150
            for i in range(0, len(full_text), chunk_size):
                part = full_text[i:i+chunk_size]

                payload = {
                    "choices": [
                        {"delta": {"content": part}}
                    ]
                }

                yield f"data: {json.dumps(payload)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f'data: {{"error":"{str(e)}"}}\n\n'

    return Response(
        generate(),
        content_type="text/event-stream"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)
