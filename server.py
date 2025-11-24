from flask import Flask, request, jsonify
from flask_cors import CORS
import groq

app = Flask(__name__)
CORS(app)

# API Key مالك
client = groq.Client(api_key="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")

SYSTEM_PROMPT = """
You are OILNOVA Chat-AI — a bilingual (Arabic + English) petroleum engineering assistant.
You ONLY answer questions related to:
ESP, artificial lift, reservoir engineering, drilling, production, logging, data analysis.

If the user writes Arabic → reply Arabic.
If English → reply English.

Respond clearly, technically, and concisely.

If question is outside petroleum engineering → politely decline.
"""

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )

        reply = completion.choices[0].message["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # مهم حتى يشتغل على Render
    app.run(host="0.0.0.0", port=5000)
