# backend/adaptation/adaptation_handler.py

import os
import sys
import difflib
import logging
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import json

# Setup logging
logging.basicConfig(level=logging.INFO)

# ✅ Add backend to sys.path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import gemini_client

load_dotenv()

def extract_text_from_pdf(path):
    if not os.path.exists(path):
        logging.warning(f"{path} not found.")
        return ""
    reader = PdfReader(path)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def extract_text_from_json(path):
    if not os.path.exists(path):
        logging.warning(f"{path} not found.")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)

def generate_diff(old: str, new: str) -> str:
    return "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm=""))

def load_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def load_old_testcases(path="backend/adaptation/old_testcases.json") -> str:
    return load_file(path)

def save_adapted_testcases(adapted: str, path="backend/adaptation/adapted_testcases.json"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(adapted)
    logging.info(f"✅ Adapted test cases saved at {path}")

def adapt_test_cases(merged_diff: str, old_testcases: str) -> str:
    prompt = f"""
    Below are detected changes across application artifacts (BRD, source code, Figma):

    {merged_diff}

    Existing Test Cases:
    {old_testcases}

    Based on the above changes, update the test cases:
    - Add tests for new features or changes
    - Remove outdated tests
    - Keep valid ones

    Return only updated test cases in JSON array format.
    """
    logging.info("Sending prompt to Gemini...")
    return gemini_client.generate_text([prompt])

def main():
    # Step 1: BRD diff
    old_brd = extract_text_from_pdf("backend/adaptation/old_BRD.pdf")
    new_brd = extract_text_from_pdf("backend/adaptation/new_BRD.pdf")
    brd_diff = generate_diff(old_brd, new_brd)

    # Step 2: Code diff from Git
    os.system("git fetch origin main")
    os.system("git diff origin/main -- '*.py' '*.js' '*.jsx' > backend/adaptation/code_diff.txt")
    code_diff = load_file("backend/adaptation/code_diff.txt")

    # Step 3: Figma diff (as JSON)
    old_figma = extract_text_from_json("backend/adaptation/old_figma.json")
    new_figma = extract_text_from_json("backend/adaptation/new_figma.json")
    figma_diff = generate_diff(old_figma, new_figma)

    # Step 4: Merge all diffs
    merged_diff = f"""
==== BRD CHANGES ====
{brd_diff}

==== SOURCE CODE CHANGES ====
{code_diff}

==== FIGMA CHANGES ====
{figma_diff}
"""

    old_testcases = load_old_testcases()
    adapted = adapt_test_cases(merged_diff, old_testcases)

    logging.info("🔁 Adapted Response from Gemini:")
    print(adapted)

    save_adapted_testcases(adapted)

if __name__ == "__main__":
    main()
