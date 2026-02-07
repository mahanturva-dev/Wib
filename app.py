import json
import streamlit as st
import streamlit.components.v1 as components
from textwrap import dedent


def mock_structured_summary(paper_name: str):
    # Mocked structured JSON response for a single paper
    return {
        "title": paper_name,
        "problem": "Limited generalization to out-of-distribution datasets.",
        "method": "Hybrid RAG with a transformer-based retriever and lightweight reader.",
        "results": "Up to 15% improvement on in-domain benchmarks; mixed OOD performance.",
        "limitations": "Small evaluation set; no ablation on hyperparameters." 
    }


def mock_comparison(papers):
    # Mocked structured JSON response for comparison across papers
    return {p: mock_structured_summary(p) for p in papers}


st.set_page_config(page_title="Research Paper Analyzer", layout="wide")

st.markdown(
    """
    <style>
    /* Control-room aesthetic */
    .stApp { background: linear-gradient(180deg,#071021 0%, #0b1623 100%); color: #e6f0f6 }
    .title { font-family: 'Inter', sans-serif; font-weight:700; font-size:30px; color:#bfe3ff }
    .card { background: rgba(255,255,255,0.03); padding:14px; border-radius:8px; margin:8px }
    .chip { background:#0f2030; color:#c7e6ff; padding:6px 10px; border-radius:18px; margin-right:8px }
    .chip:hover { background:#143142; cursor:pointer }
    .dominant-viz { display:flex; justify-content:center; align-items:center }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='title'>Research Paper Analyzer — Control Room</div>", unsafe_allow_html=True)
st.caption("Upload PDFs, pick papers as cards, ask guided questions, and inspect structured JSON outputs.")

# ---------- File uploader (top, not sidebar) ----------
uploaded_files = st.file_uploader("Upload 1–6 research PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.info(f"{len(uploaded_files)} paper(s) uploaded — view as cards below.")

# Initialize selection state
if "selections" not in st.session_state:
    st.session_state.selections = {}

paper_items = [f.name for f in uploaded_files] if uploaded_files else []

# Selection controls: allow single / multi / all
sel_col1, sel_col2, sel_col3 = st.columns([1, 3, 1])
with sel_col1:
    selection_mode = st.radio("Selection mode", ["Multi", "Single"], key="selection_mode")
with sel_col2:
    if st.button("Select All"):
        for p in paper_items:
            st.session_state.selections[p] = True
    st.write("")
with sel_col3:
    if st.button("Clear Selection"):
        st.session_state.selections = {}


# ---------- Paper cards area ----------
if paper_items:
    cards_container = st.container()
    with cards_container:
        cols = st.columns(min(4, len(paper_items)))
        for i, paper in enumerate(paper_items):
            col = cols[i % len(cols)]
            with col:
                selected = st.session_state.selections.get(paper, False)
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"**📄 {paper}**")
                if selection_mode == "Single":
                    if st.button(f"Select (single) — {paper}", key=f"single_{paper}"):
                        # make this the only selection
                        st.session_state.selections = {paper: True}
                        selected = True
                else:
                    chk = st.checkbox("Select", value=selected, key=f"chk_{paper}")
                    st.session_state.selections[paper] = chk

                st.markdown("<div style='color:#9fb8cf;font-size:13px'>Uploaded PDF preview not shown — mock data used.</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


# ---------- Question chips + input (must not be empty) ----------
st.subheader("Ask a question")
chip_col = st.container()
with chip_col:
    chips = [
        ("Summarize", "Summarize the selected paper(s) into Problem / Method / Results / Limitations"),
        ("Compare", "Compare methods and results across selected papers"),
        ("Datasets", "What datasets were used in the selected paper(s)?"),
        ("Methods", "List and compare the methods used in selected paper(s)."),
        ("Limitations", "What are the limitations of the selected paper(s)?"),
    ]
    for label, q in chips:
        if st.button(label, key=f"chip_{label}"):
            st.session_state.question = q

question = st.text_input("Question (required)", value=st.session_state.get("question", ""))

selected_list = [p for p, v in st.session_state.selections.items() if v]

if not selected_list:
    st.warning("Select at least one paper card to proceed.")

if not question.strip():
    st.error("Question cannot be empty — use a chip or type a question.")

ask_btn = st.button("Ask — Analyze")

if ask_btn:
    if not selected_list:
        st.error("Please select one or more papers before asking a question.")
    elif not question.strip():
        st.error("Question is empty. Use the suggested chips or enter a question.")
    else:
        # Intent detection
        q_low = question.lower()
        comparison_intent = False
        if len(selected_list) > 1:
            comparison_intent = True
        if "compare" in q_low or "compare" in question:
            comparison_intent = True

        if comparison_intent:
            st.success("Intent: Comparison detected — presenting comparison view and evidence visualization.")
            # Center-dominant visualization
            viz_col = st.container()
            with viz_col:
                st.markdown("<div class='dominant-viz'>", unsafe_allow_html=True)
                components.html(open("three_viz.html").read(), height=520)
                st.markdown("</div>", unsafe_allow_html=True)

            # Show structured comparison JSON and a simple table
            comp = mock_comparison(selected_list)
            left, right = st.columns([2, 3])
            with left:
                st.subheader("Structured Comparison JSON")
                st.json(comp)
            with right:
                st.subheader("Side-by-side review")
                for p in selected_list:
                    s = comp[p]
                    st.markdown(f"**{s['title']}**")
                    st.markdown(f"- **Problem:** {s['problem']}")
                    st.markdown(f"- **Method:** {s['method']}")
                    st.markdown(f"- **Results:** {s['results']}")
                    st.markdown(f"- **Limitations:** {s['limitations']}")
                    st.write("---")

        else:
            # Single-paper focused structured summary
            target = selected_list[0]
            st.success(f"Intent: Single-paper summary — focusing on {target}")
            summary = mock_structured_summary(target)
            summary_col, raw_col = st.columns([2, 1])
            with summary_col:
                st.subheader("Structured Summary")
                st.markdown(f"**Problem:** {summary['problem']}")
                st.markdown(f"**Method:** {summary['method']}")
                st.markdown(f"**Results:** {summary['results']}")
                st.markdown(f"**Limitations:** {summary['limitations']}")
            with raw_col:
                st.subheader("Structured JSON")
                st.json(summary)

        # Save last action to session for traceability
        st.session_state.last_query = {
            "question": question,
            "selected": selected_list,
            "comparison": comparison_intent,
        }

# Footer / quick help
st.markdown("---")
st.caption("Tip: Use the chips to fill the question quickly. Comparison visualizations appear when comparing multiple papers.")

