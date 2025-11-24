from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from groq import Groq

app = Flask(__name__)

# ====== CORS FIX 100% ======
CORS(app, resources={
    r"/*": {
        "origins": ["https://petroai-iq.web.app", "*"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ====== Groq Client ======
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

FOUNDERS_INFO = {
    "founder": "مؤسس منصة OILNOVA هو المهندس حيدر نسيم السامرائي — مهندس نفط، مبرمج، وصانع محتوى من سامراء. "
               "تخرّج من جامعة كركوك / كلية الهندسة / قسم النفط سنة 2025 بتقدير جيد جدًا.",

    "ali": "علي بلال — خريج هندسة نفط من جامعة الموصل، دفعة 2025، بتقدير جيد.",
    "noor": "نور كنعان — خريجة هندسة نفط من الموصل، كردية، دفعة 2025، بتقدير جيد.",
    "arzo": "أرزو متين — تركمانية من كركوك، خريجة هندسة نفط دفعة 2025 بتقدير جيد."
}

@app.route("/")
def home():
    return "OILNOVA CHAT BACKEND IS RUNNING OK"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_msg = request.json.get("message", "")

        # ردود خاصة بفريق المنصة
        msg_lower = user_msg.lower()

        if "منو مؤسس" in user_msg or "المؤسس" in user_msg or "founder" in msg_lower:
            return jsonify({"reply": FOUNDERS_INFO["founder"]})

        if "علي بلال" in user_msg or "ali" in msg_lower:
            return jsonify({"reply": FOUNDERS_INFO["ali"]})

        if "نور" in user_msg or "noor" in msg_lower:
            return jsonify({"reply": FOUNDERS_INFO["noor"]})

        if "ارزو" in user_msg or "arzo" in msg_lower:
            return jsonify({"reply": FOUNDERS_INFO["arzo"]})

        # ====== AI COMPLETION ======
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are OILNOVA AI Assistant. Answer ONLY petroleum engineering questions "
                        "or questions about the OILNOVA platform team."
                    )
                },
                {"role": "user", "content": user_msg}
            ]
        )

        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
