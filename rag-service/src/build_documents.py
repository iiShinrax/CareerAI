import json
import os

INPUT_FILE = r"data/processed/onet/occupation_profiles.jsonl"
OUTPUT_FILE = "data/processed/onet/rag_documents.jsonl"


def format_skills(skills):
    lines = []

    for skill in skills:
        lines.append(
            f"- {skill['name']} "
            f"(importance: {skill['importance']}, "
            f"level: {skill['level']})"
        )

    return "\n".join(lines)


def format_knowledge(knowledge):
    lines = []

    for item in knowledge:
        lines.append(
            f"- {item['name']} "
            f"(importance: {item['importance']}, "
            f"level: {item['level']})"
        )

    return "\n".join(lines)


def format_tasks(tasks):
    lines = []

    for task in tasks:
        lines.append(f"- {task['task']} ({task['type']})")

    return "\n".join(lines)


def format_software(software):
    lines = []

    for item in software:
        flags = []

        if item.get("hot_technology") == "Y":
            flags.append("hot technology")

        if item.get("in_demand") == "Y":
            flags.append("in demand")

        flag_text = f" [{', '.join(flags)}]" if flags else ""

        lines.append(
            f"- {item['name']} "
            f"({item['category']}){flag_text}"
        )

    return "\n".join(lines)


def build_document(profile):
    document = f"""
Occupation: {profile['title']}
O*NET-SOC Code: {profile['occupation_code']}
Job Zone: {profile['job_zone']}

Description:
{profile['description']}

Core and Supplemental Tasks:
{format_tasks(profile.get('tasks', []))}

Essential Skills:
{format_skills(profile.get('essential_skills', []))}

Transferable Skills:
{format_skills(profile.get('transferable_skills', []))}

Knowledge Areas:
{format_knowledge(profile.get('knowledge', []))}

Software and Technologies:
{format_software(profile.get('software', []))}
""".strip()

    return document


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    count = 0

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            profile = json.loads(line)

            document = {
                "id": profile["occupation_code"],
                "title": profile["title"],
                "occupation_code": profile["occupation_code"],
                "job_zone": profile["job_zone"],
                "text": build_document(profile),
            }

            outfile.write(
                json.dumps(
                    document,
                    ensure_ascii=False
                ) + "\n"
            )

            count += 1

    print(f"Created {count} RAG documents")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()