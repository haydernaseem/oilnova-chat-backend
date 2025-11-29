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

# ====== معلومات الفريق المحسنة ======
FOUNDERS_INFO = {
    "hayder": {
        "arabic": """المهندس حيدر نسيم السامرائي - مؤسس منصة OILNOVA
• مهندس نفط، محلل بيانات، مبرمج فرونت إند و Firebase باك إند
• خريج جامعة كركوك / كلية الهندسة / قسم هندسة النفط 2025
• من عشيرة السادة البنيسان الحسنية في سامراء
• أسس أويل نوفا كأول منصة عربية نفطية تستخدم الذكاء الاصطناعي

للتواصل: haydernaseem02@gmail.com""",
        
        "english": """Engineer Hayder Naseem Al-Samarrai - Founder of OILNOVA Platform
• Petroleum Engineer, Data Analyst, Frontend & Firebase Backend Developer
• Graduate of Kirkuk University / College of Engineering / Petroleum Engineering Dept. 2025
• Descendant of Al-Sadah Al-Benisian Al-Hasaniyah tribe in Samarra
• Founded OILNOVA as the first Arabic oil platform using AI technologies

Contact: haydernaseem02@gmail.com"""
    },
    
    "ali": {
        "arabic": """علي بلال عبدالله خلف
• مبرمج بايثون وشغوف بمجال التكنولوجيا
• من مدينة الموصل / ناحية زمار / عشيرة الجبور
• مواليد 2001
• خريج هندسة نفط

للتواصل: ali.bilalabdullahkhalaf@gmail.com""",
        
        "english": """Ali Bilal Abdullah Khalaf
• Python Programmer passionate about technology
• From Mosul City / Al-Zumar District / Al-Jubour Tribe
• Born 2001
• Petroleum Engineering Graduate

Contact: ali.bilalabdullahkhalaf@gmail.com"""
    },
    
    "noor": {
        "arabic": """نور كنعان حيدر
• مبرمجة بايثون وشغوفة بمجال التكنولوجيا
• كردية من كركوك
• مواليد 2004
• خريجة هندسة نفط - جامعة كركوك 2025
• مستقبل مهني مشرق في مجال البرمجة

للتواصل: noorkanaanhaider@gmail.com""",
        
        "english": """Noor Kanaan Haider
• Python Programmer passionate about technology
• Kurdish from Kirkuk
• Born 2004
• Petroleum Engineering Graduate - Kirkuk University 2025
• Promising professional future in programming field

Contact: noorkanaanhaider@gmail.com"""
    },
    
    "arzo": {
        "arabic": """أرزو متين
• تركمانية من كركوك مواليد 2004
• محللة بيانات ومبرمجة بايثون
• شغوفة بالتكنولوجيا ومؤسسة مشاركة لمنصة أويل نوفا
• مستقبل مهني كبير متوقع في مجال تحليل البيانات

للتواصل: engarzo699@gmail.com""",
        
        "english": """Arzu Metin
• Turkmen from Kirkuk, born 2004
• Data Analyst and Python Programmer
• Technology enthusiast and co-founder of OILNOVA platform
• Expected significant professional future in data analysis

Contact: engarzo699@gmail.com"""
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
        # إذا كانت متساوية، ننظر إلى الكلمات
        arabic_words = len(re.findall(r'\b[\u0600-\u06FF]+\b', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        return 'arabic' if arabic_words >= english_words else 'english'

def clean_response(text):
    """تنظيف الرد من الأحرف العشوائية والمشاكل النصية"""
    # إزالة الأحرف غير المرغوب فيها
    cleaned = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9\s\.\,\!\?\-\:\;\(\)\%\&\"\'\@\#\$\*\+\=\/\<\>\[\]\\]', '', text)
    
    # إصلاح المسافات الزائدة
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # تأكد من أن النص يبدأ بحرف مناسب
    cleaned = cleaned.strip()
    
    return cleaned

def get_founder_info(founder_key, user_language):
    """الحصول على معلومات المؤسس باللغة المناسبة"""
    if founder_key in FOUNDERS_INFO:
        return FOUNDERS_INFO[founder_key].get(user_language, FOUNDERS_INFO[founder_key]['arabic'])
    return "لم يتم العثور على المعلومات المطلوبة."

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

        # كشف لغة المستخدم
        user_language = detect_language(user_msg)
        
        # استرجاع تاريخ المحادثة
        session_data = get_conversation_history(session_id)
        conversation_history = session_data['messages']

        # ====== SYSTEM PROMPT المحسن والاحترافي ======
        system_prompt_arabic = """
أنت مساعد OILNOVA الذكي - مساعد متخصص في هندسة النفط والغاز.

🎯 **التخصص الأساسي**: 
- هندسة النفط والغاز بشكل حصري
- أنظمة ESP والرفع الاصطناعي
- هندسة المكامن والتنقيب
- عمليات الحفر والإنتاج
- التسجيل الجيوفيزيائي وتحليل البيانات النفطية

🌐 **قواعد اللغة الصارمة**:
- إذا كان السؤال بالعربية → أجب بالعربية فقط
- إذا كان السؤال بالإنجليزية → أجب بالإنجليزية فقط  
- لا تخلط اللغات أبداً في الرد الواحد
- إذا اضطررت لاستخدام مصطلح تقني إنجليزي، اكتبه ثم اشرحه بين قوسين

👥 **معلومات الفريق (فقط عند السؤال المباشر)**:
- حيدر نسيم: مؤسس المنصة، مهندس نفط، مبرمج
- علي بلال: مبرمج بايثون من الموصل
- نور كنعان: مبرمجة بايثون من كركوك
- أرزو متين: محللة بيانات ومبرمجة بايثون من كركوك

🚫 **السياسات**:
- لا تعطي معلومات شخصية إلا عند السؤال المباشر عن أعضاء الفريق
- للأسئلة خارج تخصص النفط: "أنا متخصص في هندسة النفط والغاز فقط"
- حافظ على الاحترافية والدقة التقنية
- رتب الردود بشكل منظم وسهل القراءة
"""

        system_prompt_english = """
You are OILNOVA Smart Assistant - specialized in oil and gas engineering.

🎯 **Primary Specialization**: 
- Oil and gas engineering exclusively
- ESP systems and artificial lift
- Reservoir engineering and exploration
- Drilling and production operations
- Geophysical logging and oil data analysis

🌐 **Strict Language Rules**:
- If question is in Arabic → reply ONLY in Arabic
- If question is in English → reply ONLY in English  
- Never mix languages in the same response
- If you must use an English technical term, write it then explain in parentheses

👥 **Team Information (only when directly asked)**:
- Hayder Naseem: Platform founder, petroleum engineer, programmer
- Ali Bilal: Python programmer from Mosul
- Noor Kanaan: Python programmer from Kirkuk
- Arzu Metin: Data analyst and Python programmer from Kirkuk

🚫 **Policies**:
- Do not give personal information unless directly asked about team members
- For non-oil/gas questions: "I specialize only in oil and gas engineering"
- Maintain professionalism and technical accuracy
- Organize responses in a structured, easy-to-read format
"""

        # اختيار النظام المناسب بناءً على لغة المستخدم
        system_prompt = system_prompt_arabic if user_language == 'arabic' else system_prompt_english

        # ====== ردود خاصة بفريق المنصة ======
        msg_lower = user_msg.lower()
        
        # كلمات البحث العربية والإنجليزية
        hayder_keywords_arabic = ["حيدر", "هايدر", "نسيم", "المؤسس", "منو مؤسس", "مؤسس المنصة", "بنيسان", "سامراء"]
        hayder_keywords_english = ["hayder", "naseem", "founder", "owner", "creator", "samarra"]
        
        ali_keywords_arabic = ["علي بلال", "علي", "بلال", "زبور", "زمار", "موصل"]
        ali_keywords_english = ["ali", "bilal", "mosul", "jubour"]
        
        noor_keywords_arabic = ["نور", "كنعان", "كردية", "كركوك"]
        noor_keywords_english = ["noor", "kanaan", "kurdish", "kirkuk"]
        
        arzo_keywords_arabic = ["ارزو", "أرزو", "متين", "تركمانية"]
        arzo_keywords_english = ["arzo", "arzu", "metin", "turkmen"]

        # التحقق من طلبات معلومات الفريق
        if any(keyword in msg_lower for keyword in hayder_keywords_arabic + [k.lower() for k in hayder_keywords_english]):
            reply = get_founder_info("hayder", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        elif any(keyword in msg_lower for keyword in ali_keywords_arabic + [k.lower() for k in ali_keywords_english]):
            reply = get_founder_info("ali", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        elif any(keyword in msg_lower for keyword in noor_keywords_arabic + [k.lower() for k in noor_keywords_english]):
            reply = get_founder_info("noor", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        elif any(keyword in msg_lower for keyword in arzo_keywords_arabic + [k.lower() for k in arzo_keywords_english]):
            reply = get_founder_info("arzo", user_language)
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
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9
        )

        reply = completion.choices[0].message.content
        
        # تنظيف الرد
        cleaned_reply = clean_response(reply)
        
        # تحديث تاريخ المحادثة
        add_message_to_history(session_id, "user", user_msg)
        add_message_to_history(session_id, "assistant", cleaned_reply)

        return jsonify({
            "reply": cleaned_reply,
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
