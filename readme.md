# Kubernetes AI Configuration Checker & Auto-Fix Tool

An intelligent Kubernetes configuration scanner that uses AI to detect security misconfigurations and automatically fix them. Powered by Groq's fast inference API.

## Features

- 🔍 **Rule-Based Scanning** - Detects common Kubernetes misconfigurations
- 🤖 **AI-Powered Suggestions** - Get intelligent fix recommendations for each issue
- 🔧 **Auto-Fix Mode** - Automatically corrects configurations and generates fixed YAML files
- 📊 **HTML Reports** - Beautiful, styled reports with severity levels and AI suggestions
- 🚀 **Fast Processing** - Leverages Groq's lightning-fast inference

## Security Checks

The tool scans for:

- **Resource Management**: Missing CPU/memory requests and limits
- **Security Context**: Privileged containers and root user execution
- **Image Tags**: Usage of `latest` tag instead of specific versions
- **Service Exposure**: Risky LoadBalancer or NodePort configurations
- **RBAC Permissions**: Overly permissive Role/ClusterRole rules with wildcards
- **Namespace Configuration**: Missing namespace specifications

## Prerequisites

- Python 3.7+
- Groq API key (get one at [console.groq.com](https://console.groq.com))

## Installation

1. Clone or download the script

2. Install required dependencies:
```bash
pip install groq pyyaml python-dotenv
```

3. Create a `.env` file in the same directory:
```bash
GROQ_API_KEY=your_groq_api_key_here
```

## Usage

### Basic Scanning

Scan a single YAML file:
```bash
python main.py deployment.yaml
```

Scan an entire directory:
```bash
python main.py ./k8s-configs/
```

### Auto-Fix Mode

Automatically fix configurations and generate corrected files:
```bash
python main.py ./k8s-configs/ --autofix
```

This will:
- Scan all YAML files
- Generate an HTML report
- Create `*_fixed.yaml` versions of each file with AI-applied corrections

## Output

### HTML Report

The tool generates `k8s_ai_report.html` containing:
- All detected issues with severity levels (High/Medium/Low)
- Detailed messages about each misconfiguration
- AI-generated fix suggestions for each issue

**Severity Levels:**
- 🔴 **High**: Critical security issues (privileged containers, root users, RBAC wildcards, external exposure)
- 🟠 **Medium**: Resource management issues (missing limits/requests)
- 🔵 **Low**: Best practice violations (latest tags, missing namespaces)

### Fixed YAML Files

When using `--autofix`, corrected files are saved with the suffix `_fixed.yaml`:
- `deployment.yaml` → `deployment_fixed.yaml`
- `service.yml` → `service_fixed.yml`

## Example

```bash
# Scan and fix a directory
python main.py ./manifests/ --autofix

# Output:
🔍 Scanning ./manifests/ ...
⚠️ Found 8 issues. Generating report...
📄 Report saved as: /path/to/k8s_ai_report.html

🤖 Running AI-powered autofix...

🤖 Auto-fixing: ./manifests/deployment.yaml
✓ YAML validation passed
✅ Fixed file saved: ./manifests/deployment_fixed.yaml

📝 Preview of fixed content (first 15 lines):
------------------------------------------------------------
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
spec:
  replicas: 3
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: web
        image: nginx:1.21.0
...
------------------------------------------------------------

🎯 Auto-fix completed.
```

## AI Fixes Applied

The auto-fix feature applies best practices including:

1. **Resource Limits**: Adds CPU and memory requests/limits
2. **Security Context**: Sets `runAsNonRoot: true` and `runAsUser: 1000`
3. **Privilege Removal**: Removes `privileged: true` flags
4. **Image Tags**: Replaces `latest` with specific version tags
5. **Namespaces**: Adds appropriate namespace specifications
6. **RBAC**: Tightens overly permissive wildcard rules

## Configuration

The tool uses the `llama-3.3-70b-versatile` model from Groq for reliable YAML generation. You can modify the model in the code if needed:

```python
model="llama-3.3-70b-versatile"  # Change to another Groq model
```

## Limitations

- The tool provides AI-generated suggestions that should be reviewed by a human
- Auto-fix mode uses AI which may occasionally generate suboptimal configurations
- Always test fixed configurations in a development environment before production use
- YAML validation is performed, but semantic correctness should be manually verified

## Troubleshooting

**"AI unavailable" error:**
- Check your Groq API key in the `.env` file
- Ensure you have internet connectivity
- Verify your API key has available credits

**YAML validation warnings:**
- Review the generated YAML manually
- The tool will still save the file but may need manual correction

**No issues found:**
- Your configurations already follow best practices!
- Try running on different YAML files

## Contributing

Feel free to enhance the security checks or improve the AI prompts for better fix suggestions.

## License

This tool is provided as-is for educational and security improvement purposes.

## Acknowledgments

- Powered by [Groq](https://groq.com) for ultra-fast AI inference
- Built for Kubernetes security best practices
