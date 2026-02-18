from flask import Flask, request, Response
from flask_cors import CORS
import os
import json
import requests

app = Flask(__name__)
CORS(app)

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")

@app.route("/stream", methods=["POST"])
def stream():
    data = request.get_json()
    prompt = data.get("prompt", "")

    def generate():
        try:
            # ✅ Immediate first chunk (latency requirement)
            yield 'data: {"choices":[{"delta":{"content":"Starting..."}}]}\n\n'

            url = "https://aipipe.org/openrouter/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {AIPIPE_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "openai/gpt-4.1-nano",
                "messages": [{"role": "user", "content": prompt}],
                "stream": True
            }

            with requests.post(url, headers=headers, json=payload, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode("utf-8")

                        if decoded.startswith("data: "):
                            yield decoded + "\n\n"

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
