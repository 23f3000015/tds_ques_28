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

    data = request.json
    prompt = data.get("prompt")

    def generate():
        try:
            # 🔥 Instant first chunk (latency fix)
            yield 'data: {"content": "Starting..."}\n\n'
            time.sleep(0.05)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content

                    # 🔥 Break into smaller pieces manually
                    for i in range(0, len(text), 5):
                        piece = text[i:i+5]
                        yield f'data: {json.dumps({"content": piece})}\n\n'
                        time.sleep(0.02)

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        },
        direct_passthrough=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)

