import streamlit as st
from main import run_scan, auto_fix_file

st.set_page_config(
    page_title="Kubernetes AI Config Checker", page_icon="📝", layout="centered"
)

st.title("Kubernetes AI Config Checker")
st.write(
    "Upload a Kubernetes YAML file, and let AI detect and fix issues automatically!"
)

uploaded_file = st.file_uploader("📁 Upload your Kubernetes YAML", type=["yaml", "yml"])

autofix = st.checkbox("Enable Auto-Fix with Groq AI", value=False)

if uploaded_file:
    yaml_text = uploaded_file.read().decode("utf-8")
    st.subheader("📄 File Content")
    st.code(yaml_text, language="yaml")

    with st.spinner("Scanning configuration..."):
        issues = run_scan(yaml_text)

    if issues:
        st.subheader("🚨 Detected Issues")
        for issue in issues:
            color = (
                "red"
                if issue["severity"] == "High"
                else "orange"
                if issue["severity"] == "Medium"
                else "blue"
            )
            st.markdown(
                f"- <span style='color:{color};font-weight:bold'>[{issue['severity']}]</span> {issue['message']}",
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ No issues found!")

    if autofix:
        st.subheader("🤖 Auto-Fixed YAML (AI Suggested)")
        with st.spinner("Using Groq AI to fix issues..."):
            fixed_yaml = auto_fix_file(yaml_text)
        st.code(fixed_yaml, language="yaml")

        st.download_button(
            "⬇️ Download Fixed YAML", fixed_yaml, file_name="fixed_config.yaml"
        )
