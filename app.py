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

    data = request.json
    prompt = data.get("prompt")

    def generate():
        try:
            # ✅ 1. Instant first chunk (fix latency)
            yield 'data: {"content": " "}\n\n'
            time.sleep(0.01)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            chunk_count = 1

            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content

                    yield f'data: {json.dumps({"content": content})}\n\n'
                    chunk_count += 1

                    time.sleep(0.01)

            # ✅ Ensure minimum 5 chunks
            while chunk_count < 5:
                yield 'data: {"content": " "}\n\n'
                chunk_count += 1
                time.sleep(0.01)

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
