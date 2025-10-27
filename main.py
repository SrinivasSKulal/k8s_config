import os
import yaml
import sys
import re
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def check_config(obj, file_path):
    """Performs rule-based scanning for common Kubernetes misconfigurations."""
    issues = []
    kind = obj.get("kind", "Unknown")
    metadata = obj.get("metadata", {})
    spec = obj.get("spec", {})

    containers = []
    if "containers" in spec:
        containers = spec["containers"]
    elif "template" in spec and "spec" in spec["template"]:
        containers = spec["template"]["spec"].get("containers", [])

    for c in containers:
        name = c.get("name", "unknown-container")
        resources = c.get("resources", {})
        if "limits" not in resources or "requests" not in resources:
            issues.append(
                {
                    "severity": "Medium",
                    "message": f"{file_path} [{kind}/{metadata.get('name', '')}] Container '{name}' missing resource requests/limits",
                    "snippet": yaml.dump(c),
                }
            )

        security = c.get("securityContext", {})
        if security.get("privileged", False):
            issues.append(
                {
                    "severity": "High",
                    "message": f"{file_path} [{kind}/{metadata.get('name', '')}] Container '{name}' runs as privileged",
                    "snippet": yaml.dump(c),
                }
            )

        if security.get("runAsUser", 0) == 0:
            issues.append(
                {
                    "severity": "High",
                    "message": f"{file_path} [{kind}/{metadata.get('name', '')}] Container '{name}' runs as root user",
                    "snippet": yaml.dump(c),
                }
            )

        image = c.get("image", "")
        if ":latest" in image or image.endswith(":"):
            issues.append(
                {
                    "severity": "Low",
                    "message": f"{file_path} [{kind}/{metadata.get('name', '')}] Container '{name}' uses 'latest' image tag",
                    "snippet": yaml.dump(c),
                }
            )

    if kind == "Service" and "namespace" not in metadata:
        issues.append(
            {
                "severity": "Low",
                "message": f"{file_path} [Service/{metadata.get('name', '')}] has no namespace specified",
                "snippet": yaml.dump(obj),
            }
        )

    if kind == "Service":
        svc_type = spec.get("type", "ClusterIP")
        if svc_type in ["LoadBalancer", "NodePort"]:
            issues.append(
                {
                    "severity": "High",
                    "message": f"{file_path} [Service/{metadata.get('name', '')}] uses {svc_type}, which may expose workloads externally",
                    "snippet": yaml.dump(obj),
                }
            )

    if kind in ["Role", "ClusterRole"]:
        rules = spec.get("rules", [])
        for rule in rules:
            verbs = rule.get("verbs", [])
            resources = rule.get("resources", [])
            if "*" in verbs or "*" in resources:
                issues.append(
                    {
                        "severity": "High",
                        "message": f"{file_path} [{kind}/{metadata.get('name', '')}] has overly permissive RBAC rule: verbs={verbs}, resources={resources}",
                        "snippet": yaml.dump(rule),
                    }
                )

    return issues


def clean_yaml_response(response_text):
    """Extract and clean YAML content from AI response."""
    # Remove markdown code blocks
    response_text = re.sub(r"^```ya?ml\s*\n", "", response_text, flags=re.MULTILINE)
    response_text = re.sub(r"\n```\s*$", "", response_text)
    response_text = re.sub(r"^```\s*\n", "", response_text, flags=re.MULTILINE)
    response_text = re.sub(r"\n```\s*$", "", response_text)

    # Remove any leading/trailing whitespace
    return response_text.strip()


def ai_fix_suggestion(snippet, message, full=False):
    """Generate AI-based fix suggestions or YAML corrections using Groq."""
    if full:
        prompt = f"""
You are a Kubernetes expert. Fix the following misconfigured YAML based on the issue:
Issue: {message}
YAML:
{snippet}

Return ONLY the corrected YAML manifest with the fix applied. Do not include any explanations or markdown formatting.
"""
    else:
        prompt = f"""
You are a Kubernetes configuration expert.
Analyze this YAML snippet and issue:
Issue: {message}
YAML:
{snippet}

Provide a short, clear one-line fix suggestion.
"""

    try:
        response = client.chat.completions.create(
            model="groq/compound",  # Using a more reliable model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(AI unavailable: {e})"


def scan_file(file_path):
    """Parse and analyze a single YAML file."""
    issues = []
    try:
        with open(file_path, "r") as f:
            docs = yaml.safe_load_all(f)
            for obj in docs:
                if obj:
                    issues.extend(check_config(obj, file_path))
    except Exception as e:
        issues.append(
            {
                "severity": "Low",
                "message": f"Error parsing {file_path}: {e}",
                "snippet": "",
            }
        )
    return issues


def scan_directory(path):
    """Scan all YAML files in a directory."""
    all_issues = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith((".yml", ".yaml")):
                full_path = os.path.join(root, file)
                all_issues.extend(scan_file(full_path))
    return all_issues


def run_scan(path):
    """Run scanner on a directory or single file."""
    if os.path.isdir(path):
        return scan_directory(path)
    else:
        return scan_file(path)


def generate_html_report(issues, output_file="k8s_ai_report.html"):
    """Generate a styled HTML report for results."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Kubernetes Config Audit (AI Enhanced)</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 20px; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background: #0078D4; color: white; }
            tr:nth-child(even) { background: #f9f9f9; }
            .severity-High { color: red; font-weight: bold; }
            .severity-Medium { color: orange; font-weight: bold; }
            .severity-Low { color: teal; font-weight: bold; }
        </style>
    </head>
    <body>
    <div class="container">
    <h1>🚀 Kubernetes Configuration Security Report (AI Enhanced)</h1>
    <table>
        <tr><th>Severity</th><th>Message</th><th>AI Suggestion</th></tr>
    """

    for issue in issues:
        suggestion = ai_fix_suggestion(issue.get("snippet", ""), issue["message"])
        html += f"""
        <tr>
            <td class="severity-{issue["severity"]}">{issue["severity"]}</td>
            <td>{issue["message"]}</td>
            <td>{suggestion}</td>
        </tr>
        """

    html += "</table></div></body></html>"

    with open(output_file, "w") as f:
        f.write(html)

    return output_file


def auto_fix_files(path):
    """Automatically apply AI corrections and write *_fixed.yaml files."""
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".yml", ".yaml")) and not file.endswith(
                    "_fixed.yaml"
                ):
                    full_path = os.path.join(root, file)
                    auto_fix_file(full_path)
    else:
        auto_fix_file(path)


def auto_fix_file(file_path):
    """Apply AI corrections to a single YAML file."""
    print(f"\n🤖 Auto-fixing: {file_path}")
    try:
        with open(file_path, "r") as f:
            original = f.read()

        prompt = f"""You are a Kubernetes security expert. Review and correct this YAML configuration to follow best practices:

1. Add resource requests and limits if missing
2. Ensure containers don't run as root (add runAsNonRoot: true, runAsUser: 1000)
3. Remove privileged: true if present
4. Use specific image tags instead of 'latest'
5. Add appropriate namespaces
6. Fix overly permissive RBAC rules

IMPORTANT: Return ONLY the corrected YAML without any explanations, comments, or markdown formatting.

Original YAML:
{original}
"""

        response = client.chat.completions.create(
            model="groq/compound",  # More reliable for structured output
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
        )

        fixed_yaml = clean_yaml_response(response.choices[0].message.content)

        # Validate that the output is valid YAML
        try:
            yaml.safe_load_all(fixed_yaml)
            print("✓ YAML validation passed")
        except yaml.YAMLError as e:
            print(f"⚠️ Warning: Generated YAML may have issues: {e}")
            print("Attempting to save anyway...")

        # Determine output path
        base, ext = os.path.splitext(file_path)
        new_path = f"{base}_fixed{ext}"

        with open(new_path, "w") as out:
            out.write(fixed_yaml)

        print(f"✅ Fixed file saved: {new_path}")

        # Show a preview of changes
        print("\n📝 Preview of fixed content (first 15 lines):")
        print("-" * 60)
        for i, line in enumerate(fixed_yaml.split("\n")[:15], 1):
            print(line)
        if len(fixed_yaml.split("\n")) > 15:
            print("...")
        print("-" * 60)

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        import traceback

        print(traceback.format_exc())


def get_corrected_yaml_content(file_content: str) -> str:
    """Return the corrected YAML content as a string (for Streamlit display)."""
    try:
        prompt = f"""You are a Kubernetes security expert. Review and correct this YAML configuration to follow best practices:

1. Add resource requests and limits if missing
2. Ensure containers don't run as root (add runAsNonRoot: true, runAsUser: 1000)
3. Remove privileged: true if present
4. Use specific image tags instead of 'latest'
5. Add appropriate namespaces
6. Fix overly permissive RBAC rules

IMPORTANT: Return ONLY the corrected YAML without any explanations, comments, or markdown formatting.

Original YAML:
{file_content}
"""

        response = client.chat.completions.create(
            model="groq/compound",  # More reliable for structured output
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
        )

        fixed_yaml = clean_yaml_response(response.choices[0].message.content)
        return fixed_yaml
    except Exception as e:
        return f"⚠️ Unable to read corrected file: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python k8s_ai_autofix_checker.py <path> [--autofix]")
        sys.exit(1)

    scan_path = sys.argv[1]
    autofix = "--autofix" in sys.argv

    print(f"🔍 Scanning {scan_path} ...")
    issues = run_scan(scan_path)

    if not issues:
        print("✅ No issues found.")
    else:
        print(f"⚠️ Found {len(issues)} issues. Generating report...")
        report = generate_html_report(issues)
        print(f"📄 Report saved as: {os.path.abspath(report)}")

    if autofix:
        print("\n🤖 Running AI-powered autofix...")
        auto_fix_files(scan_path)
        print("\n🎯 Auto-fix completed.")
