
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
    # -----------------------------------------------------
    # Core AI / ML
    # -----------------------------------------------------

    "artificial intelligence": 1.0,
    "machine learning": 1.0,
    "deep learning": 1.0,

    "neural network": 0.9,
    "neural networks": 0.9,

    # -----------------------------------------------------
    # AI Specializations
    # -----------------------------------------------------

    "computer vision": 0.9,
    "natural language processing": 0.9,
    "predictive modeling": 0.8,
    "pattern recognition": 0.7,

    # -----------------------------------------------------
    # Data / AI ecosystem
    # -----------------------------------------------------

    "data science": 0.8,
    "data scientist": 1.0,
    "data mining": 0.7,

    # -----------------------------------------------------
    # Generic technical concepts
    #
    # Keep these relatively weak because they can occur
    # in many occupations.
    # -----------------------------------------------------

    "algorithm": 0.2,
    "analytics": 0.2,

    # -----------------------------------------------------
    # Modern AI application development
    # -----------------------------------------------------

    "large language model": 1.0,
    "large language models": 1.0,
    "llm": 1.0,
    "llms": 1.0,

    "generative ai": 1.0,
    "generative artificial intelligence": 1.0,

    "transformer": 0.8,
    "transformers": 0.8,

    "natural language": 0.6,

    "reinforcement learning": 0.9,

    "computer vision systems": 0.9,

    # -----------------------------------------------------
    # AI application / engineering concepts
    # -----------------------------------------------------

    "ai application": 1.0,
    "ai applications": 1.0,
    "ai system": 0.9,
    "ai systems": 0.9,

    "ml application": 0.9,
    "ml applications": 0.9,

    "model deployment": 0.8,
    "machine learning model": 0.9,
    "machine learning models": 0.9,
}


# =========================================================
# Query Skill Detection
# =========================================================
def detect_skills(query):

    text = query.lower()

    detected = []

    for skill, data in SKILL_FAMILIES.items():

        for keyword in data["keywords"]:

            pattern = r"\b" + re.escape(
                keyword.lower()
            ) + r"\b"

            if re.search(pattern, text):

                detected.append(skill)

                break

    # -------------------------------------------------
    # Standalone AI
    # -------------------------------------------------

    if re.search(r"\bai\b", text):

        if "artificial_intelligence" not in detected:

            detected.append(
                "artificial_intelligence"
            )

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
    Calculate compatibility between the user's
    technical skills and the occupation.

    Exact skill matches receive the strongest score.
    Related technical concepts receive partial credit.

    Career-oriented technical terms such as software
    development and programming can support AI application
    building without being treated as direct AI skills.
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
        # Exact skill match
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
        # Related skill match
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
        # Score direct skill compatibility
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

    # =====================================================
    # Career-oriented technical compatibility
    # =====================================================

    technical_career_terms = {

        "software development": 0.30,
        "software developer": 0.30,
        "software developers": 0.30,

        "software engineering": 0.30,
        "software engineer": 0.30,
        "software engineers": 0.30,

        "programming": 0.25,
        "computer programming": 0.25,

        "application development": 0.30,
        "application developer": 0.30,

        "application software": 0.25,

        "web development": 0.15,

        "computer software": 0.20,

        "systems development": 0.20,

        "systems engineering": 0.20,

        "data analysis": 0.20,

        "data analytics": 0.20,
    }

    career_bonus = 0.0

    career_matches = 0

    for term, bonus in technical_career_terms.items():

        if contains_term(
            text,
            term
        ):

            career_bonus += bonus

            career_matches += 1

            if term not in matched_terms:

                matched_terms.append(
                    term
                )

    # -----------------------------------------------------
    # Cap the career bonus so generic technical careers
    # cannot overwhelm genuine skill matches.
    # -----------------------------------------------------

    career_bonus = min(
        career_bonus,
        0.40
    )

    # -----------------------------------------------------
    # AI application-building intent
    # -----------------------------------------------------

    ai_application_terms = [

        "software development",
        "software engineering",
        "application development",
        "application software",
        "programming",
        "computer programming",
        "software developer",
        "software developers",
        "software engineer",
        "software engineers",
    ]

    ai_application_match = False

    for term in ai_application_terms:

        if contains_term(
            text,
            term
        ):

            ai_application_match = True

            break

    if ai_application_match:

        ai_skills = {
            "machine_learning",
            "deep_learning",
            "artificial_intelligence",
            "computer_vision",
            "nlp",
        }

        if ai_skills.intersection(
            set(detected_skills)
        ):

            career_bonus += 0.20

            career_bonus = min(
                career_bonus,
                0.50
            )

    # =====================================================
    # Final score
    # =====================================================

    if max_score == 0:

        return 0.0, matched_terms

    base_score = (
        total_score /
        max_score
    )

    # Add career compatibility without allowing it
    # to dominate direct skill matching.

    score = min(
        base_score + career_bonus,
        1.0
    )

    return score, matched_terms

# =========================================================
# AI Relevance
# =========================================================

def calculate_ai_relevance(
    title,
    text,
    detected_skills
):
    """
    Measures how strongly the occupation matches
    the AI-related skills explicitly detected in
    the user's query.

    The score is based on user-relevant AI skills
    rather than the entire global AI vocabulary.
    """

    combined = normalize(
        title + " " + text
    )

    if not detected_skills:
        return 0.0

    ai_skill_weights = {

        "machine_learning": 1.0,

        "deep_learning": 1.0,

        "artificial_intelligence": 1.0,

        "computer_vision": 0.9,

        "nlp": 0.9,

        "data_science": 0.8,
    }

    relevant_skills = [
        skill
        for skill in detected_skills
        if skill in ai_skill_weights
    ]

    if not relevant_skills:
        return 0.0

    total_score = 0.0
    max_score = 0.0

    for skill in relevant_skills:

        weight = ai_skill_weights[skill]

        max_score += weight

        data = SKILL_FAMILIES[skill]

        exact_match = False

        related_matches = 0

        # -------------------------------------------------
        # Exact AI skill match
        # -------------------------------------------------

        for keyword in data["keywords"]:

            if contains_term(
                combined,
                keyword
            ):

                exact_match = True
                break

        # -------------------------------------------------
        # Related AI concepts
        # -------------------------------------------------

        for keyword in data["related"]:

            if contains_term(
                combined,
                keyword
            ):

                related_matches += 1

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
        return 0.0

    return min(
        total_score / max_score,
        1.0
    )

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
# AI Application Development Score
# =========================================================

def calculate_ai_application_score(
    title,
    text
):
    """
    Measures how strongly an occupation is related to
    building AI / ML applications and systems.

    The score prioritizes:
    1. AI/ML-specific development evidence
    2. AI/ML concepts
    3. AI-focused career titles
    4. Generic software development evidence
    """

    combined = normalize(
        title + " " + text
    )

    normalized_title = normalize(
        title
    )

    # -----------------------------------------------------
    # Strong AI / ML development evidence
    # -----------------------------------------------------

    ai_development_terms = [

        "ai applications",
        "ai application",
        "artificial intelligence applications",
        "artificial intelligence application",

        "machine learning applications",
        "machine learning application",

        "ai systems",
        "ai system",
        "artificial intelligence systems",
        "artificial intelligence system",

        "machine learning systems",
        "machine learning system",

        "develop ai",
        "develop artificial intelligence",
        "develop machine learning",

        "implement ai",
        "implement artificial intelligence",
        "implement machine learning",

        "build ai",
        "build artificial intelligence",
        "build machine learning",

        "ai software",
        "artificial intelligence software",

        "machine learning software",

        "ai models",
        "machine learning models",
        "deep learning models",
    ]

    # -----------------------------------------------------
    # General AI / ML evidence
    # -----------------------------------------------------

    ai_terms = [

        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",
        "neural networks",
        "computer vision",
        "natural language processing",
        "predictive modeling",
        "data science",
        "deep neural",
        "machine intelligence",
    ]

    # -----------------------------------------------------
    # Generic software development evidence
    # -----------------------------------------------------

    development_terms = [

        "software development",
        "software engineering",
        "application development",
        "programming",
        "programming languages",
        "develop software",
        "develop applications",
        "software developer",
        "software developers",
        "software engineer",
        "software engineers",
    ]

    # -----------------------------------------------------
    # AI-focused career titles
    # -----------------------------------------------------

    ai_title_terms = [

        "data scientist",
        "data scientists",

        "machine learning",
        "machine learning engineer",
        "machine learning engineers",

        "artificial intelligence",
        "ai engineer",
        "ai engineers",
        "ai developer",
        "ai developers",

        "computer vision",
        "computer vision engineer",
        "computer vision engineers",

        "natural language processing",
        "nlp engineer",
        "nlp engineers",

        "robotics engineer",
        "robotics engineers",
    ]

    # -----------------------------------------------------
    # Count AI development evidence
    # -----------------------------------------------------

    ai_development_matches = 0

    for term in ai_development_terms:

        if contains_term(
            combined,
            term
        ):

            ai_development_matches += 1

    # -----------------------------------------------------
    # Count general AI evidence
    # -----------------------------------------------------

    ai_matches = 0

    for term in ai_terms:

        if contains_term(
            combined,
            term
        ):

            ai_matches += 1

    # -----------------------------------------------------
    # Count generic development evidence
    # -----------------------------------------------------

    development_matches = 0

    for term in development_terms:

        if contains_term(
            combined,
            term
        ):

            development_matches += 1

    # -----------------------------------------------------
    # Count AI-focused title evidence
    # -----------------------------------------------------

    title_matches = 0

    for term in ai_title_terms:

        if contains_term(
            normalized_title,
            term
        ):

            title_matches += 1

    # -----------------------------------------------------
    # No AI evidence
    # -----------------------------------------------------

    if (
        ai_development_matches == 0
        and ai_matches == 0
        and title_matches == 0
    ):

        return 0.0

    # -----------------------------------------------------
    # Normalize individual signals
    # -----------------------------------------------------

    ai_development_score = min(
        ai_development_matches / 3.0,
        1.0
    )

    ai_score = min(
        ai_matches / 4.0,
        1.0
    )

    development_score = min(
        development_matches / 3.0,
        1.0
    )

    title_score = min(
        title_matches / 2.0,
        1.0
    )

    # -----------------------------------------------------
    # Final score
    # -----------------------------------------------------

    score = (

        0.40 * ai_development_score

        + 0.30 * ai_score

        + 0.20 * title_score

        + 0.10 * development_score

    )

    return min(
        score,
        1.0
    )

    # -----------------------------------------------------
    # Development evidence score
    # -----------------------------------------------------

    development_score = min(
        development_matches / 3.0,
        1.0
    )

    # -----------------------------------------------------
    # Title specialization score
    # -----------------------------------------------------

    title_score = min(
        title_matches / 2.0,
        1.0
    )

    # -----------------------------------------------------
    # Final AI application score
    # -----------------------------------------------------

    score = (
        0.50 * ai_score
        + 0.30 * development_score
        + 0.20 * title_score
    )

    return min(
        score,
        1.0
    )

    ai_score = min(
        ai_matches / 4.0,
        1.0
    )

    development_score = min(
        development_matches / 3.0,
        1.0
    )

    return (
        0.60 * ai_score
        + 0.40 * development_score
    )


# =========================================================
# Technical Domain Score
# =========================================================

def calculate_domain_score(
    title,
    text
):
    """
    Determines how strongly an occupation belongs
    to a technical/computing career domain.

    Title evidence is given much more importance than
    incidental technology names appearing in the
    occupation description.
    """

    title = normalize(title)
    text = normalize(text)

    # -----------------------------------------------------
    # Strong technical career titles
    # -----------------------------------------------------

    strong_title_terms = [
        "software developer",
        "software developers",
        "software engineer",
        "software engineers",
        "computer programmer",
        "computer programmers",
        "programmer",
        "programmers",
        "application developer",
        "application developers",
        "application engineer",
        "application engineers",
        "artificial intelligence engineer",
        "artificial intelligence developer",
        "ai engineer",
        "ai developer",
        "machine learning engineer",
        "machine learning developer",
        "ml engineer",
        "ml developer",
        "data scientist",
        "data scientists",
        "computer scientist",
        "computer scientists",
        "computer systems analyst",
        "computer systems analysts",
        "systems engineer",
        "systems engineers",
        "computer engineer",
        "computer engineers",
    ]

    for term in strong_title_terms:

        if contains_term(
            title,
            term
        ):

            return 1.0

    # -----------------------------------------------------
    # Other strongly technical titles
    # -----------------------------------------------------

    technical_title_terms = [
        "software",
        "programming",
        "developer",
        "engineering",
        "engineer",
        "computer",
        "computing",
        "technology",
        "systems",
        "robotics",
        "data",
        "information technology",
        "cybersecurity",
        "network",
        "database",
    ]

    title_matches = 0

    for term in technical_title_terms:

        if contains_term(
            title,
            term
        ):

            title_matches += 1

    # -----------------------------------------------------
    # Technical evidence in occupation text
    # -----------------------------------------------------

    technical_text_terms = [
        "software development",
        "software engineering",
        "programming",
        "computer programming",
        "application development",
        "data science",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "computer vision",
        "natural language processing",
        "database",
        "software development tools",
        "programming languages",
    ]

    text_matches = 0

    for term in technical_text_terms:

        if contains_term(
            text,
            term
        ):

            text_matches += 1

    # -----------------------------------------------------
    # Title-driven score
    # -----------------------------------------------------

    if title_matches > 0:

        title_score = min(
            title_matches / 2.0,
            1.0
        )

    else:

        title_score = 0.0

    # -----------------------------------------------------
    # Text-driven score
    #
    # Text evidence is deliberately capped because
    # O*NET software lists can contain incidental tools
    # unrelated to the actual occupation.
    # -----------------------------------------------------

    text_score = min(
        text_matches / 4.0,
        1.0
    )

    # -----------------------------------------------------
    # Combine title + occupation evidence
    #
    # Title is much more important than incidental text.
    # -----------------------------------------------------

    score = (
        title_score * 0.75
        +
        text_score * 0.25
    )

    return min(
        score,
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
    Measures how closely the occupation title matches
    the user's technical specialization.

    AI/ML careers receive the strongest relevance,
    followed by software and programming careers.
    """

    title = normalize(title)

    if not detected_skills:
        return 0.0

    skills = set(detected_skills)

    ai_user = bool(
        {
            "machine_learning",
            "deep_learning",
            "artificial_intelligence",
            "computer_vision",
            "nlp",
            "data_science",
        }.intersection(skills)
    )

    if not ai_user:
        return 0.0

    # -----------------------------------------------------
    # Strong AI / ML careers
    # -----------------------------------------------------

    strong_ai_titles = [
        "artificial intelligence engineer",
        "artificial intelligence developer",
        "ai engineer",
        "ai developer",
        "machine learning engineer",
        "machine learning developer",
        "ml engineer",
        "ml developer",
        "deep learning engineer",
        "deep learning developer",
    ]

    for term in strong_ai_titles:
        if term in title:
            return 1.0

    # -----------------------------------------------------
    # Data Science
    # -----------------------------------------------------

    data_titles = [
        "data scientist",
        "data scientists",
        "data science",
    ]

    for term in data_titles:
        if term in title:
            return 0.90

    # -----------------------------------------------------
    # Computer Vision
    # -----------------------------------------------------

    vision_titles = [
        "computer vision engineer",
        "computer vision",
        "vision engineer",
    ]

    if "computer_vision" in skills:

        for term in vision_titles:
            if term in title:
                return 0.90

    # -----------------------------------------------------
    # NLP / LLM
    # -----------------------------------------------------

    nlp_titles = [
        "natural language processing",
        "nlp engineer",
        "language model engineer",
        "llm engineer",
        "large language model",
    ]

    if "nlp" in skills:

        for term in nlp_titles:
            if term in title:
                return 0.90

    # -----------------------------------------------------
    # Robotics
    # -----------------------------------------------------

    robotics_titles = [
        "robotics engineer",
        "robotics",
        "robotic engineer",
    ]

    for term in robotics_titles:
        if term in title:
            return 0.60

    # -----------------------------------------------------
    # Software Engineering
    # -----------------------------------------------------

    software_titles = [
        "software engineer",
        "software developer",
        "software developers",
        "application developer",
        "application software developer",
    ]

    for term in software_titles:
        if term in title:
            return 0.80

    # -----------------------------------------------------
    # General programming
    # -----------------------------------------------------

    programming_titles = [
        "computer programmer",
        "computer programmers",
    ]

    for term in programming_titles:
        if term in title:
            return 0.65

    return 0.0
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
    ai_application_score,
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

     # -----------------------------------------------------
    # Standard technical query
    # -----------------------------------------------------

    semantic_weight = 0.25
    technical_weight = 0.35
    ai_weight = 0.15
    ai_application_weight = 0.10
    domain_weight = 0.05
    title_weight = 0.10

    # -----------------------------------------------------
    # AI-focused query
    # -----------------------------------------------------

    if ai_intent:

        semantic_weight = 0.15
        technical_weight = 0.25
        ai_weight = 0.20
        ai_application_weight = 0.25
        domain_weight = 0.05
        title_weight = 0.10

    final_score = (

    semantic_score *
    semantic_weight

    + technical_score *
    technical_weight

    + ai_relevance *
    ai_weight

    + ai_application_score *
    ai_application_weight

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

    Instead of keeping only the highest-scoring chunk,
    this function combines the text from all retrieved
    chunks belonging to the same occupation.

    This gives the ranking system access to the full
    occupation information when calculating technical
    and AI relevance.
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
            result.get("onet_code")
            or result.get("O*NET-SOC Code")
            or result.get("soc_code")
            or result.get("code")
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
        # Create occupation
        # -------------------------------------------------

        if code not in unique:

            unique[code] = {
                "result": dict(result),
                "semantic_score": float(
                    semantic_score
                ),
            }

        else:

            existing = unique[code]

            # -------------------------------------------------
            # Keep highest semantic score
            # -------------------------------------------------

            if semantic_score > existing[
                "semantic_score"
            ]:

                existing[
                    "semantic_score"
                ] = float(semantic_score)

            # -------------------------------------------------
            # Combine text from all chunks
            # -------------------------------------------------

            existing_text = existing[
                "result"
            ].get(
                "text",
                ""
            )

            new_text = result.get(
                "text",
                ""
            )

            if new_text and new_text not in existing_text:

                existing[
                    "result"
                ]["text"] = (
                    existing_text
                    + "\n"
                    + new_text
                )

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
        # AI application development score
        # -------------------------------------------------

        ai_application_score = (
        calculate_ai_application_score(
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
        ai_application_score,
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
                
            "ai_application_score":
                ai_application_score,   
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
         f"AI Application Score: "
         f"{item['ai_application_score']:.4f}"
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
