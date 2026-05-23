import streamlit as st
import os
import json
import csv
import io

from pdf_reader import extract_text_from_pdf
from parsers.invoice import extract_invoice_data
from parsers.resume import extract_resume_data


# -----------------------------
# PAGE CONFIG
#-----------------------------
st.set_page_config(
    page_title="Document Extractor",
    page_icon="📄",
    layout="centered"
)

st.title("📄Document Extractor")

st.write(
    "Upload PDF or TXT documents and extract structured "
    "information from invoices or resumes."
)


# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Document",
    type=["pdf", "txt"]
)


# -----------------------------
# DOCUMENT TYPE
# -----------------------------
doc_type = st.selectbox(
    "Select Document Type",
    ["invoice", "resume"]
)


# -----------------------------
# PROCESS BUTTON
# -----------------------------
if uploaded_file is not None:

    if st.button("Extract Data"):

        # Create uploads folder if missing
        os.makedirs("uploads", exist_ok=True)

        # Save uploaded file
        file_path = os.path.join(
            "uploads",
            uploaded_file.name
        )

        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        # -----------------------------
        # EXTRACT TEXT
        # -----------------------------
        file_extension = uploaded_file.name.split(".")[-1].lower()

        if file_extension == "pdf":
            text = extract_text_from_pdf(file_path)

        elif file_extension == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

        else:
            text = ""

        # -----------------------------
        # PARSE DOCUMENT
        # -----------------------------
        if doc_type == "invoice":
            data = extract_invoice_data(text)

        elif doc_type == "resume":
            data = extract_resume_data(text)

        else:
            data = {"Error": "Unsupported document type"}

        # -----------------------------
        # DISPLAY RESULTS
        # -----------------------------
        st.subheader("Extracted Data")

        st.json(data)

        # -----------------------------
        # JSON DOWNLOAD
        # -----------------------------
        json_data = json.dumps(
            data,
            indent=4
        )

        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name="extracted_data.json",
            mime="application/json"
        )

        # -----------------------------
        # CSV CONVERSION
        # -----------------------------
        output = io.StringIO()

        writer = csv.DictWriter(
            output,
            fieldnames=[
                "Field",
                "Value",
                "Confidence",
                "Note"
            ]
        )

        writer.writeheader()
        for field, details in data["fields"].items():
            writer.writerow({
                "Field": field,
                "Value": details["value"],
                "Confidence": details["confidence"],
                "Note": details["note"]
            })

        csv_data = output.getvalue()

        # -----------------------------
        # CSV DOWNLOAD
        # -----------------------------
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="extracted_data.csv",
            mime="text/csv"
        )