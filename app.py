import streamlit as st
from main import run_scan, auto_fix_file, get_corrected_yaml_content
import yaml

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(
    page_title="Kubernetes AI Config Checker",
    page_icon="🧠",
    layout="wide",
)

# ---------------------- HEADER ----------------------
st.title("🧠 Kubernetes AI Configuration Checker")
st.markdown(
    """
    This tool automatically **detects, classifies, and fixes** Kubernetes YAML misconfigurations.  
    It uses **rule-based validation** + **Groq-powered AI** for semantic auto-correction.
    """
)
st.divider()

# ---------------------- FILE UPLOAD ----------------------
uploaded_file = st.file_uploader("📁 Upload your Kubernetes YAML", type=["yaml", "yml"])

autofix = st.toggle("🤖 Enable Auto-Fix with Groq AI", value=False)

# ---------------------- MAIN LOGIC ----------------------
if uploaded_file:
    yaml_text = uploaded_file.read().decode("utf-8")

    st.subheader("📄 Uploaded YAML File")
    st.code(yaml_text, language="yaml")

    with st.spinner("🔍 Scanning configuration for misconfigurations..."):
        issues = run_scan(yaml_text)

    st.divider()

    # ---------------------- NO ISSUES FOUND ----------------------
    if not issues:
        st.success("✅ No issues found! Your configuration looks secure and compliant.")
    else:
        # ---------------------- ISSUE SUMMARY ----------------------
        st.subheader("🚨 Detected Issues Summary")

        high = sum(1 for i in issues if i["severity"] == "High")
        medium = sum(1 for i in issues if i["severity"] == "Medium")
        low = sum(1 for i in issues if i["severity"] == "Low")

        st.markdown(
            f"""
            **Summary:**  
            🟥 High: {high}  🟧 Medium: {medium}  🟦 Low: {low}
            """
        )

        st.divider()
        st.markdown("### ⚠️ Detailed Findings")

        # ---------------------- DETAILED ISSUE VIEW ----------------------
        for idx, issue in enumerate(issues, 1):
            sev = issue["severity"]
            msg = issue["message"]
            snippet = issue.get("snippet", "")

            color = (
                "red"
                if sev == "High"
                else "orange"
                if sev == "Medium"
                else "blue"
            )
            icon = "🟥" if sev == "High" else "🟧" if sev == "Medium" else "🟦"

            with st.expander(f"{icon} **[{sev}]** {msg}"):
                st.markdown(
                    f"<span style='color:{color};font-weight:bold;'>Severity: {sev}</span>",
                    unsafe_allow_html=True,
                )
                if snippet:
                    st.code(snippet, language="yaml")
                else:
                    st.info("No snippet available for this issue.")

        st.divider()

    # ---------------------- AUTO-FIX SECTION ----------------------
    if autofix:
        st.subheader("🤖 AI-Suggested Fixed YAML")
        with st.spinner("Generating corrected YAML using Groq AI..."):
            fixed_yaml = get_corrected_yaml_content(yaml_text)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📝 Original YAML**")
            st.code(yaml_text, language="yaml")

        with col2:
            st.markdown("**✅ Corrected YAML**")
            st.code(fixed_yaml, language="yaml")

        st.download_button(
            "⬇️ Download Fixed YAML",
            fixed_yaml,
            file_name="fixed_config.yaml",
            mime="text/yaml",
        )

    st.info("💡 Tip: You can disable Auto-Fix to just view detected issues.")
