import os
import glob
import shutil
import re
import json
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

old_data_dir = "old_data"
scientists_dir = "assets/scientists"
images_dir = "assets/images"

os.makedirs(scientists_dir, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)

def extract_text(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def process_person(person_dir, date_str):
    print(f"Processing {person_dir} with date {date_str}")
    
    txt_files = glob.glob(os.path.join(person_dir, "*.txt")) + \
                glob.glob(os.path.join(person_dir, "*.rtf")) + \
                glob.glob(os.path.join(person_dir, "*.rtfd", "TXT.rtf"))
    
    txt_files = [f for f in txt_files if os.path.isfile(f) and not f.endswith("to_be_fixed.rtf")]
    if not txt_files:
        return

    # prefer non-empty text files
    txt_files.sort(key=lambda f: os.path.getsize(f), reverse=True)
    text_content = extract_text(txt_files[0])
    if not text_content or len(text_content.strip()) < 10:
        return
        
    img_files = glob.glob(os.path.join(person_dir, "*.png")) + \
                glob.glob(os.path.join(person_dir, "*.jpg")) + \
                glob.glob(os.path.join(person_dir, "*.jpeg"))
    
    img_file = img_files[0] if img_files else None
    
    prompt = f"""
    Given the following text (which might contain RTF tags) and the date context {date_str}, extract the biographical information about the scientific personality described. 
    The personality either died or was born on this day. If the text mentions multiple people briefly, focus on the primary subject of the text.
    
    Return a JSON object with the following keys. All keys must be present. If you don't know the value, use an empty string or empty array.
    - name (string, first names)
    - surname (string, last name)
    - gender (string)
    - nationality (string)
    - birth_date (string, format YYYY-MM-DD or unknown)
    - death_date (string, format YYYY-MM-DD or unknown)
    - disciplines (array of strings)
    - headline (string, a short one-sentence summary of what they are famous for)
    - quote (string, a famous quote by them, if none, empty string)
    
    Text:
    {text_content[:4000]}
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
    except Exception as e:
        print(f"  Error calling Gemini: {e}")
        return

    name = data.get("name", "").strip()
    surname = data.get("surname", "").strip()
    
    if not name and not surname:
        print("  Could not extract name/surname")
        return
        
    md_filename = f"{name.lower().replace(' ', '-')}-{surname.lower().replace(' ', '-')}.md".strip("-")
    md_path = os.path.join(scientists_dir, md_filename)
    
    if os.path.exists(md_path):
        print(f"  {md_path} already exists. Skipping.")
        return
        
    img_name = ""
    if img_file:
        ext = os.path.splitext(img_file)[1].lower()
        img_name = f"{name.lower().replace(' ', '-')}-{surname.lower().replace(' ', '-')}{ext}".strip("-")
        dest_img_path = os.path.join(images_dir, img_name)
        shutil.copy2(img_file, dest_img_path)
    
    data["image"] = img_name
    
    yaml_lines = ["---"]
    for k, v in data.items():
        if isinstance(v, list):
            yaml_lines.append(f"{k}:")
            for item in v:
                clean_item = str(item).replace('"', '\\"').replace('\n', ' ')
                yaml_lines.append(f"  - \"{clean_item}\"")
        else:
            val = str(v).replace('"', '\\"').replace('\n', ' ')
            yaml_lines.append(f'{k}: "{val}"')
    yaml_lines.append("---")
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(yaml_lines) + "\n")
    print(f"  Created {md_path}")

def main():
    for root, dirs, files in os.walk(old_data_dir):
        if root.endswith(".rtfd") or root.endswith(".pkgf"):
            continue
            
        txt_files = [f for f in files if f.endswith(".txt") or f.endswith(".rtf")]
        rtfd_dirs = [d for d in dirs if d.endswith(".rtfd")]
        
        if txt_files or rtfd_dirs:
            parts = root.split(os.sep)
            date_str = ""
            for p in parts:
                if "-" in p or p in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]:
                    date_str += p + " "
            process_person(root, date_str.strip())
            
if __name__ == "__main__":
    main()
