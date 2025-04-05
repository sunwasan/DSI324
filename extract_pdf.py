from tqdm import tqdm
import os
import pandas as pd
from fixthaipdf import clean
import re
import pdfplumber
# from PyPDF2 import PdfReader
from tqdm import tqdm
from pathlib import Path
import json 

file_dir = str(Path(__file__).resolve().parent)
pdf_dir = os.path.join(file_dir, "pdf")
chunks_dir = os.path.join(file_dir, "chunks")

pdf_files = os.listdir(pdf_dir)

if not os.path.exists(chunks_dir):
    os.makedirs(chunks_dir)
    
if not os.path.exists(pdf_dir):
    print(f"Directory {pdf_dir} does not exist.")
    exit(1)
    
unicode_box_dict = {
    "\uf0fe" : "\n<include>",
    "\uf052" : "\n<include>",
    "\uf06f" : "\n<exclude>",
    "\uf0a3" : "\n<exclude>",
    
}

def find_unicode_string(string):
    return re.findall(r'[\uE000-\uF8FF]', string)

def clean_text(text):
    cleaned_text = clean(text)
    cleaned_text = cleaned_text.replace("เป็น", "")
    cleaned_text = cleaned_text.replace("...", "")
    
    for unicode_box, replacement in unicode_box_dict.items():
        cleaned_text = cleaned_text.replace(unicode_box, replacement)
    
    lines = cleaned_text.split("\n")
    lines_cleaned = []
    for line in lines:
        if line.startswith("<include>"):
            line += "</include>"
        elif line.startswith("<exclude>"):
            line += "</exclude>"
        lines_cleaned.append(line.strip())
    cleaned_text = "\n".join(lines_cleaned)
    
    
    return cleaned_text

def extract_text_from_pdf(pdf_path:str) -> list:
    file_content = []


    with pdfplumber.open(os.path.join(pdf_dir, pdf_path)) as pdf:
        for page in tqdm(pdf.pages, desc="Processing pages", unit="page"):
            try:
                if not page.objects["char"]:  # Skip pages without text
                    break
                
                
                text = page.extract_text(x_tolerance=3, y_tolerance=3)  # Faster text extraction
                
                if text and text.strip():
                    file_content.append(text)
            except Exception as e:
                print(f"Skipping page {page.page_number} due to error: {e}")
                break
            
    file_content_cleaned = [clean_text(cont) for cont in file_content]
    return file_content_cleaned


def file_content_to_header_page(file_content: list) -> dict:
    contain_kws = []
    for ind, content in enumerate(file_content):
        header_pattern = re.compile(rf"หมวดที่\s*[0-9].*\s*([ก-ฮ]+)")
        if 'สารบัญ' in content:
            continue
        if re.findall(header_pattern, content):
            contain_kws.append((ind, content))
            
    header_page = {}
    for i in range(1,10):
        headline_pattern = re.compile(rf"หมวดที่\s*{i}.*\s*([ก-ฮ]+)")
        for ind, content in contain_kws:
            if re.findall(headline_pattern, content):
                header_page[i] = ind
                
    return header_page

def header_page_to_chunk(file_content:list, header_page:dict):

    start = None
    stop = None    
    sector_to_page_chunks = {}
    for key, value in header_page.items():
        start = value 
        stop = header_page.get(key+1, None) 
        if stop is None:
            stop = len(file_content) - 1
        if start != stop:
            
            stop = stop - 1   
            
        sector_to_page_chunks[f'หมวดที่ {key}'] = (start, stop)    
    return sector_to_page_chunks

def page_chunk_to_content(file_content: list, sector_to_page_chunks: dict) -> dict:
    sector_to_content = {}

    for key, value in sector_to_page_chunks.items():
        sector = key
        start, stop = value
        content = []  # Initialize content list at the start of each sector

        if stop > start:
            for i in range(start, stop + 1):
                if i < len(file_content):
                    content.append(file_content[i])
        else:
            if start < len(file_content):
                content.append(file_content[start])

        # Store the joined content in the dictionary
        sector_to_content[sector] = ' '.join(content)

    return sector_to_content

        
def extract_from_file_path(pdf_path: str) -> dict:
    file_content = extract_text_from_pdf(pdf_path)
    header_page = file_content_to_header_page(file_content)
    sector_to_page_chunks = header_page_to_chunk(file_content,header_page)
    sector_to_content = page_chunk_to_content(file_content, sector_to_page_chunks)
    return sector_to_content


def save_to_json(file_name:str, data:dict):
    file_path = os.path.join(chunks_dir, f"{file_name}.json")
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
        

def main():
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs", unit="file"):
        if pdf_file.endswith(".pdf"):
            print(f"Processing {pdf_file}...")
            pdf_path = os.path.join(pdf_dir, pdf_file)
            file_name = pdf_file.replace(".pdf", "")
            data = extract_from_file_path(pdf_path)
            save_to_json(file_name, data)
            print(f"Saved chunks to {file_name}.txt")
            
if __name__ == "__main__":
    main()