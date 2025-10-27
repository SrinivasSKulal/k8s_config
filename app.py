import streamlit as st
from main import run_scan, auto_fix_file, get_corrected_yaml_content

st.set_page_config(page_title="K8s Config Checker", page_icon="🧠", layout="centered")

st.title("🧠 Kubernetes Config Checker & AutoFix Tool")
st.caption(
    "Powered by Groq | Analyze, fix, and improve Kubernetes YAML files automatically."
)

uploaded_file = st.file_uploader(
    "📤 Upload your Kubernetes YAML file", type=["yaml", "yml"]
)

if uploaded_file:
    # Save uploaded file
    file_path = f"uploaded_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    st.success(f"✅ File `{uploaded_file.name}` uploaded successfully!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Analyze Config"):
            with st.spinner("Analyzing configuration with Groq..."):
                report = run_scan(file_path)
            st.subheader("🧾 Analysis Report")
            st.text_area("Results", report, height=300)

    with col2:
        if st.button("🛠️ Auto Fix Config"):
            with st.spinner("Fixing configuration..."):
                output_path = auto_fix_file(file_path)
                fixed_content = get_corrected_yaml_content(output_path)

            st.subheader("✅ Corrected YAML Configuration")
            st.code(fixed_content, language="yaml")

            # Download button
            st.download_button(
                label="⬇️ Download Fixed YAML",
                data=fixed_content,
                file_name="corrected.yaml",
                mime="text/yaml",
            )
