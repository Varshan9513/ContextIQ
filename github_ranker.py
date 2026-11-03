
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


STOP_WORDS = {
    "what", "which", "where", "when", "why", "how",
    "find", "search", "show", "give", "tell", "explain",
    "the", "and", "for", "with", "from", "into",
    "using", "used", "use", "can", "could", "would",
    "should", "about", "that", "this", "are", "is",
    "was", "were", "does", "do", "did", "has", "have",
    "code", "source", "example", "examples", "project",
    "system", "application", "implementation"
}


def tokenize(text):

    words = re.findall(
        r"[a-zA-Z0-9]+",
        str(text).lower()
    )

    return [
        word for word in words
        if len(word) > 2 and word not in STOP_WORDS
    ]


def clean_text(text):

    return " ".join(tokenize(text))


def calculate_keyword_score(question, document):

    keywords = set(tokenize(question))

    if not keywords:
        return 0.0

    document_text = " ".join([
        str(document.get("text", "")),
        str(document.get("path", "")),
        str(document.get("description", "")),
        str(document.get("title", ""))
    ])

    document_words = set(tokenize(document_text))

    matched = keywords.intersection(document_words)

    return len(matched) / len(keywords)


def calculate_implementation_score(document):

    text = str(document.get("text", ""))

    # Count meaningful code structures.
    features = {
        "function": r"\bdef\s+\w+|\bfunction\s+\w+",
        "class": r"\bclass\s+\w+",
        "imports": r"\bimport\s+\w+|\bfrom\s+\w+\s+import\b",
        "conditionals": r"\bif\b|\belse\b|\bswitch\b",
        "loops": r"\bfor\b|\bwhile\b",
        "error_handling": r"\btry\b|\bexcept\b|\bcatch\b",
        "return": r"\breturn\b"
    }

    matched = sum(
        bool(re.search(pattern, text))
        for pattern in features.values()
    )

    return round(matched / len(features), 4)


def calculate_path_score(document, question):

    path = str(document.get("path", "")).lower()
    keywords = set(tokenize(question))

    if not keywords:
        return 0.0

    matched = sum(
        1 for keyword in keywords
        if keyword in path
    )

    return matched / len(keywords)


def rank_github_documents(question, documents, top_k=10):

    if not documents:
        return []

    valid_documents = [
        doc for doc in documents
        if isinstance(doc, dict)
        and str(doc.get("text", doc.get("content", ""))).strip()
    ]

    if not valid_documents:
        return []

    # Prepare actual source content.
    document_texts = []

    for doc in valid_documents:

        content = " ".join([
            str(doc.get("text", doc.get("content", ""))),
            str(doc.get("path", "")),
            str(doc.get("description", "")),
            str(doc.get("title", ""))
        ])

        document_texts.append(content)

    # TF-IDF similarity.
    try:

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=15000
        )

        matrix = vectorizer.fit_transform(
            [question] + document_texts
        )

        similarities = cosine_similarity(
            matrix[0:1],
            matrix[1:]
        ).flatten()

    except ValueError:

        similarities = [0.0] * len(valid_documents)

    ranked = []

    for index, doc in enumerate(valid_documents):

        similarity = float(similarities[index])

        keyword_score = calculate_keyword_score(
            question,
            doc
        )

        implementation_score = calculate_implementation_score(
            doc
        )

        path_score = calculate_path_score(
            doc,
            question
        )

        # Relevance score: implementation is deliberately excluded.
        final_score = (
            0.60 * similarity
            + 0.30 * keyword_score
            + 0.10 * path_score
        )

        result = doc.copy()

        result["similarity"] = round(similarity, 4)

        result["keyword_score"] = round(
            keyword_score, 4
        )

        result["implementation_score"] = round(
            implementation_score, 4
        )

        result["path_score"] = round(
            path_score, 4
        )

        result["final_score"] = round(
            final_score, 4
        )

        ranked.append(result)

    # Sort by actual relevance.
    ranked.sort(
        key=lambda item: item["final_score"],
        reverse=True
    )

    # Do not show completely unrelated files.
    relevant = [
        item for item in ranked
        if item["similarity"] > 0
        or item["keyword_score"] > 0
        or item["path_score"] > 0
    ]

    return relevant[:top_k]
