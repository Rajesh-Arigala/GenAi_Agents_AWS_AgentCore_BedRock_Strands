# AWS Bedrock AgentCore - Environment Setup

This document describes the complete environment setup for developing AWS Bedrock AgentCore applications on macOS.

---

# Prerequisites

- macOS
- Python 3.13+
- Homebrew
- AWS Account
- AWS IAM User with Programmatic Access

---

# 1. Create a Virtual Environment

Never install AWS SDKs into the base Anaconda environment.

```bash
python3 -m venv .venv
```

Activate the virtual environment.

```bash
source .venv/bin/activate
```

---

# 2. Upgrade pip

```bash
pip install --upgrade pip
```

---

# 3. Install AWS SDK

```bash
pip install boto3
```

This installs compatible versions of:

- boto3
- botocore
- s3transfer

No manual installation of these packages is required.

---

# 4. Install AWS CLI

Install AWS CLI using Homebrew instead of pip.

```bash
brew install awscli
```

Verify installation.

```bash
aws --version
```

Example:

```text
aws-cli/2.x.x Python/3.x Darwin/arm64
```

---

# 5. Configure AWS Credentials

Configure your AWS account.

```bash
aws configure
```

Provide:

```
AWS Access Key ID
AWS Secret Access Key
Default Region
Output Format
```

Example:

```
Region : us-east-1
Output : json
```

---

# 6. Verify AWS Credentials

```bash
aws sts get-caller-identity
```

If configured correctly, AWS returns your:

- User ID
- AWS Account ID
- ARN

---

# 7. Install Bedrock Development Libraries

```bash
pip install \
boto3 \
langchain \
langchain-aws \
langgraph \
python-dotenv \
pydantic \
ipykernel
```

---

# 8. Install Amazon Bedrock AgentCore SDK

```bash
pip install \
bedrock-agentcore \
bedrock-agentcore-starter-toolkit
```

---

# 9. Verify boto3 Installation

```bash
python -c "import boto3; print(boto3.__version__)"
```

---

# 10. Verify botocore Installation

```bash
python -c "import botocore; print(botocore.__version__)"
```

---

# 11. Register Jupyter Kernel (Optional)

```bash
python -m ipykernel install \
--user \
--name=bedrock-agentcore \
--display-name="Python (Bedrock AgentCore)"
```

---

# Installed Packages

Core AWS

- boto3
- botocore
- awscli

LLM Frameworks

- langchain
- langchain-aws
- langgraph

AWS Agent SDK

- bedrock-agentcore
- bedrock-agentcore-starter-toolkit

Utilities

- python-dotenv
- pydantic
- ipykernel

---

# Recommended Project Structure

```
AgentCore_bedrock/
│
├── .venv/
├── notebooks/
├── src/
├── prompts/
├── agents/
├── tools/
├── .env
├── requirements.txt
└── README.md
```

---

# Generate requirements.txt

Freeze the environment for reproducibility.

```bash
pip freeze > requirements.txt
```

---

# Common Commands

Activate environment

```bash
source .venv/bin/activate
```

Deactivate environment

```bash
deactivate
```

Upgrade packages

```bash
pip install --upgrade pip
```

Check installed packages

```bash
pip list
```

Check AWS identity

```bash
aws sts get-caller-identity
```

Check AWS CLI version

```bash
aws --version
```

---

# Notes

- Use a dedicated virtual environment for each project.
- Install AWS CLI using Homebrew instead of pip.
- Install Python packages only inside the virtual environment.
- Store credentials securely using `aws configure`.
- Avoid modifying the global Anaconda base environment.