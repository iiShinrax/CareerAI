# import arrcorr # مكتبتك السحرية!
import json
from llama_cpp import Llama

print("⏳ جاري تشغيل محرك الصعوبة التكيفية (الوجهة الثالثة)...")
MODEL_PATH = r"D:\Desktop\creearAi\CareerAI\src\llm\qwen2.5-3b-instruct.Q4_K_M.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

# بنختبر مهارة وحدة بس للتجربة
skill_to_test = "Python"
job_role = "AI Engineer"

# 1. دالة لتوليد السؤال بناءً على الصعوبة
def generate_question(skill, level):
    prompt = f"""
    You are a Technical Interviewer. 
    Ask ONE short, direct technical question about '{skill}' for a {level} level {job_role}.
    Do NOT provide the answer. Just ask the question.
    """
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7 # نعطيه شوية إبداع عشان ينوع الأسئلة
    )
    return response["choices"][0]["message"]["content"].strip()

# 2. دالة التقييم الخفي (الصارم)
def evaluate_answer(question, answer, level):
    prompt = f"""
    You are a STRICT Technical Evaluator.
    Question Level: {level}
    Question: "{question}"
    Candidate Answer: "{answer}"
    
    Evaluate if the candidate's answer is technically correct and matches the expected depth for a {level} level.
    You MUST output ONLY valid JSON format exactly like this:
    {{
        "score": <number 0-100>,
        "justification": "<short strict reason>"
    }}
    """
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.1 # صرامة تامة
    )
    
    raw_output = response["choices"][0]["message"]["content"].strip()
    if raw_output.startswith("```json"):
         raw_output = raw_output.replace("```json", "", 1).replace("```", "", 1).strip()
    
    try:
        return json.loads(raw_output)
    except:
        return {"score": 0, "justification": "System Error: Invalid JSON"}

# ==========================================
# 3. حلقة المعركة التكيفية (Adaptive Loop)
# ==========================================
levels = ["Junior (Easy)", "Mid-Level (Medium)", "Senior (Hard)"]
final_status = "Low Readiness"

print(f"\n🎯 بدء الاختبار التقني لمهارة: {skill_to_test}")
print("=" * 60)

for level in levels:
    print(f"\n📈 المرحلة: {level}")
    
    # يولد السؤال
    question = generate_question(skill_to_test, level)
    print(f"🤖 CareerAI: {question}")
    
    # تاخذ إجابتك من الكيبورد (عشان التجربة تكون سريعة)
    user_answer = input("👤 You (Answer): ")
    
    if user_answer.lower() in ['exit', 'quit']:
        break
        
    print("🔍 (المقيّم الخفي يحلل إجابتك...)")
    evaluation = evaluate_answer(question, user_answer, level)
    
    score = evaluation.get("score", 0)
    print(f"📊 التقييم: {score}/100")
    print(f"📝 السبب: {evaluation.get('justification', '')}")
    
    # 4. بوابات القرار (State Machine Logic)
    if score < 50:
        print(f"\n❌ النتيجة: رسبت في مستوى {level}.")
        if level == "Junior (Easy)":
            final_status = "مرفوض (جاهزية منخفضة جداً)"
        elif level == "Mid-Level (Medium)":
            final_status = "مناسب لمنصب Junior فقط"
        elif level == "Senior (Hard)":
            final_status = "مناسب للمنصب الحالي (Mid-Level) بنجاح"
        break # نوقف اختبار هذي المهارة لأنك تعثرت
    else:
        print(f"✅ وحش! تجاوزت مستوى {level} بنجاح.")
        if level == "Senior (Hard)":
            final_status = "أسطورة! أوصي بترقيته لمنصب Senior"

print("\n" + "=" * 60)
print(f"🏁 القرار النهائي لمهارة {skill_to_test}: {final_status}")
print("=" * 60)