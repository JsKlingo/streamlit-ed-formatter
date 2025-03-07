import streamlit as st
import re
import json
from fpdf import FPDF

# Debug output to confirm the app loads
st.write("App loaded successfully!")

# ----------------------------
# Utility Functions
# ----------------------------

def load_abbreviations(uploaded_file, default_abbreviations):
    """
    Load abbreviations from an uploaded JSON file.
    If there is any error, return the default abbreviations.
    """
    try:
        file_content = uploaded_file.read().decode("utf-8")
        return json.loads(file_content)
    except Exception as e:
        st.error(f"Error loading JSON file. Using default abbreviations. (Error: {e})")
        return default_abbreviations

def parse_sections(text, section_patterns):
    """
    Parse the raw text into structured sections using a combined regex pattern.
    """
    # Create a combined regex with named groups.
    group_names = {}
    combined_parts = []
    for section, pattern in section_patterns.items():
        # Convert section name into a valid regex group name by replacing non-word characters with underscores.
        valid_group = re.sub(r'\W', '_', section)
        group_names[valid_group] = section
        combined_parts.append(f"(?P<{valid_group}>{pattern})")
    combined_pattern = re.compile("|".join(combined_parts), re.IGNORECASE)

    # Find all matches in the text
    matches = list(combined_pattern.finditer(text))
    structured_data = {}

    if matches:
        for i, match in enumerate(matches):
            # Determine which section was matched
            section_found = None
            for group, value in match.groupdict().items():
                if value is not None:
                    section_found = group_names[group]
                    break
            if section_found is None:
                continue

            start_index = match.start()
            end_index = matches[i+1].start() if i+1 < len(matches) else len(text)
            section_content = text[start_index:end_index].strip()

            # Remove the header text from the content
            header_regex = re.compile(section_patterns[section_found], re.IGNORECASE)
            header_match = header_regex.match(section_content)
            if header_match:
                section_content = section_content[header_match.end():].strip()

            structured_data[section_found] = section_content

    # Mark any sections not found as "[Missing Data]"
    for section in section_patterns.keys():
        if section not in structured_data:
            structured_data[section] = "[Missing Data]"

    return structured_data

def apply_abbreviations(structured_data, abbreviations):
    """
    Replace long-form medical terms with abbreviations in each section.
    """
    for section, content in structured_data.items():
        for term, abbr in abbreviations.items():
            # re.escape handles any special characters in the term
            content = re.sub(rf"\b{re.escape(term)}\b", abbr, content, flags=re.IGNORECASE)
        structured_data[section] = content
    return structured_data

def format_ed_data(text, abbreviations):
    """
    Process the raw ED note text into structured sections with abbreviations applied.
    """
    if not text.strip():
        return {"Error": "No data provided"}
    
    # Normalize newlines
    text = re.sub(r"\n+", "\n", text.strip())

    # Define section patterns
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
    st.write("Extracted Sections:", structured_data)  # Debug output

    structured_data = apply_abbreviations(structured_data, abbreviations)
    return structured_data

def generate_pdf(text):
    """
    Generate a PDF from the given text using FPDF.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest="S").encode("latin1")

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

# Use user-uploaded abbreviations if available
if uploaded_file is not None:
    user_abbreviations = load_abbreviations(uploaded_file, default_abbreviations)
else:
    user_abbreviations = default_abbreviations

# Button to process the ED note data
if st.button("Format Data"):
    structured_data = format_ed_data(raw_text, user_abbreviations)
    
    if "Error" in structured_data:
        st.error(structured_data["Error"])
    else:
        st.subheader("Live Editable Sections")
        editable_output = {}
        for section, content in structured_data.items():
            editable_output[section] = st.text_area(section, content, height=100)
        
        if st.button("Save Edits"):
            # Build formatted text using markdown for clarity
            formatted_text = "\n\n".join([f"**{section}**:\n{content}" for section, content in editable_output.items()])
            st.markdown("### Final Formatted Output")
            st.markdown(formatted_text)
            
            # Provide download options
            st.download_button("Download as Text", formatted_text, file_name="formatted_ed_note.txt", mime="text/plain")
            pdf_bytes = generate_pdf(formatted_text)
            st.download_button("Download as PDF", pdf_bytes, file_name="formatted_ed_note.pdf", mime="application/pdf")
