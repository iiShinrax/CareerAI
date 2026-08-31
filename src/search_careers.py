import json
import re

import faiss
from sentence_transformers import SentenceTransformer


# =========================================================
# Configuration
# =========================================================

INDEX_FILE = "vector_db/index.faiss"
METADATA_FILE = "vector_db/metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"

TOP_K = 10


# =========================================================
# Skill Families
# =========================================================

SKILL_FAMILIES = {

    "python": {
        "keywords": [
            "python",
            "python programming",
            "python software",
        ],
        "related": [
            "programming",
            "software development",
            "object oriented programming",
            "data analysis",
            "data science",
        ],
    },

    "machine_learning": {
        "keywords": [
            "machine learning",
            "machine-learning",
            "predictive modeling",
            "statistical learning",
        ],
        "related": [
            "data science",
            "data mining",
            "statistical modeling",
            "artificial intelligence",
            "analytics",
            "pattern recognition",
        ],
    },

    "deep_learning": {
        "keywords": [
            "deep learning",
            "neural network",
            "neural networks",
            "deep neural network",
            "deep neural networks",
        ],
        "related": [
            "machine learning",
            "artificial intelligence",
            "computer vision",
            "natural language processing",
            "pattern recognition",
        ],
    },

    "artificial_intelligence": {
        "keywords": [
            "artificial intelligence",
            "ai applications",
            "ai application",
            "ai",
        ],
        "related": [
            "machine learning",
            "deep learning",
            "neural networks",
            "computer vision",
            "natural language processing",
            "expert systems",
            "data science",
        ],
    },

    "data_science": {
        "keywords": [
            "data science",
            "data scientist",
            "data analysis",
            "data analytics",
        ],
        "related": [
            "machine learning",
            "statistics",
            "data mining",
            "predictive modeling",
            "python",
        ],
    },

    "computer_vision": {
        "keywords": [
            "computer vision",
            "image recognition",
            "image classification",
            "object detection",
        ],
        "related": [
            "deep learning",
            "machine learning",
            "neural networks",
            "image processing",
            "artificial intelligence",
        ],
    },

    "nlp": {
        "keywords": [
            "natural language processing",
            "nlp",
            "language model",
            "large language model",
            "llm",
        ],
        "related": [
            "deep learning",
            "machine learning",
            "artificial intelligence",
            "text analysis",
            "linguistics",
        ],
    },
}


# =========================================================
# Query Skill Detection
# =========================================================

def detect_skills(query):
    """
    Detect technical skill families mentioned in the query.
    """

    text = query.lower()

    detected = []

    for skill, data in SKILL_FAMILIES.items():

        for keyword in data["keywords"]:

            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

            if re.search(pattern, text):
                detected.append(skill)
                break

    return detected


# =========================================================
# Text Normalization
# =========================================================

def normalize(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    )


# =========================================================
# Technical Matching
# =========================================================

def calculate_technical_match(text, detected_skills):
    """
    Calculate how strongly an occupation matches
    the user's technical profile.

    AI/ML-related skills receive more weight than
    generic programming skills.
    """

    text = normalize(text)

    if not detected_skills:
        return 0.0, []

    # Importance of each skill family.
    #
    # Higher values mean the skill has greater influence
    # on the final technical compatibility score.
    skill_weights = {

        "python": 0.8,

        "machine_learning": 1.5,

        "deep_learning": 1.7,

        "artificial_intelligence": 1.6,

        "data_science": 1.3,

        "computer_vision": 1.5,

        "nlp": 1.5,
    }

    total_score = 0.0
    max_score = 0.0

    matched_terms = []

    for skill in detected_skills:

        data = SKILL_FAMILIES[skill]

        weight = skill_weights.get(skill, 1.0)

        max_score += weight

        exact_match = False

        related_matches = 0

        # -------------------------------------------------
        # Exact keyword matching
        # -------------------------------------------------

        for keyword in data["keywords"]:

            pattern = r"\b" + re.escape(
                keyword.lower()
            ) + r"\b"

            if re.search(pattern, text):

                exact_match = True

                if keyword not in matched_terms:
                    matched_terms.append(keyword)

                break

        # -------------------------------------------------
        # Related keyword matching
        # -------------------------------------------------

        for keyword in data["related"]:

            pattern = r"\b" + re.escape(
                keyword.lower()
            ) + r"\b"

            if re.search(pattern, text):

                related_matches += 1

                if keyword not in matched_terms:
                    matched_terms.append(keyword)

        # -------------------------------------------------
        # Scoring
        # -------------------------------------------------

        if exact_match:

            total_score += weight

        elif related_matches > 0:

            related_score = min(
                0.45 * related_matches,
                0.75
            )

            total_score += weight * related_score

    if max_score == 0:

        return 0.0, matched_terms

    score = total_score / max_score

    return min(score, 1.0), matched_terms


# =========================================================
# Technical Domain Boost
# =========================================================

def technical_domain_boost(
    title,
    text,
    detected_skills
):
    """
    Detect whether an occupation belongs strongly
    to a technical/AI/data domain.

    This is intentionally generic and does not
    hard-code specific career titles.
    """

    combined = normalize(
        title + " " + text
    )

    technical_terms = [

        "computer",

        "software",

        "programming",

        "developer",

        "engineering",

        "engineer",

        "data",

        "technology",

        "artificial intelligence",

        "machine learning",

        "deep learning",

        "robotics",

        "systems",

        "algorithm",

        "analytics",

        "scientific",

        "research",

    ]

    matches = 0

    for term in technical_terms:

        pattern = r"\b" + re.escape(term) + r"\b"

        if re.search(pattern, combined):

            matches += 1

    # Base technical boost

    if matches >= 7:
        boost = 0.12

    elif matches >= 5:
        boost = 0.10

    elif matches >= 3:
        boost = 0.06

    elif matches >= 1:
        boost = 0.03

    else:
        boost = 0.0

    # -----------------------------------------------------
    # Additional AI-domain boost
    # -----------------------------------------------------

    ai_skills = {
        "machine_learning",
        "deep_learning",
        "artificial_intelligence",
        "computer_vision",
        "nlp",
    }

    detected_ai_skills = ai_skills.intersection(
        set(detected_skills)
    )

    if detected_ai_skills:

        ai_terms = [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "neural network",
            "neural networks",
            "computer vision",
            "natural language processing",
            "natural language",
            "predictive modeling",
            "pattern recognition",
            "data mining",
            "data science",
        ]

        ai_matches = 0

        for term in ai_terms:

            pattern = r"\b" + re.escape(term) + r"\b"

            if re.search(pattern, combined):

                ai_matches += 1

        # Extra boost for AI-oriented occupations

        if ai_matches >= 4:

            boost += 0.10

        elif ai_matches >= 2:

            boost += 0.06

        elif ai_matches >= 1:

            boost += 0.03

    return min(boost, 0.22)


# =========================================================
# AI Relevance Score
# =========================================================

def calculate_ai_relevance(
    title,
    text,
    detected_skills
):
    """
    Measures how strongly the occupation itself is
    related to AI/ML/Data Science.

    This helps prevent generic technical careers
    from outranking genuinely AI-focused careers.
    """

    combined = normalize(
        title + " " + text
    )

    if not detected_skills:

        return 0.0

    ai_terms = {

        "artificial intelligence": 1.0,

        "machine learning": 1.0,

        "deep learning": 1.0,

        "neural network": 0.9,

        "neural networks": 0.9,

        "computer vision": 0.9,

        "natural language processing": 0.9,

        "predictive modeling": 0.8,

        "data science": 0.8,

        "data scientist": 1.0,

        "data mining": 0.7,

        "pattern recognition": 0.7,

        "algorithm": 0.4,

        "analytics": 0.4,

        "artificial intelligence applications": 1.0,
    }

    score = 0.0

    max_possible = 0.0

    for term, weight in ai_terms.items():

        # Only count AI concepts relevant to the
        # skills the user actually mentioned.

        max_possible += weight

        pattern = r"\b" + re.escape(term) + r"\b"

        if re.search(pattern, combined):

            score += weight

    if max_possible == 0:

        return 0.0

    return min(
        score / max_possible,
        1.0
    )


# =========================================================
# Career Ranking
# =========================================================

def calculate_final_score(
    semantic_score,
    technical_score,
    domain_boost,
    ai_relevance,
    detected_skills
):
    """
    Combine all ranking signals.

    Semantic similarity remains important,
    but technical compatibility and AI relevance
    receive stronger influence for technical queries.
    """

    if not detected_skills:

        return semantic_score

    # Main weights

    semantic_weight = 0.40

    technical_weight = 0.40

    ai_weight = 0.15

    domain_weight = 0.05

    final_score = (

        semantic_score * semantic_weight

        + technical_score * technical_weight

        + ai_relevance * ai_weight

        + domain_boost * domain_weight
    )

    return final_score


# =========================================================
# Main Search
# =========================================================

def main():

    print("Loading vector database...")

    # -----------------------------------------------------
    # Load FAISS
    # -----------------------------------------------------

    index = faiss.read_index(
        INDEX_FILE
    )

    # -----------------------------------------------------
    # Load metadata
    # -----------------------------------------------------

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        metadata = json.load(f)

    print(
        f"Loaded {index.ntotal} vectors."
    )

    # -----------------------------------------------------
    # Load embedding model
    # -----------------------------------------------------

    model = SentenceTransformer(
        MODEL_NAME
    )

    # -----------------------------------------------------
    # User query
    # -----------------------------------------------------

    query = input(
        "\nEnter your career query: "
    )

    # -----------------------------------------------------
    # Detect technical skills
    # -----------------------------------------------------

    detected_skills = detect_skills(
        query
    )

    if detected_skills:

        print(
            "\nDetected technical terms:"
        )

        print(
            ", ".join(
                detected_skills
            )
        )

    else:

        print(
            "\nNo specific technical skills detected."
        )

    # -----------------------------------------------------
    # Create query embedding
    # -----------------------------------------------------

    query_embedding = model.encode(

        [query],

        convert_to_numpy=True,

        normalize_embeddings=True,
    )

    # -----------------------------------------------------
    # Search FAISS
    # -----------------------------------------------------

    # Retrieve more candidates than we finally display.
    #
    # This gives our ranking system enough candidates
    # to choose from.

    search_k = min(
        50,
        index.ntotal
    )

    scores, indices = index.search(

        query_embedding.astype(
            "float32"
        ),

        search_k,
    )

    # -----------------------------------------------------
    # Rank candidates
    # -----------------------------------------------------

    ranked_results = []

    for semantic_score, index_id in zip(
        scores[0],
        indices[0]
    ):

        if index_id < 0:

            continue

        result = metadata[index_id]

        title = result.get(
            "title",
            ""
        )

        text = result.get(
            "text",
            ""
        )

        # Technical compatibility

        technical_score, matched_terms = (
            calculate_technical_match(
                text,
                detected_skills
            )
        )

        # Technical domain

        domain_boost = technical_domain_boost(

            title,

            text,

            detected_skills
        )

        # AI relevance

        ai_relevance = calculate_ai_relevance(

            title,

            text,

            detected_skills
        )

        # Final ranking

        final_score = calculate_final_score(

            semantic_score,

            technical_score,

            domain_boost,

            ai_relevance,

            detected_skills
        )

        ranked_results.append({

            "result": result,

            "semantic_score": float(
                semantic_score
            ),

            "technical_score": float(
                technical_score
            ),

            "domain_boost": float(
                domain_boost
            ),

            "ai_relevance": float(
                ai_relevance
            ),

            "final_score": float(
                final_score
            ),

            "matched_terms": matched_terms,
        })

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    ranked_results.sort(

        key=lambda x: x[
            "final_score"
        ],

        reverse=True
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

    for rank, item in enumerate(

        ranked_results[
            :TOP_K
        ],

        start=1
    ):

        result = item[
            "result"
        ]

        print(
            f"\n#{rank}"
        )

        print(
            f"Career: {result['title']}"
        )

        print(
            f"O*NET Code: "
            f"{result['occupation_code']}"
        )

        print(
            f"Job Zone: "
            f"{result['job_zone']}"
        )

        print(
            f"Semantic Score: "
            f"{item['semantic_score']:.4f}"
        )

        print(
            f"Technical Match: "
            f"{item['technical_score']:.4f}"
        )

        print(
            f"AI Relevance: "
            f"{item['ai_relevance']:.4f}"
        )

        print(
            f"Domain Boost: "
            f"{item['domain_boost']:.4f}"
        )

        print(
            f"Final Score: "
            f"{item['final_score']:.4f}"
        )

        if item["matched_terms"]:

            # Remove duplicates while keeping order

            unique_terms = list(
                dict.fromkeys(
                    item["matched_terms"]
                )
            )

            print(
                "Matched Terms: "
                + ", ".join(
                    unique_terms[:12]
                )
            )

        print(
            "-" * 70
        )

        # Show a useful amount of context

        text = result.get(
            "text",
            ""
        )

        print(
            text[:900]
            + "..."
        )

        print(
            "-" * 70
        )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    main()