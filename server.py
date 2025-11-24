from flask import Flask, request, jsonify
from flask_cors import CORS
import groq
import os

app = Flask(__name__)
CORS(app)

client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are OILNOVA Chat-AI — a bilingual (Arabic + English) petroleum engineering assistant.
You ONLY answer questions related to ESP, reservoir, drilling, production, logs, data analysis.
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

        # 👇 هنا التعديل المهم
        reply = completion.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
