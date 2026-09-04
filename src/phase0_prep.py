import builtins
import arabic_reshaper
from bidi.algorithm import get_display

# نحفظ دالة الطباعة الأصلية
original_print = builtins.print

# نصنع دالة طباعة ذكية تدعم العربي
def smart_arabic_print(*args, **kwargs):
    new_args = []
    for arg in args:
        if isinstance(arg, str): # إذا كان النص سترينج (كلمات)
            new_args.append(get_display(arabic_reshaper.reshape(arg)))
        else:
            new_args.append(arg)
    original_print(*new_args, **kwargs)

# نستبدل دالة البايثون الأساسية بدالتنا الذكية!
builtins.print = smart_arabic_print

# ==========================================
# من هنا وتحت.. كودك القديم خله زي ما هو ولا تعدل فيه حرف!

import json
from llama_cpp import Llama

# ==========================================
# 1. تشغيل المودل
# ==========================================
print("⏳ جاري تشغيل المودل للمرحلة 0 (تحليل البيانات)...")
MODEL_PATH = r"D:\Desktop\creearAi\CareerAI\src\llm\qwen2.5-3b-instruct.Q4_K_M.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

# ==========================================
# 2. بيانات تجريبية (الـ CV ووصف الوظيفة)
# ==========================================
# تخيل إن هذي البيانات بتجينا بعدين من واجهة الموقع (Front-end)
my_cv = """
Name: Jamal
Role: AI Engineer
Experience: 
- Built a Voice-based AI Interviewer using Python, Whisper, and Llama-cpp.
- Fine-tuned Qwen 3B model for HR technical assessments.
- Strong knowledge in Python, Prompt Engineering, and RAG architectures.
"""

job_description = """
Job Title: Senior AI Engineer
Requirements:
- Deep understanding of Large Language Models (LLMs) and local deployment.
- Experience with Python and audio processing (STT/TTS).
- Ability to design complex prompt pipelines and Multi-Agent systems.
"""

# ==========================================
# 3. هندسة الأوامر (Prompt Engineering) لإجبار المودل على JSON
# ==========================================
system_prompt = """
You are an expert Technical HR Analyst. 
Your task is to analyze the provided CV and Job Description.
1. Extract 2-3 specific, testable claims from the CV (to verify candidate's honesty).
2. Extract 3 core technical skills from the Job Description (for the technical interview).

You MUST output ONLY valid JSON format exactly like this structure:
{
    "cv_claims": ["claim 1", "claim 2"],
    "core_skills": ["skill 1", "skill 2", "skill 3"]
}
Do not write any introductory text, markdown, or explanations. Just the JSON object.
"""

user_prompt = f"CV:\n{my_cv}\n\nJob Description:\n{job_description}"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

# ==========================================
# 4. الاستخراج والتحليل (LLM Call)
# ==========================================
print("🔍 جاري تحليل السيرة الذاتية واستخراج المهارات...")
response = llm.create_chat_completion(
    messages=messages,
    max_tokens=250,
    temperature=0.1, # حرارة منخفضة جداً عشان ما يهلوس ويعطينا JSON دقيق
)

raw_output = response["choices"][0]["message"]["content"].strip()

# تنظيف النص في حال المودل أضاف علامات الماركدوان (```json ... ```)
if raw_output.startswith("```json"):
    raw_output = raw_output.replace("```json", "", 1).replace("```", "", 1).strip()
elif raw_output.startswith("```"):
    raw_output = raw_output.replace("```", "", 1).replace("```", "", 1).strip()

print("\n📦 المخرجات الخام من المودل:")
print(raw_output)
print("-" * 50)

# ==========================================
# 5. تحويل النص إلى قاموس بايثون (Dictionary) للـ State Machine
# ==========================================
try:
    extracted_data = json.loads(raw_output)
    print("✅ ممتاز! تم تحويل البيانات بنجاح إلى قاموس بايثون:")
    print(f"📌 ادعاءات الـ CV المستخرجة (للوجهة الأولى): {extracted_data['cv_claims']}")
    print(f"🎯 المهارات المطلوبة (للوجهة الثالثة): {extracted_data['core_skills']}")
except json.JSONDecodeError:
    print("❌ خطأ: المودل لم يخرج JSON صحيح. حاول تشغيل الكود مرة أخرى أو تعديل البرومبت.")