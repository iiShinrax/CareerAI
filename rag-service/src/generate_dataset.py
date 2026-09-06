import pandas as pd
import json
import random

# 1. قراءة ملفات قاعدة البيانات حقتكم
print("Loading CSV files...")
try:
    skills_df = pd.read_csv(r"D:\Desktop\creearAi\CareerAI\data\raw\onet\essential_skills.csv") # استدعاء ملف المهارات
    tasks_df = pd.read_csv(r"D:\Desktop\creearAi\CareerAI\data\raw\onet\task_statements.csv")   # استدعاء ملف المهام
except FileNotFoundError:
    print("تأكد إن ملفات الـ CSV موجودة في نفس المجلد!")
    exit()

# تنظيف البيانات (أخذ عينة لتسريع العملية، تقدر تعدلها)
skills = skills_df['Skill_Name'].dropna().unique().tolist() if 'Skill_Name' in skills_df.columns else ["Python", "Machine Learning", "SQL", "Data Analysis"]
tasks = tasks_df['Task_Statement'].dropna().unique().tolist() if 'Task_Statement' in tasks_df.columns else ["Build predictive models", "Optimize database queries"]

dataset = []

# 2. القوالب التفاعلية (لدمج المحادثة الطبيعية مع الداتا)
instructions = [
    "You are CareerAI, a friendly and professional AI interviewer. Ask a technical question based on the candidate's skill.",
    "You are CareerAI. Conduct a conversational technical interview."
]

# 3. توليد أسئلة من المهارات (essential_skills)
print("Generating skills questions...")
for _ in range(500): # بنولد 500 محادثة عن المهارات
    skill = random.choice(skills)
    dataset.append({
        "instruction": random.choice(instructions),
        "input": f"Candidate: I have extensive experience working with {skill}.",
        "output": f"That's excellent! {skill} is very highly valued in the industry right now. Can you walk me through a specific project where you utilized {skill} to solve a complex problem?"
    })

# 4. توليد أسئلة من المهام (task_statements)
print("Generating task questions...")
for _ in range(500): # بنولد 500 محادثة عن المهام الوظيفية
    task = random.choice(tasks)
    dataset.append({
        "instruction": "You are CareerAI. Ask a behavioral/scenario question based on job tasks.",
        "input": f"Candidate: I want to know what challenges I might face in this role.",
        "output": f"Great question! In this role, one of the key responsibilities is to {task.lower()}. How would you approach this task, and what strategies would you use to ensure success?"
    })

# 5. إضافة داتا من نوع Hugging Face (أسئلة HR وتقييم)
hr_data = [
    {
        "instruction": "You are CareerAI. Evaluate the candidate's answer constructively.",
        "input": "Candidate: When I face a bug, I usually ask a senior developer immediately to save time.",
        "output": "I appreciate your focus on efficiency. However, as an engineer, it's also important to show independent problem-solving. A stronger approach would be to spend some time debugging and researching before escalating the issue. Does that make sense?"
    },
    {
         "instruction": "You are CareerAI. Ask an HR question about career goals.",
         "input": "Candidate: I am ready for the HR portion of the interview.",
         "output": "Perfect! Let's talk about your future. Where do you see your career heading in the next 3 to 5 years, particularly in the tech industry?"
    }
]

dataset.extend(hr_data * 50) # تكرارها عشان تثبت شخصية المودل

# 6. حفظ الداتاسيت النهائية
output_file = "massive_interview_dataset.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print(f"✅ تم توليد الداتاسيت بنجاح! تم حفظ {len(dataset)} مثال في ملف {output_file}")