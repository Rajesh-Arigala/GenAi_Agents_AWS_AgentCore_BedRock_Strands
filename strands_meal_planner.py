from strands import Agent, tool
from strands_tools import calculator
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import requests
import boto3
from datetime import datetime

app = BedrockAgentCoreApp()

# ─────────────────────────────────────────────────────────────
# CONFIGURATION — memory_id hardcoded at deploy time
# ─────────────────────────────────────────────────────────────
region    = boto3.Session().region_name
MEMORY_ID = "mealPlannerMemory-fMBfEU2NEF"

agentcore_data = boto3.client("bedrock-agentcore", region_name=region)


# ─────────────────────────────────────────────────────────────
# MEMORY HELPERS
# ─────────────────────────────────────────────────────────────
def retrieve_preferences(user_id: str, query: str) -> str:
    if not MEMORY_ID:
        return ""
    try:
        response = agentcore_data.retrieve_memory_records(
            memoryId=MEMORY_ID,
            namespace=f"/users/{user_id}/preferences/",
            searchCriteria={"searchQuery": query, "topK": 5}
        )
        records = response.get("memoryRecordSummaries", [])
        return "\n".join(
            f"  - {r['content']['text']}"
            for r in records
            if r.get("content", {}).get("text")
        )
    except Exception as e:
        print(f"Memory retrieve warning: {e}")
        return ""


def save_interaction(user_id: str, session_id: str, user_msg: str, agent_msg: str):
    if not MEMORY_ID:
        return
    try:
        agentcore_data.create_event(
            memoryId=MEMORY_ID,
            actorId=user_id,
            sessionId=session_id,
            eventTimestamp=datetime.now(),
            payload=[
                {"conversational": {"content": {"text": user_msg},  "role": "USER"}},
                {"conversational": {"content": {"text": agent_msg}, "role": "ASSISTANT"}}
            ]
        )
    except Exception as e:
        print(f"Memory save warning: {e}")


# ─────────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────────
@tool
def search_recipe(dish: str) -> str:
    """Search for a recipe by dish name using TheMealDB API"""
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={dish}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not data.get("meals"):
            return f"No recipe found for '{dish}'"
        meal = data["meals"][0]
        ingredients = []
        for i in range(1, 21):
            ing     = meal.get(f"strIngredient{i}", "").strip()
            measure = meal.get(f"strMeasure{i}", "").strip()
            if ing:
                ingredients.append(f"  - {measure} {ing}".strip())
        return (
            f"Recipe: {meal['strMeal']}\n"
            f"Category: {meal['strCategory']}  |  Cuisine: {meal['strArea']}\n\n"
            f"Ingredients:\n" + "\n".join(ingredients) +
            f"\n\nInstructions:\n{meal['strInstructions'][:700]}..."
        )
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_meals_by_category(category: str) -> str:
    """Get meal ideas by category.
    Categories: Beef, Chicken, Dessert, Lamb, Pasta, Pork, Seafood, Vegan, Vegetarian, Breakfast"""
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not data.get("meals"):
            return f"No meals found for '{category}'"
        meals = [m["strMeal"] for m in data["meals"][:6]]
        return f"Popular {category} dishes:\n" + "\n".join(f"  * {m}" for m in meals)
    except Exception as e:
        return f"Error: {str(e)}"


# ─────────────────────────────────────────────────────────────
# MODEL — Amazon Nova 2 Lite
# ─────────────────────────────────────────────────────────────
BASE_SYSTEM_PROMPT = """You are a warm, friendly personal meal planner and recipe assistant.
You help users discover delicious recipes, suggest meals based on their dietary needs,
and can scale recipes for different serving sizes using the calculator tool.
Always be respectful of dietary restrictions and allergies."""

model = BedrockModel(model_id="global.amazon.nova-2-lite-v1:0")


# ─────────────────────────────────────────────────────────────
# AGENTCORE ENTRYPOINT
# ─────────────────────────────────────────────────────────────
@app.entrypoint
def meal_planner_agent(payload):
    user_id    = payload.get("user_id", "defaultUser")
    user_input = payload.get("prompt")
    session_id = payload.get("session_id", f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}")

    print(f"User: {user_id} | Session: {session_id}")

    preferences = retrieve_preferences(user_id, user_input)
    if preferences:
        system_prompt = BASE_SYSTEM_PROMPT + f"\n\nIMPORTANT - Known user preferences:\n{preferences}"
    else:
        system_prompt = BASE_SYSTEM_PROMPT

    agent = Agent(
        model=model,
        tools=[search_recipe, get_meals_by_category, calculator],
        system_prompt=system_prompt
    )
    response = agent(user_input)
    result   = response.message["content"][0]["text"]

    save_interaction(user_id, session_id, user_input, result)
    return result


if __name__ == "__main__":
    app.run()
