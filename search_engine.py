
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

documents = [
    {
        "source": "updated_circular.txt",
        "text": "Official Updated Circular. Date November 12. Final project submission deadline is December 5. This circular supersedes all previous project submission deadline announcements. Issued by College Administration.",
    },
    {
        "source": "student_message.txt",
        "text": "Student Message. Date November 15. Some students have heard that the final-year project submission deadline may be November 30. This information has not been confirmed by the college administration.",
    },
    {
        "source": "faculty_email.txt",
        "text": "Faculty Email. Date November 12. Faculty members recommend submitting final-year projects by November 28.",
    },
    {
        "source": "college_announcement.txt",
        "text": "College Announcement. Date November 10. College administration announces that all final-year students should submit their completed projects by November 25.",
    },
    {
        "source": "old_notice.txt",
        "text": "Project Submission Notice. Date November 5. All final-year students are informed that the project submission deadline is November 20.",
    }
]


def calculate_evidence_score(doc, relevance):
    text = doc["text"].lower()

    # Source authority
    authority = 0.0
    if "college administration" in text:
        authority = 1.0
    elif "faculty" in text:
        authority = 0.6
    elif "student" in text:
        authority = 0.2

    # Direct evidence of a deadline
    directness = 1.0 if "deadline is" in text else 0.3

    # Explicitly supersedes previous announcements
    supersedes = 1.0 if "supersedes all previous" in text else 0.0

    # Combined score (heuristic demo weights)
    final_score = (
        0.35 * relevance
        + 0.25 * authority
        + 0.20 * directness
        + 0.20 * supersedes
    )

    return final_score


def search_documents(query):
    texts = [doc["text"] for doc in documents]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    matrix = vectorizer.fit_transform(texts + [query])

    relevance_scores = cosine_similarity(
        matrix[-1],
        matrix[:-1]
    ).flatten()

    max_score = max(relevance_scores)

    results = []

    for doc, score in zip(documents, relevance_scores):
        relevance = float(score) / max_score if max_score > 0 else 0

        evidence_score = calculate_evidence_score(
            doc, relevance
        )

        results.append((doc, relevance, evidence_score))

    results.sort(key=lambda item: item[2], reverse=True)

    print("\nCONTEXTIQ - INTELLIGENT EVIDENCE RESULTS")
    print("=" * 50)

    for doc, relevance, evidence_score in results:
        print("\nSource:", doc["source"])
        print("Relevance:", round(relevance, 3))
        print("Evidence quality score:", round(evidence_score, 3))
        print("Evidence:", doc["text"])

    if results:
        best_doc = results[0][0]
        print("\n" + "=" * 50)
        print("STRONGEST EVIDENCE:")
        print(best_doc["source"])
        print(best_doc["text"])


if __name__ == "__main__":
    question = input("Ask ContextIQ a question: ")
    search_documents(question)
