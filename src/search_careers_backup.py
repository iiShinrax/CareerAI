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
RETRIEVAL_K = 50


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
# AI / Technical Occupation Terms
# =========================================================

AI_TERMS = {
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
    
}


# =========================================================
# Query Skill Detection
# =========================================================

def detect_skills(query):
    """
    Detect technical skill families mentioned
    in the user's query.
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
# Generic Keyword Matching
# =========================================================

def contains_term(text, term):

    pattern = r"\b" + re.escape(
        term.lower()
    ) + r"\b"

    return bool(
        re.search(pattern, text)
    )


# =========================================================
# Technical Matching
# =========================================================

def calculate_technical_match(
    text,
    detected_skills
):
    """
    Measures how strongly the occupation matches
    the user's detected technical skill families.

    Exact matches are strongest.
    Related concepts provide partial credit.
    """

    text = normalize(text)

    if not detected_skills:
        return 0.0, []

    skill_weights = {
        "python": 1.0,
        "machine_learning": 1.5,
        "deep_learning": 1.6,
        "artificial_intelligence": 1.5,
        "data_science": 1.4,
        "computer_vision": 1.5,
        "nlp": 1.5,
    }

    total_possible = 0.0
    total_score = 0.0

    matched_terms = []

    for skill in detected_skills:

        family = SKILL_FAMILIES.get(skill)

        if not family:
            continue

        weight = skill_weights.get(skill, 1.0)

        total_possible += weight

        exact_match = any(
            contains_term(text, keyword)
            for keyword in family["keywords"]
        )

        related_matches = [
            keyword
            for keyword in family["related"]
            if contains_term(text, keyword)
        ]

        if exact_match:

            total_score += weight

            for keyword in family["keywords"]:
                if contains_term(text, keyword):
                    if keyword not in matched_terms:
                        matched_terms.append(keyword)

        elif related_matches:

            # Related concepts receive partial credit
            related_score = min(
                0.25 * len(related_matches),
                0.50
            )

            total_score += weight * related_score

            for keyword in related_matches:
                if keyword not in matched_terms:
                    matched_terms.append(keyword)

    if total_possible == 0:
        return 0.0, matched_terms

    score = total_score / total_possible

    return min(score, 1.0), matched_terms
    """
    Calculate compatibility between the user's
    technical skills and the occupation.

    Exact skill matches receive the strongest score.
    Related concepts receive a smaller score.
    """

    text = normalize(text)

    if not detected_skills:

        return 0.0, []

    skill_weights = {

        "python": 0.8,

        "machine_learning": 1.6,

        "deep_learning": 1.8,

        "artificial_intelligence": 1.7,

        "data_science": 1.4,

        "computer_vision": 1.6,

        "nlp": 1.6,
    }

    total_score = 0.0
    max_score = 0.0

    matched_terms = []

    for skill in detected_skills:

        data = SKILL_FAMILIES[skill]

        weight = skill_weights.get(
            skill,
            1.0
        )

        max_score += weight

        exact_match = False
        related_matches = 0

        # -------------------------------------------------
        # Exact match
        # -------------------------------------------------

        for keyword in data["keywords"]:

            if contains_term(
                text,
                keyword
            ):

                exact_match = True

                if keyword not in matched_terms:

                    matched_terms.append(
                        keyword
                    )

                break

        # -------------------------------------------------
        # Related matches
        # -------------------------------------------------

        for keyword in data["related"]:

            if contains_term(
                text,
                keyword
            ):

                related_matches += 1

                if keyword not in matched_terms:

                    matched_terms.append(
                        keyword
                    )

        # -------------------------------------------------
        # Score
        # -------------------------------------------------

        if exact_match:

            total_score += weight

        elif related_matches > 0:

            related_score = min(
                0.40 * related_matches,
                0.70
            )

            total_score += (
                weight * related_score
            )

    if max_score == 0:

        return 0.0, matched_terms

    score = (
        total_score /
        max_score
    )

    return min(
        score,
        1.0
    ), matched_terms


# =========================================================
# AI Relevance
# =========================================================

def calculate_ai_relevance(
    title,
    text,
    detected_skills
):
    """
    Measures how directly the occupation is related
    to the user's AI/ML skill profile.
    """

    combined = normalize(
        title + " " + text
    )

    if not detected_skills:
        return 0.0

    ai_skill_terms = {
        "machine_learning": [
            "machine learning",
            "predictive modeling",
            "statistical learning",
        ],

        "deep_learning": [
            "deep learning",
            "neural network",
            "neural networks",
        ],

        "artificial_intelligence": [
            "artificial intelligence",
            "ai systems",
            "ai applications",
            "expert systems",
        ],

        "computer_vision": [
            "computer vision",
            "image recognition",
            "image processing",
            "object detection",
        ],

        "nlp": [
            "natural language processing",
            "nlp",
            "language model",
        ],

        "data_science": [
            "data science",
            "data scientist",
            "data mining",
            "data modeling",
            "analytics",
        ],
    }

    ai_skills = {
        "machine_learning",
        "deep_learning",
        "artificial_intelligence",
        "computer_vision",
        "nlp",
        "data_science",
    }

    relevant_skills = (
        ai_skills.intersection(set(detected_skills))
    )

    if not relevant_skills:
        return 0.0

    matched = 0

    for skill in relevant_skills:

        terms = ai_skill_terms.get(
            skill,
            []
        )

        if any(
            contains_term(combined, term)
            for term in terms
        ):
            matched += 1

    return matched / len(relevant_skills)
    """
    Measures how strongly the occupation is
    related to AI / ML / Data Science.

    This is especially important when the user
    explicitly mentions AI-related skills.
    """

    combined = normalize(
        title + " " + text
    )

    if not detected_skills:

        return 0.0

    ai_skills = {
        "machine_learning",
        "deep_learning",
        "artificial_intelligence",
        "computer_vision",
        "nlp",
        "data_science",
    }

    if not ai_skills.intersection(
        set(detected_skills)
    ):

        return 0.0

    score = 0.0
    max_possible = 0.0

    for term, weight in AI_TERMS.items():

        max_possible += weight

        if contains_term(
            combined,
            term
        ):

            score += weight

    if max_possible == 0:

        return 0.0

    return min(
        score / max_possible,
        1.0
    )


# =========================================================
# Technical Domain Score
# =========================================================

def calculate_domain_score(
    title,
    text
):
    """
    Measures whether the occupation belongs to a
    genuinely technical/computing domain.

    Generic words such as 'scientific' or 'research'
    are not sufficient by themselves.
    """

    combined = normalize(
        title + " " + text
    )

    strong_terms = [
        "software",
        "programming",
        "developer",
        "computer",
        "data science",
        "data scientist",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "artificial intelligence engineer",
        "machine learning engineer",
        "computer vision",
        "natural language processing",
        "robotics",
        "algorithm",
        "database",
        "cloud computing",
        "software engineering",
    ]

    matches = sum(
        1
        for term in strong_terms
        if contains_term(combined, term)
    )

    return min(
        matches / 5.0,
        1.0
    )
    """
    Determines how technical the occupation is.

    Unlike the old boost, this returns a normalized
    score that can be used directly in ranking.
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

        if contains_term(
            combined,
            term
        ):

            matches += 1

    return min(
        matches / 7.0,
        1.0
    )


# =========================================================
# Title Relevance
# =========================================================

def calculate_title_relevance(
    title,
    detected_skills
):
    """
    Gives additional importance to the occupation title.

    This prevents generic technical occupations from
    beating careers that directly represent the user's
    desired specialization.
    """

    title = normalize(title)

    if not detected_skills:

        return 0.0

    score = 0.0

    # Strong AI/Data titles

    title_groups = {

        "ai": [
            "artificial intelligence",
            "ai",
            "machine learning",
            "deep learning",
        ],

        "data": [
            "data scientist",
            "data science",
            "data analyst",
            "statistician",
        ],

        "software": [
            "software developer",
            "software engineer",
            "computer programmer",
            "programmer",
        ],

        "computer_vision": [
            "computer vision",
        ],

        "robotics": [
            "robotics",
            "robotic",
        ],
    }

    # -----------------------------------------------------
    # AI-related user
    # -----------------------------------------------------

    ai_user = bool(
        {
            "machine_learning",
            "deep_learning",
            "artificial_intelligence",
            "computer_vision",
            "nlp",
        }.intersection(
            set(detected_skills)
        )
    )

    if ai_user:

        for term in title_groups["ai"]:

            if contains_term(
                title,
                term
            ):

                score = max(
                    score,
                    1.0
                )

        for term in title_groups["data"]:

            if contains_term(
                title,
                term
            ):

                score = max(
                    score,
                    0.85
                )

        for term in title_groups["computer_vision"]:

            if contains_term(
                title,
                term
            ):

                score = max(
                    score,
                    0.90
                )

        for term in title_groups["robotics"]:

            if contains_term(
                title,
                term
            ):

                score = max(
                    score,
                    0.55
                )

        for term in title_groups["software"]:

            if contains_term(
                title,
                term
            ):

                score = max(
                    score,
                    0.60
                )

    # -----------------------------------------------------
    # Python / general programming user
    # -----------------------------------------------------

    if "python" in detected_skills:

        for term in title_groups["software"]:

            if contains_term(
                title,
                term
            ):

                score = max(
                    score,
                    0.75
                )

    return min(
        score,
        1.0
    )


# =========================================================
# User Intent Detection
# =========================================================

def detect_ai_intent(query):

    text = normalize(query)

    intent_terms = [

        "build ai",
        "building ai",
        "ai applications",
        "ai application",
        "artificial intelligence applications",
        "artificial intelligence application",
        "build machine learning",
        "machine learning applications",
        "ml applications",
        "deep learning applications",
        "build models",
        "build ai systems",
        "ai systems",
    ]

    for term in intent_terms:

        if contains_term(
            text,
            term
        ):

            return True

    return False


# =========================================================
# Final Ranking Score
# =========================================================

def calculate_final_score(
    semantic_score,
    technical_score,
    ai_relevance,
    domain_score,
    title_relevance,
    ai_intent,
    detected_skills
):
    """
    Combines semantic retrieval with technical,
    specialization, title, and domain signals.
    """

    if not detected_skills:

        return semantic_score

    # -----------------------------------------------------
    # Standard technical query
    # -----------------------------------------------------

    semantic_weight = 0.30
    technical_weight = 0.35
    ai_weight = 0.15
    domain_weight = 0.05
    title_weight = 0.15

    # -----------------------------------------------------
    # AI-focused query
    # -----------------------------------------------------

    if ai_intent:

        semantic_weight = 0.20
        technical_weight = 0.30
        ai_weight = 0.30
        domain_weight = 0.05
        title_weight = 0.15

    final_score = (

        semantic_score *
        semantic_weight

        + technical_score *
        technical_weight

        + ai_relevance *
        ai_weight

        + domain_score *
        domain_weight

        + title_relevance *
        title_weight
    )

    return min(
        final_score,
        1.0
    )


# =========================================================
# Build Unique Occupation Candidates
# =========================================================

def collect_unique_candidates(
    metadata,
    scores,
    indices
):
    """
    FAISS may return multiple chunks belonging to
    the same occupation.

    This function merges them so every occupation
    appears only once.

    The highest semantic similarity is retained.
    """

    unique = {}

    for semantic_score, index_id in zip(
        scores[0],
        indices[0]
    ):

        if index_id < 0:

            continue

        result = metadata[index_id]

        code = (
            result.get(
                "onet_code"
            )
            or result.get(
                "O*NET-SOC Code"
            )
            or result.get(
                "soc_code"
            )
            or result.get(
                "code"
            )
        )

        title = result.get(
            "title",
            ""
        )

        # -------------------------------------------------
        # Fallback key
        # -------------------------------------------------

        if not code:

            code = title.lower().strip()

        # -------------------------------------------------
        # Keep highest semantic result
        # -------------------------------------------------

        if (
            code not in unique
            or semantic_score >
            unique[code]["semantic_score"]
        ):

            unique[code] = {

                "result": result,

                "semantic_score":
                    float(
                        semantic_score
                    ),
            }

    return list(
        unique.values()
    )


# =========================================================
# Generate Explanation
# =========================================================

def generate_explanation(
    title,
    matched_terms,
    technical_score,
    ai_relevance,
    title_relevance
):
    """
    Creates a human-readable explanation
    for the recommendation.
    """

    reasons = []

    # Technical matches

    if matched_terms:

        useful_terms = matched_terms[:4]

        reasons.append(
            "matches " +
            ", ".join(
                useful_terms
            )
        )

    # AI relevance

    if ai_relevance >= 0.20:

        reasons.append(
            "strongly related to AI/data work"
        )

    elif ai_relevance >= 0.08:

        reasons.append(
            "has some AI/data relevance"
        )

    # Title relevance

    if title_relevance >= 0.80:

        reasons.append(
            "the career title closely matches "
            "your specialization"
        )

    elif title_relevance >= 0.50:

        reasons.append(
            "the career title is related "
            "to your technical direction"
        )

    # Technical alignment

    if technical_score >= 0.65:

        reasons.append(
            "strong technical skill alignment"
        )

    elif technical_score >= 0.30:

        reasons.append(
            "moderate technical skill alignment"
        )

    if not reasons:

        return (
            f"{title} was retrieved as a potentially "
            "relevant career based on semantic similarity."
        )

    return (
        f"{title} is recommended because it "
        + "; ".join(reasons)
        + "."
    )


# =========================================================
# Main Search
# =========================================================

def main():

    print(
        "Loading vector database..."
    )

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

    print(
        "Loading embedding model..."
    )

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
    # Detect skills
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
    # Detect intent
    # -----------------------------------------------------

    ai_intent = detect_ai_intent(
        query
    )

    if ai_intent:

        print(
            "Detected AI application-building intent."
        )

    # -----------------------------------------------------
    # Query embedding
    # -----------------------------------------------------

    query_embedding = model.encode(

        [query],

        convert_to_numpy=True,

        normalize_embeddings=True,
    )

    # -----------------------------------------------------
    # FAISS retrieval
    # -----------------------------------------------------

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
    # Deduplicate occupations
    # -----------------------------------------------------

    candidates = collect_unique_candidates(
        metadata,
        scores,
        indices
    )

    # -----------------------------------------------------
    # Calculate ranking features
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
        # Technical match
        # -------------------------------------------------

        technical_score, matched_terms = (
            calculate_technical_match(
                text,
                detected_skills
            )
        )

        # -------------------------------------------------
        # AI relevance
        # -------------------------------------------------

        ai_relevance = (
            calculate_ai_relevance(
                title,
                text,
                detected_skills
            )
        )

        # -------------------------------------------------
        # Domain score
        # -------------------------------------------------

        domain_score = (
            calculate_domain_score(
                title,
                text
            )
        )

        # -------------------------------------------------
        # Title relevance
        # -------------------------------------------------

        title_relevance = (
            calculate_title_relevance(
                title,
                detected_skills
            )
        )

        # -------------------------------------------------
        # Final score
        # -------------------------------------------------

        final_score = (
            calculate_final_score(
                semantic_score,
                technical_score,
                ai_relevance,
                domain_score,
                title_relevance,
                ai_intent,
                detected_skills
            )
        )

        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        explanation = (
            generate_explanation(
                title,
                matched_terms,
                technical_score,
                ai_relevance,
                title_relevance
            )
        )

        ranked_results.append({

            "result": result,

            "semantic_score":
                semantic_score,

            "technical_score":
                technical_score,

            "ai_relevance":
                ai_relevance,

            "domain_score":
                domain_score,

            "title_relevance":
                title_relevance,

            "final_score":
                final_score,

            "matched_terms":
                matched_terms,

            "explanation":
                explanation,
        })

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    ranked_results.sort(

        key=lambda x:
            x["final_score"],

        reverse=True
    )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print(
        "\n" +
        "=" * 70
    )

    print(
        "TOP CAREER MATCHES"
    )

    print(
        "=" * 70
    )

    shown = 0

    seen_codes = set()

    for item in ranked_results:

        if shown >= TOP_K:

            break

        result = item[
            "result"
        ]

        title = result.get(
            "title",
            "Unknown Career"
        )

        code = (
            result.get(
                "onet_code"
            )
            or result.get(
                "O*NET-SOC Code"
            )
            or result.get(
                "soc_code"
            )
            or result.get(
                "code"
            )
            or title
        )

        # Extra duplicate protection

        if code in seen_codes:

            continue

        seen_codes.add(code)

        shown += 1

        print(
            f"\n#{shown}"
        )

        print(
            f"Career: {title}"
        )

        print(
            f"O*NET Code: {code}"
        )

        if "job_zone" in result:

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
            f"Domain Score: "
            f"{item['domain_score']:.4f}"
        )

        print(
            f"Title Relevance: "
            f"{item['title_relevance']:.4f}"
        )

        print(
            f"Final Score: "
            f"{item['final_score']:.4f}"
        )

        if item["matched_terms"]:

            print(
                "Matched Terms: " +
                ", ".join(
                    item["matched_terms"][:6]
                )
            )

        print(
            "Why: " +
            item["explanation"]
        )

        print(
            "-" * 70
        )

        # -------------------------------------------------
        # Occupation information
        # -------------------------------------------------

        occupation_text = result.get(
            "text",
            ""
        )

        if occupation_text:

            print(
                occupation_text[:1000]
                + (
                    "..."
                    if len(
                        occupation_text
                    ) > 1000
                    else ""
                )
            )

            print(
                "-" * 70
            )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    main()