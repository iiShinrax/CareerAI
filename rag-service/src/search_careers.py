import json
import re

import faiss
from sentence_transformers import SentenceTransformer


# =========================================================
# Career Intent Detection
# =========================================================

CAREER_INTENTS = {

    "data_scientist": {
        "title_terms": [
            "data scientist",
            "data science",
        ],
        "related_terms": [
            "data analysis",
            "data analytics",
            "machine learning",
            "data mining",
            "statistics",
            "predictive modeling",
        ],
    },

    "machine_learning_engineer": {
        "title_terms": [
            "machine learning engineer",
            "machine learning engineering",
            "ml engineer",
            "ml engineering",
        ],
        "related_terms": [
            "machine learning",
            "model deployment",
            "machine learning models",
            "predictive modeling",
        ],
    },

    "ai_engineer": {
        "title_terms": [
            "ai engineer",
            "ai engineering",
            "artificial intelligence engineer",
            "artificial intelligence engineering",
        ],
        "related_terms": [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "ai applications",
            "ai systems",
        ],
    },

    "software_engineer": {
        "title_terms": [
            "software engineer",
            "software engineering",
            "software developer",
            "software development",
        ],
        "related_terms": [
            "programming",
            "application development",
            "computer programming",
        ],
    },

    "computer_vision": {
        "title_terms": [
            "computer vision",
            "computer vision engineer",
        ],
        "related_terms": [
            "image recognition",
            "image classification",
            "object detection",
            "deep learning",
        ],
    },

    "nlp": {
        "title_terms": [
            "nlp",
            "natural language processing",
            "nlp engineer",
        ],
        "related_terms": [
            "language model",
            "large language model",
            "text analysis",
            "deep learning",
        ],
    },
}


def detect_career_intent(query):

    text = normalize(query)

    detected = []

    for career, data in CAREER_INTENTS.items():

        for term in data["title_terms"]:

            if contains_term(text, term):

                detected.append(career)
                break

    return detected


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
            "sql",
        ],
    },

    "sql": {
        "keywords": [
            "sql",
            "structured query language",
            "mysql",
            "postgresql",
            "postgres",
            "sqlite",
            "t-sql",
            "pl/sql",
        ],
        "related": [
            "database",
            "databases",
            "database management",
            "data analysis",
            "data science",
            "data warehousing",
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
    "pattern recognition": 0.7,

    "data science": 0.8,
    "data scientist": 1.0,
    "data mining": 0.7,

    "algorithm": 0.2,
    "analytics": 0.2,

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
# Text Normalization
# =========================================================

def normalize(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text).lower()
    ).strip()


# =========================================================
# Generic Keyword Matching
# =========================================================

def contains_term(text, term):

    text = normalize(text)
    term = normalize(term)

    if not text or not term:
        return False

    pattern = r"\b" + re.escape(term) + r"\b"

    return bool(
        re.search(pattern, text)
    )


# =========================================================
# Query Skill Detection
# =========================================================

def detect_skills(query):

    text = normalize(query)

    detected = []

    for skill, data in SKILL_FAMILIES.items():

        for keyword in data["keywords"]:

            if contains_term(
                text,
                keyword
            ):

                detected.append(skill)
                break

    # -----------------------------------------------------
    # Standalone AI
    # -----------------------------------------------------

    if contains_term(text, "ai"):

        if "artificial_intelligence" not in detected:

            detected.append(
                "artificial_intelligence"
            )

    return detected


# =========================================================
# Technical Matching
# =========================================================

def calculate_technical_match(
    text,
    detected_skills
):

    """
    Measures compatibility between the user's skills
    and the occupation.

    Important principle:

        Python/programming alone should NOT make an
        occupation an AI career.

    AI/ML skills receive much stronger weight than
    generic programming.
    """

    text = normalize(text)

    if not detected_skills:
        return 0.0, []

    skill_weights = {

        "python": 0.65,

        "machine_learning": 1.60,

        "deep_learning": 1.80,

        "artificial_intelligence": 1.70,

        "data_science": 1.40,

        "computer_vision": 1.60,

        "nlp": 1.60,

        "sql": 0.70,
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
        # Score
        # -------------------------------------------------

        if exact_match:

            total_score += weight

        elif related_matches > 0:

            related_score = min(
                0.25 * related_matches,
                0.60
            )

            total_score += (
                weight * related_score
            )

    # =====================================================
    # Generic career compatibility
    # =====================================================

    # Generic programming should provide only a small
    # amount of additional evidence.

    generic_terms = {

        "software development": 0.08,
        "software engineering": 0.08,

        "application development": 0.08,

        "programming": 0.05,
        "computer programming": 0.05,

        "software developer": 0.08,
        "software developers": 0.08,

        "software engineer": 0.08,
        "software engineers": 0.08,

        "data analysis": 0.08,
        "data analytics": 0.08,
    }

    generic_bonus = 0.0

    for term, bonus in generic_terms.items():

        if contains_term(
            text,
            term
        ):

            generic_bonus += bonus

            if term not in matched_terms:

                matched_terms.append(term)

    generic_bonus = min(
        generic_bonus,
        0.15
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

    score = min(
        base_score + generic_bonus,
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
    Measures direct AI/ML relevance.

    Title evidence is important.
    Direct AI concepts receive strong scores.
    Generic programming does not count as AI evidence.
    """

    title = normalize(title)
    text = normalize(text)

    combined = (
        title +
        " " +
        text
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
        # Exact AI skill
        # -------------------------------------------------

        for keyword in data["keywords"]:

            if contains_term(
                combined,
                keyword
            ):

                exact_match = True
                break

        # -------------------------------------------------
        # Related AI evidence
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
                0.30 * related_matches,
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


# =========================================================
# AI Application Development Score
# =========================================================

def calculate_ai_application_score(
    title,
    text
):

    """
    Measures whether an occupation is useful for
    building AI/ML applications.

    Direct AI engineering evidence is strongest.

    Generic software development can help, but it
    should never be enough by itself to classify a
    career as an AI career.
    """

    title = normalize(title)
    text = normalize(text)

    combined = (
        title +
        " " +
        text
    )

    # -----------------------------------------------------
    # Strong AI development evidence
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
    # General AI evidence
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
    # Generic development evidence
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
    # AI-focused title evidence
    # -----------------------------------------------------

    ai_title_terms = [

        "data scientist",
        "data scientists",

        "machine learning engineer",
        "machine learning engineers",

        "artificial intelligence engineer",
        "artificial intelligence engineers",

        "ai engineer",
        "ai engineers",

        "ai developer",
        "ai developers",

        "computer vision engineer",
        "computer vision engineers",

        "nlp engineer",
        "nlp engineers",
    ]

    # -----------------------------------------------------
    # Count evidence
    # -----------------------------------------------------

    ai_development_matches = sum(
        1
        for term in ai_development_terms
        if contains_term(combined, term)
    )

    ai_matches = sum(
        1
        for term in ai_terms
        if contains_term(combined, term)
    )

    development_matches = sum(
        1
        for term in development_terms
        if contains_term(combined, term)
    )

    title_matches = sum(
        1
        for term in ai_title_terms
        if contains_term(title, term)
    )

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
    # Normalize
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
        development_matches / 4.0,
        1.0
    )

    title_score = min(
        title_matches / 2.0,
        1.0
    )

    # -----------------------------------------------------
    # Important:
    #
    # Generic development has low weight.
    # AI evidence has high weight.
    # -----------------------------------------------------

    score = (

        0.45 * ai_development_score

        + 0.35 * ai_score

        + 0.15 * title_score

        + 0.05 * development_score
    )

    return min(
        score,
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
    Measures whether an occupation belongs to a
    technical/computing domain.

    This is a broad signal and therefore should NOT
    dominate career matching.
    """

    title = normalize(title)
    text = normalize(text)

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

    title_matches = sum(
        1
        for term in technical_title_terms
        if contains_term(title, term)
    )

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

    text_matches = sum(
        1
        for term in technical_text_terms
        if contains_term(text, term)
    )

    title_score = min(
        title_matches / 2.0,
        1.0
    )

    text_score = min(
        text_matches / 4.0,
        1.0
    )

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
    the user's technical direction.
    """

    title = normalize(title)

    if not detected_skills:
        return 0.0

    skills = set(
        detected_skills
    )

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
    # Direct AI careers
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

        if contains_term(
            title,
            term
        ):

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

        if contains_term(
            title,
            term
        ):

            return 0.90

    # -----------------------------------------------------
    # Computer Vision
    # -----------------------------------------------------

    if "computer_vision" in skills:

        vision_titles = [

            "computer vision engineer",
            "computer vision",
            "vision engineer",
        ]

        for term in vision_titles:

            if contains_term(
                title,
                term
            ):

                return 0.90

    # -----------------------------------------------------
    # NLP / LLM
    # -----------------------------------------------------

    if "nlp" in skills:

        nlp_titles = [

            "natural language processing",
            "nlp engineer",
            "language model engineer",
            "llm engineer",
            "large language model",
        ]

        for term in nlp_titles:

            if contains_term(
                title,
                term
            ):

                return 0.90

    # -----------------------------------------------------
    # Software
    #
    # Strong adjacent career.
    # -----------------------------------------------------

    software_titles = [

        "software engineer",
        "software developer",
        "software developers",

        "application developer",
        "application software developer",
    ]

    for term in software_titles:

        if contains_term(
            title,
            term
        ):

            return 0.75

    # -----------------------------------------------------
    # Robotics
    #
    # Related but NOT a direct AI career.
    # -----------------------------------------------------

    robotics_titles = [

        "robotics engineer",
        "robotic engineer",
        "robotics",
    ]

    for term in robotics_titles:

        if contains_term(
            title,
            term
        ):

            return 0.45

    # -----------------------------------------------------
    # General programming
    # -----------------------------------------------------

    programming_titles = [

        "computer programmer",
        "computer programmers",
    ]

    for term in programming_titles:

        if contains_term(
            title,
            term
        ):

            return 0.30

    return 0.0


# =========================================================
# User Intent Detection
# =========================================================

def detect_ai_intent(query):

    text = normalize(query)

    # -----------------------------------------------------
    # Direct AI career intent
    # -----------------------------------------------------

    direct_ai_terms = [

        "ai engineer",
        "artificial intelligence engineer",

        "machine learning engineer",
        "ml engineer",

        "data scientist",

        "ai developer",
        "artificial intelligence developer",

        "machine learning developer",
    ]

    for term in direct_ai_terms:

        if contains_term(
            text,
            term
        ):

            return True

    # -----------------------------------------------------
    # AI application-building intent
    # -----------------------------------------------------

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
# Career Goal Score
# =========================================================

def calculate_career_goal_score(
    title,
    career_goal,
    preferred_roles,
    domains
):

    """
    Measures how closely the occupation matches the
    user's explicit career goal.

    This is deliberately title-focused.

    Example:

        User wants AI Engineer

        AI Engineer
            -> 1.00

        Machine Learning Engineer
            -> 0.95

        Data Scientist
            -> 0.85

        Software Developer
            -> 0.65

        Data Engineer
            -> 0.60

        Robotics Engineer
            -> 0.35

        Computer Programmer
            -> 0.00

    This prevents generic words such as "programming"
    from turning unrelated careers into AI careers.
    """

    title = normalize(title)
    goal = normalize(career_goal)

    roles = [
        normalize(role)
        for role in preferred_roles
        if normalize(role)
    ]

    domains_text = " ".join(
        normalize(domain)
        for domain in domains
        if normalize(domain)
    )

    target = " ".join(
        [
            goal,
            " ".join(roles),
            domains_text,
        ]
    )

    # =====================================================
    # Exact goal / preferred role title
    # =====================================================

    for role in roles:

        if contains_term(
            title,
            role
        ):

            return 1.0

    if goal and contains_term(
        title,
        goal
    ):

        return 1.0

    # =====================================================
    # Detect AI goal
    # =====================================================

    ai_goal = (
        contains_term(target, "ai")
        or
        contains_term(
            target,
            "artificial intelligence"
        )
        or
        contains_term(
            target,
            "machine learning"
        )
        or
        contains_term(
            target,
            "deep learning"
        )
    )

    # =====================================================
    # AI career hierarchy
    # =====================================================

    if ai_goal:

        # -------------------------------------------------
        # Direct AI / ML titles
        # -------------------------------------------------

        direct_ai_titles = [

            "ai engineer",
            "artificial intelligence engineer",

            "machine learning engineer",
            "ml engineer",

            "deep learning engineer",

            "ai developer",
            "artificial intelligence developer",

            "machine learning developer",
            "ml developer",
        ]

        for term in direct_ai_titles:

            if contains_term(
                title,
                term
            ):

                return 0.95

        # -------------------------------------------------
        # Data Scientist
        # -------------------------------------------------

        if (
            contains_term(
                title,
                "data scientist"
            )
            or
            contains_term(
                title,
                "data science"
            )
        ):

            return 0.85

        # -------------------------------------------------
        # Computer Scientist
        # -------------------------------------------------

        if contains_term(
            title,
            "computer scientist"
        ):

            return 0.70

        # -------------------------------------------------
        # Software Developer / Engineer
        #
        # Strong adjacent AI implementation career.
        # -------------------------------------------------

        software_titles = [

            "software developer",
            "software engineer",

            "application developer",
            "application engineer",
        ]

        for term in software_titles:

            if contains_term(
                title,
                term
            ):

                return 0.65

        # -------------------------------------------------
        # Data Engineering
        # -------------------------------------------------

        data_engineering_titles = [

            "data engineer",
            "data engineering",

            "database engineer",
        ]

        for term in data_engineering_titles:

            if contains_term(
                title,
                term
            ):

                return 0.60

        # -------------------------------------------------
        # Robotics
        #
        # AI-related, but not the target career.
        # -------------------------------------------------

        robotics_titles = [

            "robotics engineer",
            "robotic engineer",
            "robotics",
        ]

        for term in robotics_titles:

            if contains_term(
                title,
                term
            ):

                return 0.35

        # -------------------------------------------------
        # Computer Programmer
        #
        # Programming alone is NOT enough for AI career
        # matching.
        # -------------------------------------------------

        if (
            contains_term(
                title,
                "computer programmer"
            )
            or
            contains_term(
                title,
                "programmer"
            )
        ):

            return 0.15

        # -------------------------------------------------
        # AI-related technical titles
        # -------------------------------------------------

        ai_related_titles = [

            "computer vision",
            "nlp",
            "natural language processing",
        ]

        for term in ai_related_titles:

            if contains_term(
                title,
                term
            ):

                return 0.75

        return 0.0

    # =====================================================
    # Non-AI goal
    # =====================================================

    # Exact title word overlap only.

    goal_words = [
        word
        for word in goal.split()
        if len(word) > 3
    ]

    if not goal_words:

        return 0.0

    matches = sum(
        1
        for word in goal_words
        if contains_term(
            title,
            word
        )
    )

    if matches == len(goal_words):

        return 0.90

    if matches >= 2:

        return 0.60

    if matches == 1:

        return 0.30

    return 0.0


# =========================================================
# Goal-Aware Final Score
# =========================================================

def calculate_goal_aware_score(
    base_score,
    career_goal_score,
    title_relevance,
    ai_intent
):

    """
    Adds explicit career-goal alignment to the existing
    ranking score.

    Career goal is important, but it should not completely
    override technical evidence.
    """

    # -----------------------------------------------------
    # Goal alignment
    # -----------------------------------------------------

    goal_bonus = (
        career_goal_score * 0.18
    )

    # -----------------------------------------------------
    # Small title bonus
    # -----------------------------------------------------

    title_bonus = (
        title_relevance * 0.03
    )

    final_score = (
        base_score
        +
        goal_bonus
        +
        title_bonus
    )

    return min(
        final_score,
        1.0
    )


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
    Combines retrieval and ranking signals.

    AI-focused searches prioritize:
        AI relevance
        AI application evidence
        technical skills
        title
        semantic similarity
    """

    if not detected_skills:

        return semantic_score

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
        ai_weight = 0.25
        ai_application_weight = 0.20
        domain_weight = 0.03
        title_weight = 0.12

    final_score = (

        semantic_score
        * semantic_weight

        +

        technical_score
        * technical_weight

        +

        ai_relevance
        * ai_weight

        +

        ai_application_score
        * ai_application_weight

        +

        domain_score
        * domain_weight

        +

        title_relevance
        * title_weight
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
    FAISS may return multiple chunks from the same
    occupation.

    Combine chunks belonging to the same occupation.
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
                ] = float(
                    semantic_score
                )

            # -------------------------------------------------
            # Combine text
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

            if (
                new_text
                and
                new_text not in existing_text
            ):

                existing[
                    "result"
                ]["text"] = (
                    existing_text
                    +
                    "\n"
                    +
                    new_text
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
    title_relevance,
    career_goal_score=0.0
):

    reasons = []

    # -----------------------------------------------------
    # Technical matches
    # -----------------------------------------------------

    if matched_terms:

        useful_terms = matched_terms[:4]

        reasons.append(
            "matches "
            +
            ", ".join(
                useful_terms
            )
        )

    # -----------------------------------------------------
    # Career goal
    # -----------------------------------------------------

    if career_goal_score >= 0.90:

        reasons.append(
            "directly matches your career goal"
        )

    elif career_goal_score >= 0.70:

        reasons.append(
            "strongly aligns with your career goal"
        )

    elif career_goal_score >= 0.50:

        reasons.append(
            "is a strong adjacent career to your goal"
        )

    elif career_goal_score >= 0.30:

        reasons.append(
            "is related to your career goal"
        )

    # -----------------------------------------------------
    # AI relevance
    # -----------------------------------------------------

    if ai_relevance >= 0.60:

        reasons.append(
            "strong AI/ML relevance"
        )

    elif ai_relevance >= 0.25:

        reasons.append(
            "moderate AI/ML relevance"
        )

    elif ai_relevance >= 0.08:

        reasons.append(
            "some AI/data relevance"
        )

    # -----------------------------------------------------
    # Title relevance
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Technical alignment
    # -----------------------------------------------------

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
        +
        "; ".join(reasons)
        +
        "."
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

    print(
        "Retrieval system ready."
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

    print(
        "\nDetected technical terms:"
    )

    if detected_skills:

        print(
            ", ".join(
                detected_skills
            )
        )

    else:

        print(
            "None"
        )

    # -----------------------------------------------------
    # Detect career intent
    # -----------------------------------------------------

    career_intents = detect_career_intent(
        query
    )

    if career_intents:

        print(
            "\nDetected career intents:"
        )

        print(
            ", ".join(
                career_intents
            )
        )

    # -----------------------------------------------------
    # Detect AI intent
    # -----------------------------------------------------

    ai_intent = detect_ai_intent(
        query
    )

    if ai_intent:

        print(
            "Detected AI-focused career/application intent."
        )

    # -----------------------------------------------------
    # Query embedding
    # -----------------------------------------------------

    print(
        "\nGenerating retrieval embedding..."
    )

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
    # Deduplicate
    # -----------------------------------------------------

    candidates = collect_unique_candidates(
        metadata,
        scores,
        indices
    )

    print(
        f"Retrieved {len(candidates)} unique occupations."
    )

    # =====================================================
    # Extract career goal information
    #
    # The LLM retriever can pass these fields when this
    # module is imported.
    #
    # For standalone use, infer them from the query.
    # =====================================================

    career_goal = query

    preferred_roles = []

    domains = []

    # -----------------------------------------------------
    # If the query directly contains an AI career target,
    # normalize it into a career goal.
    # -----------------------------------------------------

    if contains_term(
        query,
        "ai engineer"
    ):

        career_goal = "AI engineer"
        preferred_roles = [
            "AI Engineer"
        ]
        domains = [
            "AI",
            "machine learning",
            "software engineering"
        ]

    elif contains_term(
        query,
        "machine learning engineer"
    ):

        career_goal = "Machine Learning Engineer"
        preferred_roles = [
            "Machine Learning Engineer"
        ]
        domains = [
            "machine learning",
            "AI",
            "software engineering"
        ]

    elif contains_term(
        query,
        "data scientist"
    ):

        career_goal = "Data Scientist"
        preferred_roles = [
            "Data Scientist"
        ]
        domains = [
            "data science",
            "machine learning",
            "AI"
        ]

    # =====================================================
    # Calculate ranking features
    # =====================================================

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
        # AI application score
        # -------------------------------------------------

        ai_application_score = (
            calculate_ai_application_score(
                title,
                text
            )
        )

        # -------------------------------------------------
        # Domain
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
        # Career goal score
        # -------------------------------------------------

        career_goal_score = (
            calculate_career_goal_score(
                title,
                career_goal,
                preferred_roles,
                domains
            )
        )

        # -------------------------------------------------
        # Base ranking
        # -------------------------------------------------

        base_score = (
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
        # Goal-aware ranking
        # -------------------------------------------------

        final_score = (
            calculate_goal_aware_score(
                base_score,
                career_goal_score,
                title_relevance,
                ai_intent
            )
        )

        # -------------------------------------------------
        # AI query filtering
        #
        # If user explicitly wants an AI career, do not
        # allow completely unrelated occupations into the
        # final ranking just because they have programming
        # or semantic similarity.
        # -------------------------------------------------

        if ai_intent:

            meaningful_match = (

                career_goal_score >= 0.30

                or

                ai_relevance >= 0.10

                or

                ai_application_score >= 0.15
            )

            if not meaningful_match:

                continue

        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        explanation = (
            generate_explanation(
                title,
                matched_terms,
                technical_score,
                ai_relevance,
                title_relevance,
                career_goal_score
            )
        )

        ranked_results.append({

            "result":
                result,

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

            "base_score":
                base_score,

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

            or

            result.get(
                "O*NET-SOC Code"
            )

            or

            result.get(
                "soc_code"
            )

            or

            result.get(
                "code"
            )

            or

            title
        )

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
            f"Career Goal Score: "
            f"{item['career_goal_score']:.4f}"
        )

        print(
            f"Base Final Score: "
            f"{item['base_score']:.4f}"
        )

        print(
            f"Final Score: "
            f"{item['final_score']:.4f}"
        )

        if item["matched_terms"]:

            print(
                "Matched Terms: "
                +
                ", ".join(
                    item["matched_terms"][:6]
                )
            )

        print(
            "Why: "
            +
            item["explanation"]
        )

        print(
            "-" * 70
        )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    main()