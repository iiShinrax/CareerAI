import os
import json
import sys
import subprocess
import re

import faiss
from sentence_transformers import SentenceTransformer


# =========================================================
# Import existing CareerAI ranking functions
# =========================================================

sys.path.append("src")

from search_careers import (
    RETRIEVAL_K,
    calculate_technical_match,
    calculate_ai_relevance,
    calculate_ai_application_score,
    calculate_domain_score,
    calculate_title_relevance,
    calculate_final_score,
    collect_unique_candidates,
    generate_explanation,
    detect_skills,
)


# =========================================================
# Configuration
# =========================================================

INDEX_FILE = "vector_db/index.faiss"
METADATA_FILE = "vector_db/metadata.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# =========================================================
# Load FAISS
# =========================================================

print("Loading CareerAI retrieval system...")

index = faiss.read_index(INDEX_FILE)

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"Loaded {index.ntotal} vectors.")


# =========================================================
# Load embedding model
# =========================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("Retrieval system ready.")


# =========================================================
# QWEN ANALYSIS
# =========================================================

def analyze_query_with_qwen(query):

    print("\nStarting Qwen analysis...")

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..")
    )

    model_path = os.path.join(
        project_root,
        "src",
        "llm",
        "model.py"
    )

    result = subprocess.run(
        [
            sys.executable,
            model_path,
            "--json",
            query
        ],
        capture_output=True,
        text=True,
        cwd=project_root
    )

    if result.returncode != 0:

        print("\nQwen failed.")

        print(result.stderr)

        raise RuntimeError(
            "Qwen analysis failed."
        )

    output_lines = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    if not output_lines:
        raise ValueError(
            "Qwen returned no output."
        )

    json_output = output_lines[-1]

    try:

        profile = json.loads(json_output)

    except json.JSONDecodeError:

        print("\nInvalid JSON returned by Qwen:")

        print(result.stdout)

        raise

    return profile


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(value):

    if value is None:
        return ""

    return " ".join(
        str(value)
        .lower()
        .strip()
        .split()
    )


# =========================================================
# SAFE TERM MATCHING
# =========================================================

def contains_term(text, term):

    text = normalize_text(text)
    term = normalize_text(term)

    if not text or not term:
        return False

    # Multi-word phrase
    if " " in term:
        return term in text

    # Single word
    return re.search(
        rf"\b{re.escape(term)}\b",
        text
    ) is not None


# =========================================================
# CAREER FAMILIES
# =========================================================

CAREER_FAMILIES = {

    "ai_ml": [

        "ai engineer",
        "artificial intelligence engineer",
        "machine learning engineer",
        "ml engineer",
        "machine learning",
        "artificial intelligence",
        "deep learning",
        "ai",
        "ml",

    ],

    "data_science": [

        "data scientist",
        "data science",
        "data analyst",
        "data analysis",
        "statistics",
        "statistical analysis",

    ],

    "cybersecurity": [

        "cybersecurity",
        "cyber security",
        "information security",
        "infosec",
        "security analyst",
        "cybersecurity analyst",
        "information security analyst",
        "infosec analyst",
        "security engineer",
        "penetration testing",
        "penetration tester",
        "ethical hacking",
        "digital forensics",

    ],

    "software": [

        "software engineer",
        "software developer",
        "software development",
        "application developer",
        "application development",

        # IMPORTANT:
        # Do NOT include:
        # programmer
        # programming
        #
        # They are too generic and create false matches.

    ],

    "robotics": [

        "robotics",
        "robotics engineer",
        "robotics technician",
        "robotic systems",
        "autonomous systems",

    ],

    "electronics": [

        "electronics engineer",
        "electrical engineer",
        "electronics",
        "electrical engineering",
        "embedded systems",
        "embedded engineer",
        "microcontroller",

    ],

    "mechanical": [

        "mechanical engineer",
        "mechanical engineering",
        "mechanical systems",

    ],

    "data_engineering": [

        "data engineer",
        "data engineering",
        "data warehouse",
        "data warehousing",
        "database engineer",
        "database administrator",
        "etl",

    ],

    "networking": [

        "network engineer",
        "networking",
        "network administrator",
        "computer networks",
        "network security",

    ],

    "cloud": [

        "cloud engineer",
        "cloud computing",
        "cloud architect",
        "cloud infrastructure",
        "aws",
        "azure",
        "gcp",

    ],
}


# =========================================================
# TARGET FAMILY DETECTION
# =========================================================

def detect_target_families(target_text):

    target_text = normalize_text(target_text)

    families = []

    for family, terms in CAREER_FAMILIES.items():

        for term in terms:

            if contains_term(target_text, term):

                families.append(family)

                break

    return list(
        dict.fromkeys(families)
    )


# =========================================================
# OCCUPATION FAMILY DETECTION
# =========================================================

def detect_occupation_families(
    title_text,
    occupation_text
):

    title_text = normalize_text(title_text)
    occupation_text = normalize_text(
        occupation_text
    )

    families = []

    for family, terms in CAREER_FAMILIES.items():

        for term in terms:

            # -------------------------------------------------
            # IMPORTANT
            #
            # Career family should primarily come from the
            # occupation TITLE.
            #
            # Otherwise an occupation such as Robotics Engineer
            # may become "AI" simply because its description
            # mentions AI.
            # -------------------------------------------------

            if contains_term(title_text, term):

                families.append(family)

                break

    return list(
        dict.fromkeys(families)
    )


# =========================================================
# CAREER GOAL SCORE
# =========================================================

def calculate_career_goal_score(
    title,
    text,
    career_goal,
    preferred_roles,
    domains
):

    """
    Measures how closely an O*NET occupation matches
    the user's explicit career goal.

    This version is intentionally TITLE-FOCUSED.

    Generic words such as "programming" inside an occupation
    description should NOT make an occupation an AI career.

    Score philosophy:

        1.00  = exact role/title
        0.90+ = direct target career
        0.75  = strongly related
        0.60  = good adjacent implementation career
        0.35  = distant but relevant adjacent career
        0.00  = no meaningful career-goal match
    """

    title_text = normalize_text(title)

    occupation_text = normalize_text(
        text
    )

    goal_text = normalize_text(
        career_goal
    )

    preferred_roles = preferred_roles or []
    domains = domains or []

    role_text = " ".join(
        normalize_text(role)
        for role in preferred_roles
        if normalize_text(role)
    )

    domain_text = " ".join(
        normalize_text(domain)
        for domain in domains
        if normalize_text(domain)
    )

    target_text = " ".join(
        [
            goal_text,
            role_text,
            domain_text,
        ]
    )

    target_families = detect_target_families(
        target_text
    )

    occupation_families = detect_occupation_families(
        title_text,
        occupation_text
    )

    score = 0.0

    # =====================================================
    # 1. EXACT CAREER GOAL / ROLE TITLE
    # =====================================================

    role_candidates = []

    if goal_text:
        role_candidates.append(
            goal_text
        )

    role_candidates.extend(
        normalize_text(role)
        for role in preferred_roles
        if normalize_text(role)
    )

    for role in role_candidates:

        if not role:
            continue

        if role == title_text:

            return 1.0

        if contains_term(
            title_text,
            role
        ):

            score = max(
                score,
                0.95
            )

    # =====================================================
    # 2. DIRECT FAMILY MATCH
    # =====================================================

    matching_families = (
        set(target_families)
        .intersection(
            occupation_families
        )
    )

    for family in matching_families:

        if family == "ai_ml":

            score = max(
                score,
                0.95
            )

        elif family == "data_science":

            score = max(
                score,
                0.85
            )

        elif family == "software":

            score = max(
                score,
                0.65
            )

        elif family == "data_engineering":

            score = max(
                score,
                0.60
            )

        elif family == "cybersecurity":

            score = max(
                score,
                0.60
            )

        else:

            score = max(
                score,
                0.50
            )

    # =====================================================
    # 3. AI/ML CAREER → RELATED CAREERS
    # =====================================================

    if "ai_ml" in target_families:

        # -------------------------------------------------
        # Data Science
        # -------------------------------------------------

        if "data_science" in occupation_families:

            score = max(
                score,
                0.82
            )

        # -------------------------------------------------
        # Software
        # -------------------------------------------------

        if "software" in occupation_families:

            score = max(
                score,
                0.65
            )

        # -------------------------------------------------
        # Data Engineering
        # -------------------------------------------------

        if "data_engineering" in occupation_families:

            score = max(
                score,
                0.60
            )

        # -------------------------------------------------
        # Robotics
        #
        # Robotics is relevant to AI, but should NOT beat
        # direct AI/software careers.
        # -------------------------------------------------

        if (
            "robotics" in occupation_families
            and "robotics" not in target_families
        ):

            score = max(
                score,
                0.35
            )

        # -------------------------------------------------
        # Computer / adjacent engineering
        # -------------------------------------------------

        if "electronics" in occupation_families:

            score = max(
                score,
                0.25
            )

        if "mechanical" in occupation_families:

            score = max(
                score,
                0.20
            )

    # =====================================================
    # 4. DOMAIN SUPPORT
    # =====================================================

    # Domain information can support an existing family
    # match, but should NOT create a career match by itself.

    if matching_families:

        for family in matching_families:

            family_terms = CAREER_FAMILIES[
                family
            ]

            domain_matches = sum(
                1
                for term in family_terms
                if contains_term(
                    domain_text,
                    term
                )
            )

            if domain_matches > 0:

                score = max(
                    score,
                    min(
                        score + 0.05,
                        1.0
                    )
                )

    # =====================================================
    # 5. PREFERRED ROLE WORD OVERLAP
    # =====================================================

    title_words = set(
        title_text.split()
    )

    for role in preferred_roles:

        role = normalize_text(role)

        if not role:
            continue

        role_words = set(
            role.split()
        )

        common_words = (
            role_words
            .intersection(title_words)
        )

        # Require meaningful overlap.
        #
        # "AI Engineer" vs "Computer Engineer"
        # should NOT match just because both contain
        # "engineer".

        if (
            len(role_words) >= 2
            and len(common_words) >= 2
        ):

            overlap_ratio = (
                len(common_words)
                /
                len(role_words)
            )

            if overlap_ratio >= 0.75:

                score = max(
                    score,
                    0.55
                )

    # =====================================================
    # 6. IMPORTANT:
    # DESCRIPTION-ONLY AI MATCHES DO NOT CREATE
    # CAREER-GOAL MATCHES.
    # =====================================================

    # We intentionally DO NOT do something like:
    #
    # "if 'machine learning' appears twice in description:
    #       score = 0.55"
    #
    # because this caused unrelated occupations to look like
    # AI careers.

    # =====================================================
    # 7. ROBOTICS SAFETY CAP
    # =====================================================

    if (
        "robotics" in occupation_families
        and "ai_ml" in target_families
        and "robotics" not in target_families
    ):

        score = min(
            score,
            0.35
        )

    return min(
        score,
        1.0
    )


# =========================================================
# GOAL-AWARE SCORE
# =========================================================

def calculate_goal_aware_score(
    base_score,
    career_goal_score,
    title_relevance,
    ai_intent
):

    """
    Adds career-goal alignment to the existing
    O*NET ranking score.

    Career goal is important, but should NOT dominate
    semantic / technical evidence.
    """

    # -----------------------------------------------------
    # Reduced from 0.35
    #
    # Previously:
    #
    # career_goal_score * 0.35
    #
    # That was too powerful.
    # -----------------------------------------------------

    goal_bonus = (
        career_goal_score * 0.15
    )

    # Small title bonus.
    #
    # Title relevance is already represented in the
    # underlying ranking, so this should remain small.

    title_bonus = (
        title_relevance * 0.03
    )

    final_score = (
        base_score
        + goal_bonus
        + title_bonus
    )

    return min(
        final_score,
        1.0
    )


# =========================================================
# GET O*NET CODE
# =========================================================

def get_onet_code(result):

    possible_keys = [
        "onet_code",
        "O*NET Code",
        "O_NET Code",
        "code",
        "occupation_code",
    ]

    for key in possible_keys:

        if key in result:

            return result[key]

    return "N/A"


# =========================================================
# BUILD RETRIEVAL QUERY
# =========================================================

def build_retrieval_query(profile):

    career_goal = profile.get(
        "career_goal",
        ""
    )

    skills = profile.get(
        "skills",
        []
    )

    preferred_roles = profile.get(
        "preferred_roles",
        []
    )

    domains = profile.get(
        "domains",
        []
    )

    career_intent = profile.get(
        "career_intent",
        ""
    )

    query_parts = []

    if career_goal:

        query_parts.append(
            f"Career goal: {career_goal}"
        )

    if skills:

        query_parts.append(
            "Skills: "
            + ", ".join(skills)
        )

    if preferred_roles:

        query_parts.append(
            "Preferred roles: "
            + ", ".join(preferred_roles)
        )

    if domains:

        query_parts.append(
            "Domains: "
            + ", ".join(domains)
        )

    if career_intent:

        query_parts.append(
            f"Career intent: {career_intent}"
        )

    return "\n".join(
        query_parts
    )


# =========================================================
# BUILD RANKING QUERY
# =========================================================

def build_ranking_query(profile):

    parts = []

    career_goal = profile.get(
        "career_goal",
        ""
    )

    skills = profile.get(
        "skills",
        []
    )

    preferred_roles = profile.get(
        "preferred_roles",
        []
    )

    domains = profile.get(
        "domains",
        []
    )

    career_intent = profile.get(
        "career_intent",
        ""
    )

    if career_goal:
        parts.append(
            career_goal
        )

    if skills:
        parts.extend(skills)

    if preferred_roles:
        parts.extend(preferred_roles)

    if domains:
        parts.extend(domains)

    if career_intent:
        parts.append(
            career_intent
        )

    return " ".join(
        str(x)
        for x in parts
        if x
    )


# =========================================================
# AI INTENT DETECTION
# =========================================================

def detect_ai_intent(profile):

    goal = normalize_text(
        profile.get(
            "career_goal",
            ""
        )
    )

    domains = " ".join(
        normalize_text(x)
        for x in profile.get(
            "domains",
            []
        )
    )

    roles = " ".join(
        normalize_text(x)
        for x in profile.get(
            "preferred_roles",
            []
        )
    )

    combined = " ".join(
        [
            goal,
            domains,
            roles
        ]
    )

    ai_terms = [
        "ai engineer",
        "artificial intelligence",
        "artificial intelligence engineer",
        "machine learning",
        "machine learning engineer",
        "ml engineer",
        "deep learning",
        "ai",
        "ml",
    ]

    return any(
        contains_term(
            combined,
            term
        )
        for term in ai_terms
    )


# =========================================================
# RETRIEVE CAREERS
# =========================================================

def retrieve_careers(
    profile,
    top_k=10
):

    # =====================================================
    # Build queries
    # =====================================================

    retrieval_query = build_retrieval_query(
        profile
    )

    ranking_query = build_ranking_query(
        profile
    )

    print("\n" + "=" * 70)

    print(
        "LLM-GENERATED RETRIEVAL QUERY"
    )

    print("=" * 70)

    print(
        retrieval_query
    )

    print("\n" + "=" * 70)

    print(
        "RANKING QUERY"
    )

    print("=" * 70)

    print(
        ranking_query
    )

    # =====================================================
    # Detect ranking skills
    # =====================================================

    detected_skills = detect_skills(
        ranking_query
    )

    print(
        "\nDetected ranking skills:"
    )

    print(
        ", ".join(
            detected_skills
        )
    )

    # =====================================================
    # Detect AI intent
    # =====================================================

    ai_intent = detect_ai_intent(
        profile
    )

    print(
        f"\nAI career intent detected: "
        f"{ai_intent}"
    )

    # =====================================================
    # Generate embedding
    # =====================================================

    print(
        "\nGenerating retrieval embedding..."
    )

    query_embedding = (
        embedding_model.encode(
            [retrieval_query],
            normalize_embeddings=True
        )
    )

    query_embedding = (
        query_embedding
        .astype("float32")
    )

    # =====================================================
    # FAISS SEARCH
    # =====================================================

    scores, indices = index.search(
        query_embedding,
        RETRIEVAL_K
    )

    candidates = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0:
            continue

        try:

            item = metadata[idx]

        except (
            IndexError,
            KeyError
        ):

            continue

        if isinstance(item, dict):

            result = dict(item)

        else:

            continue

        # Store semantic score
        result["_semantic_score"] = float(
            score
        )

        candidates.append(
            result
        )

    # =====================================================
    # Remove duplicates
    # =====================================================

    candidates = collect_unique_candidates(
    metadata,
    scores,
    indices
)

    print(
        f"\nRetrieved {len(candidates)} "
        f"unique occupations."
    )

    # =====================================================
    # Ranking
    # =====================================================

    ranked_results = []

    career_goal = profile.get(
        "career_goal",
        ""
    )

    preferred_roles = profile.get(
        "preferred_roles",
        []
    )

    domains = profile.get(
        "domains",
        []
    )

    for candidate in candidates:

        title = candidate.get(
            "title",
            candidate.get(
                "occupation",
                candidate.get(
                    "name",
                    ""
                )
            )
        )

        description = candidate.get(
            "description",
            candidate.get(
                "text",
                candidate.get(
                    "occupation_text",
                    ""
                )
            )
        )

        # =================================================
        # Existing ranking metrics
        # =================================================

        semantic_score = float(
            candidate.get(
                "_semantic_score",
                0.0
            )
        )

        technical_score = calculate_technical_match(
            description,
            detected_skills
        )

        ai_relevance = calculate_ai_relevance(
            title,
            description,
            detected_skills
        )

        ai_application_score = (
            calculate_ai_application_score(
                title,
                description
            )
        )

        domain_score = calculate_domain_score(
            title,
            description
        )

        title_relevance = calculate_title_relevance(
            title,
            detected_skills
        )

        base_score = calculate_final_score(
            semantic_score,
            technical_score,
            ai_relevance,
            ai_application_score,
            domain_score,
            title_relevance
        )

        # =================================================
        # Career goal score
        # =================================================

        career_goal_score = (
            calculate_career_goal_score(
                title=title,
                text=description,
                career_goal=career_goal,
                preferred_roles=preferred_roles,
                domains=domains
            )
        )

        # =================================================
        # AI INTENT FILTER
        # =================================================

        # If the user explicitly wants AI/ML, remove
        # occupations that have no meaningful connection
        # to that goal.
        #
        # This prevents things such as:
        #
        # CNC Tool Programmers
        # Computer Repairers
        # unrelated Electronics occupations
        #
        # from entering the top results simply because
        # they contain "programming" somewhere.

        if ai_intent:

            meaningful_ai_match = (
                ai_relevance > 0
                or ai_application_score >= 0.15
                or career_goal_score >= 0.30
            )

            if not meaningful_ai_match:

                continue

        # =================================================
        # Goal-aware final score
        # =================================================

        final_score = calculate_goal_aware_score(
            base_score=base_score,
            career_goal_score=career_goal_score,
            title_relevance=title_relevance,
            ai_intent=ai_intent
        )

        # =================================================
        # Explanation
        # =================================================

        explanation = generate_explanation(
            title,
            description,
            detected_skills,
            semantic_score,
            technical_score,
            ai_relevance,
            ai_application_score,
            domain_score,
            title_relevance
        )

        # =================================================
        # Save result
        # =================================================

        result = dict(candidate)

        result.update({

            "career": title,

            "onet_code": get_onet_code(
                candidate
            ),

            "semantic_score": semantic_score,

            "technical_match": technical_score,

            "ai_relevance": ai_relevance,

            "ai_application_score":
                ai_application_score,

            "domain_score":
                domain_score,

            "title_relevance":
                title_relevance,

            "career_goal_score":
                career_goal_score,

            "base_final_score":
                base_score,

            "final_score":
                final_score,

            "explanation":
                explanation,

        })

        ranked_results.append(
            result
        )

    # =====================================================
    # Sort
    # =====================================================

    ranked_results.sort(
        key=lambda x: x.get(
            "final_score",
            0.0
        ),
        reverse=True
    )

    return ranked_results[:top_k]


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n" + "=" * 70)

    print(
        "CareerAI LLM + O*NET RETRIEVAL TEST"
    )

    print("=" * 70)

    query = input(
        "\nEnter your career query: "
    ).strip()

    if not query:

        print(
            "No query entered."
        )

        return

    # =====================================================
    # Qwen
    # =====================================================

    print(
        "\nAnalyzing query with Qwen..."
    )

    profile = analyze_query_with_qwen(
        query
    )

    # =====================================================
    # Print Qwen profile
    # =====================================================

    print("\n" + "=" * 70)

    print(
        "QWEN CAREER PROFILE"
    )

    print("=" * 70)

    print(
        json.dumps(
            profile,
            indent=4,
            ensure_ascii=False
        )
    )

    # =====================================================
    # Retrieve
    # =====================================================

    results = retrieve_careers(
        profile,
        top_k=10
    )

    # =====================================================
    # Print results
    # =====================================================

    print("\n" + "=" * 70)

    print(
        "TOP CAREER MATCHES"
    )

    print("=" * 70)

    if not results:

        print(
            "\nNo meaningful career matches found."
        )

        return

    for i, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n#{i}"
        )

        print(
            f"Career: "
            f"{result.get('career', 'N/A')}"
        )

        print(
            f"O*NET Code: "
            f"{result.get('onet_code', 'N/A')}"
        )

        print(
            f"Semantic Score: "
            f"{result.get('semantic_score', 0):.4f}"
        )

        print(
            f"Technical Match: "
            f"{result.get('technical_match', 0):.4f}"
        )

        print(
            f"AI Relevance: "
            f"{result.get('ai_relevance', 0):.4f}"
        )

        print(
            f"AI Application Score: "
            f"{result.get('ai_application_score', 0):.4f}"
        )

        print(
            f"Domain Score: "
            f"{result.get('domain_score', 0):.4f}"
        )

        print(
            f"Title Relevance: "
            f"{result.get('title_relevance', 0):.4f}"
        )

        print(
            f"Career Goal Score: "
            f"{result.get('career_goal_score', 0):.4f}"
        )

        print(
            f"Base Final Score: "
            f"{result.get('base_final_score', 0):.4f}"
        )

        print(
            f"Final Score: "
            f"{result.get('final_score', 0):.4f}"
        )

        print(
            f"Matched Terms: "
            f"{result.get('matched_terms', 'N/A')}"
        )

        print(
            f"Why: "
            f"{result.get('explanation', 'N/A')}"
        )

        print("-" * 150)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()