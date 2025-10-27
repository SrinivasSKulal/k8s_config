import os
import yaml
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_scan(file_path: str) -> str:
    """Read and analyze a Kubernetes YAML configuration."""
    with open(file_path, "r") as f:
        content = f.read()

    prompt = f"""
    Analyze the following Kubernetes configuration and identify potential issues,
    security risks, or best-practice violations. Assign a severity level
    (Low, Medium, High, Critical) for each problem.

    Configuration:
    {content}
    """

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def auto_fix_file(file_path: str, output_path: str = "corrected.yaml") -> str:
    """Automatically fix the configuration file using Groq."""
    with open(file_path, "r") as f:
        content = f.read()

    prompt = f"""
    You are a Kubernetes configuration expert. Fix the following YAML configuration
    by correcting any errors, misconfigurations, or missing best practices.
    Ensure valid syntax and maintain the structure.

    Input YAML:
    {content}

    Return only the corrected YAML configuration.
    """

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )

    fixed_yaml = response.choices[0].message.content.strip()

    with open(output_path, "w") as f:
        f.write(fixed_yaml)

    return output_path


def get_corrected_yaml_content(file_path: str) -> str:
    """Return the corrected YAML content as a string (for Streamlit display)."""
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"⚠️ Unable to read corrected file: {e}"
