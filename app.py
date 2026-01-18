"""
RLM Streamlit GUI - Claude Co-worker Style

A web interface for the Recursive Language Model runtime.
Styled to match Claude's co-worker aesthetic.

Run with: streamlit run app.py
"""

import os
from pathlib import Path

# Load .env file BEFORE any other imports
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

import streamlit as st
import json
import time

# Must be first Streamlit command
st.set_page_config(
    page_title="RLM Runtime",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Claude-style CSS
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;500&display=swap');

    /* Root variables - Claude color palette */
    :root {
        --claude-orange: #D97757;
        --claude-orange-light: #E8A088;
        --claude-orange-dark: #C45D3E;
        --claude-cream: #FAF9F7;
        --claude-bg: #FFFFFF;
        --claude-bg-secondary: #F7F6F3;
        --claude-text: #1A1915;
        --claude-text-secondary: #6B6B6B;
        --claude-border: #E8E6E3;
        --claude-border-light: #F0EFEC;
        --claude-success: #2E7D32;
        --claude-warning: #ED6C02;
        --claude-error: #D32F2F;
    }

    /* Global styles */
    .stApp {
        background-color: var(--claude-cream);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: var(--claude-text);
        letter-spacing: -0.02em;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--claude-bg);
        border-right: 1px solid var(--claude-border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    /* Custom header component */
    .claude-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 0.75rem 0 1.5rem 0;
        margin-bottom: 1rem;
    }

    .claude-logo {
        width: 44px;
        height: 44px;
        background: linear-gradient(145deg, var(--claude-orange) 0%, var(--claude-orange-dark) 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 22px;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(217, 119, 87, 0.25);
    }

    .claude-title-container {
        display: flex;
        flex-direction: column;
    }

    .claude-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--claude-text);
        letter-spacing: -0.03em;
        line-height: 1.2;
    }

    .claude-subtitle {
        font-size: 0.9rem;
        color: var(--claude-text-secondary);
        margin-top: 2px;
        font-weight: 400;
    }

    /* Card styling */
    .claude-card {
        background: var(--claude-bg);
        border: 1px solid var(--claude-border);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    .claude-card-header {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--claude-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 1rem;
    }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--claude-text);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(145deg, var(--claude-orange) 0%, var(--claude-orange-dark) 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 1.5rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(217, 119, 87, 0.25);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(217, 119, 87, 0.35);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Secondary buttons */
    div[data-testid="column"]:not(:last-child) .stButton > button {
        background: var(--claude-bg);
        color: var(--claude-text);
        border: 1px solid var(--claude-border);
        box-shadow: none;
    }

    div[data-testid="column"]:not(:last-child) .stButton > button:hover {
        background: var(--claude-bg-secondary);
        box-shadow: none;
    }

    /* Input styling */
    .stTextArea textarea {
        border: 1px solid var(--claude-border);
        border-radius: 12px;
        font-family: 'Source Code Pro', monospace;
        font-size: 0.9rem;
        background-color: var(--claude-bg);
        padding: 1rem;
        line-height: 1.5;
    }

    .stTextArea textarea:focus {
        border-color: var(--claude-orange);
        box-shadow: 0 0 0 3px rgba(217, 119, 87, 0.12);
    }

    .stTextArea textarea::placeholder {
        color: #A0A0A0;
    }

    /* Select box */
    .stSelectbox > div > div {
        border-radius: 10px;
        border-color: var(--claude-border);
        background: var(--claude-bg);
    }

    /* Slider styling */
    .stSlider > div > div > div > div {
        background-color: var(--claude-orange) !important;
    }

    .stSlider > div > div > div[data-baseweb="slider"] > div {
        background: var(--claude-border) !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--claude-bg);
        border: 1px solid var(--claude-border);
        border-radius: 12px;
        padding: 1rem 1.25rem;
    }

    [data-testid="stMetric"] label {
        color: var(--claude-text-secondary);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 500;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--claude-text);
        font-weight: 600;
        font-size: 1.4rem;
    }

    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 0.9rem;
        font-weight: 500;
    }

    .status-completed {
        background: #E8F5E9;
        color: #2E7D32;
    }

    .status-partial {
        background: #FFF3E0;
        color: #E65100;
    }

    .status-error {
        background: #FFEBEE;
        color: #C62828;
    }

    /* Result sections */
    .result-section {
        background: var(--claude-bg);
        border: 1px solid var(--claude-border);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.875rem;
    }

    .result-section-title {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--claude-orange);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.625rem;
    }

    .result-section-content {
        color: var(--claude-text);
        line-height: 1.65;
        font-size: 0.95rem;
    }

    /* Key points */
    .key-point {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 1rem;
        background: var(--claude-bg-secondary);
        border-radius: 12px;
        margin-bottom: 0.625rem;
        border: 1px solid var(--claude-border-light);
    }

    .key-point-number {
        width: 26px;
        height: 26px;
        background: var(--claude-orange);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        flex-shrink: 0;
    }

    .key-point-text {
        color: var(--claude-text);
        line-height: 1.5;
        font-size: 0.95rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--claude-bg-secondary);
        border-radius: 10px;
        font-weight: 500;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--claude-bg-secondary);
        padding: 4px;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        background: transparent;
        border: none;
        font-weight: 500;
        color: var(--claude-text-secondary);
    }

    .stTabs [aria-selected="true"] {
        background: var(--claude-bg) !important;
        color: var(--claude-text) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid var(--claude-border);
        margin: 1.5rem 0;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--claude-border);
        border-radius: 14px;
        padding: 1.5rem;
        background: var(--claude-bg);
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--claude-orange-light);
    }

    /* JSON display */
    .stJson {
        background: var(--claude-bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--claude-border);
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--claude-text-secondary);
    }

    .empty-state-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        opacity: 0.6;
    }

    .empty-state-text {
        font-size: 1rem;
        color: #9E9E9E;
    }

    /* Sidebar section titles */
    .sidebar-section {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--claude-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    /* Stats bar */
    .stats-bar {
        display: flex;
        gap: 1rem;
        padding: 0.5rem 0;
        font-size: 0.85rem;
        color: var(--claude-text-secondary);
    }

    /* Document title display */
    .doc-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--claude-text);
        margin-bottom: 0.25rem;
    }

    .doc-type {
        font-size: 0.85rem;
        color: var(--claude-text-secondary);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Import RLM modules
from rlm.runtime import run_task
from rlm.guards import GuardConfig
from rlm.context_access import get_access_log
from tasks.example_task import analyze_document, find_errors_in_log, extract_entities


# Task registry
TASKS = {
    "Analyze Document": {
        "fn": analyze_document,
        "description": "Extract title, abstract, key points, and conclusion",
        "icon": "📄",
    },
    "Find Errors in Log": {
        "fn": find_errors_in_log,
        "description": "Find and classify errors by severity",
        "icon": "🔍",
    },
    "Extract Entities": {
        "fn": extract_entities,
        "description": "Extract people, organizations, locations, dates",
        "icon": "🏷️",
    },
}


def render_header():
    """Render Claude-style header."""
    st.markdown("""
        <div class="claude-header">
            <div class="claude-logo">✦</div>
            <div class="claude-title-container">
                <div class="claude-title">RLM Runtime</div>
                <div class="claude-subtitle">LLMs reason, code controls, budgets matter</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Render a status badge."""
    if status == "completed":
        return '<span class="status-badge status-completed">✓ Completed</span>'
    elif status == "partial":
        return '<span class="status-badge status-partial">⚠ Partial Results</span>'
    else:
        return '<span class="status-badge status-error">✕ Error</span>'


def main():
    # Initialize session state
    if "context_text" not in st.session_state:
        st.session_state.context_text = ""
    if "result" not in st.session_state:
        st.session_state.result = None

    # Sidebar
    with st.sidebar:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.5rem;">
                <div style="width: 32px; height: 32px; background: linear-gradient(145deg, #D97757, #C45D3E);
                            border-radius: 8px; display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 16px;">✦</div>
                <span style="font-weight: 600; font-size: 1.1rem; color: #1A1915;">RLM</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">Task</div>', unsafe_allow_html=True)
        task_name = st.selectbox(
            "Task",
            options=list(TASKS.keys()),
            label_visibility="collapsed",
        )
        task_info = TASKS[task_name]
        st.caption(task_info['description'])

        st.markdown('<div class="sidebar-section">Budget Limits</div>', unsafe_allow_html=True)

        max_cost = st.slider(
            "Max Cost ($)",
            min_value=0.05,
            max_value=2.00,
            value=0.50,
            step=0.05,
        )

        max_runtime = st.slider(
            "Max Runtime (sec)",
            min_value=10,
            max_value=300,
            value=60,
            step=10,
        )

        max_tokens = st.slider(
            "Max Tokens/Call",
            min_value=1000,
            max_value=8000,
            value=4000,
            step=500,
        )

        st.markdown('<div class="sidebar-section">Model</div>', unsafe_allow_html=True)
        model = st.selectbox(
            "Model",
            options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("---")

        st.markdown("""
            <div style="font-size: 0.85rem; color: #6B6B6B; line-height: 1.6;">
                <strong style="color: #1A1915;">About RLM</strong><br>
                The Recursive Language Model paradigm ensures predictable costs,
                consistent reasoning, and full auditability.
            </div>
        """, unsafe_allow_html=True)

    # Main content
    render_header()

    # Two-column layout
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-header">Input</div>', unsafe_allow_html=True)

        # Input tabs
        tab1, tab2 = st.tabs(["Paste Text", "Upload File"])

        with tab1:
            context_input = st.text_area(
                "Content",
                value=st.session_state.context_text,
                height=380,
                placeholder="Paste your document or log content here...\n\nThe RLM runtime will navigate this context programmatically, making bounded LLM calls only on relevant sections.",
                label_visibility="collapsed",
            )
            if context_input != st.session_state.context_text:
                st.session_state.context_text = context_input

        with tab2:
            uploaded_file = st.file_uploader(
                "Upload",
                type=["txt", "log", "md", "json", "csv"],
                label_visibility="collapsed",
            )
            if uploaded_file:
                st.session_state.context_text = uploaded_file.read().decode("utf-8")
                st.success(f"✓ {uploaded_file.name} ({len(st.session_state.context_text):,} chars)")

        # Action buttons
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

        with col_btn1:
            if st.button("Sample", use_container_width=True):
                sample_path = Path(__file__).parent / "sample_context.txt"
                if sample_path.exists():
                    st.session_state.context_text = sample_path.read_text()
                    st.rerun()

        with col_btn2:
            if st.button("Clear", use_container_width=True):
                st.session_state.context_text = ""
                st.session_state.result = None
                st.rerun()

        # Context stats
        if st.session_state.context_text:
            char_count = len(st.session_state.context_text)
            word_count = len(st.session_state.context_text.split())
            line_count = st.session_state.context_text.count('\n') + 1
            st.markdown(
                f'<div class="stats-bar">{char_count:,} chars · {word_count:,} words · {line_count:,} lines</div>',
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown('<div class="section-header">Output</div>', unsafe_allow_html=True)

        # Run button
        if st.button(
            f"▶  Run {task_name}",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.context_text,
        ):
            if st.session_state.context_text:
                config = GuardConfig(
                    max_cost=max_cost,
                    max_runtime_seconds=max_runtime,
                    max_tokens_per_subcall=max_tokens,
                    model=model,
                )

                with st.spinner("Processing..."):
                    try:
                        st.session_state.result = run_task(
                            task_info["fn"],
                            st.session_state.context_text,
                            config,
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.session_state.result = None

        # Display results
        if st.session_state.result:
            result = st.session_state.result
            status = result.get("status", "unknown")

            # Status badge
            st.markdown(render_status_badge(status), unsafe_allow_html=True)

            if result.get("error") and status != "completed":
                st.caption(f"_{result['error']}_")

            st.markdown("")

            # Budget metrics
            budget = result.get("budget_summary", {})
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Cost", f"${budget.get('total_cost_usd', 0):.4f}")
            with m2:
                st.metric("Calls", budget.get("total_calls", 0))
            with m3:
                tokens = budget.get("total_input_tokens", 0) + budget.get("total_output_tokens", 0)
                st.metric("Tokens", f"{tokens:,}")
            with m4:
                st.metric("Time", f"{budget.get('elapsed_seconds', 0):.1f}s")

            st.markdown("---")

            # Results
            task_result = result.get("result")
            if task_result and task_name == "Analyze Document":
                analysis = task_result.get("analysis", {})

                # Title
                if analysis.get("title"):
                    st.markdown(f'<div class="doc-title">{analysis["title"]}</div>', unsafe_allow_html=True)
                    if analysis.get("document_type"):
                        st.markdown(f'<div class="doc-type">Type: {analysis["document_type"]}</div>', unsafe_allow_html=True)

                # Abstract
                if analysis.get("abstract"):
                    st.markdown(f"""
                        <div class="result-section">
                            <div class="result-section-title">Abstract</div>
                            <div class="result-section-content">{analysis["abstract"]}</div>
                        </div>
                    """, unsafe_allow_html=True)

                # Key points
                if analysis.get("key_points"):
                    st.markdown('<div class="result-section-title" style="margin-top: 0.5rem;">Key Points</div>', unsafe_allow_html=True)
                    for i, point in enumerate(analysis["key_points"], 1):
                        conf = point.get("confidence", "")
                        badge = "🟢" if conf == "high" else "🟡" if conf == "medium" else "⚪"
                        st.markdown(f"""
                            <div class="key-point">
                                <div class="key-point-number">{i}</div>
                                <div class="key-point-text">{badge} {point.get('claim', 'N/A')}</div>
                            </div>
                        """, unsafe_allow_html=True)

                # Conclusion
                if analysis.get("conclusion"):
                    st.markdown(f"""
                        <div class="result-section">
                            <div class="result-section-title">Conclusion</div>
                            <div class="result-section-content">{analysis["conclusion"]}</div>
                        </div>
                    """, unsafe_allow_html=True)

            elif task_result and task_name == "Find Errors in Log":
                errors = task_result.get("errors", [])
                summary = task_result.get("summary", {})

                st.markdown(f"**{summary.get('total_matches', 0)}** matches found, **{summary.get('analyzed', 0)}** analyzed")

                for error in errors:
                    sev = error.get("severity", "info")
                    icon = "🔴" if sev == "critical" else "🟠" if sev == "warning" else "🔵"
                    st.markdown(f"""
                        <div class="result-section">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>{icon} <strong>Line {error.get('line', '?')}</strong></span>
                                <span style="color: #6B6B6B; font-size: 0.85rem; background: #F7F6F3;
                                             padding: 2px 8px; border-radius: 4px;">{error.get('category', '')}</span>
                            </div>
                            <div style="margin-top: 0.5rem; color: #6B6B6B;">{error.get('message', '')}</div>
                        </div>
                    """, unsafe_allow_html=True)

            elif task_result and task_name == "Extract Entities":
                entities = task_result.get("entities", {})
                for entity_type, items in entities.items():
                    if items:
                        st.markdown(f"""
                            <div class="result-section">
                                <div class="result-section-title">{entity_type}</div>
                                <div class="result-section-content">{', '.join(items)}</div>
                            </div>
                        """, unsafe_allow_html=True)

            # Raw JSON
            with st.expander("View Raw JSON"):
                st.json(result)

        else:
            st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-icon">✦</div>
                    <div class="empty-state-text">Enter text and click Run to analyze</div>
                </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
