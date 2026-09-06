import pandas as pd
import json
import random
from datasets import load_dataset

def main():
    final_dataset = []

    # ==========================================
    # 1. سحب بيانات حقيقية من Hugging Face
    # ==========================================
    print("⏳ جاري سحب بيانات حقيقية من Hugging Face...")
    try:
        hf_data = load_dataset("tatsu-lab/alpaca", split="train")
        
        keywords = ["interview", "career", "job", "developer", "engineer", "explain"]
        def is_relevant(example):
            text = (example["instruction"] + " " + example["input"]).lower()
            return any(kw in text for kw in keywords)

        filtered_hf = hf_data.filter(is_relevant)
        hf_sample = filtered_hf.shuffle(seed=42).select(range(min(300, len(filtered_hf))))
        
        for item in hf_sample:
            final_dataset.append({
                "instruction": item["instruction"],
                "input": item["input"],
                "output": item["output"]
            })
        print(f"✅ تم سحب {len(hf_sample)} مثال احترافي من Hugging Face.")
    except Exception as e:
        print(f"❌ صار خطأ في تحميل Hugging Face: {e}")

    # ==========================================
    # 2. قراءة ملفاتك المحلية (بذكاء لاكتشاف أسماء الأعمدة)
    # ==========================================
    print("\n⏳ جاري قراءة ملفات الـ CSV (المهارات والمهام)...")
    try:
        skills_df = pd.read_csv("data/raw/onet/essential_skills.csv")
        tasks_df = pd.read_csv("data/raw/onet/task_statements.csv")
        
        # البحث الذكي عن اسم عمود المهارات
        possible_skill_cols = ['Skill_Name', 'Element Name', 'Skill', 'name', 'Title']
        skill_col = next((col for col in possible_skill_cols if col in skills_df.columns), None)
        if not skill_col: skill_col = skills_df.columns[0] # إذا ما لقى الاسم، ياخذ أول عمود

        # البحث الذكي عن اسم عمود المهام
        possible_task_cols = ['Task_Statement', 'Task', 'Task Statement', 'Statement']
        task_col = next((col for col in possible_task_cols if col in tasks_df.columns), None)
        if not task_col: task_col = tasks_df.columns[0]

        # أخذ العينة العشوائية 
        skills_count = min(100, len(skills_df))
        tasks_count = min(100, len(tasks_df))
        
        skills = skills_df[skill_col].dropna().sample(n=skills_count, random_state=42).tolist()
        tasks = tasks_df[task_col].dropna().sample(n=tasks_count, random_state=42).tolist()
        
        print(f"✅ تم استخراج عينة: {len(skills)} مهارة و {len(tasks)} مهمة بنجاح.")
    except Exception as e:
        print(f"❌ حدث خطأ في قراءة الملفات: {e}")
        return

    # ==========================================
    # 3. توليد المحادثات بصيغ مختلفة
    # ==========================================
    positive_responses = [
        "That's excellent! {skill} is a highly requested skill. Can you share a specific project where you used it?",
        "Impressive. Working with {skill} shows strong technical foundation. How do you stay updated with it?",
        "Great to hear. Since you know {skill}, how would you approach debugging a critical issue related to it?"
    ]
    
    for skill in skills:
        final_dataset.append({
            "instruction": "You are CareerAI, an expert technical interviewer.",
            "input": f"Candidate: I have extensive experience working with {skill}.",
            "output": random.choice(positive_responses).format(skill=skill)
        })

    for task in tasks:
        final_dataset.append({
            "instruction": "You are CareerAI, evaluating a candidate based on job tasks.",
            "input": f"Candidate: What is the most challenging part of this role?",
            "output": f"One of the key responsibilities is to {task}. A strong candidate would need to handle this efficiently. How would you plan your workflow to accomplish this?"
        })

    # ==========================================
    # 4. حفظ الداتاسيت
    # ==========================================
    output_file = "career_ai_training_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=4, ensure_ascii=False)
    
    print(f"\n🎉 تم دمج وتوليد البيانات! العدد الإجمالي: {len(final_dataset)} محادثة.")
    
    # ==========================================
    # 5. فحص الجودة (Quality Audit)
    # ==========================================
    print("\n🔍 ================== فحص جودة البيانات (QA Audit) ================== 🔍")
    
    empty_outputs = 0
    short_outputs = 0
    total_length = 0

    for data in final_dataset:
        out_len = len(str(data['output']).split())
        total_length += out_len
        if not str(data['output']).strip(): empty_outputs += 1
        if out_len < 5: short_outputs += 1

    avg_length = total_length / len(final_dataset)

    print(f"📊 متوسط طول الإجابة: {avg_length:.1f} كلمة (المثالي بين 15 إلى 40 كلمة للمقابلات).")
    print(f"⚠️ الإجابات الفارغة (يجب أن تكون 0): {empty_outputs}")
    print(f"⚠️ الإجابات القصيرة جداً (غير تفاعلية): {short_outputs}")
    
    if empty_outputs == 0 and short_outputs < (len(final_dataset) * 0.05):
        print("✅ تقييم النظام: البيانات ممتازة، متنوعة، وجاهزة للتدريب (Fine-Tuning) بسلام! 🚀")
    else:
        print("❌ تقييم النظام: الداتا تحتاج تنظيف، فيه إجابات قصيرة أو فاضية كثيرة بتخرب تدريب المودل.")

    print("\n👁️ عينة عشوائية للتحقق البشري:")
    sample_check = random.sample(final_dataset, 1)[0]
    print(f"Instruction: {sample_check['instruction']}")
    print(f"Input: {sample_check['input']}")
    print(f"Output: {sample_check['output']}")

if __name__ == "__main__":
    main()