import os
import glob
import re
import json
import time
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

scientists_dir = "assets/scientists"
md_files = glob.glob(os.path.join(scientists_dir, "*.md"))

batch_size = 10
for i in range(0, len(md_files), batch_size):
    chunk_files = md_files[i:i+batch_size]
    
    scientists_info = []
    file_mapping = {}
    
    for fpath in chunk_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        parts = content.split("---")
        if len(parts) >= 3:
            frontmatter = parts[1]
            
            name_m = re.search(r'name:\s*"([^"]*)"', frontmatter)
            surname_m = re.search(r'surname:\s*"([^"]*)"', frontmatter)
            headline_m = re.search(r'headline:\s*"([^"]*)"', frontmatter)
            
            name = name_m.group(1) if name_m else ""
            surname = surname_m.group(1) if surname_m else ""
            headline = headline_m.group(1) if headline_m else ""
            
            full_name = f"{name} {surname}".strip()
            scientists_info.append({"name": full_name, "headline": headline})
            file_mapping[full_name] = {"path": fpath, "frontmatter": frontmatter}

    print(f"Processing batch {i//batch_size + 1}/{(len(md_files) + batch_size - 1)//batch_size}...")
    
    prompt = f"""
    You are a witty, slightly cheeky writer creating engaging, conversational content for social media about scientists.
    Write a short summary (maximum 2200 characters) for each of the following scientists and their achievements.
    
    Guidelines:
    - Act like a real human writing for social media.
    - Vary your sentence length and use contractions.
    - Feel free to use a few emojis.
    - DO NOT use AI buzzwords like 'delve', 'tapestry', 'testament', 'landscape', or 'unlock'.
    - Keep it focused on their actual achievements but make it sound cool and relatable.
    
    Return a JSON object where the keys are the exact names provided and the values are the generated summary text.
    
    Scientists:
    {json.dumps(scientists_info, ensure_ascii=False)}
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
        
        for scientist_name, summary in data.items():
            if scientist_name in file_mapping:
                fpath = file_mapping[scientist_name]["path"]
                frontmatter = file_mapping[scientist_name]["frontmatter"]
                
                new_content = f"---{frontmatter}---\n\n{summary}\n"
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                    
    except Exception as e:
        print(f"Error querying Gemini: {e}")
        time.sleep(2)

print("Finished generating summaries.")
