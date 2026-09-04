import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


INPUT_FILE = "data/processed/onet/rag_documents.jsonl"
VECTOR_DB_DIR = "vector_db"

INDEX_FILE = os.path.join(VECTOR_DB_DIR, "index.faiss")
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "metadata.json")

MODEL_NAME = "all-MiniLM-L6-v2"


def create_chunks(profile):
    """
    Create semantically meaningful chunks for one occupation.
    """

    title = profile["title"]
    code = profile["occupation_code"]
    job_zone = profile["job_zone"]

    chunks = []

    # Description
    description = profile.get("description", "")

    if description:
        chunks.append({
            "occupation_code": code,
            "title": title,
            "job_zone": job_zone,
            "section": "description",
            "text": (
                f"Occupation: {title}\n"
                f"O*NET-SOC Code: {code}\n"
                f"Job Zone: {job_zone}\n\n"
                f"Section: Description\n"
                f"{description}"
            )
        })

    # Tasks
    tasks = profile.get("tasks", [])

    if tasks:
        task_text = "\n".join(
            f"- {task['task']} ({task['type']})"
            for task in tasks
        )

        chunks.append({
            "occupation_code": code,
            "title": title,
            "job_zone": job_zone,
            "section": "tasks",
            "text": (
                f"Occupation: {title}\n"
                f"O*NET-SOC Code: {code}\n\n"
                f"Section: Tasks\n"
                f"The typical tasks performed by {title} include:\n"
                f"{task_text}"
            )
        })

    # Essential skills
    skills = profile.get("essential_skills", [])

    if skills:
        skill_text = "\n".join(
            f"- {skill['name']} "
            f"(importance: {skill['importance']}, "
            f"level: {skill['level']})"
            for skill in skills
        )

        chunks.append({
            "occupation_code": code,
            "title": title,
            "job_zone": job_zone,
            "section": "essential_skills",
            "text": (
                f"Occupation: {title}\n"
                f"O*NET-SOC Code: {code}\n\n"
                f"Section: Essential Skills\n"
                f"The essential skills for {title} include:\n"
                f"{skill_text}"
            )
        })

    # Transferable skills
    transferable = profile.get("transferable_skills", [])

    if transferable:
        skill_text = "\n".join(
            f"- {skill['name']} "
            f"(importance: {skill['importance']}, "
            f"level: {skill['level']})"
            for skill in transferable
        )

        chunks.append({
            "occupation_code": code,
            "title": title,
            "job_zone": job_zone,
            "section": "transferable_skills",
            "text": (
                f"Occupation: {title}\n"
                f"O*NET-SOC Code: {code}\n\n"
                f"Section: Transferable Skills\n"
                f"The transferable skills for {title} include:\n"
                f"{skill_text}"
            )
        })

    # Knowledge
    knowledge = profile.get("knowledge", [])

    if knowledge:
        knowledge_text = "\n".join(
            f"- {item['name']} "
            f"(importance: {item['importance']}, "
            f"level: {item['level']})"
            for item in knowledge
        )

        chunks.append({
            "occupation_code": code,
            "title": title,
            "job_zone": job_zone,
            "section": "knowledge",
            "text": (
                f"Occupation: {title}\n"
                f"O*NET-SOC Code: {code}\n\n"
                f"Section: Knowledge Areas\n"
                f"Important knowledge areas for {title} include:\n"
                f"{knowledge_text}"
            )
        })

    # Software
    software = profile.get("software", [])

    if software:
        software_text = "\n".join(
            f"- {item['name']} "
            f"({item['category']})"
            + (
                " [hot technology]"
                if item.get("hot_technology") == "Y"
                else ""
            )
            + (
                " [in demand]"
                if item.get("in_demand") == "Y"
                else ""
            )
            for item in software
        )

        chunks.append({
            "occupation_code": code,
            "title": title,
            "job_zone": job_zone,
            "section": "software",
            "text": (
                f"Occupation: {title}\n"
                f"O*NET-SOC Code: {code}\n\n"
                f"Section: Software and Technologies\n"
                f"Software and technologies associated with {title} include:\n"
                f"{software_text}"
            )
        })

    return chunks


def main():

    os.makedirs(VECTOR_DB_DIR, exist_ok=True)

    print("Loading occupation profiles...")

    documents = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            documents.append(json.loads(line))

    print(f"Loaded {len(documents)} RAG documents.")

    print("\nPreparing RAG documents...")

    chunks = []

    for document in documents:

        chunks.append({
            "occupation_code": document["occupation_code"],
            "title": document["title"],
            "job_zone": document["job_zone"],
            "section": "full_profile",
            "text": document["text"],
        })

    # --- التعديل هنا: طلعنا باقي الكود برا اللوب (for) ورتبنا المسافات ---

    print(f"Prepared {len(chunks)} RAG chunks.")

    print(f"Created {len(chunks)} semantic chunks.")

    print("\nLoading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    print("\nGenerating embeddings...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embeddings = embeddings.astype("float32")

    print(f"\nEmbedding shape: {embeddings.shape}")

    dimension = embeddings.shape[1]

    print(f"Creating FAISS index with dimension {dimension}...")

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    print(f"FAISS index contains {index.ntotal} vectors.")

    print("\nSaving index...")

    faiss.write_index(index, INDEX_FILE)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            chunks,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 60)
    print("VECTOR DATABASE REBUILT SUCCESSFULLY")
    print("=" * 60)
    print(f"Documents:   {len(documents)}")
    print(f"Chunks:      {len(chunks)}")
    print(f"Vectors:     {index.ntotal}")
    print(f"Dimension:   {dimension}")
    print(f"Model:       {MODEL_NAME}")


if __name__ == "__main__":
    main()
