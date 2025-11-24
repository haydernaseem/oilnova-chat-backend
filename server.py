import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# ================== إعدادات أساسية ==================
app = Flask(__name__)

# السماح للفرونت من Firebase + السماح مؤقتاً لباقي الأورجنز
CORS(
    app,
    resources={r"/*": {"origins": ["https://petroai-iq.web.app", "*"]}},
    supports_credentials=True,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oilnova-chat-backend")

# ================== عميل Groq ==================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set in environment variables")
    # ما نوقف السيرفر، بس نخلي الرسالة تظهر في الردود

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ================== معلومات المنصة و الفريق ==================
OILNOVA_CONTEXT_AR = """
أنت OILNOVA Chat AI، مساعد ذكي متخصص في:
- هندسة النفط والغاز (Drilling, Reservoir, Production, Artificial Lift, Logging, Well Testing, Data Analysis)
- الإجابة عن الأسئلة المتعلقة بمنصة OILNOVA وفريق العمل.

معلومات مؤكَّدة يجب الالتزام بها عند الإجابة:

1) مؤسس المنصة:
- الاسم: حيدر نسيم السامرائي
- التخصص: مهندس نفط ومبرمج، وصانع محتوى
- المدينة: سامراء – العراق
- التخرج: جامعة كركوك، كلية الهندسة، قسم النفط، سنة 2025
- التقدير: جيد جداً

2) أعضاء فريق OILNOVA:
- علي بلال:
  - خريج هندسة نفط، نفس سنة التخرج 2025
  - من الموصل – العراق
  - التقدير: جيد
  - خلفيته عربية

- نور كنعان:
  - خريجة هندسة نفط، سنة 2025
  - من الموصل – العراق
  - كردية
  - التقدير: جيد

- أرزو متين:
  - خريجة هندسة نفط، سنة 2025
  - من كركوك – العراق
  - تركمانية
  - التقدير: جيد

سياسة الإجابة عن فريق العمل:
- إذا كان السؤال: "من هو مؤسس المنصة؟" أو "منو مؤسس OILNOVA؟"
  → أجب فقط عن المؤسس: حيدر نسيم السامرائي، مع وصف مختصر عنه.
- إذا كان السؤال عن أحد أعضاء الفريق بالاسم (مثلاً: منو علي بلال؟ أو عرفني على نور كنعان؟)
  → أجب بتفاصيل الشخص المطلوب، ويمكنك الإشارة باختصار إلى أنه ضمن فريق OILNOVA الذي أسسه حيدر.
- إذا كان السؤال عن "فريق OILNOVA" بشكل عام
  → اذكر المؤسس ثم أعضاء الفريق الأربعة باختصار.

سياسة اللغة عند الأسئلة باللغة العربية:
- أجب باللغة العربية الفصحى الواضحة، ويمكنك استخدام لهجة عراقية خفيفة عند الاقتباس أو الشرح، لكن الأساس فصيح.
- استخدم اللغة الإنجليزية فقط عند:
  - كتابة المصطلحات التقنية (مثل ESP, IPR, VLP, GOR, API gravity, etc.)
  - كتابة المعادلات أو الرموز.
- لا تخلط كلمات إنجليزية عشوائية داخل جملة عربية (مثل: belki, maybe, ok bro).
- حافظ على تنسيق نظيف وسهل القراءة، بدون خربطة حروف أو دمج غريب بين اللغتين.

سياسة المجال العلمي:
- ركّز دائماً على مواضيع النفط والغاز:
  - Drilling Engineering
  - Reservoir Engineering
  - Production Engineering
  - Artificial Lift (خاصة ESP)
  - Well Logging & Interpretation
  - Well Testing
  - Petroleum Economics بشكل مبسط
  - Data Analysis و AI/ML في هندسة النفط
- إذا كان السؤال خارج المجال (مثلاً طبخ، ألعاب، مواضيع سياسية بحتة):
  - أجب باحترام أنك مخصص لهندسة النفط ومنصة OILNOVA، ويمكنك إعطاء نصيحة عامة قصيرة فقط.

طريقة الإجابة:
- كن رسميًا، مهنيًا، وواضحًا.
- استخدم فقرات قصيرة ونقاط عند الحاجة.
- إذا كان السؤال تقنيًا، اذكر المبدأ، ثم المعادلة (إن وجدت)، ثم مثال بسيط.
"""

OILNOVA_CONTEXT_EN = """
You are OILNOVA Chat AI, a domain-specialized assistant for:
- Petroleum engineering (Drilling, Reservoir, Production, Artificial Lift, Logging, Well Testing, Data Analysis)
- Questions about the OILNOVA platform and its team.

Confirmed facts:

1) Founder:
- Name: Haider Naseem Al-Samarrai
- Role: Petroleum engineer, programmer, and content creator
- City: Samarra, Iraq
- Graduation: University of Kirkuk, College of Engineering, Petroleum Department, Class of 2025
- Grade: Very Good

2) Team members:
- Ali Bilal:
  - Petroleum engineering graduate, Class of 2025
  - From Mosul, Iraq
  - Grade: Good
  - Arabic background

- Noor Kanaan:
  - Petroleum engineering graduate, Class of 2025
  - From Mosul, Iraq
  - Kurdish
  - Grade: Good

- Arzu Metin:
  - Petroleum engineering graduate, Class of 2025
  - From Kirkuk, Iraq
  - Turkmen
  - Grade: Good

Answering policy about the team:
- If the user asks “Who is the founder of the platform / OILNOVA?”
  → Only answer about the founder, Haider Naseem Al-Samarrai, with a short professional description.
- If the user asks about a specific team member by name
  → Answer with details about that person, and you may briefly mention they are part of the OILNOVA team founded by Haider.
- If the user asks about the OILNOVA team in general
  → Mention the founder and then the three team members with a short description.

Language policy:
- If the question is in English → answer in English.
- Use clear, professional language suitable for petroleum engineers and students.
- When writing in English, you may of course use standard technical terms and formulas.

Domain policy:
- Focus strictly on oil & gas topics:
  - Drilling Engineering
  - Reservoir Engineering
  - Production Engineering
  - Artificial Lift (especially ESP)
  - Well Logging & Interpretation
  - Well Testing
  - Basic Petroleum Economics
  - Data Analysis and AI/ML in petroleum engineering
- For clearly irrelevant questions (e.g., cooking recipes, purely political topics), politely mention that you are specialized in petroleum engineering and OILNOVA, and optionally provide a very short, generic suggestion.

Style:
- Be concise but complete.
- Use bullet points when helpful.
- For technical topics, explain the concept, then equations (if relevant), then a simple example.
"""

# ================== دوال مساعدة ==================


def detect_language(text: str) -> str:
    """
    محاولة بسيطة لمعرفة إذا كانت الرسالة عربية أو إنجليزية.
    لو فيها أحرف عربية → نعتبرها عربية.
    """
    for ch in text:
        if "\u0600" <= ch <= "\u06FF":
            return "arabic"
    return "english"


def build_system_prompt(lang: str) -> str:
    """
    يرجّع الـ system prompt المناسب حسب اللغة المتوقعة.
    """
    if lang == "arabic":
        return OILNOVA_CONTEXT_AR
    else:
        return OILNOVA_CONTEXT_EN


def call_groq_chat(user_message: str) -> str:
    """
    استدعاء Groq Chat Completion وإرجاع النص فقط.
    """
    if client is None:
        return (
            "⚠️ عذراً، خادم OILNOVA Chat AI غير قادر حالياً على الاتصال بمحرك الذكاء الاصطناعي.\n"
            "يبدو أن مفتاح GROQ_API_KEY غير مضبوط في الخادم، يرجى مراجعة الإعدادات."
        )

    # اكتشاف لغة المستخدم
    lang = detect_language(user_message)
    system_prompt = build_system_prompt(lang)

    # تعليمات إضافية قوية لمنع خربطة اللغة
    if lang == "arabic":
        extra_instruction = """
قواعد صارمة للغة:
- أجب باللغة العربية الفصحى فقط.
- يُسمح باستخدام رموز أو اختصارات إنجليزية للمصطلحات التقنية (مثل ESP, IPR, VLP, GOR).
- لا تكتب كلمات إنجليزية عشوائية داخل الجملة العربية (مثل: maybe, bro, ok, belki).
- تأكد أن يكون النص منسقاً ونظيفاً، بدون خلط غريب بين الأبجدية العربية واللاتينية.
"""
    else:
        extra_instruction = """
Language rules:
- Answer in clear, professional English.
- Use appropriate petroleum engineering technical terminology.
"""

    full_system_prompt = system_prompt + "\n\n" + extra_instruction

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-specfree",  # نموذج حديث مدعوم من Groq
            messages=[
                {"role": "system", "content": full_system_prompt},
                {
                    "role": "user",
                    "content": user_message.strip(),
                },
            ],
            temperature=0.25,
            max_tokens=900,
            top_p=0.9,
        )

        reply_text = completion.choices[0].message.content
        return reply_text.strip()
    except Exception as e:
        logger.exception("Error while calling Groq API")
        return f"⚠️ حدث خطأ داخلي أثناء توليد الإجابة من OILNOVA Chat AI.\nتفاصيل تقنية: {str(e)}"


# ================== المسارات ==================


@app.route("/", methods=["GET", "HEAD"])
def root():
    """
    مسار بسيط للـ health check حتى Render ما يعطي 404.
    """
    if request.method == "HEAD":
        return ("", 200)
    return ("OILNOVA Chat Backend is running.", 200)


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        # يتم التعامل معها غالباً من flask-cors، لكن نرجِّع 200 احتياطاً
        return ("", 200)

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")

    if not user_message or not isinstance(user_message, str):
        return jsonify({"error": "Missing 'message' field in request body."}), 400

    logger.info("New chat message: %s", user_message[:200])

    reply = call_groq_chat(user_message)
    return jsonify({"reply": reply})


# ================== نقطة تشغيل محلية ==================
if __name__ == "__main__":
    # للتشغيل المحلي: python server.py
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
