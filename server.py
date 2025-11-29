from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# ====== CORS FIX ======
CORS(app, resources={
    r"/*": {
        "origins": ["https://petroai-iq.web.app", "*"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

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
    }
}

# ====== قاعدة بيانات الأسئلة الشائعة ======
OIL_GAS_KNOWLEDGE = {
    "arabic": {
        "drilling": """🛢️ **تقنيات الحفر الحديثة**

• **الحفر الأفقي**: يزيد مساحة التماس مع المكمن
• **الحرمائي**: يستخدم البخار لاستخراج النفط الثقيل  
• **التكسير الهيدروليكي**: لزيادة نفاذية الصخور
• **الحفر البحري**: في المياه العميقة

**المعدات المتطورة**:
١. أنظمة الحفر الآلي
٢. مستشعرات الوقت الحقيقي
٣. طفالات الحفر الذكية""",

        "production": """⚡ **تحسين إنتاجية الحقول النفطية**

**استراتيجيات التحسين**:
• تحسين أنظمة الرفع الاصطناعي (ESP)
• حقن الغاز أو الماء للحفاظ على الضغط
• استخدام المحفزات الكيميائية
• المراقبة المستمرة لأداء الآبار

**نتائج التحسين**:
١. زيادة معدل الاستخراج
٢. إطالة عمر الحقل
٣. تقليل التكاليف""",

        "esp": """🔧 **أنظمة المضخات الغاطسة (ESP)**

**مكونات النظام**:
• المضخة الغاطسة
• المحرك الكهربائي
• كابلات القدرة
• أنظمة التحكم

**مميزات ESP**:
١. كفاءة عالية في الإنتاج
٢. مناسبة للآبار العميقة
٣. سعة إنتاجية كبيرة""",

        "reservoir": """🏭 **هندسة المكامن**

**أنواع المكامن**:
• مكامن رملية
• مكامن كربونات
• مكامن صخرية

**تقنيات التقييم**:
١. التسجيل الجيوفيزيائي
٢. تحليل البيانات الزلزالية
٣. نمذجة المكامن ثلاثية الأبعاد"""
    },
    "english": {
        "drilling": """🛢️ **Modern Drilling Technologies**

• **Horizontal Drilling**: Increases reservoir contact area
• **Thermal Recovery**: Uses steam for heavy oil extraction  
• **Hydraulic Fracturing**: Enhances rock permeability
• **Offshore Drilling**: In deepwater environments

**Advanced Equipment**:
1. Automated drilling systems
2. Real-time sensors
3. Smart drilling fluids""",

        "production": """⚡ **Improving Oil Field Productivity**

**Optimization Strategies**:
• Enhance artificial lift systems (ESP)
• Implement gas/water injection for pressure maintenance
• Use chemical stimulants
• Continuous well performance monitoring

**Expected Results**:
1. Increased recovery rates
2. Extended field life
3. Reduced operational costs""",

        "esp": """🔧 **Electrical Submersible Pump (ESP) Systems**

**System Components**:
• Submersible pump
• Electric motor
• Power cables
• Control systems

**ESP Advantages**:
1. High production efficiency
2. Suitable for deep wells
3. Large production capacity""",

        "reservoir": """🏭 **Reservoir Engineering**

**Reservoir Types**:
• Sandstone reservoirs
• Carbonate reservoirs
• Shale formations

**Evaluation Techniques**:
1. Geophysical logging
2. Seismic data analysis
3. 3D reservoir modeling"""
    }
}

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

def convert_english_numbers_to_arabic(text):
    """تحويل الأرقام الإنجليزية إلى عربية"""
    number_map = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    }
    
    for eng_num, arabic_num in number_map.items():
        text = text.replace(eng_num, arabic_num)
    
    return text

def format_arabic_text(text):
    """تنسيق النص العربي بشكل احترافي"""
    text = convert_english_numbers_to_arabic(text)
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
            
        if re.match(r'^\d+\.', line):
            line = re.sub(r'^(\d+)\.', r' \1.', line)
            line = convert_english_numbers_to_arabic(line)
        
        elif re.match(r'^[-•*]', line):
            line = re.sub(r'^[-•*]\s*', '• ', line)
        
        formatted_lines.append(line)
    
    formatted_text = '\n'.join(formatted_lines)
    formatted_text = re.sub(r'\n\s*\n', '\n\n', formatted_text)
    formatted_text = re.sub(r' +', ' ', formatted_text)
    
    return formatted_text.strip()

def format_english_text(text):
    """تنسيق النص الإنجليزي بشكل احترافي"""
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
            
        if re.match(r'^\d+\.', line):
            line = re.sub(r'^(\d+)\.', r'\1. ', line)
        
        elif re.match(r'^[-•*]', line):
            line = re.sub(r'^[-•*]\s*', '- ', line)
        
        formatted_lines.append(line)
    
    formatted_text = '\n'.join(formatted_lines)
    formatted_text = re.sub(r'\n\s*\n', '\n\n', formatted_text)
    formatted_text = re.sub(r' +', ' ', formatted_text)
    
    return formatted_text.strip()

def format_final_response(text, language):
    """تنسيق الرد النهائي بشكل احترافي"""
    if not text:
        return text
    
    text = re.sub(r'[^\u0600-\u06FFa-zA-Z0-9\s\.\,\!\?\-\:\;\(\)\%\&\"\'\@\#\$\*\+\=\/\<\>\[\]\\\n]', '', text)
    text = re.sub(r'\s+', ' ', text)
    
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
    
    else:  # English
        if member_key == "hayder":
            return f"""🛢️ **{member_info['name']}** - {member_info['role']}

{member_info['background']}, {member_info['education']}. {member_info['heritage']}, and {member_info['achievement']}.

📧 **Contact**: {member_info['contact']}"""
        
        elif member_key == "ali":
            return f"""👨‍💻 **{member_info['name']}**

{member_info['role']} who is {member_info['background']}. {member_info['education']} from {member_info['heritage']} ({member_info['birth']}).

📧 **Contact**: {member_info['contact']}"""

def get_oil_gas_response(user_message, language):
    """إرجاع ردود ذكية بناءً على السؤال"""
    msg_lower = user_message.lower()
    
    if language == "arabic":
        if any(word in msg_lower for word in ["حفر", "حفار", "تقنيات الحفر", "drilling"]):
            return OIL_GAS_KNOWLEDGE["arabic"]["drilling"]
        elif any(word in msg_lower for word in ["إنتاج", "إنتاجية", "حقول", "production"]):
            return OIL_GAS_KNOWLEDGE["arabic"]["production"]
        elif any(word in msg_lower for word in ["مضخات", "غاطس", "esp", "مضخة"]):
            return OIL_GAS_KNOWLEDGE["arabic"]["esp"]
        elif any(word in msg_lower for word in ["مكمن", "مكامن", "reservoir"]):
            return OIL_GAS_KNOWLEDGE["arabic"]["reservoir"]
        else:
            return """🛢️ **مساعد OILNOVA المتخصص**

أنا متخصص في مجال هندسة النفط والغاز. يمكنني مساعدتك في:

• **تقنيات الحفر** والإنتاج
• **أنظمة المضخات الغاطسة (ESP)**
• **هندسة المكامن** والاستكشاف
• **تحسين إنتاجية** الحقول

اطرح سؤالك التقني وسأجيبك بأفضل المعلومات!"""
    
    else:  # English
        if any(word in msg_lower for word in ["drill", "drilling", "technolog"]):
            return OIL_GAS_KNOWLEDGE["english"]["drilling"]
        elif any(word in msg_lower for word in ["production", "productivity", "field"]):
            return OIL_GAS_KNOWLEDGE["english"]["production"]
        elif any(word in msg_lower for word in ["esp", "pump", "submersible"]):
            return OIL_GAS_KNOWLEDGE["english"]["esp"]
        elif any(word in msg_lower for word in ["reservoir", "formation"]):
            return OIL_GAS_KNOWLEDGE["english"]["reservoir"]
        else:
            return """🛢️ **OILNOVA Specialized Assistant**

I specialize in oil and gas engineering. I can help you with:

• **Drilling technologies** and operations
• **ESP systems** and artificial lift
• **Reservoir engineering** and exploration
• **Field productivity** optimization

Ask your technical question and I'll provide the best information!"""

@app.route("/")
def home():
    return "OILNOVA CHAT BACKEND IS RUNNING OK - ENHANCED PROFESSIONAL VERSION"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_msg = data.get("message", "").strip()
        session_id = data.get("session_id", "default")

        if not user_msg:
            return jsonify({"error": "الرسالة فارغة"}), 400

        user_language = detect_language(user_msg)
        
        # ====== التحقق من طلبات معلومات الفريق ======
        msg_lower = user_msg.lower()
        
        hayder_keywords_arabic = ["حيدر", "هايدر", "نسيم", "المؤسس", "مؤسس"]
        hayder_keywords_english = ["hayder", "naseem", "founder", "owner"]
        
        ali_keywords_arabic = ["علي بلال", "علي", "بلال"]
        ali_keywords_english = ["ali", "bilal"]

        if any(keyword in msg_lower for keyword in hayder_keywords_arabic + [k.lower() for k in hayder_keywords_english]):
            reply = rewrite_team_member_info("hayder", user_language)
            return jsonify({"reply": reply, "session_id": session_id})

        elif any(keyword in msg_lower for keyword in ali_keywords_arabic + [k.lower() for k in ali_keywords_english]):
            reply = rewrite_team_member_info("ali", user_language)
            return jsonify({"reply": reply, "session_id": session_id})

        # ====== الحصول على رد ذكي ======
        ai_reply = get_oil_gas_response(user_msg, user_language)
        
        # ✅ تطبيق التنسيق المحسن
        formatted_reply = format_final_response(ai_reply, user_language)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
