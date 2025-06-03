"""
Read a PDF file and extract all words into a textfile.
"""

import sys

import pymupdf


def extract_text_from_pdf_pymupdf(pdf_path: str) -> str:
    """use pymupdf to extract text from PDF file."""
    extracted_text: str = ""
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            extracted_text += page.get_text()
    return extracted_text


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python pdf2wordlist.py <pdf_file_path>")
        sys.exit(1)

    pdf_file_path = sys.argv[1]
    text = extract_text_from_pdf_pymupdf(pdf_file_path)
    if text != "":
        with open("wordlist.txt", "w", encoding="utf-8") as file:
            file.write(text)
        word_list: list[str] = []
        with open("wordlist.txt", "r", encoding="utf-8") as file:
            for line in file:
                word_list.append(line.strip())
        # df = pd.DataFrame(word_list, columns=["word"])
        # df.to_csv("wordlist.csv", index=False)
        print(f"Extracted {len(text)} unique words from the PDF.")
    else:
        print("No text extracted from the PDF.")
