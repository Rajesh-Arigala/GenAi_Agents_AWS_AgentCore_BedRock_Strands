# AgentCore Meal Planner UI

Render-ready frontend for the live AWS Bedrock AgentCore meal planner runtime.

## Runtime Flow

Browser UI posts to the Flask API. The API invokes the live AgentCore Runtime ARN with `boto3.client("bedrock-agentcore").invoke_agent_runtime(...)`.

```text
Browser -> Render Flask API -> AWS Bedrock AgentCore Runtime -> Strands meal planner -> AgentCore Memory + tools
```

## Required Render Environment Variables

Set these in Render before deploying:

```text
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:825187895465:runtime/meal_planner_agent-8GOBzZCg4S
AGENT_RUNTIME_QUALIFIER=DEFAULT
MOCK_AGENTCORE=false
```

The AWS identity needs permission for `bedrock-agentcore:InvokeAgentRuntime` on the runtime ARN.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
MOCK_AGENTCORE=true python app.py
```

Open `http://127.0.0.1:8000`.

## Render Deploy

1. Push this folder to GitHub.
2. Create a new Render Web Service from the repo.
3. Use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Add the environment variables above.
5. Deploy.
