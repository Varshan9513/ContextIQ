
import streamlit as st
import traceback

# --------------------------------------------------
# IMPORT PROJECT MODULES
# --------------------------------------------------

from contextiq_engine import (
    load_documents,
    search_documents,
    generate_answer
)

from github_search import github_search
from github_ranker import rank_github_documents
from wikipedia_search import wikipedia_search
from website_search import website_search


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ContextIQ",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    color: #ffffff;
}

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0px;
}

.tagline {
    font-size: 16px;
    color: #a0aec0;
    margin-bottom: 25px;
}

.section-title {
    font-size: 23px;
    font-weight: 700;
    color: #ffffff;
    margin-top: 20px;
}

.result-card {
    background-color: #1c2333;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #30394d;
    margin-bottom: 15px;
}

.small-text {
    color: #a0aec0;
    font-size: 13px;
}

div.stButton > button {
    background-color: #5b7cfa;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 10px 20px;
    font-weight: bold;
}

div.stButton > button:hover {
    background-color: #4565e8;
    color: white;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULTS = {
    "search_completed": False,
    "last_question": "",
    "drive_results": [],
    "drive_answer": "",
    "github_results": [],
    "wikipedia_results": [],
    "website_results": [],
    "source_errors": {}
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# GOOGLE DRIVE CACHE
# --------------------------------------------------

@st.cache_data(show_spinner=False, ttl=600)
def get_drive_documents():
    return load_documents()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.markdown("## 🔎 ContextIQ")

    st.caption("Intelligent Context Selection Engine")

    st.divider()

    st.markdown("### Navigation")

    st.markdown("""
    - 📁 Document Search
    - 💻 GitHub Code Search
    - 📚 Wikipedia Search
    - 🌐 Website Search
    - 📊 Evidence Analysis
    """)

    st.divider()

    st.markdown("### Search Sources")

    st.write("📁 Google Drive")
    st.write("💻 GitHub")
    st.write("📚 Wikipedia")
    st.write("🌐 Websites")

    st.divider()

    st.markdown("### About")

    st.caption(
        "ContextIQ retrieves information from multiple "
        "sources and presents relevant results with "
        "supporting references."
    )

    if st.button("🔄 Refresh Google Drive Files", use_container_width=True):

        get_drive_documents.clear()

        st.session_state.search_completed = False

        st.success("Google Drive cache refreshed!")

        st.rerun()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🔎 ContextIQ</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="tagline">'
    'Search Smarter. Trust Better. Answer Accurately.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    "Ask a question and retrieve relevant information "
    "from Google Drive, GitHub, Wikipedia and websites."
)


# --------------------------------------------------
# QUESTION INPUT
# --------------------------------------------------

question = st.text_input(
    "Enter your question",
    placeholder="Example: How does machine learning work?",
    key="question_input"
)

search_button = st.button(
    "🔍 Search All Sources",
    use_container_width=True
)


# --------------------------------------------------
# SEARCH EXECUTION
# --------------------------------------------------

if search_button:

    if not question.strip():

        st.warning("Please enter a question before searching.")

    else:

        # Reset previous results
        for key in [
            "drive_results",
            "drive_answer",
            "github_results",
            "wikipedia_results",
            "website_results"
        ]:
            st.session_state[key] = []

        st.session_state.source_errors = {}
        st.session_state.last_question = question

        # ------------------------------------------
        # GOOGLE DRIVE SEARCH
        # ------------------------------------------

        with st.spinner("Searching Google Drive documents..."):

            try:

                drive_documents = get_drive_documents()

                if drive_documents:

                    drive_results = search_documents(
                        question,
                        drive_documents
                    )

                    answer = generate_answer(
                        question,
                        drive_results
                    )

                    st.session_state.drive_results = (
                        drive_results if drive_results else []
                    )

                    st.session_state.drive_answer = (
                        answer if answer else
                        "No answer could be generated from the retrieved documents."
                    )

                else:

                    st.session_state.drive_answer = (
                        "No Google Drive documents were found."
                    )

            except Exception as error:

                st.session_state.source_errors["Google Drive"] = str(error)

        # ------------------------------------------
        # GITHUB SEARCH
        # ------------------------------------------

        with st.spinner("Searching GitHub repositories and code files..."):

            try:

                github_documents = github_search(
                    question,
                    limit=5
                )

                if github_documents:

                    ranked_results = rank_github_documents(
                        question,
                        github_documents,
                        top_k=10
                    )

                    st.session_state.github_results = (
                        ranked_results if ranked_results else []
                    )

                else:

                    st.session_state.github_results = []

            except Exception as error:

                st.session_state.source_errors["GitHub"] = str(error)

        # ------------------------------------------
        # WIKIPEDIA SEARCH
        # ------------------------------------------

        with st.spinner("Searching Wikipedia..."):

            try:

                wiki_results = wikipedia_search(
                    question,
                    limit=5
                )

                st.session_state.wikipedia_results = (
                    wiki_results if wiki_results else []
                )

            except Exception as error:

                st.session_state.source_errors["Wikipedia"] = str(error)

        # ------------------------------------------
        # WEBSITE SEARCH
        # ------------------------------------------

        with st.spinner("Searching websites..."):

            try:

                web_results = website_search(
                    question,
                    limit=5
                )

                st.session_state.website_results = (
                    web_results if web_results else []
                )

            except Exception as error:

                st.session_state.source_errors["Websites"] = str(error)

        st.session_state.search_completed = True


# --------------------------------------------------
# DISPLAY SEARCH RESULTS
# --------------------------------------------------

if st.session_state.search_completed:

    st.divider()

    st.markdown("## 📊 Search Overview")

    st.caption(
        f"Results for: {st.session_state.last_question}"
    )

    drive_count = len(st.session_state.drive_results)
    github_count = len(st.session_state.github_results)
    wiki_count = len(st.session_state.wikipedia_results)
    website_count = len(st.session_state.website_results)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Google Drive", drive_count)
    col2.metric("GitHub Files", github_count)
    col3.metric("Wikipedia", wiki_count)
    col4.metric("Websites", website_count)

    st.divider()

    # ==============================================
    # GOOGLE DRIVE RESULTS
    # ==============================================

    st.markdown(
        '<div class="section-title">📁 Google Drive Results</div>',
        unsafe_allow_html=True
    )

    if st.session_state.drive_answer:

        st.markdown("### 📝 Generated Answer")

        st.info(st.session_state.drive_answer)

    if st.session_state.drive_results:

        st.markdown("### Supporting Documents")

        for index, item in enumerate(
            st.session_state.drive_results,
            start=1
        ):

            source = (
                item.get("source")
                or item.get("filename")
                or f"Document {index}"
            )

            with st.expander(f"📄 {source}"):

                st.write(
                    item.get("text")
                    or item.get("content")
                    or "No text available."
                )

                if item.get("evidence_score") is not None:

                    st.metric(
                        "Evidence Score",
                        f"{item['evidence_score']:.4f}"
                    )

    elif not st.session_state.drive_answer:

        st.info("No relevant Google Drive documents found.")

    st.divider()

    # ==============================================
    # GITHUB RESULTS
    # ==============================================

    st.markdown(
        '<div class="section-title">💻 GitHub Code Results</div>',
        unsafe_allow_html=True
    )

    if st.session_state.github_results:

        st.success(
            f"{github_count} relevant code files retrieved."
        )

        for index, item in enumerate(
            st.session_state.github_results,
            start=1
        ):

            title = (
                item.get("path")
                or item.get("filename")
                or f"Code file {index}"
            )

            repository = item.get("repository", "GitHub repository")

            with st.expander(
                f"💻 {index}. {repository} — {title}"
            ):

                st.write("**Repository:**", repository)

                st.write("**File:**", title)

                if item.get("url"):

                    st.markdown(
                        f"[Open source code]({item['url']})"
                    )

                if item.get("stars") is not None:

                    st.write(
                        "**Repository Stars:**",
                        item["stars"]
                    )

                # Ranking metrics
                col1, col2, col3 = st.columns(3)

                similarity = item.get("similarity", 0)
                keyword_score = item.get("keyword_score", 0)
                implementation_score = item.get(
                    "implementation_score", 0
                )

                col1.metric(
                    "Text Similarity",
                    f"{similarity:.4f}"
                )

                col2.metric(
                    "Keyword Match",
                    f"{keyword_score:.4f}"
                )

                col3.metric(
                    "Implementation Score",
                    f"{implementation_score:.4f}"
                )

                col4, col5 = st.columns(2)

                col4.metric(
                    "Path Match",
                    f"{item.get('path_score', 0):.4f}"
                )

                col5.metric(
                    "Final Score",
                    f"{item.get('final_score', 0):.4f}"
                )

                st.markdown("**Source Code Preview**")

                code = (
                    item.get("text")
                    or item.get("content")
                    or "No source code available."
                )

                st.code(code[:5000])

    else:

        st.warning(
            "No matching GitHub code files were found. "
            "Try a more specific question or check your GitHub API access."
        )

    st.divider()

    # ==============================================
    # WIKIPEDIA RESULTS
    # ==============================================

    st.markdown(
        '<div class="section-title">📚 Wikipedia Results</div>',
        unsafe_allow_html=True
    )

    if st.session_state.wikipedia_results:

        for index, item in enumerate(
            st.session_state.wikipedia_results,
            start=1
        ):

            title = (
                item.get("title")
                or item.get("source")
                or f"Wikipedia result {index}"
            )

            with st.expander(f"📚 {title}"):

                st.write(
                    item.get("text")
                    or item.get("content")
                    or "No summary available."
                )

                if item.get("url"):

                    st.markdown(
                        f"[Read on Wikipedia]({item['url']})"
                    )

    else:

        st.info("No Wikipedia results found.")

    st.divider()

    # ==============================================
    # WEBSITE RESULTS
    # ==============================================

    st.markdown(
        '<div class="section-title">🌐 Website Search Results</div>',
        unsafe_allow_html=True
    )

    if st.session_state.website_results:

        for index, item in enumerate(
            st.session_state.website_results,
            start=1
        ):

            title = (
                item.get("title")
                or item.get("source")
                or f"Website {index}"
            )

            with st.expander(f"🌐 {title}"):

                st.write(
                    item.get("text")
                    or item.get("content")
                    or "No extracted content available."
                )

                if item.get("url"):

                    st.markdown(
                        f"[Visit Website]({item['url']})"
                    )

    else:

        st.info("No website results found.")

    st.divider()

    # ==============================================
    # ERROR REPORT
    # ==============================================

    if st.session_state.source_errors:

        st.markdown("## ⚠️ Source Errors")

        st.warning(
            "Some sources could not be searched successfully."
        )

        for source, error in st.session_state.source_errors.items():

            with st.expander(f"{source} error"):

                st.code(str(error))

    # ==============================================
    # FOOTER
    # ==============================================

    st.divider()

    st.caption(
        "ContextIQ | Intelligent Context Selection Engine"
    )

    st.caption(
        "Search results and similarity scores are indicators "
        "of relevance, not guarantees of factual accuracy."
    )
