from strands import Agent, tool
from strands_tools import calculator
from strands.models import BedrockModel
import requests
import json
import argparse

# ─────────────────────────────────────────────────────────────
# TOOL 1: Search a recipe by dish name
# Uses TheMealDB — completely free, no API key needed
# ─────────────────────────────────────────────────────────────
@tool
def search_recipe(dish: str) -> str:
    """Search for a recipe by dish name using TheMealDB API"""
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={dish}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if not data.get('meals'):
            return f"No recipe found for '{dish}'. Try a different name."

        meal = data['meals'][0]

        # Build ingredients list from the 20 possible ingredient slots
        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f'strIngredient{i}', '').strip()
            measure = meal.get(f'strMeasure{i}', '').strip()
            if ing:
                ingredients.append(f"  - {measure} {ing}".strip())

        return (
            f"Recipe: {meal['strMeal']}\n"
            f"Category: {meal['strCategory']}  |  Cuisine: {meal['strArea']}\n\n"
            f"Ingredients:\n" + "\n".join(ingredients) +
            f"\n\nInstructions:\n{meal['strInstructions'][:700]}..."
        )
    except requests.RequestException as e:
        return f"Error fetching recipe: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 2: Browse meals by food category
# ─────────────────────────────────────────────────────────────
@tool
def get_meals_by_category(category: str) -> str:
    """Get meal ideas by category.
    Available: Beef, Chicken, Dessert, Lamb, Pasta, Pork,
    Seafood, Side, Starter, Vegan, Vegetarian, Breakfast, Goat"""
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if not data.get('meals'):
            return f"No meals found for category '{category}'. Check the category name."

        meals = [m['strMeal'] for m in data['meals'][:6]]
        return f"Popular {category} dishes:\n" + "\n".join(f"  • {m}" for m in meals)
    except requests.RequestException as e:
        return f"Error fetching category: {str(e)}"


# ─────────────────────────────────────────────────────────────
# AGENT SETUP — Amazon Nova 2 Lite via Amazon Bedrock
# ─────────────────────────────────────────────────────────────
model_id = "global.amazon.nova-2-lite-v1:0"
model = BedrockModel(model_id=model_id)

agent = Agent(
    model=model,
    tools=[search_recipe, get_meals_by_category, calculator],
    system_prompt="""You are a warm, friendly personal meal planner and recipe assistant.
You help users discover delicious recipes, suggest meals based on their dietary needs,
and can scale recipes for different serving sizes using the calculator tool.
Always be respectful of dietary restrictions and allergies.
Suggest alternatives when a dish does not fit the user's needs."""
)


def meal_planner(payload: dict) -> str:
    user_input = payload.get("prompt")
    response = agent(user_input)
    return response.message['content'][0]['text']


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=str)
    args = parser.parse_args()
    result = meal_planner(json.loads(args.payload))
    print(result)
