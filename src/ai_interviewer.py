import speech_recognition as sr
import win32com.client  # 👈 المحرك الجديد المضمون لويندوز
from llama_cpp import Llama

# ==========================================
# 1. إعداد الصوت والنطق (محرك ويندوز SAPI5)
# ==========================================
print("⏳ جاري إعداد محرك الصوت الخاص بويندوز...")
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Rate = 1  # سرعة الصوت (تقدر تخليها 0 أو 2 حسب رغبتك)

def speak(text):
    print("🔊 (CareerAI يتحدث الآن...)")
    try:
        speaker.Speak(text)
    except Exception as e:
        print(f"⚠️ مشكلة في تشغيل السماعات: {e}")

recognizer = sr.Recognizer()

# دالة الاستماع الذكية (تنتظر الين تقول I am done)
def listen_until_done():
    full_answer = ""
    with sr.Microphone() as source:
        print("\n🎤 المايك مفتوح... (خذ راحتك في الكلام)")
        print("💡 (عشان تنهي إجابتك، قل فقط: 'I am done')")
        
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.pause_threshold = 2.0 
        
        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                text = recognizer.recognize_whisper(audio, model="base.en").strip()
                
                if text and len(text) > 2: 
                    print(f"🗣️ سمعتك تقول: {text}")
                    full_answer += " " + text
                    
                    if "i am done" in text.lower() or "i'm done" in text.lower():
                        print("✅ تم استلام الإجابة بالكامل! جاري التفكير...")
                        break
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print(f"⚠️ خطأ في المايك: {e}")
                break
                
    clean_answer = full_answer.lower().replace("i am done", "").replace("i'm done", "").strip()
    return clean_answer

# ==========================================
# 2. تشغيل المودل (CareerAI)
# ==========================================
print("⏳ جاري تشغيل العقل المدبر لـ CareerAI...")
MODEL_PATH = r"D:\Desktop\creearAi\CareerAI\src\llm\qwen2.5-3b-instruct.Q4_K_M.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

system_prompt = "You are CareerAI, a friendly and professional AI interviewer. Conduct a technical and HR interview with the candidate based on their responses. Keep your answers concise (2-3 sentences max) so they are easy to listen to."

messages = [{"role": "system", "content": system_prompt}]

# ==========================================
# 3. حلقة المقابلة الصوتية
# ==========================================
MAX_QUESTIONS = 4
question_count = 0

print("\n✅ CareerAI جاهز! المقابلة الصوتية ستبدأ الآن.")
print("="*60)

welcome_msg = "Hello Jamal! I am CareerAI. Are you ready to start the interview?"
print(f"🤖 CareerAI: {welcome_msg}")
speak(welcome_msg) 

while question_count < MAX_QUESTIONS:
    user_input = listen_until_done() # هنا بيقعد يسمعك ويجمع كلامك لين تقول I am done
    
    if not user_input:
        continue 
        
    if 'exit' in user_input or 'stop' in user_input:
        goodbye = "Alright, the interview is concluded. Best of luck!"
        print(f"🤖 CareerAI: {goodbye}")
        speak(goodbye)
        break
        
    messages.append({"role": "user", "content": user_input})
    
    print("\n🤖 CareerAI (يكتب): ", end="", flush=True)
    
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=100,
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
    
    messages.append({"role": "assistant", "content": full_response})
    
    # هنا بينطق الرد كامل ومستحيل يعلق إن شاء الله
    speak(full_response)
    
    question_count += 1

# ==========================================
# 4. التقييم النهائي 
# ==========================================
if question_count == MAX_QUESTIONS:
    print("\n📊 جاري إصدار التقييم النهائي...\n")
    
    eval_prompt = "The interview is over. Provide a very short 2-sentence feedback highlighting strengths and a score out of 100."
    messages.append({"role": "user", "content": eval_prompt})
    
    evaluation_response = llm.create_chat_completion(
        messages=messages,
        max_tokens=150,
        temperature=0.2
    )
    
    final_feedback = evaluation_response["choices"][0]["message"]["content"]
    
    print("📈 التقييم النهائي من CareerAI:")
    print("="*60)
    print(final_feedback)
    print("\n" + "="*60)
    
    speak("The interview is complete. Here is your final feedback.")
    speak(final_feedback)