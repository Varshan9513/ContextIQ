import streamlit as st

# Page configuration
st.set_page_config(
    page_title="ContextIQ",
    page_icon="🧠",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: white;
}

.main-title {
    font-size: 42px;
    font-weight: 700;
    color: #8B9CF6;
}

.subtitle {
    font-size: 18px;
    color: #AAB0C0;
}

</style>
""", unsafe_allow_html=True)

# Header
st.markdown(
    '<div class="main-title">🧠 ContextIQ</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Search Smarter. Trust Better. Answer Accurately.</div>',
    unsafe_allow_html=True
)

st.divider()

# Main section
st.header("Ask ContextIQ")

question = st.text_input(
    "Enter your question",
    placeholder="Example: What is the final project submission deadline?"
)

if st.button("Search Documents", type="primary"):
    if question.strip():
        st.info("Your question: " + question)
        st.warning("Search engine integration is coming next!")
    else:
        st.error("Please enter a question.")

# Sidebar
with st.sidebar:
    st.title("ContextIQ")
    st.caption("Intelligent Context Selection Engine")
    st.divider()
    st.write("📂 Document Search")
    st.write("📊 Evidence Analysis")
    st.write("📚 Source References")