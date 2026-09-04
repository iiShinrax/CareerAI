from llama_cpp import Llama

print("⏳ جاري تشغيل CareerAI... (جهازك بيكون مرتاح لا تخاف!)")

# 1. تحديد مسار المودل (حطيت الـ r قبل النص عشان مسارات الويندوز)
MODEL_PATH = r"D:\Desktop\creearAi\CareerAI\src\llm\qwen2.5-3b-instruct.Q4_K_M.gguf"

# 2. تحميل المودل
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,      # حجم الذاكرة وسياق المحادثة
    n_threads=4,     # عدد أنوية المعالج (تسرع الكتابة عندك)
    verbose=False    # عشان ما يزعجك بالنصوص التقنية وقت التشغيل
)

print("\n✅ CareerAI جاهز! تقدر تبدأ المقابلة (اكتب 'exit' للخروج)")
print("="*60)

# 3. تحديد شخصية مدير التوظيف
system_prompt = "You are CareerAI, a friendly and professional AI interviewer. Conduct a technical and HR interview with the candidate based on their responses. Keep your answers concise, engaging, and professional."

# سجل المحادثة (عشان يتذكر وش قلت له قبل شوي)
messages = [
    {"role": "system", "content": system_prompt}
]

# 4. حلقة المحادثة (الشات) مع عداد للأسئلة
MAX_QUESTIONS = 4  # تقدر تغير الرقم لعدد الأسئلة اللي تبغاها
question_count = 0

while question_count < MAX_QUESTIONS:
    user_input = input("👤 You (Candidate): ")
    
    if user_input.lower() == 'exit':
        print("👋 انتهت المقابلة، بالتوفيق!")
        break
        
    # إضافة كلامك للسجل
    messages.append({"role": "user", "content": user_input})
    
    print("🤖 CareerAI: ", end="", flush=True)
    
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=150,
        temperature=0.3,
        stream=True
    )
    
    full_response = ""
    for chunk in response:
        if "content" in chunk["choices"][0]["delta"]:
            word = chunk["choices"][0]["delta"]["content"]
            print(word, end="", flush=True)
            full_response += word
            
    print("\n" + "-"*60)
    
    # إضافة رد المودل للسجل
    messages.append({"role": "assistant", "content": full_response})
    
    question_count += 1 # نزيد العداد

# 5. التقييم النهائي (يشتغل بس إذا خلصت الأسئلة وما طلعت بـ exit)
if question_count == MAX_QUESTIONS:
    print("\n📊 جاري إصدار التقييم النهائي من المودل...\n")
    
    # نعطي المودل تعليمة مخفية عشان يقيّمك
    eval_prompt = "The interview is now over. Based on the candidate's answers above, provide a short overall evaluation highlighting their technical strengths, weaknesses, and give a final score out of 100%."
    messages.append({"role": "user", "content": eval_prompt})
    
    evaluation_response = llm.create_chat_completion(
        messages=messages,
        max_tokens=250,
        temperature=0.2, # قللنا الإبداع عشان يكون التقييم دقيق وواقعي
        stream=False     # يطبع التقييم دفعة وحدة
    )
    
    print("📈 التقييم النهائي من CareerAI:")
    print("="*60)
    print(evaluation_response["choices"][0]["message"]["content"])
    print("\n" + "="*60)
    print("👋 انتهت المقابلة بنجاح!")
    
    # إضافة رد المودل للسجل عشان يكمل عليه السؤال الجاي
    messages.append({"role": "assistant", "content": full_response})