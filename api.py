from fastapi import FastAPI, UploadFile, File, Form

import os
import uuid

from pdf_reader import extract_text_from_pdf

from parsers.invoice import extract_invoice_data
from parsers.resume import extract_resume_data


# -----------------------------
# APP SETUP
# -----------------------------
app = FastAPI()


# -----------------------------
# UPLOAD FOLDER
# -----------------------------
UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# -----------------------------
# HOME ROUTE
# -----------------------------
@app.get("/")
def home():

    return {
        "message": "Document Extractor API Running"
    }


# -----------------------------
# EXTRACT ROUTE
# -----------------------------
@app.post("/extract")
async def extract_document(

    file: UploadFile = File(...),
    document_type: str = Form(...)

):

    # -----------------------------
    # UNIQUE FILE NAME
    # -----------------------------
    unique_name = f"{uuid.uuid4()}_{file.filename}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_name
    )

    # -----------------------------
    # SAVE FILE
    # -----------------------------
    with open(file_path, "wb") as f:

        f.write(await file.read())

    # -----------------------------
    # EXTRACT TEXT
    # -----------------------------
    if file.filename.endswith(".pdf"):

        text = extract_text_from_pdf(file_path)

    elif file.filename.endswith(".txt"):

        with open(file_path, "r", encoding="utf-8") as f:

            text = f.read()

    else:

        return {
            "error": "Unsupported file type"
        }

    # -----------------------------
    # EMPTY TEXT CHECK
    # -----------------------------
    if not text.strip():

        return {
            "error": "No readable text found"
        }

    # -----------------------------
    # DOCUMENT PARSING
    # -----------------------------
    if document_type == "invoice":

        data = extract_invoice_data(text)

    elif document_type == "resume":

        data = extract_resume_data(text)

    else:

        return {
            "error": "Invalid document type"
        }

    # -----------------------------
    # RETURN RESPONSE
    # -----------------------------
    return data