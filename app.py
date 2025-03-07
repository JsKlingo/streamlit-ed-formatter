import re
import json
import streamlit as st
from io import BytesIO
from fpdf import FPDF
from collections import OrderedDict

st.title("ED Note Formatter")
raw_text = st.text_area("Paste your raw ED data here:")
uploaded_file = st.file_uploader("Upload an abbreviation JSON file (optional)", type=["json"])

# Ordered section patterns to maintain processing sequence
section_patterns = OrderedDict([
    ("Chief Complaint", r"(Chief Complaint:|Reason for Visit:|CC:|Presenting Complaint:)"),
    ("HPI", r"(History of Present Illness:|HPI:|Present Illness:)"),
    ("ROS", r"(Review of Systems:|ROS:|System Review:)"),
    ("ED Vitals", r"(Triage Vitals:|Vital Signs:|VS:|Vitals:)"),
    ("Physical Exam", r"(Physical Exam:|PE:|Exam Findings:)"),
    ("Labs & Imaging", r"(Labs:|Laboratory Results:|Imaging Studies:|Diagnostics:)"),
    ("MDM", r"(Medical Decision Making:|MDM:|Clinical Reasoning:)"),
    ("Prior to Admission", r"(Past Medical History:|PMH:|Previous Admissions:)")
])

default_abbreviations = {
    "myocardial infarction": "MI",
    "hypertension": "HTN",
    # ... (keep existing default abbreviations)
}

if uploaded_file:
    try:
        user_abbreviations = json.load(uploaded_file)
        # Merge with defaults (user abbreviations take precedence)
        user_abbreviations = {**default_abbreviations, **user_abbreviations}
    except Exception as e:
        st.error(f"Invalid JSON file: {str(e)}")
        user_abbreviations = default_abbreviations
else:
    user_abbreviations = default_abbreviations

def format_ed_data(text, abbreviations):
    if not text.strip():
        return {"Error": "No data provided"}

    structured_data = {section: "[Missing Data]" for section in section_patterns}
    text = re.sub(r"\n+", "\n", text.strip())
    remaining_text = text
    processed_indices = []

    # Process sections in order
    for i, (section, pattern) in enumerate(section_patterns.items()):
        matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
        if not matches:
            continue
            
        # Use first match if multiple found
        match = matches[0]
        start = match.start()
        end = match.end()
        
        # Find next section start
        next_start = len(remaining_text)
        for next_pattern in list(section_patterns.values())[i+1:]:
            next_match = re.search(next_pattern, remaining_text[end:], re.IGNORECASE)
            if next_match:
                next_start = min(next_start, end + next_match.start())
                break
        
        content = remaining_text[end:next_start].strip()
        structured_data[section] = content
        processed_indices.extend(range(start, next_start))
        remaining_text = remaining_text[:start] + remaining_text[next_start:]

    # Handle unmatched content
    unmatched = ""
    for idx, char in enumerate(remaining_text):
        if idx not in processed_indices:
            unmatched += char
    if unmatched.strip():
        structured_data["Uncategorized"] = unmatched.strip()

    # Apply abbreviations (longest terms first)
    for section in structured_data:
        if section == "Error":
            continue
        content = structured_data[section]
        for term in sorted(abbreviations.keys(), key=len, reverse=True):
            content = re.sub(rf"(?i)\b{re.escape(term)}\b", abbreviations[term], content)
        structured_data[section] = content

    return structured_data

def generate_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for section, content in text.items():
        if section == "Uncategorized":
            continue
        pdf.set_font(style='B')
        pdf.cell(0, 10, section, ln=True)
        pdf.set_font(style='')
        pdf.multi_cell(0, 8, content)
        pdf.ln(5)
    
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    return pdf_output.getvalue()

if st.button("Format Data"):
    structured_data = format_ed_data(raw_text, user_abbreviations)
    
    if "Error" in structured_data:
        st.error(structured_data["Error"])
    else:
        st.subheader("Structured ED Note")
        editable_output = {}

        # Add Uncategorized section if present
        if "Uncategorized" in structured_data:
            section_patterns["Uncategorized"] = "Uncategorized Content"

        for section in section_patterns:
            content = structured_data.get(section, "[Missing Data]")
            key = f"edit_{section}"
            if key not in st.session_state:
                st.session_state[key] = content
            editable_output[section] = st.text_area(
                label=section,
                value=st.session_state[key],
                height=150 if section == "Uncategorized" else 100,
                key=key
            )

        if st.button("Generate Final Report"):
            final_output = OrderedDict()
            for section in section_patterns:
                if section == "Uncategorized" and not editable_output[section].strip():
                    continue
                final_output[section] = st.session_state[f'edit_{section}']
            
            # Create formatted text
            formatted_text = "\n\n".join(
                [f"**{section}**:\n{content}" for section, content in final_output.items()]
            )
            
            st.markdown("### Final Report")
            st.markdown(formatted_text)

            # Download buttons
            st.download_button(
                "Download as Text",
                formatted_text,
                file_name="ed_note.txt"
            )
            
            pdf_bytes = generate_pdf(final_output)
            st.download_button(
                "Download as PDF",
                pdf_bytes,
                file_name="ed_note.pdf",
                mime="application/pdf"
            )