import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, jsonify, render_template, request


DEFAULT_AGENT_ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:825187895465:"
    "runtime/meal_planner_agent-8GOBzZCg4S"
)
DEFAULT_REGION = "us-east-1"

app = Flask(__name__)


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_config():
    return {
        "agent_arn": os.getenv("AGENT_RUNTIME_ARN", DEFAULT_AGENT_ARN),
        "aws_region": os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or DEFAULT_REGION,
        "qualifier": os.getenv("AGENT_RUNTIME_QUALIFIER", "DEFAULT"),
        "mock_mode": env_flag("MOCK_AGENTCORE", False),
    }


def decode_response_value(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return json.dumps(value)


def normalize_text(text):
    stripped = text.strip()
    if not stripped:
        return ""

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped

    if isinstance(parsed, str):
        return parsed
    if isinstance(parsed, dict):
        for key in ("response", "output", "result", "text", "message"):
            value = parsed.get(key)
            if isinstance(value, list) and value:
                return decode_response_value(value[0]).strip()
            if isinstance(value, str):
                return value.strip()
    if isinstance(parsed, list) and parsed:
        return decode_response_value(parsed[0]).strip()
    return stripped


def read_agentcore_response(response):
    content_type = response.get("contentType", "")
    body = response.get("response")
    chunks = []

    if body is None:
        return ""

    if "text/event-stream" in content_type and hasattr(body, "iter_lines"):
        for line in body.iter_lines(chunk_size=1):
            decoded = decode_response_value(line).strip()
            if decoded.startswith("data: "):
                chunks.append(decoded[6:])
            elif decoded:
                chunks.append(decoded)
        return normalize_text("".join(chunks))

    if hasattr(body, "iter_lines"):
        for line in body.iter_lines(chunk_size=1):
            chunks.append(decode_response_value(line))
        return normalize_text("".join(chunks))

    if isinstance(body, (str, bytes)):
        return normalize_text(decode_response_value(body))

    for event in body:
        if isinstance(event, dict):
            if "chunk" in event:
                raw = event["chunk"].get("bytes", b"")
                chunks.append(decode_response_value(raw))
            elif "bytes" in event:
                chunks.append(decode_response_value(event["bytes"]))
            else:
                chunks.append(json.dumps(event))
        else:
            chunks.append(decode_response_value(event))

    return normalize_text("".join(chunks))


def invoke_agentcore(prompt, user_id, session_id):
    config = get_config()

    if config["mock_mode"]:
        return {
            "answer": (
                "Mock AgentCore response: I would use AgentCore Memory for "
                f"{user_id}, route your prompt through the Strands meal planner, "
                "and return a recipe-aware answer here."
            ),
            "mode": "mock",
        }

    payload = {
        "prompt": prompt,
        "user_id": user_id,
        "session_id": session_id,
    }

    client = boto3.client("bedrock-agentcore", region_name=config["aws_region"])
    response = client.invoke_agent_runtime(
        agentRuntimeArn=config["agent_arn"],
        qualifier=config["qualifier"],
        payload=json.dumps(payload),
    )

    answer = read_agentcore_response(response)
    return {"answer": answer, "mode": "agentcore"}


@app.get("/")
def index():
    config = get_config()
    return render_template(
        "index.html",
        agent_arn=config["agent_arn"],
        aws_region=config["aws_region"],
        qualifier=config["qualifier"],
        mock_mode=config["mock_mode"],
        build_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


@app.get("/api/health")
def health():
    config = get_config()
    return jsonify(
        {
            "ok": True,
            "service": "agentcore-meal-planner-ui",
            "region": config["aws_region"],
            "qualifier": config["qualifier"],
            "mock_mode": config["mock_mode"],
        }
    )


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()
    user_id = str(data.get("user_id", "guest")).strip() or "guest"
    session_id = str(data.get("session_id", "")).strip() or f"session-{uuid.uuid4()}"

    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    try:
        result = invoke_agentcore(prompt, user_id, session_id)
    except (BotoCoreError, ClientError) as exc:
        return (
            jsonify(
                {
                    "error": "AgentCore Runtime invocation failed.",
                    "detail": str(exc),
                }
            ),
            502,
        )
    except Exception as exc:
        return jsonify({"error": "Unexpected server error.", "detail": str(exc)}), 500

    return jsonify(
        {
            "answer": result["answer"],
            "mode": result["mode"],
            "user_id": user_id,
            "session_id": session_id,
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
