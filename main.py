import os
import csv

from pdf_reader import extract_text_from_pdf
from parsers.invoice import extract_invoice_data
from parsers.resume import extract_resume_data


UPLOAD_FOLDER = "uploads"


def read_txt_file(filepath):

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()

    except FileNotFoundError:
        print("TXT file not found")
        exit()

    except Exception as e:
        print(f"Error reading TXT file: {e}")
        exit()


def save_to_csv(data, filename="output.csv"):

    try:
        with open(filename, "w", newline="", encoding="utf-8") as csv_file:

            writer = csv.writer(csv_file)

            # Header row
            writer.writerow([
                "Field",
                "Value",
                "Confidence",
                "Note"
            ])

            # Data rows
            for field, details in data["fields"].items():

                writer.writerow([
                    field,
                    details["value"],
                    details["confidence"],
                    details["note"]
                ])

        print(f"\nData exported to {filename}")

    except Exception as e:
        print(f"Error saving CSV: {e}")


# Get all supported files from uploads folder
files = [
    f for f in os.listdir(UPLOAD_FOLDER)
    if f.endswith((".pdf", ".txt"))
]


# Handle empty uploads folder
if not files:
    print("No supported files found in uploads folder")
    exit()


print("\nAvailable Files:\n")

for i, file in enumerate(files, start=1):
    print(f"{i}. {file}")


# Handle invalid input
try:
    choice = int(input("\nChoose a file number: "))

    if choice < 1 or choice > len(files):
        print("Invalid file number")
        exit()

except ValueError:
    print("Please enter a valid number")
    exit()


selected_file = files[choice - 1]

# Create full file path
filepath = os.path.join(UPLOAD_FOLDER, selected_file)


# File type detection
if selected_file.endswith(".pdf"):
    text = extract_text_from_pdf(filepath)

elif selected_file.endswith(".txt"):
    text = read_txt_file(filepath)

else:
    print("Unsupported file type")
    exit()


# Handle empty extracted text
if not text.strip():
    print("File contains no readable text")
    exit()


doc_type = input("\nEnter document type (invoice/resume): ").lower()


if doc_type == "invoice":
    data = extract_invoice_data(text)

elif doc_type == "resume":
    data = extract_resume_data(text)

else:
    print("Invalid document type")
    exit()


# Handle parser failure
if not data:
    print("No data could be extracted")
    exit()


print("\nExtracted Data:\n")

print(f"Document Type: {data['document_type']}\n")


for field, details in data["fields"].items():

    print(f"{field}")

    print(f"  Value: {details['value']}")
    print(f"  Confidence: {details['confidence']}")
    print(f"  Note: {details['note']}")

    print()


# Export extracted data to CSV
save_to_csv(data)