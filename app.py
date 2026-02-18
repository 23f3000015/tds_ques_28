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

    def event_stream():
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            for chunk in response:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if not delta or not delta.content:
                    continue

                payload = {
                    "choices": [
                        {
                            "delta": {
                                "content": delta.content
                            }
                        }
                    ]
                }

                yield f"data: {json.dumps(payload)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_payload = {
                "choices": [
                    {
                        "delta": {
                            "content": f"Error: {str(e)}"
                        }
                    }
                ]
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return Response(
        event_stream(),
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)
