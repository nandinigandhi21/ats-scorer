from typing import Optional
from datetime import datetime

import requests
import streamlit as st

from frontend.services import api_client
from frontend.components.dashboard import display_results_dashboard


def _read_jd(jd_file, jd_text: str) -> str:
    """
    Turn whatever the user provided into a plain JD string for the backend.

    For .txt files we decode in-process — that's a trivial operation, no need
    for a backend round-trip. For PDF/DOCX, we'd need the backend's parser;
    we don't have a public endpoint for that, so we ask the user to paste text
    instead for non-txt JDs.
    """
    if jd_text:
        return jd_text.strip()
    if jd_file is None:
        return ""
    if jd_file.name.lower().endswith(".txt"):
        return jd_file.getvalue().decode("utf-8", errors="ignore")
    st.warning(
        "Job description files must be `.txt` for now — paste the JD text instead "
        "if you have a PDF or DOCX."
    )
    return ""


def _show_backend_error(exc: Exception) -> None:
    """Translate a `requests` exception into a friendly Streamlit error."""
    if isinstance(exc, requests.ConnectionError):
        st.error("Could not reach the backend. Is `uvicorn backend.main:app` running on port 8000?")
    elif isinstance(exc, requests.Timeout):
        st.error("The backend took too long to respond. Try a smaller resume or check the server logs.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except ValueError:
            detail = exc.response.text
        st.error(f"Backend returned {exc.response.status_code}: {detail}")
    else:
        st.error(f"Unexpected error: {exc}")


def _summary_text(analysis: dict) -> str:
    """Detailed client-side text summary for the Download button."""
    score = analysis.get("ATS_score", analysis.get("ats_score", 0))
    interpretation = analysis.get("interpretation", "")
    
    lines = [
        "===========================================================",
        "                 ATS RESUME SCORER REPORT                  ",
        "===========================================================",
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        f"Overall ATS Score: {score:.1f}/100",
        f"Evaluation: {interpretation}",
        "",
        "-----------------------------------------------------------",
        "                      SCORE BREAKDOWN                      ",
        "-----------------------------------------------------------",
    ]
    
    cs = analysis.get("component_scores", {})
    if hasattr(cs, "model_dump"):
        cs = cs.model_dump()
    elif not isinstance(cs, dict):
        cs = cs.__dict__ if hasattr(cs, "__dict__") else {}
        
    lines.extend([
        f"- Formatting & Layout Structure: {cs.get('formatting', 0):.1f}/20",
        f"- Keyword Matching & Relevance:  {cs.get('keywords', 0):.1f}/25",
        f"- Content Quality & Impact:      {cs.get('content', 0):.1f}/25",
        f"- Skill Validation Evidence:     {cs.get('skill_validation', 0):.1f}/15",
        f"- ATS Technical Compatibility:   {cs.get('ats_compatibility', 0):.1f}/15",
        ""
    ])
    
    strengths = analysis.get("strengths") or []
    if strengths:
        lines.append("-----------------------------------------------------------")
        lines.append("                       KEY STRENGTHS                       ")
        lines.append("-----------------------------------------------------------")
        for s in strengths:
            lines.append(f"• {s}")
        lines.append("")
        
    critical = analysis.get("critical_issues") or []
    if critical:
        lines.append("-----------------------------------------------------------")
        lines.append("                      CRITICAL ISSUES                      ")
        lines.append("-----------------------------------------------------------")
        for c in critical:
            lines.append(f"• {c}")
        lines.append("")
        
    suggestions = analysis.get("suggestions") or []
    if suggestions:
        lines.append("-----------------------------------------------------------")
        lines.append("                   KEY AREAS TO IMPROVE                    ")
        lines.append("-----------------------------------------------------------")
        for s in suggestions:
            lines.append(f"• {s}")
        lines.append("")
        
    # Detailed feedback items
    raw_feedback = analysis.get("detailed_feedback") or []
    def to_dict(item):
        if isinstance(item, dict):
            return item
        return item.model_dump() if hasattr(item, 'model_dump') else item.__dict__
    detailed_feedback = [to_dict(fb) for fb in raw_feedback]
    
    if detailed_feedback:
        lines.append("-----------------------------------------------------------")
        lines.append("                DETAILED AUDIT RECOMMENDATIONS             ")
        lines.append("-----------------------------------------------------------")
        for fb in detailed_feedback:
            issue = fb.get("issue_title", fb.get("issue_description", ""))
            severity = fb.get("severity_level", "").upper()
            impact = fb.get("ats_impact", "")
            explanation = fb.get("explanation", "")
            fix = fb.get("how_to_fix", fb.get("suggestions", ""))
            example = fb.get("example_improvement", "")
            action_items = fb.get("action_items", [])
            
            lines.append(f"[{severity}] Issue: {issue}")
            if impact:
                lines.append(f"  ATS Impact: {impact}")
            if explanation:
                lines.append(f"  Explanation: {explanation}")
            if fix:
                lines.append(f"  Recommendation: {fix}")
            if example:
                lines.append(f"  Example of Improvement: {example}")
            if action_items:
                lines.append("  Action Items:")
                for item in action_items:
                    lines.append(f"    - {item}")
            lines.append("")
            
    # Skill validation
    svd = analysis.get("skill_validation_details") or {}
    if hasattr(svd, "model_dump"):
        svd = svd.model_dump()
    elif not isinstance(svd, dict):
        svd = svd.__dict__ if hasattr(svd, "__dict__") else {}
        
    if svd:
        lines.append("-----------------------------------------------------------")
        lines.append("                 AI SKILL VALIDATION ANALYSIS              ")
        lines.append("-----------------------------------------------------------")
        val_pct = svd.get("validation_pct", 0.0)
        lines.append(f"Skill Validation Rate: {val_pct:.1f}%")
        validated = svd.get("validated") or []
        unvalidated = svd.get("unvalidated") or []
        if validated:
            val_names = ", ".join(item.get("skill", "") for item in validated)
            lines.append(f"Demonstrated Skills: {val_names}")
        if unvalidated:
            unval_names = ", ".join(unvalidated)
            lines.append(f"Skills Lacking Evidence: {unval_names}")
        lines.append("")
        
    # JD comparison
    jd = analysis.get("jd_match_analysis") or analysis.get("jd_comparison") or {}
    if hasattr(jd, "model_dump"):
        jd = jd.model_dump()
    elif not isinstance(jd, dict):
        jd = jd.__dict__ if hasattr(jd, "__dict__") else {}
        
    if jd:
        lines.append("-----------------------------------------------------------")
        lines.append("                JOB DESCRIPTION MATCH ANALYSIS             ")
        lines.append("-----------------------------------------------------------")
        lines.append(f"JD Match Score: {jd.get('match_percentage', 0.0):.1f}%")
        lines.append(f"Semantic Similarity: {jd.get('semantic_similarity', 0.0):.2f}")
        
        matched = jd.get("matched_keywords") or []
        missing = jd.get("missing_keywords") or []
        gap = jd.get("skills_gap") or []
        
        if matched:
            lines.append(f"Matched Keywords: {', '.join(matched)}")
        if missing:
            lines.append(f"Missing Keywords to add: {', '.join(missing)}")
        if gap:
            lines.append(f"Skills Gap: {', '.join(gap)}")
        lines.append("")
        
    lines.append("===========================================================")
    lines.append("            END OF REPORT — CONFIDENTIAL DATA              ")
    lines.append("===========================================================")
    
    return "\n".join(lines)


def _render_upload_area(analysis_mode: str):
    """Two-column upload widgets. Returns (resume_file, jd_file, jd_text)."""
    left, right = st.columns(2)

    with left:
        st.markdown("### 📄 Upload Resume")
        resume_file = st.file_uploader(
            "Choose your resume file",
            type=["pdf", "doc", "docx"],
            help="Supported: PDF, DOC, DOCX (max 5 MB)",
            key="resume_upload",
        )
        if resume_file:
            st.success(f"✅ {resume_file.name} ({resume_file.size / 1024:.1f} KB)")

    jd_file: Optional[object] = None
    jd_text = ""

    with right:
        if analysis_mode == "Job Description Comparison":
            st.markdown("### 📋 Job Description")
            jd_method = st.radio(
                "Input method:",
                ["Paste Text", "Upload .txt File"],
                horizontal=True,
                key="jd_input_method",
            )
            if jd_method == "Upload .txt File":
                jd_file = st.file_uploader(
                    "Choose JD file (.txt only)",
                    type=["txt"],
                    key="jd_upload",
                )
                if jd_file:
                    st.success(f"✅ {jd_file.name}")
            else:
                jd_text = st.text_area(
                    "Paste job description text:",
                    height=200,
                    placeholder="Paste the JD here...",
                    key="jd_text",
                )
                if jd_text:
                    st.success(f"✅ {len(jd_text)} characters")
        else:
            st.markdown("### 📋 Job Description")
            st.info("Switch to 'Job Description Comparison' mode to enable JD matching.")

    return resume_file, jd_file, jd_text


def _render_export_buttons(analysis: dict) -> None:
    st.markdown("### 📥 Export Results")
    c1, c2 = st.columns(2)

    with c1:
        # Lazy: only call the backend the first time the user clicks expand.
        if st.button("📑 Generate PDF Report", use_container_width=True, type="primary"):
            try:
                with st.spinner("Generating PDF on backend..."):
                    pdf_bytes = api_client.generate_pdf(
                        analysis,
                        access_token=st.session_state["access_token"],
                    )
                st.session_state["scorer_pdf_bytes"] = pdf_bytes
            except requests.RequestException as exc:
                _show_backend_error(exc)

        if "scorer_pdf_bytes" in st.session_state:
            st.download_button(
                "⬇️ Download PDF",
                data=st.session_state["scorer_pdf_bytes"],
                file_name="ats_resume_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_report",
            )

    with c2:
        st.download_button(
            "📄 Download Summary (.txt)",
            data=_summary_text(analysis),
            file_name="ats_summary.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_summary",
        )


def render() -> None:
    st.title("🎯 ATS Resume Scorer")
    st.markdown("Upload your resume — and optionally a job description — for a comprehensive analysis.")

    with st.sidebar:
        st.markdown("---")
        st.markdown("## 📊 Analysis Options")
        st.info(
            "**General ATS Score**: resume only — overall compatibility.\n\n"
            "**JD Comparison**: resume + job description — targeted match analysis."
        )

    st.markdown("---")

    analysis_mode = st.radio(
        "Select Analysis Mode:",
        ["General ATS Score", "Job Description Comparison"],
        horizontal=True,
    )

    st.markdown("---")

    resume_file, jd_file, jd_text = _render_upload_area(analysis_mode)

    st.markdown("---")

    if not resume_file:
        st.info("👆 Upload your resume to begin.")
        # If we have a prior result in session, render it again.
        if st.session_state.get("scorer_analysis"):
            display_results_dashboard(st.session_state["scorer_analysis"])
        return

    access_token = st.session_state.get("access_token")
    if not access_token:
        st.warning("⚠️ Sign in from the sidebar to analyze a resume.")
        return

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        analyze = st.button("🚀 Analyze Resume", use_container_width=True, type="primary")

    if not analyze:
        # Re-show previous result on rerun (e.g. after PDF generation).
        if st.session_state.get("scorer_analysis"):
            display_results_dashboard(st.session_state["scorer_analysis"])
            _render_export_buttons(st.session_state["scorer_analysis"])
        return

    # Fresh analysis — drop any cached PDF/result.
    st.session_state.pop("scorer_pdf_bytes", None)
    st.session_state.pop("scorer_analysis", None)

    job_description = _read_jd(jd_file, jd_text) if analysis_mode == "Job Description Comparison" else ""

    try:
        with st.spinner("Analyzing your resume... this can take 10–30 seconds."):
            analysis = api_client.analyze_resume(
                resume_file=resume_file,
                access_token=access_token,
                job_description=job_description,
            )
    except requests.RequestException as exc:
        _show_backend_error(exc)
        return

    st.session_state["scorer_analysis"] = analysis
    st.success("✅ Analysis complete!")
    display_results_dashboard(analysis)
    _render_export_buttons(analysis)
