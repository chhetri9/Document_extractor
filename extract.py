from pdf_reader import extract_text_from_pdf

def extract_text(file_path):

    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    else:
        return "Unsupported file type"