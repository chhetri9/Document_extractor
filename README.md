# Document Extractor

A Python tool that extracts structured data from invoices and resumes in PDF or TXT format. It ships with three interfaces — a CLI, a Streamlit web app, and a FastAPI REST endpoint — so you can use it however fits your workflow best.

---

## Table of Contents

- [Features]
- [Project Structure]
- [Setup]
- [Running the App]
- [Prompt Design]
- [Output Schema]
- [Extraction Failure Handling]

---

## Features

- Supports PDF and TXT input files
- Extracts structured fields from invoices and resumes
- Each extracted field carries a `value`, `confidence` score, and a human-readable `note`
- Three interfaces: CLI (`main.py`), Streamlit UI (`app.py`), REST API (`api.py`)
- Export results as JSON or CSV

---

## Project Structure

   
Document_extractor/
├── main.py          # CLI entry point

├── app.py           # Streamlit web UI

├── api.py           # FastAPI REST API

├── pdf_reader.py    # PDF text extraction via PyMuPDF

├── extract.py       # Thin routing wrapper for text extraction

├── utils.py         # Shared field builder helper

├── parsers/

│   ├── invoice.py   # Invoice-specific extraction logic

│   └── resume.py    # Resume-specific extraction logic

├── outputs/         # Saved output files

└── requirements.txt
   

---

## Setup

### 1. Clone the repository


git clone https://github.com/chhetri9/Document_extractor.git
cd Document_extractor
   

### 2. Create and activate a virtual environment (recommended)

 
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
   

### 3. Install dependencies

        
pip install -r requirements.txt
   

The main libraries used are:

| Library | Purpose |

| `PyMuPDF` (`fitz`) | PDF text extraction |
| `pdfplumber` / `pdfminer.six` | Additional PDF parsing support |
| `streamlit` | Web UI |
| `fastapi` + `uvicorn` | REST API server |
| `openai` | LLM-based extraction (if used inside parsers) |

### 4. Create the uploads directory

        
mkdir uploads
   

---

## Running the App

### CLI

        
python main.py
   

You will be prompted to choose a file from the `uploads/` folder and then select the document type (`invoice` or `resume`). Results are printed to the terminal and saved as `output.csv`.

### Streamlit Web UI

        
streamlit run app.py
   

Open your browser to `http://localhost:8501`. Upload a PDF or TXT file, select the document type, click **Extract Data**, and download results as JSON or CSV.

### FastAPI REST API

        
uvicorn api:app --reload
   

The API runs at `http://localhost:8000`.

**Endpoint:** `POST /extract`

        
curl -X POST http://localhost:8000/extract \
  -F "file=@invoice.pdf" \
  -F "document_type=invoice"
   

**Response:** JSON object following the output schema described below.

Interactive API docs are available at `http://localhost:8000/docs`.

---

## Prompt Design

Each parser (`parsers/invoice.py`, `parsers/resume.py`) is responsible for locating specific fields in free-form document text. The design philosophy is:

**Targeted field extraction over open-ended summarisation.** Rather than asking a model to "summarise this document", each parser is directed at specific named fields — for example, `invoice_number`, `vendor_name`, `total_amount` for invoices, or `name`, `email`, `skills`, `experience` for resumes.

Where an LLM is used to assist extraction, the prompt follows these principles:

1. **Explicit field list** — The prompt names every field to extract, leaving nothing to inference. This avoids hallucinated field names that don't map to the output schema.
2. **Structured output instruction** — The model is instructed to return only valid JSON matching the output schema, with no preamble or commentary.
3. **Confidence guidance** — The prompt instructs the model to set `confidence` to `"high"` when the value is clearly present in the text, `"medium"` when inferred or partially matched, and `"low"` when absent or uncertain. This allows downstream consumers to filter or flag fields that need human review.
4. **Graceful absence handling** — The prompt explicitly tells the model to return `null` for any field it cannot find, rather than guessing or leaving the key out of the response. This keeps the schema consistent regardless of document quality.
5. **Document text is passed verbatim** — The raw extracted text is injected directly into the prompt. No pre-processing or summarisation is applied before the model sees it, which preserves layout cues (spacing, line breaks) that help locate fields like addresses and dates.

---

## Output Schema

Every extracted document — regardless of type — returns a JSON object with the following top-level shape:

   json
{
  "document_type": "invoice",
  "fields": {
    "<field_name>": {
      "value": "<extracted value or null>",
      "confidence": "high | medium | low",
      "note": "<human-readable explanation>"
    }
  }
}
   

Each field object is produced by the shared `create_field()` helper in `utils.py`:

   python
def create_field(value=None, confidence="low", note=None):
    return {
        "value": value,
        "confidence": confidence,
        "note": note
    }
   

Fields default to `value=None` and `confidence="low"` — so any field that could not be found is still present in the output with a clear low-confidence signal, rather than being silently absent.

### Invoice fields

| Field | Description |
|---|---|
| `invoice_number` | Unique invoice identifier |
| `invoice_date` | Date the invoice was issued |
| `due_date` | Payment due date |
| `vendor_name` | Name of the issuing vendor |
| `vendor_address` | Vendor's address |
| `client_name` | Name of the billed client |
| `client_address` | Client's address |
| `line_items` | List of itemised charges |
| `subtotal` | Pre-tax total |
| `tax` | Tax amount |
| `total_amount` | Final amount due |
| `currency` | Currency of the invoice |
| `payment_terms` | Payment terms (e.g. "Net 30") |

### Resume fields

| Field | Description |
|---|---|
| `name` | Candidate's full name |
| `email` | Contact email address |
| `phone` | Contact phone number |
| `location` | City / region |
| `summary` | Professional summary or objective |
| `skills` | List of technical and soft skills |
| `experience` | Work history entries |
| `education` | Educational qualifications |
| `certifications` | Professional certifications |
| `languages` | Spoken languages |

### CSV export

When exported to CSV (via CLI or Streamlit), the flat structure is:

   
Field, Value, Confidence, Note
invoice_number, INV-2045, high, Found in header
due_date, null, low, Not present in document
...
   

---

## Extraction Failure Handling

The project handles failures at multiple layers:

### 1. Empty or unreadable files
Both the CLI and API check whether the text extracted from a file is blank after stripping whitespace. If so, execution halts with a clear error message before any parsing is attempted:

   
# CLI
if not text.strip():
    print("File contains no readable text")
    exit()

# API
if not text.strip():
    return {"error": "No readable text found"}
   

This catches scanned PDFs with no embedded text layer, corrupted files, and genuinely empty uploads.

### 2. Unsupported file types
Only `.pdf` and `.txt` are accepted. Any other extension returns an unsupported file type error immediately, without attempting extraction.

### 3. Invalid document type
If the user passes a document type other than `invoice` or `resume`, all three interfaces return a clear error rather than running a parser with no matching logic.

### 4. Parser returning no data
After the parser runs, both the CLI and the API confirm that data was actually returned before proceeding. If the parser returns `None` or an empty result, the CLI prints `"No data could be extracted"` and exits cleanly.

### 5. Field-level failures (null + low confidence)
The most important failure mode is a field that exists in the schema but couldn't be found in the document. Rather than omitting the field or raising an exception, the `create_field()` helper always returns a complete field object with `value=None` and `confidence="low"`. This means:

- The output schema is always fully populated and predictable.
- Consumers can filter on `confidence == "low"` to identify fields needing human review.
- The `note` field explains *why* a value is missing (e.g. `"Not present in document"`, `"Could not parse date format"`).

### 6. File I/O errors (CLI)
The CLI wraps file reads in `try/except` blocks, catching `FileNotFoundError` and generic exceptions separately so the user gets a useful error message rather than a raw Python traceback.

### 7. Unique filenames on upload (API)
The API prefixes every uploaded file with a `uuid4()` to prevent filename collisions when multiple requests arrive simultaneously:

   python
unique_name = f"{uuid.uuid4()}_{file.filename}"
   
