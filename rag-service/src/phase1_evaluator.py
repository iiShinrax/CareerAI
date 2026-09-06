import json
from llama_cpp import Llama

print("⏳ Loading the Hidden Evaluator (Strict Mode)...")
MODEL_PATH = r"D:\Desktop\creearAi\CareerAI\src\llm\qwen2.5-3b-instruct.Q4_K_M.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

# 1. الادعاء اللي استخرجناه من المرحلة 0
cv_claim = "Built a Voice-based AI Interviewer using Python, Whisper, and Llama-cpp."

# 2. سؤال المحاور (لتوضيح السياق)
interviewer_question = "In your CV, you mentioned building a Voice-based AI Interviewer using Whisper and Llama-cpp. Can you explain how you handled the voice recording to prevent the system from cutting off the user while they are thinking?"

# 3. إجابة المرشح (نجرب إجابة ضعيفة عشان نشوف صرامة المقيّم!)
candidate_answer = "Uh, I just used a microphone library in Python and it recorded the voice. Then I sent it to the AI. That's it."

# 4. البرومبت الصارم جداً للمقيّم الخفي
evaluator_prompt = f"""
You are a STRICT and UNFORGIVING Technical HR Evaluator.
Your job is to verify if the candidate actually possesses the experience they claimed in their CV based on their answer.

CV Claim: "{cv_claim}"
Interviewer Question: "{interviewer_question}"
Candidate Answer: "{candidate_answer}"

Evaluation Rules:
1. Is the answer detailed and convincing?
2. Did they actually answer the specific technical question asked?
3. Be strict. If the answer is vague or shallow, give a low score (0-40).

You MUST output ONLY valid JSON format exactly like this:
{{
    "score": <number 0-100>,
    "justification": "<one short sentence quoting the candidate's weakness or strength>"
}}
Do not write any introductory text. Just the JSON object.
"""

messages = [{"role": "user", "content": evaluator_prompt}]

print("\n🔍 Evaluating the candidate's answer strictly...")
response = llm.create_chat_completion(
    messages=messages,
    max_tokens=150,
    temperature=0.1, # حرارة شبه معدومة لضمان الصرامة
)

raw_output = response["choices"][0]["message"]["content"].strip()

# تنظيف المخرجات
if raw_output.startswith("```json"):
    raw_output = raw_output.replace("```json", "", 1).replace("```", "", 1).strip()
elif raw_output.startswith("```"):
    raw_output = raw_output.replace("```", "", 1).replace("```", "", 1).strip()

print("\n📦 The Hidden Evaluator's Verdict:")
print("-" * 50)
try:
    evaluation = json.loads(raw_output)
    print(f"📊 Final Score: {evaluation['score']} / 100")
    print(f"📝 Justification: {evaluation['justification']}")
    
    if evaluation['score'] < 50:
        print("❌ System Decision: Low Readiness (Candidate might be lying or lacks depth).")
    else:
        print("✅ System Decision: Claim Verified successfully.")
        
except json.JSONDecodeError:
    print("❌ Error parsing JSON from model:\n", raw_output)