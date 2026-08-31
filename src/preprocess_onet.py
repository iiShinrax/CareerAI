import json
from pathlib import Path

import pandas as pd


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw" / "onet"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "onet"

OUTPUT_FILE = OUTPUT_DIR / "occupation_profiles.jsonl"


# ============================================================
# Helpers
# ============================================================

def load_csv(filename: str) -> pd.DataFrame:
    """Load an O*NET CSV file."""
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    print(f"Loading {filename}...")
    return pd.read_csv(path)


def clean_text(value) -> str:
    """Convert a value to clean text."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def build_rated_items(df: pd.DataFrame) -> dict:
    """
    Convert O*NET skill/knowledge data from separate
    Importance and Level rows into structured items.

    Returns:
        {
            occupation_code: [
                {
                    "name": "...",
                    "importance": 4.12,
                    "level": 4.62
                }
            ]
        }
    """

    results = {}

    for code, group in df.groupby("O*NET-SOC Code"):

        items = {}

        for _, row in group.iterrows():

            element_name = clean_text(row["Element Name"])
            scale_id = clean_text(row["Scale ID"])
            data_value = row["Data Value"]

            if not element_name or pd.isna(data_value):
                continue

            if element_name not in items:
                items[element_name] = {
                    "name": element_name,
                    "importance": None,
                    "level": None,
                }

            if scale_id == "IM":
                items[element_name]["importance"] = float(data_value)

            elif scale_id == "LV":
                items[element_name]["level"] = float(data_value)

        results[code] = list(items.values())

    return results


def build_software_items(df: pd.DataFrame) -> dict:
    """Group software skills by occupation."""

    results = {}

    for code, group in df.groupby("O*NET-SOC Code"):

        software = []

        for _, row in group.iterrows():

            workplace_example = clean_text(row["Workplace Example"])
            element_name = clean_text(row["Element Name"])

            if workplace_example:
                software.append({
                    "name": workplace_example,
                    "category": element_name,
                    "hot_technology": clean_text(row["Hot Technology"]),
                    "in_demand": clean_text(row["In Demand"]),
                })

        results[code] = software

    return results


def build_tasks(df: pd.DataFrame) -> dict:
    """Group task statements by occupation."""

    results = {}

    for code, group in df.groupby("O*NET-SOC Code"):

        tasks = []

        for _, row in group.iterrows():

            task = clean_text(row["Task"])

            if task:
                tasks.append({
                    "task": task,
                    "type": clean_text(row["Task Type"]),
                })

        results[code] = tasks

    return results


# ============================================================
# Main preprocessing pipeline
# ============================================================

def main():

    print("\n========================================")
    print("CareerAI - O*NET Preprocessing")
    print("========================================\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    occupations = load_csv("occupation_data.csv")
    job_zones = load_csv("job_zones.csv")
    tasks = load_csv("task_statements.csv")
    essential_skills = load_csv("essential_skills.csv")
    transferable_skills = load_csv("transferable_skills.csv")
    knowledge = load_csv("knowledge.csv")
    software = load_csv("software_skills.csv")

    # --------------------------------------------------------
    # Build lookup dictionaries
    # --------------------------------------------------------

    print("\nBuilding skill/knowledge lookups...")

    essential_lookup = build_rated_items(essential_skills)

    transferable_lookup = build_rated_items(transferable_skills)

    knowledge_lookup = build_rated_items(knowledge)

    software_lookup = build_software_items(software)

    tasks_lookup = build_tasks(tasks)

    # Job zone lookup

    job_zone_lookup = (
        job_zones
        .drop_duplicates("O*NET-SOC Code")
        .set_index("O*NET-SOC Code")["Job Zone"]
        .to_dict()
    )

    # --------------------------------------------------------
    # Create occupation profiles
    # --------------------------------------------------------

    print("\nCreating occupation profiles...")

    profiles = []

    for _, occupation in occupations.iterrows():

        code = clean_text(occupation["O*NET-SOC Code"])
        title = clean_text(occupation["Title"])
        description = clean_text(occupation["Description"])

        profile = {
            "occupation_code": code,
            "title": title,
            "description": description,

            "job_zone": job_zone_lookup.get(code),

            "tasks": tasks_lookup.get(code, []),

            "essential_skills": essential_lookup.get(code, []),

            "transferable_skills": transferable_lookup.get(code, []),

            "knowledge": knowledge_lookup.get(code, []),

            "software": software_lookup.get(code, []),
        }

        profiles.append(profile)

    # --------------------------------------------------------
    # Save JSONL
    # --------------------------------------------------------

    print(f"\nSaving {len(profiles)} occupation profiles...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        for profile in profiles:
            f.write(
                json.dumps(
                    profile,
                    ensure_ascii=False
                ) + "\n"
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n========================================")
    print("Preprocessing complete!")
    print("========================================")

    print(f"\nOutput file:")
    print(OUTPUT_FILE)

    print(f"\nOccupation profiles: {len(profiles):,}")

    print("\nExample occupation:")
    print(profiles[0]["title"])

    print("\nTasks:", len(profiles[0]["tasks"]))
    print("Essential skills:", len(profiles[0]["essential_skills"]))
    print("Transferable skills:", len(profiles[0]["transferable_skills"]))
    print("Knowledge:", len(profiles[0]["knowledge"]))
    print("Software:", len(profiles[0]["software"]))


if __name__ == "__main__":
    main()