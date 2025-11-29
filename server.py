from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from groq import Groq
import uuid
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# ---------------- CORS ----------------
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ---------------- Groq Client ----------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------- Conversations Memory ----------------
conversations = {}

# ---------------- Team Info ----------------
FOUNDERS_INFO = {
    "hayder": {
        "arabic": """الاسم: المهندس حيدر نسيم السامرائي
الدور: مؤسس منصة OILNOVA
الخبرة: مهندس نفط، محلل بيانات، مطور Frontend و Firebase Backend
الدراسة: خريج جامعة كركوك / هندسة النفط 2025
الأصل: من عشيرة السادة البنيسان الحسنية – سامراء
الإنجاز: مؤسس أول منصة عربية نفطية تعتمد الذكاء الاصطناعي
البريد: haydernaseem02@gmail.com""",
        "english": """Name: Hayder Naseem Al-Samarrai
Role: Founder of OILNOVA Platform
Expertise: Petroleum Engineer, Data Analyst, Frontend & Firebase Backend Developer
Education: Petroleum Engineering – Kirkuk University – 2025
Heritage: Al-Benisian Al-Hasaniyah Tribe – Samarra
Achievement: Founder of the first Arabic oil & gas AI platform
Email: haydernaseem02@gmail.com"""
    },

    "ali": {
        "arabic": """الاسم: علي بلال عبدالله خلف
الدور: مبرمج بايثون
الأصل: الموصل – ناحية زمار – عشيرة الجبور
الدراسة: هندسة النفط
البريد: ali.bilalabdullahkhalaf@gmail.com""",
        "english": """Name: Ali Bilal Abdullah Khalaf
Role: Python Developer
Origin: Mosul – Al-Zumar – Al-Jubour Tribe
Education: Petroleum Engineering
Email: ali.bilalabdullahkhalaf@gmail.com"""
    },

    "noor": {
        "arabic": """الاسم: نور كنعان حيدر
الدور: مبرمجة بايثون
الأصل: كردية من كركوك
الدراسة: هندسة النفط – جامعة كركوك 2025
البريد: noorkanaanhaider@gmail.com""",
        "english": """Name: Noor Kanaan Haider
Role: Python Developer
Origin: Kurdish – Kirkuk
Education: Petroleum Engineering – Kirkuk University 2025
Email: noorkanaanhaider@gmail.com"""
    },

    "arzo": {
        "arabic": """الاسم: أرزو متين
الدور: محللة بيانات ومبرمجة بايثون
الأصل: تركمانية من كركوك – مواليد 2004
البريد: engarzo699@gmail.com""",
        "english": """Name: Arzu Metin
Role: Data Analyst & Python Developer
Origin: Turkmen – Kirkuk – Born 2004
Email: engarzo699@gmail.com"""
    }
}

# ========================================================
#  LANGUAGE DETECTION
# ========================================================
def detect_language(text):
    ar = len(re.findall(r'[\u0600-\u06FF]', text))
    en = len(re.findall(r'[a-zA-Z]', text))
    return "arabic" if ar >= en else "english"


# ========================================================
#  LIST FORMAT ENFORCER (MODE A – STRICT)
# ========================================================
def enforce_list_format(text, lang):
    # رقم + نقطة + مسافة
    numbered = re.findall(r'\d+\.\s*[^\.]+', text)
    bullets = re.findall(r'[-•]\s*[^\.]+', text)

    formatted = text

    # Format numbered lists
    for item in numbered:
        clean = item.strip()
        formatted = formatted.replace(item, f"\n{clean}")

    # Format bullet lists
    for item in bullets:
        clean = item.strip()
        formatted = formatted.replace(item, f"\n{clean}")

    # Remove double spaces and extra newlines
    formatted = re.sub(r'\n\s*\n', '\n', formatted)
    formatted = re.sub(r' +', ' ', formatted)

    # Convert numbers to Arabic if needed
    if lang == "arabic":
        table = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
        formatted = formatted.translate(table)

    return formatted.strip()


# ========================================================
#  CLEAN + NORMALIZE RESPONSE
# ========================================================
def clean(text, lang):
    if not text:
        return ""

    # Basic cleaning
    text = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9\s\.\,\!\?\-\:\(\)\/]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Add forced list formatting
    text = enforce_list_format(text, lang)

    return text


# ========================================================
#  TEAM HANDLER
# ========================================================
def handle_team_request(msg, lang):
    msg_lower = msg.lower()

    if any(k in msg_lower for k in ["حيدر", "هايدر", "المؤسس", "بنيسان", "hayder", "founder"]):
        return FOUNDERS_INFO["hayder"][lang]

    if any(k in msg_lower for k in ["علي", "بلال", "ali", "bilal"]):
        return FOUNDERS_INFO["ali"][lang]

    if any(k in msg_lower for k in ["نور", "كنعان", "noor"]):
        return FOUNDERS_INFO["noor"][lang]

    if any(k in msg_lower for k in ["ارزو", "أرزو", "arzo", "arzu"]):
        return FOUNDERS_INFO["arzo"][lang]

    return None


# ========================================================
#  SYSTEM PROMPT
# ========================================================
SYSTEM_AR = """
أنت مساعد OILNOVA الذكي المتخصص في هندسة النفط والغاز.

القواعد:
1. إذا كان السؤال بالعربية → أجب بالعربية فقط.
2. إذا كان السؤال بالإنجليزية → أجب بالإنجليزية فقط.
3. يمنع خلط اللغات.
4. عند الإجابة بنقاط، يجب أن تكون كل نقطة في سطر مستقل.
5. استخدم فقط النمط التالي:
1. نص
2. نص
3. نص
6. التزم بالدقة والاحترافية.
"""

SYSTEM_EN = """
You are OILNOVA Smart Assistant specialized in oil & gas engineering.

Rules:
1. If the question is in Arabic → answer ONLY in Arabic.
2. If the question is in English → answer ONLY in English.
3. Do not mix languages.
4. When listing steps or points, each point MUST be on a separate line.
5. Use this format only:
1. Text
2. Text
3. Text
6. Maintain accuracy and professional tone.
"""


# ========================================================
#  SESSION HANDLER
# ========================================================
def get_session(id):
    if id not in conversations:
        conversations[id] = {
            "messages": [],
            "last": datetime.now()
        }
    return conversations[id]


# ========================================================
#  ROUTES
# ========================================================
@app.route("/")
def home():
    return "OILNOVA CHAT API OK - MODE A"

@app.route("/start_session", methods=["GET"])
def start_session():
    sid = str(uuid.uuid4())
    conversations[sid] = {"messages": [], "last": datetime.now()}
    return jsonify({"session_id": sid})


# ========================================================
#  CHAT ENDPOINT
# ========================================================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data.get("message", "").strip()
    sid = data.get("session_id", "default")

    if not msg:
        return jsonify({"error": "Empty message"}), 400

    lang = detect_language(msg)
    system_prompt = SYSTEM_AR if lang == "arabic" else SYSTEM_EN

    session = get_session(sid)

    # Check team info
    t = handle_team_request(msg, lang)
    if t:
        return jsonify({"reply": t, "session_id": sid})

    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(session["messages"])
    messages.append({"role": "user", "content": msg})

    # Call Groq
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4,
        max_tokens=800
    )

    reply = completion.choices[0].message.content

    # Clean + enforce formatting
    final = clean(reply, lang)

    # Save conversation
    session["messages"].append({"role": "user", "content": msg})
    session["messages"].append({"role": "assistant", "content": final})

    return jsonify({"reply": final, "session_id": sid})


# ========================================================
#  CLEAR HISTORY
# ========================================================
@app.route("/clear_history", methods=["POST"])
def clear_history():
    sid = request.json.get("session_id", "default")
    if sid in conversations:
        conversations[sid]["messages"] = []
    return jsonify({"message": "cleared"})


# ========================================================
#  RUN
# ========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
