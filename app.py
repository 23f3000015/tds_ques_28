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
            # Immediate first chunk
            yield 'data: {"choices":[{"delta":{"content":""}}]}\n\n'

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            text = completion.choices[0].message.content

            for word in text.split():
                payload = {
                    "choices": [
                        {"delta": {"content": word + " "}}
                    ]
                }
                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(0.01)

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f'data: {{"error":"{str(e)}"}}\n\n'

    return Response(
        generate(),
        content_type="text/event-stream"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, threaded=True)
