from start_up import *
from client import client
from langchain.prompts import PromptTemplate
import os
import json
import re


key_explanation = [
  {
    "key": "faculty_name_th",
    "topic": "ชื่อคณะภาษาไทย คณะ/วิทยาลัย/สถาบัน ** this line should not leave blank **", 
    "topic_number": ""
  },
  {
    "key": "faculty_name_en",
    "topic": "ชื่อคณะภาษาอังกฤษ คณะ/วิทยาลัย/สถาบัน **if not provided translate from Thai** ** this line should not leave blank **", 
    "topic_number": ""
  },
  {
    "key": "campus",
    "topic": "ศูนย์วิทยาเขต",
    "topic_number": "1.6"
  },
  {
    "key": "curr_id",
    "topic": "รหัสหลักสูตร",
    "topic_number": "1.1"
  },
  {
    "key": "curr_type",
    "topic": "ประเภทหลักสูตร",
    "topic_number": "1.4.2"
  },
  {
    "key": "careers",
    "topic": "อาชีพที่สามารถประกอบได้หลังสำเร็จการศึกษา",
    "topic_number": "1.5"
  },
  {
    "key": "curr-name-th",
    "topic": "ชื่อหลักสูตรภาษาไทย",
    "topic_number": "1.1"
  },
  {
    "key": "curr-name-en",
    "topic": "ชื่อหลักสูตรภาษาอังกฤษ",
    "topic_number": "1.1"
  },
  {
    "key": "degree_full_th",
    "topic": "ชื่อปริญญาเต็มภาษาไทย",
    "topic_number": "1.2"
  },
  {
    "key": "degree_full_en",
    "topic": "ชื่อปริญญาเต็มภาษาอังกฤษ",
    "topic_number": "1.2"
  },
  {
    "key": "degree_abr_th",
    "topic": "ชื่อปริญญาแบบย่อภาษาไทย",
    "topic_number": "1.2"
  },
  {
    "key": "degree_abr_en",
    "topic": "ชื่อปริญญาแบบย่อภาษาอังกฤษ",
    "topic_number": "1.2"
  },
  {
    "key": "num-major",
    "topic": "จำนวนสาขาวิชาเอก",
    "topic_number": "1.3"
  },
  {
    "key": "approved-date",
    "topic": "วันที่อนุมัติหลักสูตร **in YYYY-MM-DD format**",
    "topic_number": "1.4.6"
  },
  {
    "key": "cat-name",
    "topic": "ประเภทโครงการ (โครงการปกติ/ โครงการพิเศษ/ โครงการปกติและโครงการพิเศษ) **pick an answer from parenthesis**",
    "topic_number": "1.7"
  },
  {
    "key": "organization",
    "topic": "ความร่วมมือกับสถาบันอื่น (หลักสูตรของสถาบันโดยเฉพาะ / หลักสูตรที่ได้รับความร่วมมือสนับสนุนจากสถาบันอื่น) **pick an answer from parenthesis**",
    "topic_number": "1.4.4"
  },
  {
    "key": "lang",
    "topic": "ภาษาทีใช้",
    "topic_number": "1.4.3"
  }
]

template = """ 
You are an expert in curriculum documentation.

Your task is to extract information from the provided text based on the required fields listed below.  
Do not include any explanations or extra commentary in your response made sure the most normalized format is used.

---

**Instructions:**

1. Only use the information explicitly available in the provided context.
2. Return your answer as a JSON-style dictionary.
3. Completely ignore any line enclosed within <exclude> and </exclude> tags.
4. For fields with a "topic_number":
   - Extract the value from the part of the text following the matching number.
5. For fields **without** a "topic_number":
   - Search the entire context for the matching topic and extract the relevant data.
6. If a topic includes a list of options in parentheses, select the most appropriate one based on the context.
7. No field should be left blank:
   - If the value is missing but can be inferred (e.g., translating Thai to English), do so.
   - If truly unavailable, return an empty string `""`.
8. Fields like `careers` or `organization` should be returned as a **list** of values.
9. 'organization' and 'cat-name' result should pick an answer **only from parenthesis**.
---

**Field Definitions:**
{key_explanation}

---

**Context:**
{context}

---



**Expected Output Format:**
{{
    "faculty_name_th": "",
    "faculty_name_en": "",
    "campus": "",
    "curr_id": "",
    "curr_type": "",
    "careers": [],
    "curr-name-th": "",
    "curr-name-en": "",
    "degree_full_th": "",
    "degree_full_en": "",
    "degree_abr_th": "",
    "degree_abr_en": "",
    "num-major": "",
    "approved-date": "",
    "cat-name": "",
    "organization": [],
    "lang": ""
}}
"""

import json
import os

def extract_sector_1(json_file_path: str) -> dict:
    # Load JSON input file
    with open(json_file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Extract Sector 1 data (หมวดที่ 1)
    sector1_data = data.get('หมวดที่ 1', '')

    # Format prompt using template
    formatted_prompt = template.format(context=sector1_data, key_explanation=key_explanation)

    # Build PDF file path from JSON filename
    json_file_name = os.path.basename(json_file_path)
    pdf_file_path = os.path.join(r"C:\Users\User\Desktop\project\DSI324\pdf", json_file_name.replace(".json", ".pdf"))

    print("Extracting sector 1 data...")
    print("PDF file path:", pdf_file_path)

    # Send prompt to LLM
    clientcompletion = client.chat.completions.create(
        temperature=0.0,
        model="meta-llama/llama-3.1-8b-instruct:free",
        messages=[{"role": "user", "content": formatted_prompt}]
    )

    # Extract raw response text and parse it into JSON
    response = clientcompletion.choices[0].message.content.strip()
    try:
        response_json = json.loads(response)
    except json.JSONDecodeError:
        print("❌ Failed to decode JSON from model response.")
        print("Raw response:", response)
        raise

    # Return response as {pdf_path: extracted_json}
    return {pdf_file_path: response_json}


import json 
from tqdm import tqdm
chunks_dir = r"C:\Users\User\Desktop\project\DSI324\chunks"
dest_dir = r"C:\Users\User\Desktop\project\DSI324\res\sector_1"
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
    
all_chunks = os.listdir(chunks_dir)

for json_file in tqdm(all_chunks):
    json_file_path = os.path.join(chunks_dir, json_file)
    result_dict = extract_sector_1(json_file_path)
    json_file_name = os.path.basename(json_file_path)
    with open(os.path.join(dest_dir, json_file_name), 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)
        
