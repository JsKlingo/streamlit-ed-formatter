import streamlit as st
import re
import json
import logging
from fpdf import FPDF

# ----------------------------
# Logging Configuration
# ----------------------------
logging.basicConfig(level=logging.INFO)

# Debug sidebar
def debug_log(label, data):
    with st.sidebar:
        st.write(f"**{label}**")
        st.json(data)

# ----------------------------
# Utility Functions
# ----------------------------

def load_abbreviations(uploaded_file, default_abbreviations):
    """Load abbreviations from an uploaded JSON file."""
    try:
        file_content = uploaded_file.read().decode("utf-8")
        return json.loads(file_content)
    except Exception as e:
        st.error(f"Error loading JSON file. Using default abbreviations. (Error: {e})")
        return default_abbreviations

def parse_sections(text, section_patterns):
    """Parse raw text into structured sections using optimized regex patterns."""
    compiled_patterns = {section: re.compile(pattern, re.IGNORECASE) for section, pattern in section_patterns.items()}
    
    group_names = {re.sub(r'\W', '_', section): section for section in section_patterns.keys()}
    combined_pattern = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in zip(group_names.keys(), section_patterns.values())), re.IGNORECASE)

    matches = list(combined_pattern.finditer(text))
    structured_data = {}

    if matches:
        for i, match in enumerate(matches):
            section_found = next((group_names[group] for group, value in match.groupdict().items() if value), None)
            if not section_found:
                continue

            start_index = match.start()
            end_index = matches[i+1].start() if i+1 < len(matches) else len(text)
            section_content = text[start_index:end_index].strip()

            # Remove header text
            header_match = compiled_patterns[section_found].search(section_content)
            if header_match:
                section_content = section_content[header_match.end():].strip()

            structured_data[section_found] = section_content

    structured_data = {section: structured_data.get(section, "[Missing Data]") for section in section_patterns.keys()}
    return structured_data

def apply_abbreviations(structured_data, abbreviations):
    """Replace long-form medical terms with abbreviations in each section."""
    for section, content in structured_data.items():
        for term, abbr in abbreviations.items():
            content = re.sub(rf"\b{re.escape(term)}\b", abbr, content, flags=re.IGNORECASE)
        structured_data[section] = content
    return structured_data

def format_ed_data(text, abbreviations):
    """Process raw ED note text into structured sections with abbreviations applied."""
    if not isinstance(text, str) or not text.strip():
        return {"Error": "Invalid input. Please provide a valid ED note."}

    text = re.sub(r"\n+", "\n", text.strip())

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

    structured_data = parse_sections(text, section_patterns)
    structured_data = apply_abbreviations(structured_data, abbreviations)
    
    debug_log("Extracted Sections", structured_data)
    
    return structured_data

def generate_pdf(text):
    """Generate a UTF-8 encoded PDF from text using FPDF."""
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    
    return pdf.output(dest="S").encode("utf-8")

# ----------------------------
# Main App Code
# ----------------------------

st.title("ED Note Formatter")

# Input: Raw ED note text
raw_text = st.text_area("Paste your raw ED data here:")

# Input: Upload abbreviation JSON file (optional)
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

# Load abbreviations (user-uploaded or default)
user_abbreviations = load_abbreviations(uploaded_file, default_abbreviations) if uploaded_file else default_abbreviations

# Button to process ED note
if st.button("Format Data"):
    structured_data = format_ed_data(raw_text, user_abbreviations)
    
    if "Error" in structured_data:
        st.error(structured_data["Error"])
    else:
        st.subheader("Live Editable Sections")
        editable_output = {section: st.text_area(section, content, height=100) for section, content in structured_data.items()}
        
        if st.button("Save Edits"):
            formatted_text = "\n\n".join([f"**{section}**:\n{content}" for section, content in editable_output.items()])
            st.markdown("### Final Formatted Output")
            st.markdown(formatted_text)
            
            # Provide download options
            st.download_button("Download as Text", formatted_text, file_name="formatted_ed_note.txt", mime="text/plain")
            pdf_bytes = generate_pdf(formatted_text)
            st.download_button("Download as PDF", pdf_bytes, file_name="formatted_ed_note.pdf", mime="application/pdf")
