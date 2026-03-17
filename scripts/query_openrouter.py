"""
Query GPT-3.5-turbo via OpenRouter to collect baby name recommendations.
This replicates what ChatGPT would have suggested around its Nov 2022 launch.
"""

import os
import json
import time
import requests
from collections import Counter
from pathlib import Path

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models by era - maps to different ChatGPT periods
MODELS = {
    "gpt-3.5-turbo": {
        "id": "openai/gpt-3.5-turbo",
        "launch": "2022-11-30",
        "description": "Original ChatGPT model"
    },
    "gpt-4": {
        "id": "openai/gpt-4",
        "launch": "2023-03-14",
        "description": "ChatGPT Plus with GPT-4"
    },
    "gpt-4-turbo": {
        "id": "openai/gpt-4-turbo",
        "launch": "2023-11-06",
        "description": "GPT-4 Turbo release"
    },
    "gpt-4o": {
        "id": "openai/gpt-4o",
        "launch": "2024-05-13",
        "description": "GPT-4o multimodal model"
    },
}
DEFAULT_MODEL = "gpt-3.5-turbo"

# Prompt battery - diverse ways people ask for baby names
PROMPTS = [
    # Basic requests
    "Suggest 10 baby names for a boy",
    "Suggest 10 baby names for a girl",
    "What are good baby names?",
    "I need help choosing a baby name",

    # Style-based
    "What are some unique baby names?",
    "What are classic baby names?",
    "Suggest modern baby names",
    "What are traditional baby names?",
    "Suggest trendy baby names for 2023",
    "What are timeless baby names?",

    # Gender-specific variations
    "What are popular boy names?",
    "What are popular girl names?",
    "Suggest unique boy names",
    "Suggest unique girl names",
    "What are strong names for a boy?",
    "What are elegant names for a girl?",

    # Origin-based
    "Suggest American baby names",
    "What are English baby names?",
    "Suggest biblical baby names",
    "What are nature-inspired baby names?",

    # Asking for lists
    "Give me a list of baby names",
    "What baby names are trending?",
    "What are the best baby names?",
    "Recommend some baby names for my child",
]

def query_openrouter(prompt: str, model_id: str, temperature: float = 0.8) -> str:
    """Send a single query to OpenRouter."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/chatgpt-names-study",
    }

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 500,
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]

def extract_names(text: str) -> list[str]:
    """Extract names from model response. Simple heuristic extraction."""
    import re

    names = []

    # Pattern 1: Numbered lists (1. Name, 2. Name)
    numbered = re.findall(r'\d+\.\s*\*?\*?([A-Z][a-z]+)', text)
    names.extend(numbered)

    # Pattern 2: Bullet points (- Name, * Name)
    bullets = re.findall(r'[-*]\s*\*?\*?([A-Z][a-z]+)', text)
    names.extend(bullets)

    # Pattern 3: Names in bold (**Name**)
    bold = re.findall(r'\*\*([A-Z][a-z]+)\*\*', text)
    names.extend(bold)

    # Pattern 4: Capitalized words that look like names (fallback)
    if not names:
        # Look for capitalized words 3-12 chars, not common words
        common_words = {'The', 'This', 'That', 'Here', 'Some', 'Baby', 'Name', 'Names', 'Boy', 'Girl', 'For', 'Are', 'What', 'Good', 'Best', 'Popular', 'Unique', 'Classic', 'Modern', 'Strong', 'Elegant'}
        caps = re.findall(r'\b([A-Z][a-z]{2,11})\b', text)
        names.extend([w for w in caps if w not in common_words])

    # Clean and dedupe while preserving order
    seen = set()
    clean_names = []
    for name in names:
        name_lower = name.lower()
        if name_lower not in seen and len(name) >= 2:
            seen.add(name_lower)
            # Capitalize properly
            clean_names.append(name.capitalize())

    return clean_names

def run_queries(num_iterations: int = 20, output_dir: Path = None, api_key: str = None, model: str = DEFAULT_MODEL):
    """Run all prompts multiple times and collect name frequencies."""
    global OPENROUTER_API_KEY
    if api_key:
        OPENROUTER_API_KEY = api_key
    if not OPENROUTER_API_KEY:
        print("ERROR: Set OPENROUTER_API_KEY environment variable")
        print("Get your key at: https://openrouter.ai/keys")
        return

    if model not in MODELS:
        print(f"ERROR: Unknown model '{model}'. Available: {list(MODELS.keys())}")
        return

    model_info = MODELS[model]
    model_id = model_info["id"]

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_names = Counter()

    total_queries = len(PROMPTS) * num_iterations
    query_count = 0

    # Open file for incremental writing
    responses_file = output_dir / f"chatgpt_responses_{model.replace('-', '_')}.jsonl"

    print(f"Model: {model} ({model_info['description']})")
    print(f"Launch date: {model_info['launch']}")
    print(f"Running {total_queries} queries ({len(PROMPTS)} prompts x {num_iterations} iterations)")
    print(f"Writing to: {responses_file}")
    print("-" * 50, flush=True)

    with open(responses_file, "w") as f:
        for iteration in range(num_iterations):
            for prompt in PROMPTS:
                query_count += 1
                print(f"[{query_count}/{total_queries}] {prompt[:40]}...", flush=True)

                try:
                    response = query_openrouter(prompt, model_id)
                    names = extract_names(response)

                    record = {
                        "model": model,
                        "model_id": model_id,
                        "model_launch": model_info["launch"],
                        "iteration": iteration,
                        "prompt": prompt,
                        "response": response,
                        "extracted_names": names,
                    }
                    # Write immediately
                    f.write(json.dumps(record) + "\n")
                    f.flush()

                    for name in names:
                        all_names[name] += 1

                    print(f"    Found {len(names)} names: {names[:5]}{'...' if len(names) > 5 else ''}", flush=True)

                except Exception as e:
                    print(f"    ERROR: {e}", flush=True)

                # Rate limiting
                time.sleep(0.5)

    print(f"\nSaved raw responses to: {responses_file}")

    # Save name frequencies (model-specific file)
    names_file = output_dir.parent / "processed" / f"chatgpt_names_{model.replace('-', '_')}.csv"
    names_file.parent.mkdir(parents=True, exist_ok=True)
    with open(names_file, "w") as f:
        f.write("name,frequency,model,model_launch\n")
        for name, count in all_names.most_common():
            f.write(f"{name},{count},{model},{model_info['launch']}\n")
    print(f"Saved name frequencies to: {names_file}")

    # Summary
    print("\n" + "=" * 50)
    print(f"Total unique names: {len(all_names)}")
    print(f"Total name mentions: {sum(all_names.values())}")
    print("\nTop 20 most recommended names:")
    for name, count in all_names.most_common(20):
        print(f"  {name}: {count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Query ChatGPT models for baby name recommendations")
    parser.add_argument("-n", "--iterations", type=int, default=20,
                        help="Number of iterations per prompt (default: 20)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)")
    parser.add_argument("-m", "--model", type=str, default=DEFAULT_MODEL,
                        choices=list(MODELS.keys()),
                        help=f"Model to query (default: {DEFAULT_MODEL})")
    parser.add_argument("--all-models", action="store_true",
                        help="Query all available models")
    args = parser.parse_args()

    if args.all_models:
        for model_name in MODELS.keys():
            print(f"\n{'='*60}")
            print(f"QUERYING MODEL: {model_name}")
            print(f"{'='*60}\n")
            run_queries(num_iterations=args.iterations, api_key=args.api_key, model=model_name)
    else:
        run_queries(num_iterations=args.iterations, api_key=args.api_key, model=args.model)
