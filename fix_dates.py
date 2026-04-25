import os
import glob
import json
import re
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

scientists_dir = "assets/scientists"
md_files = glob.glob(os.path.join(scientists_dir, "*.md"))

people_to_fix = []
file_mapping = {}

for md_file in md_files:
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    name_match = re.search(r'name:\s*"([^"]+)"', content)
    surname_match = re.search(r'surname:\s*"([^"]+)"', content)
    
    if not name_match or not surname_match:
        continue
        
    full_name = f"{name_match.group(1)} {surname_match.group(1)}"
    
    needs_fix = False
    if 'birth_date: "unknown"' in content or re.search(r'birth_date: "\d{4}-unknown"', content):
        needs_fix = True
    if 'death_date: "unknown"' in content or re.search(r'death_date: "\d{4}-unknown"', content):
        needs_fix = True
        
    if needs_fix:
        people_to_fix.append(full_name)
        file_mapping[full_name] = md_file

if not people_to_fix:
    print("No people to fix.")
    exit(0)

# Batch people into chunks of 20 to avoid prompt size limits or timeouts
chunk_size = 20
all_dates = {}

for i in range(0, len(people_to_fix), chunk_size):
    chunk = people_to_fix[i:i+chunk_size]
    print(f"Processing chunk {i//chunk_size + 1}: {chunk}")
    
    prompt = f"""
    Please provide the birth date and death date for the following famous scientists.
    Return the result as a JSON object where keys are the names provided, and values are objects with "birth_date" and "death_date" in YYYY-MM-DD format.
    If they are still alive, use an empty string "" for death_date.
    
    Names:
    {json.dumps(chunk)}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
        all_dates.update(data)
    except Exception as e:
        print(f"Error querying Gemini: {e}")

# Update files
for name, dates in all_dates.items():
    if name not in file_mapping:
        continue
        
    md_file = file_mapping[name]
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    new_birth = dates.get("birth_date", "")
    new_death = dates.get("death_date", "")
    
    if new_birth:
        content = re.sub(r'birth_date: "[^"]*"', f'birth_date: "{new_birth}"', content)
    if new_death != None: # allow empty string if still alive
        content = re.sub(r'death_date: "[^"]*"', f'death_date: "{new_death}"', content)
        
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content)

print("Finished updating dates.")
