from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from groq import Groq
import uuid
from datetime import datetime, timedelta

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

# ====== تخزين المحادثات ======
conversations = {}

FOUNDERS_INFO = {
    "founder": "مؤسس منصة OILNOVA هو المهندس حيدر نسيم السامرائي — مهندس نفط، مبرمج، وصانع محتوى من سامراء. "
               "تخرّج من جامعة كركوك / كلية الهندسة / قسم النفط سنة 2025 بتقدير جيد جدًا. "
               "أسس منصة أويل نوفا وهي أول منصة عربية في مجال النفط تستخدم تقنيات الذكاء الاصطناعي.",

    "ali": "علي بلال — خريج هندسة نفط من جامعة الموصل، دفعة 2025، بتقدير جيد.",
    "noor": "نور كنعان — خريجة هندسة نفط من الموصل، كردية، دفعة 2025، بتقدير جيد.",
    "arzo": "أرزو متين — تركمانية من كركوك، خريجة هندسة نفط دفعة 2025 بتقدير جيد."
}

# ====== تنظيف المحادثات القديمة ======
def cleanup_old_conversations():
    """حذف المحادثات الأقدم من ساعة"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in conversations.items():
        if current_time - session_data['last_activity'] > timedelta(hours=1):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del conversations[session_id]

def get_conversation_history(session_id):
    """استرجاع تاريخ المحادثة"""
    if session_id not in conversations:
        conversations[session_id] = {
            'messages': [],
            'last_activity': datetime.now(),
            'context': {}
        }
    else:
        conversations[session_id]['last_activity'] = datetime.now()
    
    return conversations[session_id]

def add_message_to_history(session_id, role, content):
    """إضافة رسالة جديدة للمحادثة"""
    session = get_conversation_history(session_id)
    session['messages'].append({"role": role, "content": content})
    
    # الحفاظ على آخر 12 رسالة فقط
    if len(session['messages']) > 12:
        session['messages'] = session['messages'][-12:]

@app.route("/")
def home():
    return "OILNOVA CHAT BACKEND IS RUNNING OK - ENHANCED VERSION"

@app.route("/start_session", methods=["GET"])
def start_session():
    """بدء جلسة محادثة جديدة"""
    session_id = str(uuid.uuid4())
    conversations[session_id] = {
        'messages': [],
        'last_activity': datetime.now(),
        'context': {}
    }
    return jsonify({"session_id": session_id})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_msg = data.get("message", "").strip()
        session_id = data.get("session_id", "default")

        if not user_msg:
            return jsonify({"error": "الرسالة فارغة"}), 400

        # تنظيف المحادثات القديمة
        cleanup_old_conversations()

        # استرجاع تاريخ المحادثة
        session_data = get_conversation_history(session_id)
        conversation_history = session_data['messages']

        # ====== SYSTEM PROMPT المحسن ======
        SYSTEM_PROMPT = """
You are OILNOVA Chat-AI — a specialized bilingual (Arabic/English) petroleum engineering assistant.

STRICT LANGUAGE RULES:
- If user message is in Arabic → reply ONLY in Arabic
- If user message is in English → reply ONLY in English  
- Never mix languages in the same response
- If technical terms must be used, provide Arabic translation in parentheses

TECHNICAL DOMAIN:
You ONLY answer questions related to:
- ESP systems and artificial lift
- Reservoir engineering and simulation  
- Drilling operations and technologies
- Production optimization
- Well logging and data analysis
- Petroleum geology and geophysics
- Oil field equipment and maintenance

PERSONAL INFORMATION (ONLY when specifically asked about team members):

Hayder Naseem:
- Data Analyst, Frontend & Firebase Backend Developer
- Descendant of Al-Benisian Al-Hasaniyah tribe in Samarra
- Contact: haydernaseem02@gmail.com

Ali Bilal: 
- From Mosul, Al-Zumar district, Al-Jubour tribe, born 2001
- Python programmer passionate about technology
- Contact: ali.bilalabdullahkhalaf@gmail.com

Noor Kanaan:
- Kurdish from Kirkuk, born 2004
- Python programmer, graduated from Kirkuk University 2025
- Promising future in technology field
- Contact: noorkanaanhaider@gmail.com

Arzu Metin:
- Turkmen from Kirkuk, born 2004
- Technology enthusiast, Data Analyst, Python programmer
- Co-founder of OILNOVA platform
- Expected to have significant professional future
- Contact: engarzo699@gmail.com

STRICT RESPONSE POLICY:
- For non-petroleum questions → "I specialize only in oil and gas engineering topics. For other inquiries, please contact the team members directly."
- Maintain professional, clean formatting in responses
- Never use mixed scripts or random characters
- Ensure technical accuracy with clear explanations
- For personal info → only provide when explicitly asked about specific team members
- Keep responses structured and easy to read
"""

        # ====== ردود خاصة بفريق المنصة ======
        msg_lower = user_msg.lower()

        if any(keyword in user_msg for keyword in ["منو مؤسس", "المؤسس", "حيدر", "هايدر"]) or "founder" in msg_lower:
            reply = FOUNDERS_INFO["founder"]
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        if "علي بلال" in user_msg or "ali" in msg_lower:
            reply = FOUNDERS_INFO["ali"]
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        if "نور" in user_msg or "noor" in msg_lower:
            reply = FOUNDERS_INFO["noor"]
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        if "ارزو" in user_msg or "arzo" in msg_lower:
            reply = FOUNDERS_INFO["arzo"]
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        # ====== بناء رسائل المحادثة مع السياق ======
        messages = [{"role": "system", "content": system_prompt}]
        
        # إضافة تاريخ المحادثة السابقة
        messages.extend(conversation_history)
        
        # إضافة الرسالة الحالية
        messages.append({"role": "user", "content": user_msg})

        # ====== AI COMPLETION مع تحسينات ======
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,  # لزيادة الإبداع والمرونة في الردود
            max_tokens=1024,
            top_p=0.9
        )

        reply = completion.choices[0].message.content
        
        # تحديث تاريخ المحادثة
        add_message_to_history(session_id, "user", user_msg)
        add_message_to_history(session_id, "assistant", reply)

        return jsonify({
            "reply": reply,
            "session_id": session_id
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/clear_history", methods=["POST"])
def clear_history():
    """مسح تاريخ المحادثة"""
    try:
        data = request.json
        session_id = data.get("session_id", "default")
        
        if session_id in conversations:
            conversations[session_id]['messages'] = []
        
        return jsonify({"message": "تم مسح تاريخ المحادثة", "session_id": session_id})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
