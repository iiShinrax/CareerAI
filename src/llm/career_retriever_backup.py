
import os
import json
import sys
import subprocess

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
# Load FAISS + metadata
# =========================================================

print("Loading CareerAI retrieval system...")

index = faiss.read_index(INDEX_FILE)

with open(
    METADATA_FILE,
    "r",
    encoding="utf-8"
) as f:
    metadata = json.load(f)

print(f"Loaded {index.ntotal} vectors.")

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Retrieval system ready.")


# =========================================================
# Qwen analysis in separate process
# =========================================================

def analyze_query_with_qwen(query):
    """
    Run Qwen in a separate Python process.

    This prevents Qwen and SentenceTransformer from
    sharing the same PyTorch process on Apple Silicon.
    """

    project_root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../.."
        )
    )

    model_path = os.path.join(
        project_root,
        "src",
        "llm",
        "model.py"
    )

    print("\nStarting Qwen analysis...")

    result = subprocess.run(
        [
            sys.executable,
            model_path,
            "--json",
            query,
        ],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    if result.returncode != 0:

        print("\nQwen process failed.")

        print("\nSTDOUT:")
        print(result.stdout)

        print("\nSTDERR:")
        print(result.stderr)

        raise RuntimeError(
            "Qwen analysis process failed."
        )

    output_lines = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    if not output_lines:
        raise RuntimeError(
            "Qwen returned no output."
        )

    json_output = output_lines[-1]

    try:
        profile = json.loads(
            json_output
        )

    except json.JSONDecodeError:

        print("\nQwen returned invalid JSON:")
        print(result.stdout)

        raise RuntimeError(
            "Could not parse Qwen JSON output."
        )

    return profile


# =========================================================
# Build retrieval query
# =========================================================

def build_retrieval_query(profile):
    """
    Convert the structured Qwen profile into
    a richer semantic retrieval query.
    """

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
            f"Career goal: {career_goal}"
        )

    if skills:
        parts.append(
            "Skills: "
            + ", ".join(skills)
        )

    if preferred_roles:
        parts.append(
            "Preferred roles: "
            + ", ".join(preferred_roles)
        )

    if domains:
        parts.append(
            "Domains: "
            + ", ".join(domains)
        )

    if career_intent:
        parts.append(
            f"Career intent: {career_intent}"
        )

    return "\n".join(parts)


# =========================================================
# Build ranking query
# =========================================================

def build_ranking_query(profile):

    parts = []

    if profile.get("career_goal"):
        parts.append(
            profile["career_goal"]
        )

    parts.extend(
        profile.get(
            "skills",
            []
        )
    )

    parts.extend(
        profile.get(
            "preferred_roles",
            []
        )
    )

    parts.extend(
        profile.get(
            "domains",
            []
        )
    )

    if profile.get("career_intent"):
        parts.append(
            profile["career_intent"]
        )

    return " ".join(parts)


# =========================================================
# Normalize text
# =========================================================

def normalize_text(value):

    if value is None:
        return ""

    return str(value).lower().strip()


# =========================================================
# Get O*NET code from metadata
# =========================================================

def get_onet_code(result):
    """Extract the O*NET-SOC occupation code from metadata."""
    return (
        result.get("occupation_code")
        or result.get("onet_code")
        or result.get("O*NET-SOC Code")
        or result.get("O*NET-SOC code")
        or result.get("O*NET Code")
        or result.get("soc_code")
        or result.get("SOC Code")
        or result.get("code")
    )

# =========================================================
# Career goal score
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
    the user's actual career goal.

    This is intentionally conservative.

    We do NOT want "AI engineer" to automatically make
    every software/robotics occupation an AI occupation.
    """

    title_text = normalize_text(title)
    occupation_text = normalize_text(text)

    goal_text = normalize_text(
        career_goal
    )

    role_text = " ".join(
        normalize_text(role)
        for role in preferred_roles
    )

    domain_text = " ".join(
        normalize_text(domain)
        for domain in domains
    )

    target_text = (
        goal_text
        + " "
        + role_text
    )

    score = 0.0

    # -----------------------------------------------------
    # Exact / strong target matches
    # -----------------------------------------------------

    if (
        "ai engineer" in target_text
        and "ai" in title_text
        and "engineer" in title_text
    ):
        score = max(
            score,
            1.0
        )

    # -----------------------------------------------------
    # Machine-learning-related occupations
    # -----------------------------------------------------

    ml_terms = [
        "machine learning",
        "machine-learning",
        "artificial intelligence",
        "ai",
        "deep learning",
    ]

    ml_matches = sum(
        1
        for term in ml_terms
        if term in title_text
    )

    if ml_matches:
        score = max(
            score,
            min(
                0.90,
                0.55 + (0.10 * ml_matches)
            )
        )

    # -----------------------------------------------------
    # Data science occupations
    # -----------------------------------------------------

    if (
        "data scientist" in title_text
        or "data science" in title_text
    ):

        if (
            "ai" in target_text
            or "machine learning" in domain_text
        ):
            score = max(
                score,
                0.70
            )

    # -----------------------------------------------------
    # Software development
    # -----------------------------------------------------

    if (
        "software developer" in title_text
        or "software development" in title_text
    ):

        if (
            "ai engineer" in target_text
            or "machine learning" in domain_text
            or "artificial intelligence" in domain_text
        ):
            score = max(
                score,
                0.50
            )

    # -----------------------------------------------------
    # Robotics
    # -----------------------------------------------------

    if "robotics" in title_text:

        if (
            "robotics" in target_text
            or "robotics" in domain_text
        ):
            score = max(
                score,
                0.80
            )
        else:
            # Robotics is related to AI, but it is not
            # automatically the user's target.
            score = max(
                score,
                0.25
            )

    # -----------------------------------------------------
    # Generic engineering
    # -----------------------------------------------------

    if (
        "engineer" in title_text
        and score == 0.0
    ):

        if (
            "ai engineer" in target_text
            or "machine learning" in domain_text
            or "artificial intelligence" in domain_text
        ):
            score = 0.20

    # -----------------------------------------------------
    # AI language in occupation description
    # -----------------------------------------------------

    if (
        score == 0.0
        and (
            "artificial intelligence" in occupation_text
            or "machine learning" in occupation_text
            or "deep learning" in occupation_text
        )
    ):

        score = 0.30

    return min(
        score,
        1.0
    )


# =========================================================
# Goal-aware final score
# =========================================================

def calculate_goal_aware_score(
    base_score,
    career_goal_score,
    title_relevance,
    ai_intent
):
    """
    Adjust the existing ranking score using the
    user's explicit career goal.

    We keep the adjustment moderate so the existing
    ranking system still contributes significantly.
    """

    if not ai_intent:

        return base_score

    # Give explicit career goal a meaningful influence.
    goal_bonus = (
        career_goal_score * 0.25
    )

    title_bonus = (
        title_relevance * 0.10
    )

    final_score = (
        base_score
        + goal_bonus
        + title_bonus
    )

    return final_score


# =========================================================
# Retrieve and rank careers
# =========================================================

def retrieve_careers(
    profile,
    top_k=10
):

    retrieval_query = (
        build_retrieval_query(
            profile
        )
    )

    ranking_query = (
        build_ranking_query(
            profile
        )
    )

    print("\n" + "=" * 70)
    print("LLM-GENERATED RETRIEVAL QUERY")
    print("=" * 70)

    print(retrieval_query)

    print("\n" + "=" * 70)
    print("RANKING QUERY")
    print("=" * 70)

    print(ranking_query)

    # -----------------------------------------------------
    # Detect skills
    # -----------------------------------------------------

    detected_skills = detect_skills(
        ranking_query
    )

    print("\nDetected ranking skills:")

    if detected_skills:

        print(
            ", ".join(
                detected_skills
            )
        )

    else:

        print("None")

    # -----------------------------------------------------
    # AI intent
    # -----------------------------------------------------

    goal = normalize_text(
        profile.get(
            "career_goal",
            ""
        )
    )

    domains = " ".join(
        profile.get(
            "domains",
            []
        )
    ).lower()

    ai_intent = any(
        term in (
            goal + " " + domains
        )
        for term in [
            "ai",
            "artificial intelligence",
            "machine learning",
            "deep learning",
        ]
    )

    # -----------------------------------------------------
    # Embed enriched query
    # -----------------------------------------------------

    print(
        "\nGenerating retrieval embedding..."
    )

    query_embedding = (
        embedding_model.encode(
            [retrieval_query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    )

    retrieval_k = min(
        RETRIEVAL_K,
        index.ntotal
    )

    scores, indices = index.search(
        query_embedding.astype(
            "float32"
        ),
        retrieval_k
    )

    # -----------------------------------------------------
    # Deduplicate
    # -----------------------------------------------------

    candidates = (
        collect_unique_candidates(
            metadata,
            scores,
            indices
        )
    )

    print(
        f"\nRetrieved {len(candidates)} "
        f"unique occupations."
    )

    # -----------------------------------------------------
    # Rank candidates
    # -----------------------------------------------------

    ranked_results = []

    for candidate in candidates:

        result = candidate[
            "result"
        ]

        semantic_score = candidate[
            "semantic_score"
        ]

        title = result.get(
            "title",
            ""
        )

        text = result.get(
            "text",
            ""
        )

        # -------------------------------------------------
        # Existing scores
        # -------------------------------------------------

        technical_score, matched_terms = (
            calculate_technical_match(
                text,
                detected_skills
            )
        )

        ai_relevance = (
            calculate_ai_relevance(
                title,
                text,
                detected_skills
            )
        )

        ai_application_score = (
            calculate_ai_application_score(
                title,
                text
            )
        )

        domain_score = (
            calculate_domain_score(
                title,
                text
            )
        )

        title_relevance = (
            calculate_title_relevance(
                title,
                detected_skills
            )
        )

        base_final_score = (
            calculate_final_score(
                semantic_score,
                technical_score,
                ai_relevance,
                ai_application_score,
                domain_score,
                title_relevance,
                ai_intent,
                detected_skills
            )
        )

        # -------------------------------------------------
        # NEW: career-goal score
        # -------------------------------------------------

        career_goal_score = (
            calculate_career_goal_score(
                title,
                text,
                profile.get(
                    "career_goal",
                    ""
                ),
                profile.get(
                    "preferred_roles",
                    []
                ),
                profile.get(
                    "domains",
                    []
                )
            )
        )

        # -------------------------------------------------
        # NEW: goal-aware final score
        # -------------------------------------------------

        final_score = (
            calculate_goal_aware_score(
                base_final_score,
                career_goal_score,
                title_relevance,
                ai_intent
            )
        )

        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        explanation = generate_explanation(
            title,
            matched_terms,
            technical_score,
            ai_relevance,
            title_relevance
        )

        # Add goal explanation
        if career_goal_score >= 0.80:

            explanation += (
                " Strong match to the user's "
                "explicit career goal."
            )

        elif career_goal_score >= 0.50:

            explanation += (
                " Moderately aligned with the "
                "user's explicit career goal."
            )

        elif career_goal_score > 0:

            explanation += (
                " Some relevance to the user's "
                "career goal."
            )

        ranked_results.append({

            "title": title,

            "onet_code":
                get_onet_code(
                    result
                ),

            "semantic_score":
                semantic_score,

            "technical_score":
                technical_score,

            "ai_relevance":
                ai_relevance,

            "ai_application_score":
                ai_application_score,

            "domain_score":
                domain_score,

            "title_relevance":
                title_relevance,

            "career_goal_score":
                career_goal_score,

            "base_final_score":
                base_final_score,

            "final_score":
                final_score,

            "matched_terms":
                matched_terms,

            "explanation":
                explanation,

            "occupation":
                result,
        })

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    ranked_results.sort(
        key=lambda x:
            x["final_score"],
        reverse=True
    )

    return ranked_results[:top_k]


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print(
        "CareerAI LLM + O*NET RETRIEVAL TEST"
    )
    print("=" * 70)

    user_query = input(
        "\nEnter your career query: "
    )

    # -----------------------------------------------------
    # Qwen
    # -----------------------------------------------------

    print(
        "\nAnalyzing query with Qwen..."
    )

    profile = (
        analyze_query_with_qwen(
            user_query
        )
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "QWEN CAREER PROFILE"
    )

    print(
        "=" * 70
    )

    print(
        json.dumps(
            profile,
            indent=4,
            ensure_ascii=False
        )
    )

    # -----------------------------------------------------
    # Retrieval
    # -----------------------------------------------------

    results = retrieve_careers(
        profile,
        top_k=10
    )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "TOP CAREER MATCHES"
    )

    print(
        "=" * 70
    )

    for i, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n#{i}"
        )

        print(
            f"Career: "
            f"{result['title']}"
        )

        print(
            f"O*NET Code: "
            f"{result['onet_code']}"
        )

        print(
            f"Semantic Score: "
            f"{result['semantic_score']:.4f}"
        )

        print(
            f"Technical Match: "
            f"{result['technical_score']:.4f}"
        )

        print(
            f"AI Relevance: "
            f"{result['ai_relevance']:.4f}"
        )

        print(
            f"AI Application Score: "
            f"{result['ai_application_score']:.4f}"
        )

        print(
            f"Domain Score: "
            f"{result['domain_score']:.4f}"
        )

        print(
            f"Title Relevance: "
            f"{result['title_relevance']:.4f}"
        )

        print(
            f"Career Goal Score: "
            f"{result['career_goal_score']:.4f}"
        )

        print(
            f"Base Final Score: "
            f"{result['base_final_score']:.4f}"
        )

        print(
            f"Final Score: "
            f"{result['final_score']:.4f}"
        )

        if result[
            "matched_terms"
        ]:

            print(
                "Matched Terms: "
                + ", ".join(
                    result[
                        "matched_terms"
                    ][:6]
                )
            )

        print(
            "Why: "
            + result["explanation"]
        )

        print(
            "-" * 70
        )
