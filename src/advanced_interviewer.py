# import arrcorr  
import speech_recognition as sr
import win32com.client
import json
from llama_cpp import Llama
import random
import tkinter as tk
from tkinter import filedialog
import PyPDF2
import os
import gdown
from rag_search import JobRAG
print("⏳ جاري تحميل العقل المدبر والنظام الصوتي...")

# ==========================================
# 1. إعدادات الصوت (STT & TTS)
# ==========================================
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Rate = 1

def speak(text):
    print("🔊 (CareerAI يتحدث...)")
    try:
        speaker.Speak(text)
    except Exception as e:
        pass

recognizer = sr.Recognizer()

def listen_until_done():
    full_answer = ""
    with sr.Microphone() as source:
        print("\n🎤 المايك مفتوح... (قل 'I am done' للإنهاء)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.pause_threshold = 2.0 
        
        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                text = recognizer.recognize_whisper(audio, model="base.en").strip()
                if text and len(text) > 2: 
                    print(f"🗣️ سمعتك: {text}")
                    full_answer += " " + text
                    if "i am done" in text.lower() or "i'm done" in text.lower():
                        print("✅ تم استلام الإجابة!")
                        break
            except sr.WaitTimeoutError:
                continue
            except Exception:
                break
    return full_answer.lower().replace("i am done", "").replace("i'm done", "").strip()

# ==========================================
# 2. إعداد المودل (LLM)
# ==========================================

# ==========================================
# إعداد مسار المودل وتحميله التلقائي من درايف
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "llm")
MODEL_PATH = os.path.join(MODEL_DIR, "qwen2.5-3b-instruct.Q4_K_M.gguf")

# إذا المجلد llm مو موجود، يسويه تلقائياً
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# إذا المودل مو موجود، بيحمله من رابطك في درايف مباشرة!
if not os.path.exists(MODEL_PATH):
    print("\n⏳ المودل غير موجود! جاري التحميل من قوقل درايف تلقائياً...")
    print("⚠️ (حجم الملف كبير، قد يستغرق بعض الوقت حسب سرعة النت عندك)")
    
    # الـ ID الخاص بملفك في قوقل درايف
    FILE_ID = '1I3XIB5wZ324nOG-oEihHEnIkMizpxBtJ' 
    url = f'https://drive.google.com/uc?id={FILE_ID}'
    
    # أمر التحميل
    gdown.download(url, MODEL_PATH, quiet=False)
    print("✅ تم تحميل المودل بنجاح! بنكمل تشغيل المقابلة الحين...\n")
    
print("⏳ جاري تهيئة المودل في الذاكرة (LLM)...")
llm = Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=4, verbose=False)
print("⏳ جاري تهيئة محرك البحث RAG...")
rag_engine = JobRAG()
def ask_llm(prompt, temp=0.6, max_tokens=150):
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens, temperature=temp
    )
    return response["choices"][0]["message"]["content"].strip()

def ask_llm_json(prompt):
    raw = ask_llm(prompt, temp=0.1, max_tokens=200)
    if raw.startswith("```json"): raw = raw.replace("```json", "", 1).replace("```", "", 1).strip()
    try:
        return json.loads(raw)
    except:
        return None

# ==========================================
# 3. محرك المقابلة الذكي الديناميكي
# ==========================================
class CareerAI_Dynamic:
    def __init__(self):
        self.scores = {"cv": 0, "behavioral": 0, "technical": 0}
        self.job_role = ""
        self.core_skill = ""
        self.cv_text = ""
        
    def get_cv_text(self):
        print("📁 جاري فتح نافذة اختيار ملف السيرة الذاتية (PDF)...")
        
        # إخفاء النافذة الرئيسية لـ tkinter عشان تطلع نافذة اختيار الملفات بس
        root = tk.Tk()
        root.withdraw()
        # عشان النافذة تطلع فوق كل البرامج
        root.attributes('-topmost', True) 
        
        # فتح نافذة الاختيار
        file_path = filedialog.askopenfilename(
            title="اختر ملف السيرة الذاتية (CV)",
            filetypes=[("PDF Files", "*.pdf")]
        )
        
        if file_path and os.path.exists(file_path):
            print(f"✅ تم اختيار الملف: {os.path.basename(file_path)}")
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                
                if text.strip():
                    return text.strip()
                else:
                    print("⚠️ الملف فاضي أو مقفل بصيغة صورة (ما قدرت أقرأ النص).")
            except Exception as e:
                print(f"⚠️ حصل خطأ في قراءة الملف: {e}")
        else:
            print("⚠️ ما اخترت ملف أو ألغيت العملية.")
            
        # البديل (Fallback) إذا فشل قراءة الملف أو ما تم الاختيار
        print("\n✍️ (البديل) أدخل نبذة عن مهاراتك وخبراتك يدوياً (ثم اضغط Enter):")
        return input(">> ")

    def setup_interview(self):
        print("\n" + "="*50)
        print("📄 الخطوة 1: تحليل السيرة الذاتية (CV)")
        print("="*50)
        
        # استدعاء دالة قراءة الملف الذكية
        self.cv_text = self.get_cv_text()
        
        print("\n⏳ جاري تحليل مهاراتك واقتراح الوظائف...")
        prompt_jobs = f"Analyze this CV and suggest the top 5 most suitable tech jobs. Output ONLY a valid JSON array of strings like this: ['Job 1', 'Job 2', ...]. CV: {self.cv_text}"
        
        jobs = ask_llm_json(prompt_jobs)
        if not jobs or not isinstance(jobs, list):
            jobs = ["Software Engineer", "Data Analyst", "AI Engineer", "Backend Developer", "DevOps Engineer"]
            
        print("\n🌟 بناءً على سيرتك، هذي أفضل 5 وظائف تناسبك:")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job}")
            
        print("\n6. (وظيفة مخصصة من عندي)")
        
        choice = input("\nاختر رقم الوظيفة اللي تبي تقابل عليها: ")
        if choice.strip() == '6':
            self.job_role = input("اكتب اسم الوظيفة اللي تبيها (مثلاً: Flutter Developer): ")
        else:
            try:
                self.job_role = jobs[int(choice)-1]
            except:
                self.job_role = jobs[0]
                
        print(f"\n🎯 تم اختيار وظيفة: {self.job_role}")
        
        print("⏳ جاري تجهيز الأسئلة التقنية...")
        prompt_skill = f"What is the single most important technical skill (e.g., Python, React, SQL) for a {self.job_role}? Output ONLY the skill name in one word."
        self.core_skill = ask_llm(prompt_skill, temp=0.1, max_tokens=10).replace(".", "").strip()
        print(f"⚙️ المهارة الأساسية اللي سيتم اختبارك فيها: {self.core_skill}")
        print(f"⏳ جاري سحب المعايير المهنية لوظيفة {self.job_role} من قاعدة البيانات (O*NET)...")
        self.job_context = rag_engine.search_job(self.job_role)

    def run_interview(self):
        welcome = f"Hello! I am your AI Interviewer for the {self.job_role} position. Let's begin."
        print(f"\n🤖 {welcome}")
        speak(welcome)

        # 🎯 هذا هو السطر السحري اللي بيحل مشكلة التخبيص الإملائي حق المايك
        tolerance_note = "Note: The candidate's answer is transcribed by an AI speech-to-text tool. Ignore minor spelling mistakes or phonetic typos (e.g., 'tubal' instead of 'tuple', 'ABI' instead of 'API') as long as the technical context is correct."

        # --- الوجهة 1: الـ CV ---
        q_cv = ask_llm(f"Ask ONE short interview question verifying a specific claim from this CV: '{self.cv_text}'.")
        print(f"\n🤖 {q_cv}"); speak(q_cv)
        ans_cv = listen_until_done()
        # دمجنا سطر التسامح هنا 👇
        eval_cv = ask_llm_json(f"Evaluate if this answer proves their CV claim. {tolerance_note} Output JSON {{'score': 0-100, 'justification': '...'}}. Q: {q_cv}, A: {ans_cv}")
        self.scores["cv"] = eval_cv.get("score", 0) if eval_cv else 0

        # --- الوجهة 2: السلوكي ---
        q_beh = ask_llm(f"Ask ONE short behavioral question for a {self.job_role} about handling difficult technical challenges.")
        print(f"\n🤖 {q_beh}"); speak(q_beh)
        ans_beh = listen_until_done()
        # ودمجناه هنا 👇
        eval_beh = ask_llm_json(f"Evaluate this behavioral answer for problem-solving. {tolerance_note} Output JSON {{'score': 0-100, 'justification': '...'}}. Q: {q_beh}, A: {ans_beh}")
        self.scores["behavioral"] = eval_beh.get("score", 0) if eval_beh else 0

        # --- الوجهة 3: التقني التكيفي ---
        levels = ["Junior", "Mid-Level", "Senior"]
        tech_scores = []
        tech_status = "Low Readiness"
        
        for level in levels:
            random_seed = random.randint(1, 10000)
            prompt_q = f"""
            Based on the official job requirements from our O*NET database:
            {self.job_context}
            
            Ask ONE short, direct, and UNIQUE {level} level technical question about {self.core_skill} for a {self.job_role}. 
            The question MUST be related to the tasks and skills mentioned in the database context above.
            Focus on real-world application. Random Seed: {random_seed}
            """
            q_tech = ask_llm(prompt_q, temp=0.8)
            print(f"\n📈 [مستوى {level}] 🤖 {q_tech}"); speak(q_tech)
            ans_tech = listen_until_done()
            
            # ودمجناه هنا عشان أسئلة البرمجة 👇
            eval_tech = ask_llm_json(f"Strictly evaluate if the answer matches {level} depth for {self.core_skill}. {tolerance_note} Output JSON {{'score': 0-100, 'justification': '...'}}. Q: {q_tech}, A: {ans_tech}")
            score = eval_tech.get("score", 0) if eval_tech else 0
            tech_scores.append(score)
            
            if score < 50:
                print(f"❌ لم تتجاوز مستوى {level}. (الدرجة: {score})")
                break
            else:
                print(f"✅ تجاوزت مستوى {level} بنجاح! (الدرجة: {score})")
                tech_status = level

        self.scores["technical"] = sum(tech_scores) / len(tech_scores) if tech_scores else 0

        # --- التقرير النهائي والتحسينات ---
        self.print_final_report(tech_status)

    def print_final_report(self, tech_status):
        final_score = (self.scores["cv"] * 0.10) + (self.scores["behavioral"] * 0.30) + (self.scores["technical"] * 0.60)
        
        print("\n" + "="*60 + "\nالتقرير النهائي للمقابلة (Final Report)\n" + "="*60)
        print(f"🔹 وظيفة التقديم: {self.job_role}")
        print(f"🔹 نقاط الـ CV (10%): {self.scores['cv']}")
        print(f"🔹 نقاط السلوكي (30%): {self.scores['behavioral']}")
        print(f"🔹 نقاط التقني بمهارة {self.core_skill} (60%): {self.scores['technical']:.2f}")
        print(f"🏆 النتيجة النهائية الموزونة: {final_score:.2f} / 100")
        
        # طلب نقاط التحسين من المودل بشكل ديناميكي
        improvement_prompt = f"""
        Based on this candidate's interview for {self.job_role}:
        - CV Verification Score: {self.scores['cv']}/100
        - Behavioral Score: {self.scores['behavioral']}/100
        - Technical ({self.core_skill}) Score: {self.scores['technical']}/100
        
        Provide exactly 2 specific, actionable areas of improvement for this candidate in Arabic. 
        Focus strictly on the technical and behavioral aspects related to {self.job_role}. 
        Output as a short bulleted list.
        """
        print("\n⏳ جاري تحليل نقاط الضعف وصياغة التوصيات...")
        improvements = ask_llm(improvement_prompt, temp=0.3, max_tokens=200)
        
        print("\n💡 التوصية الإدارية ومجالات التطوير:")
        print(improvements)
        
        speak("The interview is complete. Check your terminal for the detailed improvement plan. Good luck!")

if __name__ == "__main__":
    interview = CareerAI_Dynamic()
    interview.setup_interview() # الخطوة الجديدة (التحليل والاختيار)
    interview.run_interview()   # بدء المقابلة