# backend/adaptation_handler.py

import os
import sys
import difflib
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# ✅ Add backend/ to sys.path so we can import from utils/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import gemini_client

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Extract text from PDF files
def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return ""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# ✅ Generate unified diff between old and new BRD text
def generate_diff(old_text, new_text):
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    diff = difflib.unified_diff(old_lines, new_lines, lineterm="")
    return "\n".join(diff)

# ✅ Save the diff to a file
def save_diff(diff_data: str, file_path: str = "diff.txt"):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(diff_data)

# ✅ Load old test cases from JSON file
def load_old_testcases(file_path: str = "old_testcases.json") -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# ✅ Save adapted test cases to JSON file
def save_adapted_testcases(adapted: str, file_path: str = "adapted_testcases.json"):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(adapted)

# ✅ Send prompt to Gemini and return adapted test cases
def adapt_test_cases(diff_content: str, old_testcases: str) -> str:
    prompt = f"""
    The following diff has been detected in the source code or design:

    {diff_content}

    These are the previous test cases:
    {old_testcases}

    Analyze what has changed in the application. Return the updated list of test cases:
    - Add new test cases if there are new features.
    - Remove outdated test cases.
    - Keep still-valid ones.

    Return the result in JSON array format.
    """
    return gemini_client.generate_text([prompt])

# ✅ Main process combining all the above
def main():
    # Step 1: Extract BRD text and generate diff
    old_brd_text = extract_text_from_pdf("old_brd.pdf")
    new_brd_text = extract_text_from_pdf("new_brd.pdf")
    diff_text = generate_diff(old_brd_text, new_brd_text)

    if not diff_text.strip():
        print("✅ No diff detected in BRD. No updates needed.")
        return

    save_diff(diff_text)
    print("✅ Diff file generated successfully.")

    # Step 2: Load old test cases
    old_testcases = load_old_testcases()

    # Step 3: Send to Gemini and get updated test cases
    adapted = adapt_test_cases(diff_text, old_testcases)

    # Step 4: Save adapted test cases
    save_adapted_testcases(adapted)
    print("✅ Adapted test cases saved successfully.")

if __name__ == "__main__":
    main()
