from flask import Flask, request, Response, stream_with_context
import openai
import json
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/stream", methods=["POST"])
def stream():
    data = request.json
    prompt = data.get("prompt")

    def generate():
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f'data: {json.dumps({"content": content})}\n\n'

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    return Response(stream_with_context(generate()),
                    content_type="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
