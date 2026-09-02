import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"


print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


print("Loading model...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    dtype=torch.float16,
)

print("Model loaded successfully!")


SYSTEM_PROMPT = """
You are CareerAI, an intelligent career analysis system.

Your job is to analyze a user's career-related request and
extract structured information that will be used by a career
recommendation engine.

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{
    "career_goal": "",
    "skills": [],
    "experience": [],
    "education": [],
    "preferred_roles": [],
    "domains": [],
    "career_intent": ""
}

Rules:

- career_goal: The main career the user wants.
- skills: Technical skills explicitly mentioned by the user.
- experience: Work or professional experience explicitly mentioned.
- education: Education explicitly mentioned.
- preferred_roles: Career/job titles that are reasonable matches
  for the user's stated goal.
- domains: Relevant technical domains such as AI, machine learning,
  software engineering, data science, robotics, etc.
- career_intent: A short description of what the user wants.
- Do NOT invent user experience, education, or skills.
- If information is missing, return an empty list or empty string.
- Return JSON only. No explanation and no markdown.
"""


def ask_llm(prompt):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        text,
        return_tensors="pt",
    )

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.2,
            do_sample=True,
        )

    generated = outputs[0][inputs["input_ids"].shape[1]:]

    response = tokenizer.decode(
        generated,
        skip_special_tokens=True,
    )

    return response.strip()


def analyze_career_query(query):

    prompt = f"""
Analyze the following career query.

User query:
{query}

Return the required JSON structure.
"""

    response = ask_llm(prompt)

    try:

        result = json.loads(response)

        return result

    except json.JSONDecodeError:

        print("\nWARNING: LLM returned invalid JSON:")
        print(response)

        return {
            "career_goal": "",
            "skills": [],
            "experience": [],
            "education": [],
            "preferred_roles": [],
            "domains": [],
            "career_intent": "",
        }


if __name__ == "__main__":

    import sys

    # Machine-readable mode for career_retriever.py
    if len(sys.argv) > 1 and sys.argv[1] == "--json":

        query = sys.argv[2]

        result = analyze_career_query(query)

        print(
            json.dumps(
                result,
                ensure_ascii=False,
            )
        )

        sys.exit(0)

    # Normal interactive test mode
    print("\nCareerAI LLM Test")
    print("=" * 50)

    query = input(
        "Enter your career query: "
    )

    result = analyze_career_query(query)

    print("\nCareerAI Analysis")
    print("=" * 50)

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
        )
    )