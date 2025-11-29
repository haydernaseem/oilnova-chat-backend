import os
import re
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =========================== GROQ ONLY ===========================
from groq import Groq

# =========================== Firebase ===========================
HAS_FIREBASE = False
try:
    import firebase_admin
    from firebase_admin import credentials, db
    HAS_FIREBASE = True
except ImportError:
    firebase_admin = None

# =========================== إعداد CORS ===========================

FRONTEND_ORIGINS = [
    "https://petroai-iq.web.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "*",
]

# =========================== الجلسات ===========================

conversations: Dict[str, Dict[str, Any]] = {}

# =========================== معلومات الفريق ===========================

FOUNDERS_INFO = {
    "hayder": {
        "arabic": """المهندس حيدر نسيم السامرائي، مهندس نفط ومحلل بيانات ومبرمج واجهات أمامية ومطور Firebase كباك إند. خريج جامعة كركوك / كلية الهندسة / قسم هندسة النفط لعام 2025، ومن عشيرة السادة البنيسان الحسنية في سامراء. أسس منصة OILNOVA كأحد أوائل المنصات العربية النفطية التي تعتمد على تقنيات الذكاء الاصطناعي لخدمة قطاع النفط والغاز.""",
        "english": """Engineer Hayder Naseem Al-Samarrai is a petroleum engineer, data analyst, and frontend developer with Firebase backend experience. He graduated from Kirkuk University, College of Engineering, Petroleum Engineering Department (2025), and belongs to Al-Sadah Al-Benisian Al-Hasaniyah tribe in Samarra. He founded the OILNOVA platform as one of the first Arabic oil and gas platforms powered by AI technologies."""
    },

    "ali": {
        "arabic": """علي بلال عبدالله خلف، مبرمج بايثون شغوف بالتكنولوجيا ومن مدينة الموصل / ناحية زمار / عشيرة الجبور. خريج هندسة نفط. يساهم في تطوير الأنظمة الذكية والبرمجيات داخل منصة OILNOVA.""",
        "english": """Ali Bilal Abdullah Khalaf is a Python programmer passionate about technology, from Mosul/Al-Zumar district. He is a petroleum engineering graduate contributing to backend and smart tools development inside OILNOVA."""
    },

    "noor": {
        "arabic": """نور كنعان حيدر، مبرمجة بايثون وشغوفة بتحليل البيانات، كردية من كركوك من مواليد 2004 وخريجة هندسة نفط لعام 2025. تمتلك مساراً مهنياً متميزاً في تطوير الأدوات الذكية ضمن فريق OILNOVA.""",
        "english": """Noor Kanaan Haider is a Python programmer and data analysis enthusiast from Kirkuk, born in 2004. She is a petroleum engineering graduate and part of the OILNOVA smart tools development team."""
    },

    "arzo": {
        "arabic": """أرزو متين، مهندسة تركمانية من كركوك مواليد 2004، تعمل كمحللة بيانات ومبرمجة بايثون. من أعضاء فريق OILNOVA الأساسيين، وتمتلك مساراً مهنياً قوياً في تحليل البيانات.""",
        "english": """Arzu Metin is a Turkmen engineer from Kirkuk, born 2004, working as a data analyst and Python programmer. She is a key OILNOVA team member with strong potential in data analysis."""
    }
}

# =========================== Firebase Init ===========================

def init_firebase():
    global HAS_FIREBASE
    if not HAS_FIREBASE:
        print("⚠ Firebase SDK Not Installed.")
        return

    if firebase_admin._apps:
        return

    creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    db_url = os.environ.get("FIREBASE_DB_URL")

    if not creds_json or not db_url:
        print("⚠ Firebase Missing Credentials.")
        HAS_FIREBASE = False
        return

    import json
    try:
        cred_dict = json.loads(creds_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {"databaseURL": db_url})
        HAS_FIREBASE = True
        print("✅ Firebase Ready")
    except Exception as e:
        print(f"❌ Firebase Error: {e}")
        HAS_FIREBASE = False


def save_to_firebase(user_id, question, answer, lang, session_id, user_email, user_name):
    if not HAS_FIREBASE:
        return

    try:
        t = str(int(datetime.utcnow().timestamp() * 1000))

        ref = db.reference("chat_messages").child(t)
        ref.set({
            "userId": user_id or "anonymous",
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat(),
            "language": lang,
            "sessionId": session_id,
            "userEmail": user_email or "",
            "userName": user_name or "",
        })

    except Exception as e:
        print("⚠ Firebase Save Error:", e)


# =========================== لغة - تنظيف ===========================

def detect_language(text):
    ar = len(re.findall(r'[\u0600-\u06FF]', text))
    en = len(re.findall(r'[a-zA-Z]', text))
    return "arabic" if ar >= en else "english"


def clean_format(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\u0600-\u06FFa-zA-Z0-9 \n\.\,\!\?\-\:\;\(\)]", "", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


# =========================== System Prompts ===========================

PROMPT_AR = """
أنت مساعد OILNOVA الذكي، متخصص في هندسة النفط والغاز فقط.
التزم بالدقة وبشرح واضح ومنظم.
"""

PROMPT_EN = """
You are the OILNOVA Smart Assistant, specialized only in oil & gas engineering.
Use structured, precise explanations.
"""

def sys_prompt(lang):
    return PROMPT_AR if lang == "arabic" else PROMPT_EN

# =========================== Team Bio via Groq ===========================

def team_bio(key, lang):
    if key not in FOUNDERS_INFO:
        return "غير موجود." if lang == "arabic" else "Not found."

    base = FOUNDERS_INFO[key][lang]

    try:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        comp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أعد الصياغة باحتراف." if lang=="arabic" else "Rewrite professionally."},
                {"role": "user", "content": base},
            ],
            temperature=0.5,
            max_tokens=300
        )
        return clean_format(comp.choices[0].message.content)
    except:
        return clean_format(base)

# =========================== LLAMA Chat ===========================

def chat_groq(messages):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    comp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    return comp.choices[0].message.content

# =========================== جلسات ===========================

def get_session(sid):
    if sid not in conversations:
        conversations[sid] = {"messages": [], "last": datetime.utcnow()}
    else:
        conversations[sid]["last"] = datetime.utcnow()
    return conversations[sid]


def add_msg(sid, role, content):
    s = get_session(sid)
    s["messages"].append({"role": role, "content": content})
    s["messages"] = s["messages"][-20:]

# =========================== FastAPI ===========================

app = FastAPI(title="OILNOVA GROQ Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_firebase()

# =========================== Models ===========================

class ChatReq(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None


class ChatRes(BaseModel):
    reply: str
    session_id: str
    detected_language: str


# =========================== Endpoints ===========================

@app.get("/")
def home():
    return {"status": "ok", "backend": "Groq Only", "v": 2.0}


@app.post("/chat", response_model=ChatRes)
def chat(req: ChatReq):

    msg = req.message.strip()
    if not msg:
        raise HTTPException(400, "Empty message.")

    lang = detect_language(msg)
    session = get_session(req.session_id)

    msg_low = msg.lower()

    # ==== team
    TEAM_KEYS = {
        "hayder": ["حيدر", "هايدر", "hayder", "naseem"],
        "ali": ["علي", "ali", "bilal"],
        "noor": ["نور", "noor", "kanaan"],
        "arzo": ["ارزو", "arzu", "metin"],
    }

    for key, words in TEAM_KEYS.items():
        if any(w in msg_low for w in words):
            rep = team_bio(key, lang)
            add_msg(req.session_id, "user", msg)
            add_msg(req.session_id, "assistant", rep)
            save_to_firebase(req.user_id, msg, rep, lang, req.session_id, req.user_email, req.user_name)
            return ChatRes(reply=rep, session_id=req.session_id, detected_language=lang)

    # ==== main chat
    messages = [{"role": "system", "content": sys_prompt(lang)}]
    messages.extend(session["messages"])
    messages.append({"role": "user", "content": msg})

    raw = chat_groq(messages)
    cleaned = clean_format(raw)

    add_msg(req.session_id, "user", msg)
    add_msg(req.session_id, "assistant", cleaned)

    save_to_firebase(req.user_id, msg, cleaned, lang, req.session_id, req.user_email, req.user_name)

    return ChatRes(reply=cleaned, session_id=req.session_id, detected_language=lang)


@app.get("/start_session")
def start():
    sid = str(uuid.uuid4())
    get_session(sid)
    return {"session_id": sid}


@app.post("/clear_history")
def clear(req: ChatReq):
    if req.session_id in conversations:
        conversations[req.session_id]["messages"] = []
    return {"message": "cleared", "session_id": req.session_id}


@app.get("/get_session_info")
def info():
    return {"active": len(conversations), "sessions": list(conversations.keys())}
