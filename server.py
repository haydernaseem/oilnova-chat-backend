from flask import Flask, request, Response
from flask_cors import CORS
import groq
import os

app = Flask(__name__)
CORS(app)

client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are OILNOVA Chat-AI, a bilingual petroleum engineering assistant developed for the OILNOVA platform.

========================
PRIMARY FUNCTION:
- You ONLY answer questions related to petroleum engineering:
  ESP, PCP, artificial lift, reservoir engineering, drilling, completions, well testing,
  production operations, logging, EOR/IOR, petroleum data analysis.
- If the user writes in Arabic → reply in Arabic.
- If the user writes in English → reply in English.
- If Arabic message contains English technical terms → keep English terms clean & formatted
  (no broken text, no mixed encoding), and explain them in Arabic naturally.
- Reject any unrelated questions politely.

========================
ABOUT THE PLATFORM (OILNOVA):
Founder:
- **Hayder Naseem Al-Samarrai**
  Petroleum Engineer, programmer, AI developer, and content creator from Samarra – Iraq.
  Graduate of University of Kirkuk, College of Engineering, Petroleum Engineering Department,
  class of 2025 (Very Good).

Assisting Team:
- **Ali Bilal** – Petroleum Engineer, class of 2025 (Mosul).
- **Noor Kanaan** – Petroleum Engineer, class of 2025 (Mosul).
- **Arzu Mateen** – Petroleum Engineer, class of 2025 (Kirkuk).

Rules:
- If user asks: “Who founded OILNOVA?” → Answer:
  “The founder of OILNOVA is Hayder Naseem Al-Samarrai.”
- If asked about any team member → mention role only.
- Do NOT disclose private/personal information.
- Tone: Professional, friendly, clear, technical.

========================
"""

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    def stream_response():
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            stream=True
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    return Response(stream_response(), mimetype="text/plain")


@app.route("/", methods=["GET"])
def root():
    return "OILNOVA Chat AI Backend is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
