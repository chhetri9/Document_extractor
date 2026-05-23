import fitz

def extract_text_from_pdf(pdf_path):

    doc = fitz.open(pdf_path)

    document_text = ""

    for page in doc:
        document_text += page.get_text()

    return document_text