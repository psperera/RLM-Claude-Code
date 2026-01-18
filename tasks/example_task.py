"""
Example RLM Task: Document Analysis

Demonstrates the two-phase RLM pattern:
1. Programmatic narrowing: Code searches and slices context
2. Semantic interpretation: LLM reasons on bounded chunks

This task finds and analyzes key sections in a document.
"""

from __future__ import annotations

from rlm.context_access import (
    context_head,
    context_tail,
    context_search,
    context_slice,
    context_around_match,
)
from rlm.subcalls import (
    semantic_subcall,
    semantic_subcall_json,
    semantic_subcall_choice,
)


def analyze_document(context: str) -> dict:
    """
    Analyze a document to extract key information.

    This demonstrates the RLM pattern:
    - Phase 1: Programmatically narrow to relevant sections
    - Phase 2: Semantic interpretation on bounded chunks
    - Aggregation: Python constructs the final result

    Args:
        context: The full document text (NOT loaded into any prompt)

    Returns:
        Structured analysis with title, summary, key_points, and metadata
    """

    # =========================================================================
    # PHASE 1: Programmatic Narrowing
    # Code navigates context, identifies relevant regions
    # =========================================================================

    findings = {
        "document_length": len(context),
        "title": None,
        "abstract": None,
        "key_points": [],
        "conclusion": None,
        "document_type": None,
    }

    # --- Extract potential title from head ---
    # First 500 chars likely contain title/heading
    head_chunk = context_head(context, 500)

    # --- Search for key structural elements ---
    # Find section markers to understand document structure
    section_matches = context_search(
        context,
        r"(abstract|introduction|summary|conclusion|results|discussion)",
        max_hits=10,
    )

    # --- Find key claims or important statements ---
    claim_matches = context_search(
        context,
        r"(conclude|finding|result|important|significant|key|critical)",
        max_hits=5,
    )

    # =========================================================================
    # PHASE 2: Semantic Interpretation
    # LLM reasons on bounded chunks (depth=1, no recursion)
    # =========================================================================

    # --- Extract title from head ---
    findings["title"] = semantic_subcall(
        "Extract the document title or main heading from this text. "
        "Return ONLY the title text, nothing else. "
        "If no clear title exists, return 'Untitled Document'.",
        head_chunk,
    ).strip()

    # --- Classify document type ---
    findings["document_type"] = semantic_subcall_choice(
        "What type of document is this based on the opening?",
        head_chunk,
        choices=["research_paper", "report", "article", "documentation", "other"],
        default="other",
    )

    # --- Extract abstract if present ---
    abstract_matches = [m for m in section_matches if "abstract" in m.text.lower()]
    if abstract_matches:
        abstract_chunk = context_around_match(context, abstract_matches[0], before=50, after=1000)
        findings["abstract"] = semantic_subcall(
            "Extract the abstract or summary section from this text. "
            "Return only the abstract content, not the heading.",
            abstract_chunk,
        ).strip()

    # --- Extract key points from claim statements ---
    for match in claim_matches[:3]:  # Bounded: max 3 key points
        chunk = context_around_match(context, match, before=100, after=200)
        point = semantic_subcall_json(
            "Extract the key claim or finding from this text. "
            "Return JSON: {\"claim\": \"the main claim\", \"confidence\": \"high|medium|low\"}",
            chunk,
            default={"claim": "Unable to extract", "confidence": "low"},
        )
        findings["key_points"].append({
            "position": match.start,
            "line": match.line_number,
            **point,
        })

    # --- Extract conclusion from tail ---
    tail_chunk = context_tail(context, 1500)
    findings["conclusion"] = semantic_subcall(
        "Extract the main conclusion or final takeaway from this text. "
        "Summarize in 1-2 sentences. If no clear conclusion, state that.",
        tail_chunk,
    ).strip()

    # =========================================================================
    # AGGREGATION: Python constructs final result
    # No LLM call to "summarize everything"
    # =========================================================================

    return {
        "analysis": findings,
        "metadata": {
            "sections_found": len(section_matches),
            "claims_analyzed": len(findings["key_points"]),
            "has_abstract": findings["abstract"] is not None,
        },
    }


def find_errors_in_log(context: str) -> dict:
    """
    Example task: Find and classify errors in a log file.

    Demonstrates bounded iteration with early termination.

    Args:
        context: Log file content

    Returns:
        Categorized error analysis
    """

    # Phase 1: Programmatic narrowing
    error_matches = context_search(
        context,
        r"(error|exception|failed|fatal|critical)",
        max_hits=10,  # Hard limit on iterations
    )

    # Phase 2: Semantic interpretation (bounded)
    errors = []
    for match in error_matches[:5]:  # Process at most 5
        chunk = context_around_match(context, match, before=100, after=200)

        classification = semantic_subcall_json(
            "Classify this error. Return JSON: "
            "{\"severity\": \"critical|warning|info\", "
            "\"category\": \"network|database|auth|validation|other\", "
            "\"message\": \"brief description\"}",
            chunk,
            default={"severity": "info", "category": "other", "message": "Unknown error"},
        )

        errors.append({
            "position": match.start,
            "line": match.line_number,
            "matched_text": match.text,
            **classification,
        })

    # Aggregation in Python
    severity_counts = {}
    for error in errors:
        sev = error.get("severity", "info")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "errors": errors,
        "summary": {
            "total_matches": len(error_matches),
            "analyzed": len(errors),
            "by_severity": severity_counts,
        },
    }


def extract_entities(context: str) -> dict:
    """
    Example task: Extract named entities from document.

    Demonstrates chunked processing with overlap.

    Args:
        context: Document text

    Returns:
        Extracted entities by type
    """
    from rlm.context_access import context_chunks

    all_entities = {
        "people": [],
        "organizations": [],
        "locations": [],
        "dates": [],
    }

    # Process in chunks (bounded iteration)
    chunks_processed = 0
    max_chunks = 5  # Hard limit

    for start, end, chunk in context_chunks(context, chunk_size=2000, overlap=100):
        if chunks_processed >= max_chunks:
            break

        entities = semantic_subcall_json(
            "Extract named entities from this text. Return JSON: "
            "{\"people\": [...], \"organizations\": [...], "
            "\"locations\": [...], \"dates\": [...]}",
            chunk,
            default={"people": [], "organizations": [], "locations": [], "dates": []},
        )

        # Aggregate (Python handles deduplication)
        for entity_type in all_entities:
            for entity in entities.get(entity_type, []):
                if entity not in all_entities[entity_type]:
                    all_entities[entity_type].append(entity)

        chunks_processed += 1

    return {
        "entities": all_entities,
        "metadata": {
            "chunks_processed": chunks_processed,
            "document_length": len(context),
        },
    }
