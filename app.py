import re
import json
import streamlit as st
from io import BytesIO
from fpdf import FPDF

# Title of the app
st.title("ED Note Formatter")

# Text area for pasting raw ED notes
raw_text = st.text_area("Paste your raw ED data here:")

# Allow users to upload a custom abbreviation list
uploaded_file = st.file_uploader("Upload an abbreviation JSON file (optional)", type=["json"])

# Default abbreviation mapping
default_abbreviations = {
    "myocardial infarction": "MI",
    "hypertension": "HTN",
    "diabetes mellitus": "DM",
    "chronic obstructive pulmonary disease": "COPD",
    "cerebrovascular accident": "CVA",
    "acute kidney injury": "AKI",
    "deep vein thrombosis": "DVT",
    "pulmonary embolism": "PE",
    "chronic kidney disease": "CKD",
    "gastroesophageal reflux disease": "GERD",
    "atrial fibrillation": "AF",
    "congestive heart failure": "CHF",
    "coronary artery disease": "CAD"
}

# Load abbreviations from uploaded file
if uploaded_file is not None:
    try:
        user_abbreviations = json.load(uploaded_file)
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Using default abbreviations.")
        user_abbreviations = default_abbreviations
else:
    user_abbreviations = default_abbreviations

# Function to process raw text and format it into structured sections
def format_ed_data(text, abbreviations):
    if not text.strip():
        return {"Error": "No data provided"}

    # Define common section headers
    section_patterns = {
        "Chief Complaint": r"(Chief Complaint:|Reason for Visit:|CC:)",
        "HPI": r"(History of Present Illness:|HPI:)",
        "ROS": r"(Review of Systems:|ROS:)",
        "ED Vitals": r"(Triage Vitals:|Vital Signs:|VS:)",
        "Physical Exam": r"(Physical Exam:|PE:|Exam:)",
        "Labs & Imaging": r"(Labs:|Laboratory Results:|Tests:|Diagnostics:|Imaging:|Radiology:)",
        "MDM": r"(Medical Decision Making:|MDM:|ED Course:|Assessment and Plan:)",
        "Prior to Admission": r"(Prior to Admission:|Past Medical History:|PMH:|Previous Hospitalizations:)"
    }

    structured_data = {}
    text = re.sub(r"\n+", "\n", text.strip())

    for section, pattern in section_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_index = match.start()
            next_section_index = len(text)
            for other_pattern in section_patterns.values():
                next_match = re.search(other_pattern, text[start_index + 1:], re.IGNORECASE)
                if next_match:
                    next_section_index = min(next_section_index, start_index + 1 + next_match.start())
            section_content = text[start_index:next_section_index].strip()
            structured_data[section] = re.sub(pattern, "", section_content, flags=re.IGNORECASE).strip()

    # Ensure missing sections are noted
    for section in section_patterns.keys():
        if section not in structured_data:
            structured_data[section] = "[Missing Data]"

    # Apply abbreviations
    for section, content in structured_data.items():
        for term, abbr in abbreviations.items():
            content = re.sub(rf"\b{term}\b", abbr, content, flags=re.IGNORECASE)
        structured_data[section] = content

    return structured_data

# Function to generate a PDF file
def generate_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for section, content in text.items():
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, section, ln=True, align='L')
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content + "\n")
        pdf.ln(5)

    pdf_output = BytesIO()
    pdf.output(pdf_output, 'F')
    pdf_output.seek(0)
    return pdf_output

# Button to process the data
if st.button("Format Data"):
    structured_data = format_ed_data(raw_text, user_abbreviations)

    if "Error" in structured_data:
        st.error(structured_data["Error"])
    else:
        st.subheader("Live Editable Sections")
        editable_output = {}

        for section, content in structured_data.items():
            key = f"edit_{section}"
            if key not in st.session_state:
                st.session_state[key] = content  # Initialize with extracted text
            editable_output[section] = st.text_area(section, st.session_state[key], height=100, key=key)

        if st.button("Save Edits"):
            formatted_text = "\n\n".join([f"**{section}**:\n{st.session_state[f'edit_{section}']}" for section in structured_data.keys()])
            st.markdown("### Final Formatted Output")
            st.markdown(formatted_text)

            # Provide download options
            st.download_button("Download as Text", formatted_text, file_name="formatted_ed_note.txt", mime="text/plain")
            pdf_bytes = generate_pdf({section: st.session_state[f'edit_{section}'] for section in structured_data.keys()})
            st.download_button("Download as PDF", pdf_bytes, file_name="formatted_ed_note.pdf", mime="application/pdf")
