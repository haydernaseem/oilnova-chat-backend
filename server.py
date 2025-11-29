from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from groq import Groq
import uuid
from datetime import datetime, timedelta
import re

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

# ====== معلومات الفريق الأساسية (نص خام) ======
FOUNDERS_INFO = {
    "hayder": {
        "arabic": """المهندس حيدر نسيم السامرائي، مهندس نفط ومحلل بيانات ومبرمج واجهات أمامية إضافة إلى تطوير Firebase كباك إند. خريج جامعة كركوك / كلية الهندسة / قسم هندسة النفط 2025، ومن عشيرة السادة البنيسان الحسنية في سامراء. أسس منصة OILNOVA كأول منصة عربية نفطية تعتمد على تقنيات الذكاء الاصطناعي لخدمة قطاع النفط والغاز في العالم العربي.""",
        "english": """Engineer Hayder Naseem Al-Samarrai is a petroleum engineer, data analyst, and frontend developer with Firebase backend experience. He graduated from Kirkuk University, College of Engineering, Petroleum Engineering Department (2025), and belongs to Al-Sadah Al-Benisian Al-Hasaniyah tribe in Samarra. He founded the OILNOVA platform as one of the first Arabic oil & gas platforms powered by AI technologies."""
    },
    "ali": {
        "arabic": """علي بلال عبدالله خلف، مبرمج بايثون شغوف بالتكنولوجيا وتطوير الحلول البرمجية، من مدينة الموصل / ناحية زمار / عشيرة الجبور، من مواليد 2001 وخريج هندسة نفط. يساهم في تطوير أنظمة OILNOVA الخلفية وبناء أدوات ذكية تخدم المهندسين في مجال النفط والغاز.""",
        "english": """Ali Bilal Abdullah Khalaf is a Python programmer passionate about technology and software solutions. He is from Mosul city, Al-Zumar district, from Al-Jubour tribe, born in 2001 and a petroleum engineering graduate. He contributes to building OILNOVA backend systems and smart tools that support engineers in the oil and gas sector."""
    },
    "noor": {
        "arabic": """نور كنعان حيدر، مبرمجة بايثون شغوفة بمجال التكنولوجيا وتحليل البيانات، كردية من كركوك ومن مواليد 2004، خريجة هندسة نفط من جامعة كركوك لعام 2025. تمتلك شغفاً كبيراً بالبرمجة ولديها مسار مهني واعد في بناء الأدوات الذكية بمنصة OILNOVA.""",
        "english": """Noor Kanaan Haider is a Python programmer passionate about technology and data analysis. She is a Kurdish engineer from Kirkuk, born in 2004, and a petroleum engineering graduate from Kirkuk University (class of 2025). She has a promising career path in software development and in building smart tools within the OILNOVA platform."""
    },
    "arzo": {
        "arabic": """أرزو متين، مهندسة تركمانية من كركوك مواليد 2004، تعمل كمحللة بيانات ومبرمجة بايثون. تمتلك شغفاً واضحاً بالتكنولوجيا وتطوير حلول تعتمد على البيانات، وتعد من العناصر الأساسية في فريق OILNOVA مع توقع بمستقبل مهني قوي في مجال تحليل البيانات وتطوير أنظمة الذكاء الاصطناعي النفطية.""",
        "english": """Arzu Metin is a Turkmen engineer from Kirkuk, born in 2004. She works as a data analyst and Python programmer, with a clear passion for technology and data-driven solutions. She is a key member of the OILNOVA team, with a strong expected career in data analysis and the development of AI-based systems for the oil and gas industry."""
    }
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


def detect_language(text):
    """كشف لغة النص بدقة"""
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    if arabic_chars > english_chars:
        return 'arabic'
    elif english_chars > arabic_chars:
        return 'english'
    else:
        arabic_words = len(re.findall(r'\b[\u0600-\u06FF]+\b', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        return 'arabic' if arabic_words >= english_words else 'english'


def clean_response(text, language=None):
    """
    تنظيف الرد مع الحفاظ على الأسطر والقوائم (لا نحذف الـ \n أبداً).
    """
    if not text:
        return ""

    # توحيد نوع الأسطر
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # إزالة الأحرف غير المرغوبة لكن مع الإبقاء على \n
    cleaned = re.sub(
        r'[^\u0600-\u06FFa-zA-Z0-9 \t\n\.\,\!\?\-\:\;\(\)\%\&\"\'\@\#\$\*\+\=\/\<\>\[\]\\]',
        '',
        text
    )

    # ضغط المسافات والـ tab فقط (بدون المساس بالـ \n)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)

    # تقليل عدد الأسطر الفارغة المتتالية إلى اثنين
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    cleaned = cleaned.strip()
    return cleaned


def format_final_response(text, language):
    """
    تنسيق نهائي بسيط للرد:
    - يحافظ على الأسطر.
    - يضمن وجود سطر فارغ بين الفقرات الكبيرة.
    """
    if not text:
        return ""

    # تنظيف أولي
    cleaned = clean_response(text, language)

    # محاولة بسيطة لتجميل القوائم: إذا وجدنا "1." وهناك تكملة في نفس السطر، نتركها كما هي
    # لأن الـ frontend سيعرضها سطر بسطر من خلال \n
    return cleaned


def get_founder_raw_info(founder_key, user_language):
    """إرجاع النص الخام من القاموس"""
    if founder_key not in FOUNDERS_INFO:
        return None
    info = FOUNDERS_INFO[founder_key]
    if user_language == "english":
        return info.get("english", info.get("arabic", ""))
    return info.get("arabic", info.get("english", ""))


def generate_team_bio(founder_key, user_language):
    """
    توليد نص منغوم عن عضو من الفريق باستخدام Groq
    (يعيد فقرة واحدة مرتبة بنفس لغة المستخدم).
    """
    base_text = get_founder_raw_info(founder_key, user_language)
    if not base_text:
        return "لم يتم العثور على معلومات هذا العضو في الفريق." if user_language == "arabic" else "Team member information not found."

    if user_language == "arabic":
        system_prompt = (
            "أنت كاتب محتوى عربي محترف. سيصلك نص معلومات عن شخص من فريق OILNOVA. "
            "أعد كتابته في فقرة واحدة منسقة وسلسة، بدون تعداد نقطي، وبدون إضافة معلومات جديدة. "
            "حافظ على الطابع المهني واللغة الواضحة."
        )
    else:
        system_prompt = (
            "You are a professional English copywriter. You will receive a short bio of an OILNOVA team member. "
            "Rewrite it as a single, smooth paragraph without bullet points and without adding new facts. "
            "Keep it professional and clear."
        )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": base_text}
            ],
            temperature=0.4,
            max_tokens=400,
            top_p=0.9
        )
        raw_reply = completion.choices[0].message.content
        return format_final_response(raw_reply, user_language)
    except Exception as e:
        print(f"Team bio generation error: {e}")
        # في حال فشل النموذج، نرجع النص الخام المنسق يدوياً
        fallback = clean_response(base_text, user_language)
        return fallback


@app.route("/")
def home():
    return "OILNOVA CHAT BACKEND IS RUNNING OK - ENHANCED PROFESSIONAL VERSION"


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

        # كشف لغة المستخدم (أو أخذها من الـ frontend لاحقاً إذا حبيت)
        user_language = detect_language(user_msg)

        # استرجاع تاريخ المحادثة
        session_data = get_conversation_history(session_id)
        conversation_history = session_data['messages']

        # ====== SYSTEM PROMPT المحسن والاحترافي ======
        system_prompt_arabic = """
أنت مساعد OILNOVA الذكي - مساعد متخصص في هندسة النفط والغاز.

🎯 التخصص الأساسي:
- هندسة النفط والغاز فقط
- أنظمة ESP والرفع الاصطناعي
- هندسة المكامن والاستكشاف
- عمليات الحفر والإنتاج
- التسجيلات الجيوفيزيائية وتحليل البيانات النفطية

🌐 قواعد اللغة:
- إذا كان السؤال بالعربية → أجب بالعربية فقط
- إذا كان السؤال بالإنجليزية → أجب بالإنجليزية فقط
- لا تخلط اللغتين في نفس الرد
- عند استخدام مصطلح تقني إنجليزي، اكتبه ثم اشرح معناه باختصار بين قوسين

👥 معلومات الفريق (فقط عند السؤال المباشر):
- حيدر نسيم: مؤسس المنصة، مهندس نفط، مبرمج
- علي بلال: مبرمج بايثون من الموصل
- نور كنعان: مبرمجة بايثون من كركوك
- أرزو متين: محللة بيانات ومبرمجة بايثون من كركوك

🚫 السياسات:
- لا تعطي معلومات شخصية إلا عند السؤال المباشر عن أعضاء الفريق
- للأسئلة خارج تخصص النفط: قل للمستخدم أنك متخصص فقط في هندسة النفط والغاز
- التزم بالاحترافية والدقة في الشرح
- رتب الردود بعناوين، نقاط، وخلاصة قدر الإمكان
"""

        system_prompt_english = """
You are OILNOVA Smart Assistant - specialized in oil and gas engineering.

🎯 Primary specialization:
- Oil and gas engineering only
- ESP systems and artificial lift
- Reservoir engineering and exploration
- Drilling and production operations
- Geophysical logging and oilfield data analysis

🌐 Language rules:
- If the question is in Arabic → answer only in Arabic
- If the question is in English → answer only in English
- Never mix both languages in the same reply
- When using an English technical term in Arabic, briefly explain it in parentheses

👥 Team information (only when directly asked):
- Hayder Naseem: Platform founder, petroleum engineer, programmer
- Ali Bilal: Python programmer from Mosul
- Noor Kanaan: Python programmer from Kirkuk
- Arzu Metin: Data analyst and Python programmer from Kirkuk

🚫 Policies:
- Do not provide personal information unless explicitly asked about team members
- For non-oil/gas questions: clearly state that you only specialize in oil and gas engineering
- Keep responses professional, technically accurate, and well structured
"""

        system_prompt = system_prompt_arabic if user_language == 'arabic' else system_prompt_english

        # ====== ردود خاصة بفريق المنصة ======
        msg_lower = user_msg.lower()

        hayder_keywords_arabic = ["حيدر", "هايدر", "نسيم", "المؤسس", "منو مؤسس", "مؤسس المنصة", "بنيسان", "سامراء"]
        hayder_keywords_english = ["hayder", "naseem", "founder", "owner", "creator", "samarra"]

        ali_keywords_arabic = ["علي بلال", "علي", "بلال", "زبور", "زمار", "موصل"]
        ali_keywords_english = ["ali", "bilal", "mosul", "jubour"]

        noor_keywords_arabic = ["نور", "كنعان", "كردية", "كركوك"]
        noor_keywords_english = ["noor", "kanaan", "kurdish", "kirkuk"]

        arzo_keywords_arabic = ["ارزو", "أرزو", "متين", "تركمانية"]
        arzo_keywords_english = ["arzo", "arzu", "metin", "turkmen"]

        # التحقق من طلبات معلومات الفريق → نستخدم مولد الفقرة المنغومة
        if any(keyword in msg_lower for keyword in hayder_keywords_arabic + [k.lower() for k in hayder_keywords_english]):
            reply = generate_team_bio("hayder", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        if any(keyword in msg_lower for keyword in ali_keywords_arabic + [k.lower() for k in ali_keywords_english]):
            reply = generate_team_bio("ali", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        if any(keyword in msg_lower for keyword in noor_keywords_arabic + [k.lower() for k in noor_keywords_english]):
            reply = generate_team_bio("noor", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        if any(keyword in msg_lower for keyword in arzo_keywords_arabic + [k.lower() for k in arzo_keywords_english]):
            reply = generate_team_bio("arzo", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        # ====== بناء رسائل المحادثة مع السياق ======
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_msg})

        # ====== AI COMPLETION ======
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9
        )

        raw_reply = completion.choices[0].message.content

        # تنسيق الرد (بدون تكسير الأسطر)
        formatted_reply = format_final_response(raw_reply, user_language)

        # تحديث تاريخ المحادثة
        add_message_to_history(session_id, "user", user_msg)
        add_message_to_history(session_id, "assistant", formatted_reply)

        return jsonify({
            "reply": formatted_reply,
            "session_id": session_id,
            "detected_language": user_language
        })

    except Exception as e:
        print(f"Error: {e}")
        error_msg_arabic = "عذراً، حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى."
        error_msg_english = "Sorry, an error occurred during processing. Please try again."
        user_language = detect_language(user_msg) if 'user_msg' in locals() else 'arabic'
        error_msg = error_msg_arabic if user_language == 'arabic' else error_msg_english
        return jsonify({"error": error_msg}), 500


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


@app.route("/get_session_info", methods=["GET"])
def get_session_info():
    """الحصول على معلومات الجلسة"""
    return jsonify({
        "active_sessions": len(conversations),
        "sessions": list(conversations.keys())
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
