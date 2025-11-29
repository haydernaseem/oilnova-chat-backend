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
        "arabic": {
            "name": "حيدر نسيم السامرائي",
            "role": "مؤسس منصة OILNOVA",
            "background": "مهندس نفط، محلل بيانات، مبرمج فرونت إند و Firebase باك إند",
            "education": "خريج جامعة كركوك / كلية الهندسة / قسم هندسة النفط 2025",
            "heritage": "من عشيرة السادة البنيسان الحسنية في سامراء",
            "achievement": "أسس أويل نوفا كأول منصة عربية نفطية تستخدم الذكاء الاصطناعي",
            "contact": "haydernaseem02@gmail.com"
        },
        "english": {
            "name": "Hayder Naseem Al-Samarrai",
            "role": "Founder of OILNOVA Platform", 
            "background": "Petroleum Engineer, Data Analyst, Frontend & Firebase Backend Developer",
            "education": "Graduate of Kirkuk University / College of Engineering / Petroleum Engineering Dept. 2025",
            "heritage": "Descendant of Al-Sadah Al-Benisian Al-Hasaniyah tribe in Samarra",
            "achievement": "Founded OILNOVA as the first Arabic oil platform using AI technologies",
            "contact": "haydernaseem02@gmail.com"
        }
    },
    
    "ali": {
        "arabic": {
            "name": "علي بلال عبدالله خلف",
            "role": "مبرمج بايثون ومطور تقني",
            "background": "شغوف بمجال التكنولوجيا والبرمجة",
            "education": "خريج هندسة النفط",
            "heritage": "من مدينة الموصل / ناحية زمار / عشيرة الجبور",
            "birth": "مواليد 2001",
            "contact": "ali.bilalabdullahkhalaf@gmail.com"
        },
        "english": {
            "name": "Ali Bilal Abdullah Khalaf",
            "role": "Python Programmer and Tech Developer",
            "background": "Passionate about technology and programming",
            "education": "Petroleum Engineering Graduate", 
            "heritage": "From Mosul City / Al-Zumar District / Al-Jubour Tribe",
            "birth": "Born 2001",
            "contact": "ali.bilalabdullahkhalaf@gmail.com"
        }
    },
    
    "noor": {
        "arabic": {
            "name": "نور كنعان حيدر",
            "role": "مبرمجة بايثون ومطورة تقنية",
            "background": "شغوفة بمجال التكنولوجيا والبرمجة",
            "education": "خريجة هندسة النفط - جامعة كركوك 2025",
            "heritage": "كردية من كركوك",
            "birth": "مواليد 2004", 
            "future": "مستقبل مهني مشرق في مجال البرمجة",
            "contact": "noorkanaanhaider@gmail.com"
        },
        "english": {
            "name": "Noor Kanaan Haider",
            "role": "Python Programmer and Tech Developer",
            "background": "Passionate about technology and programming",
            "education": "Petroleum Engineering Graduate - Kirkuk University 2025",
            "heritage": "Kurdish from Kirkuk",
            "birth": "Born 2004",
            "future": "Promising professional future in programming field",
            "contact": "noorkanaanhaider@gmail.com"
        }
    },
    
    "arzo": {
        "arabic": {
            "name": "أرزو متين",
            "role": "محللة بيانات ومبرمجة بايثون",
            "background": "شغوفة بالتكنولوجيا ومؤسسة مشاركة لمنصة أويل نوفا",
            "heritage": "تركمانية من كركوك مواليد 2004",
            "future": "مستقبل مهني كبير متوقع في مجال تحليل البيانات",
            "contact": "engarzo699@gmail.com"
        },
        "english": {
            "name": "Arzu Metin", 
            "role": "Data Analyst and Python Programmer",
            "background": "Technology enthusiast and co-founder of OILNOVA platform",
            "heritage": "Turkmen from Kirkuk, born 2004",
            "future": "Expected significant professional future in data analysis",
            "contact": "engarzo699@gmail.com"
        }
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

# ====== FORMATTING FUNCTIONS ======
def convert_english_numbers_to_arabic(text):
    """تحويل الأرقام الإنجليزية إلى عربية"""
    number_map = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    }
    
    for eng_num, arabic_num in number_map.items():
        text = text.replace(eng_num, arabic_num)
    
    return text

def enforce_list_formatting(text, language):
    """تطبيق التنسيق الإجباري للقوائم - كل نقطة في سطر مستقل"""
    if not text:
        return text
    
    # أنماط للتعرف على القوائم المرقمة والنقطية
    numbered_pattern = r'(\d+\.\s*[^\n]+(?:\s*\d+\.\s*[^\n]+)*)'
    bullet_pattern = r'([•\-*]\s*[^\n]+(?:\s*[•\-*]\s*[^\n]+)*)'
    
    def format_lists(text):
        # معالجة القوائم المرقمة
        def format_numbered(match):
            content = match.group(0).strip()
            # تقسيم إلى عناصر فردية
            items = re.findall(r'\d+\.\s*[^\n]+', content)
            formatted_items = []
            for item in items:
                item = item.strip()
                # إضافة سطر جديد قبل كل نقطة مرقمة
                formatted_items.append('\n' + item)
            return ''.join(formatted_items).strip()
        
        # معالجة القوائم النقطية
        def format_bullet(match):
            content = match.group(0).strip()
            # تقسيم إلى عناصر فردية
            items = re.findall(r'[•\-*]\s*[^\n]+', content)
            formatted_items = []
            for item in items:
                item = item.strip()
                # إضافة سطر جديد قبل كل نقطة
                formatted_items.append('\n' + item)
            return ''.join(formatted_items).strip()
        
        # تطبيق التنسيق على القوائم المرقمة
        text = re.sub(numbered_pattern, format_numbered, text, flags=re.MULTILINE | re.DOTALL)
        
        # تطبيق التنسيق على القوائم النقطية
        text = re.sub(bullet_pattern, format_bullet, text, flags=re.MULTILINE | re.DOTALL)
        
        return text
    
    # تطبيق التنسيق بشكل متكرر لضمان معالجة جميع القوائم
    previous_text = ""
    while text != previous_text:
        previous_text = text
        text = format_lists(text)
    
    # تنظيف المسافات الزائدة بين الأسطر
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def bold_important_words(text):
    """إضافة تنسيق Bold للكلمات المهمة تلقائياً"""
    if not text:
        return text
    
    # الكلمات المهمة بالعربية والإنجليزية
    important_words = [
        'مهم', 'ملاحظة', 'تنبيه', 'Important', 'Note', 'Warning'
    ]
    
    for word in important_words:
        # البحث عن الكلمة متبوعة بنقطتين مع مسافات محتملة
        pattern = rf'\b{re.escape(word)}\s*:'
        replacement = f'**{word}:**'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # أيضًا معالجتها إذا كانت في بداية السطر
        pattern_start = rf'^\s*{re.escape(word)}\s*:'
        replacement_start = f'**{word}:**'
        text = re.sub(pattern_start, replacement_start, text, flags=re.IGNORECASE | re.MULTILINE)
    
    return text

def format_arabic_text(text):
    """تنسيق النص العربي بشكل احترافي مع الالتزام بالتنسيق الإجباري"""
    if not text:
        return text
    
    # تحويل الأرقام أولاً
    text = convert_english_numbers_to_arabic(text)
    
    # تطبيق التنسيق الإجباري للقوائم
    text = enforce_list_formatting(text, 'arabic')
    
    # إضافة تنسيق Bold للكلمات المهمة
    text = bold_important_words(text)
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
            
        # تحسين القوائم المرقمة (بعد التنسيق الإجباري)
        if re.match(r'^\d+\.', line):
            line = re.sub(r'^(\d+)\.', r'\1.', line)
            line = convert_english_numbers_to_arabic(line)
        
        # تحسين النقاط النقطية
        elif re.match(r'^[•]', line):
            line = re.sub(r'^[•]\s*', '• ', line)
        
        formatted_lines.append(line)
    
    formatted_text = '\n'.join(formatted_lines)
    
    # التنظيف النهائي
    formatted_text = re.sub(r'\n\s*\n', '\n\n', formatted_text)
    formatted_text = re.sub(r' +', ' ', formatted_text)
    
    return formatted_text.strip()

def format_english_text(text):
    """تنسيق النص الإنجليزي بشكل احترافي مع الالتزام بالتنسيق الإجباري"""
    if not text:
        return text
    
    # تطبيق التنسيق الإجباري للقوائم أولاً
    text = enforce_list_formatting(text, 'english')
    
    # إضافة تنسيق Bold للكلمات المهمة
    text = bold_important_words(text)
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
            
        # تحسين القوائم المرقمة (بعد التنسيق الإجباري)
        if re.match(r'^\d+\.', line):
            line = re.sub(r'^(\d+)\.', r'\1. ', line)
        
        # تحسين النقاط النقطية
        elif re.match(r'^[-]', line):
            line = re.sub(r'^[-]\s*', '- ', line)
        
        formatted_lines.append(line)
    
    formatted_text = '\n'.join(formatted_lines)
    
    # التنظيف النهائي
    formatted_text = re.sub(r'\n\s*\n', '\n\n', formatted_text)
    formatted_text = re.sub(r' +', ' ', formatted_text)
    
    return formatted_text.strip()

def format_final_response(text, language):
    """تنسيق الرد النهائي بشكل احترافي مع الالتزام بالتنسيق الإجباري"""
    if not text:
        return text
    
    # التنظيف الأساسي
    text = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9\s\.\,\!\?\-\:\;\(\)\%\&\"\'\@\#\$\*\+\=\/\<\>\[\]\\\n]', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    # التنسيق حسب اللغة مع الالتزام بالتنسيق الإجباري
    if language == 'arabic':
        return format_arabic_text(text)
    else:
        return format_english_text(text)

def rewrite_team_member_info(member_key, language):
    """إعادة كتابة معلومات أعضاء الفريق بشكل طبيعي وسلس"""
    if member_key not in FOUNDERS_INFO:
        return "لم يتم العثور على المعلومات المطلوبة." if language == 'arabic' else "Requested information not found."
    
    member_info = FOUNDERS_INFO[member_key][language]
    
    if language == 'arabic':
        if member_key == "hayder":
            return f"""🛢️ **{member_info['name']}** - {member_info['role']}

{member_info['background']}، {member_info['education']}. {member_info['heritage']}، و{member_info['achievement']}.

📧 **للتواصل**: {member_info['contact']}"""
        
        elif member_key == "ali":
            return f"""👨‍💻 **{member_info['name']}**

{member_info['role']} {member_info['background']}. {member_info['education']}، {member_info['heritage']} ({member_info['birth']}).

📧 **للتواصل**: {member_info['contact']}"""
        
        elif member_key == "noor":
            return f"""👩‍💻 **{member_info['name']}**

{member_info['role']} {member_info['background']}. {member_info['education']}، {member_info['heritage']} ({member_info['birth']})، و{member_info['future']}.

📧 **للتواصل**: {member_info['contact']}"""
        
        elif member_key == "arzo":
            return f"""📊 **{member_info['name']}**

{member_info['role']} {member_info['background']}. {member_info['heritage']}، و{member_info['future']}.

📧 **للتواصل**: {member_info['contact']}"""
    
    else:  # English
        if member_key == "hayder":
            return f"""🛢️ **{member_info['name']}** - {member_info['role']}

{member_info['background']}, {member_info['education']}. {member_info['heritage']}, and {member_info['achievement']}.

📧 **Contact**: {member_info['contact']}"""
        
        elif member_key == "ali":
            return f"""👨‍💻 **{member_info['name']}**

{member_info['role']} who is {member_info['background']}. {member_info['education']} from {member_info['heritage']} ({member_info['birth']}).

📧 **Contact**: {member_info['contact']}"""
        
        elif member_key == "noor":
            return f"""👩‍💻 **{member_info['name']}**

{member_info['role']} who is {member_info['background']}. {member_info['education']}, {member_info['heritage']} ({member_info['birth']}), with a {member_info['future']}.

📧 **Contact**: {member_info['contact']}"""
        
        elif member_key == "arzo":
            return f"""📊 **{member_info['name']}**

{member_info['role']} and {member_info['background']}. {member_info['heritage']}, with an {member_info['future']}.

📧 **Contact**: {member_info['contact']}"""

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

        # ====== SYSTEM PROMPT المحسن والاحترافي مع التنسيق الإجباري ======
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

📝 **التنسيق الإجباري للقوائم**:
- عند الإجابة عن أي سؤال يحتوي على أجزاء أو خطوات أو تعداد نقطي، يجب أن تكتب كل نقطة في سطر مستقل
- استخدم هذا التنسيق فقط:
  
1. [النقطة الأولى]
2. [النقطة الثانية] 
3. [النقطة الثالثة]

- أضف سطر جديد قبل كل رقم، ولا تكتب أي نقطة في نفس السطر مع نقطة أخرى

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
- التزم بالتنسيق الإجباري للقوائم في كل الإجابات
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

📝 **Mandatory List Formatting**:
- When answering any question containing parts, steps, or bullet points, you MUST write each point on a separate line
- Use this format ONLY:
  
1. [First point]
2. [Second point]
3. [Third point]

- Add a newline before each number, and never write two points on the same line

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
- Strictly adhere to mandatory list formatting in all responses
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
            reply = rewrite_team_member_info("hayder", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        elif any(keyword in msg_lower for keyword in ali_keywords_arabic + [k.lower() for k in ali_keywords_english]):
            reply = rewrite_team_member_info("ali", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        elif any(keyword in msg_lower for keyword in noor_keywords_arabic + [k.lower() for k in noor_keywords_english]):
            reply = rewrite_team_member_info("noor", user_language)
            add_message_to_history(session_id, "user", user_msg)
            add_message_to_history(session_id, "assistant", reply)
            return jsonify({"reply": reply, "session_id": session_id})

        elif any(keyword in msg_lower for keyword in arzo_keywords_arabic + [k.lower() for k in arzo_keywords_english]):
            reply = rewrite_team_member_info("arzo", user_language)
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
        
        # ✅ تطبيق التنسيق المحسن على الرد مع الالتزام بالتنسيق الإجباري
        formatted_reply = format_final_response(reply, user_language)
        
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
