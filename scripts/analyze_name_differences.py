"""
Analyze differences between GPT-3.5 and GPT-4 recommendations,
and whether ChatGPT recommends Black names.
"""

import json
from collections import Counter
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"

# Load responses
def load_names(filepath):
    names = Counter()
    with open(filepath) as f:
        for line in f:
            rec = json.loads(line)
            for name in rec['extracted_names']:
                names[name] += 1
    return names

gpt35 = load_names(data_dir / "raw" / "chatgpt_responses_gpt_3.5_turbo.jsonl")
gpt4 = load_names(data_dir / "raw" / "chatgpt_responses_gpt_4.jsonl")

print("="*60)
print("MODEL COMPARISON: GPT-3.5 vs GPT-4")
print("="*60)

print(f"\nGPT-3.5: {len(gpt35)} unique names, {sum(gpt35.values())} mentions")
print(f"GPT-4:   {len(gpt4)} unique names, {sum(gpt4.values())} mentions")

# Overlap
both = set(gpt35.keys()) & set(gpt4.keys())
only_35 = set(gpt35.keys()) - set(gpt4.keys())
only_4 = set(gpt4.keys()) - set(gpt35.keys())

print(f"\nOverlap: {len(both)} names in both")
print(f"Only GPT-3.5: {len(only_35)} names")
print(f"Only GPT-4: {len(only_4)} names")
print(f"Jaccard similarity: {len(both) / len(set(gpt35.keys()) | set(gpt4.keys())):.2%}")

# Top names comparison
print("\n" + "-"*60)
print("TOP 20 NAMES BY MODEL")
print("-"*60)
print(f"{'Rank':<6} {'GPT-3.5':<20} {'GPT-4':<20}")
print("-"*60)
top35 = gpt35.most_common(20)
top4 = gpt4.most_common(20)
for i in range(20):
    n35 = f"{top35[i][0]} ({top35[i][1]})" if i < len(top35) else ""
    n4 = f"{top4[i][0]} ({top4[i][1]})" if i < len(top4) else ""
    print(f"{i+1:<6} {n35:<20} {n4:<20}")

# Names unique to each
print("\n" + "-"*60)
print("NAMES UNIQUE TO GPT-4 (not in GPT-3.5)")
print("-"*60)
unique_4 = [(n, gpt4[n]) for n in only_4]
unique_4.sort(key=lambda x: -x[1])
for name, count in unique_4[:30]:
    print(f"  {name}: {count}")

print("\n" + "-"*60)
print("NAMES UNIQUE TO GPT-3.5 (not in GPT-4)")
print("-"*60)
unique_35 = [(n, gpt35[n]) for n in only_35]
unique_35.sort(key=lambda x: -x[1])
for name, count in unique_35[:30]:
    print(f"  {name}: {count}")

# Black names analysis
print("\n" + "="*60)
print("BLACK NAMES ANALYSIS")
print("="*60)

# Common Black names (based on research literature)
# Sources: Fryer & Levitt (2004), various baby name studies
black_names = {
    # Female names with high Black share
    'Aaliyah', 'Imani', 'Ebony', 'Shanice', 'Tamika', 'Keisha', 'Latoya',
    'Shaniqua', 'Tanisha', 'Lakisha', 'Deja', 'Jada', 'Nia', 'Zaria',
    'Kiara', 'Destiny', 'Diamond', 'Precious', 'Unique', 'Jasmine',
    'Brianna', 'Aaliah', 'Sanaa', 'Amara', 'Zuri', 'Amira',
    # Male names with high Black share
    'Jamal', 'Darnell', 'Terrell', 'Tyrone', 'Deshawn', 'Marquis',
    'Darius', 'Malik', 'Jaylon', 'Davon', 'Rashad', 'Deandre',
    'Jalen', 'Tavon', 'Trevon', 'Devonte', 'Jaylen', 'Kamari',
    'Khalil', 'Omari', 'Xavier', 'Isaiah', 'Elijah', 'Josiah',
}

# Check which Black names appear
all_recommended = set(gpt35.keys()) | set(gpt4.keys())
black_recommended = black_names & set(n.capitalize() for n in [x.lower() for x in all_recommended])

print(f"\nBlack names in our list: {len(black_names)}")
print(f"Black names recommended by ChatGPT: {len(black_recommended)}")
print(f"Coverage: {len(black_recommended)/len(black_names):.1%}")

print("\nBlack names ChatGPT DOES recommend:")
for name in sorted(black_recommended):
    freq35 = gpt35.get(name, 0)
    freq4 = gpt4.get(name, 0)
    print(f"  {name}: GPT-3.5={freq35}, GPT-4={freq4}")

print("\nBlack names ChatGPT does NOT recommend:")
not_recommended = black_names - black_recommended
for name in sorted(not_recommended)[:20]:
    print(f"  {name}")
if len(not_recommended) > 20:
    print(f"  ... and {len(not_recommended)-20} more")

# Compare to overall recommendation rate
print("\n" + "-"*60)
print("REPRESENTATION CHECK")
print("-"*60)
total_unique = len(all_recommended)
print(f"Total unique names recommended: {total_unique}")
print(f"Black names recommended: {len(black_recommended)} ({len(black_recommended)/len(black_names):.1%} of our Black name list)")

# Frequency comparison
if black_recommended:
    avg_freq_black = sum(gpt35.get(n,0) + gpt4.get(n,0) for n in black_recommended) / len(black_recommended)
    avg_freq_all = (sum(gpt35.values()) + sum(gpt4.values())) / total_unique
    print(f"\nAvg frequency (Black names): {avg_freq_black:.1f}")
    print(f"Avg frequency (all names): {avg_freq_all:.1f}")
    print(f"Ratio: {avg_freq_black/avg_freq_all:.2f}x")
