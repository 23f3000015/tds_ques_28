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
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    payload = {
                        "choices": [
                            {
                                "delta": {
                                    "content": chunk.choices[0].delta.content
                                }
                            }
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
