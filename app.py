import re
import json
import streamlit as st
from datetime import datetime

# Updated section labels, including Medications
SECTION_LABELS = [
    "Chief Complaint", "HPI", "ROS", "ED Vitals", "Physical Exam",
    "Labs & Imaging", "Medications", "MDM", "Prior to Admission", "Uncategorized"
]

# Mapping from original section to SOAP categories
section_to_soap = {
    "Chief Complaint": "Subjective",
    "HPI": "Subjective",
    "ROS": "Subjective",
    "ED Vitals": "Objective",
    "Physical Exam": "Objective",
    "Labs & Imaging": "Objective",
    "Medications": "Objective",
    "MDM": "Assessment",
    "Prior to Admission": "Plan",
    "Uncategorized": "Other"
}

# Title of the Streamlit app
st.title("ED Note Formatter - Enhanced SOAP JSON Output")

# Text area for inputting raw ED note data
raw_text = st.text_area("Paste your raw ED note data here:")

# Hardcoded abbreviation mappings
abbreviations = {
    "myocardial infarction": "MI",
    "hypertension": "HTN",
    "c/o": "complains of",
    "SOB": "shortness of breath",
    # Add more abbreviations as needed
}

def classify_segment(segment: str) -> str:
    """
    Classify a text segment into an ED note section using rule-based keyword matching.
    """
    text = segment.lower()
    if any(kw in text for kw in ["chief complaint", "c/o", "complains of"]):
        return "Chief Complaint"
    if any(kw in text for kw in ["hpi", "history of present illness"]):
        return "HPI"
    if any(kw in text for kw in ["ros", "review of systems", "denies ", "reports no "]):
        return "ROS"
    if any(kw in text for kw in ["blood pressure", "bp", "heart rate", "hr", "o2 sat", "temperature", "vitals"]):
        return "ED Vitals"
    if any(kw in text for kw in ["physical exam", "exam", "heent", "lungs", "extremities", "no edema"]):
        return "Physical Exam"
    if any(kw in text for kw in ["lab", "labs", "wbc", "hgb", "x-ray", "ct scan", "mri", "imaging", "ekg"]):
        return "Labs & Imaging"
    if any(kw in text for kw in ["medications:", "infusion", "scheduled meds", "prn meds"]):
        return "Medications"
    if any(kw in text for kw in ["mdm", "medical decision", "plan", "assessment", "differential"]):
        return "MDM"
    if any(kw in text for kw in ["prior to admission", "pta", "before arrival", "prior treatment"]):
        return "Prior to Admission"
    return "Uncategorized"

def split_text_into_segments(text: str) -> list:
    """
    Split the input text into segments (e.g., sentences) based on punctuation.
    """
    segments = re.split(r'(?<=[\.!?])\s+', text)
    return [seg.strip() for seg in segments if seg.strip()]

def format_ed_data(text: str, abbr_dict: dict) -> dict:
    """
    Format ED note data by classifying segments and applying abbreviation replacements.
    Returns a dictionary with keys for each original section.
    """
    if not text or not text.strip():
        return {"Error": "No data provided"}
    
    # Initialize all sections with empty strings
    structured_data = {section: "" for section in SECTION_LABELS}
    segments = split_text_into_segments(text)
    
    # Classify each segment and append it to the appropriate section
    for segment in segments:
        section = classify_segment(segment)
        structured_data[section] += segment.strip() + "\n\n"
    
    # Apply abbreviation replacements for consistency
    for section, content in structured_data.items():
        for term, abbr in abbr_dict.items():
            content = re.sub(rf"(?i)\b{re.escape(term)}\b", abbr, content)
        structured_data[section] = content.strip()
    
    return structured_data

def process_section_content(content: str):
    """
    If a section has multiple entries (separated by double newlines), split them into a list.
    Otherwise, return the cleaned string.
    """
    parts = [line.strip() for line in content.split("\n\n") if line.strip()]
    return parts if len(parts) > 1 else content.strip()

def parse_medications(text: str) -> dict:
    """
    Parse the Medications section into subsections.
    Looks for headings like "Continuous Infusions:", "Scheduled Meds:", and "PRN Meds:".
    Returns a dictionary with lists of entries.
    """
    meds = {}
    # Define possible subsections
    subsections = ["Continuous Infusions:", "Scheduled Meds:", "PRN Meds:"]
    for i, heading in enumerate(subsections):
        if heading in text:
            # Determine the text for this subsection
            start = text.find(heading) + len(heading)
            # Look for the next heading if available
            end = len(text)
            for other_heading in subsections[i+1:]:
                pos = text.find(other_heading, start)
                if pos != -1:
                    end = pos
                    break
            subsection_text = text[start:end].strip()
            # Split entries by double newline
            meds[heading.replace(":", "")] = [entry.strip() for entry in subsection_text.split("\n\n") if entry.strip()]
    return meds if meds else text

def convert_to_soap(structured_data: dict) -> dict:
    """
    Convert the structured data into a nested SOAP JSON format.
    Also includes a metadata block with a timestamp.
    """
    # Initialize the SOAP categories as empty dictionaries
    soap_data = {
        "Subjective": {},
        "Objective": {},
        "Assessment": {},
        "Plan": {},
        "Other": {}
    }
    
    for section, content in structured_data.items():
        if content:  # Only include sections with content
            soap_category = section_to_soap.get(section, "Other")
            processed_content = process_section_content(content)
            # Further process Medications section into subsections
            if section == "Medications":
                processed_content = parse_medications(content)
            soap_data[soap_category][section] = processed_content
    
    # Add metadata
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "note_version": "1.0"
    }
    return {"metadata": metadata, "note": soap_data}

# Process and output the JSON when the user clicks the button
if st.button("Format Data to Enhanced SOAP JSON"):
    result = format_ed_data(raw_text, abbreviations)
    if "Error" in result:
        st.error(result["Error"])
    else:
        soap_result = convert_to_soap(result)
        st.subheader("Structured ED Note (Enhanced SOAP Format)")
        st.json(soap_result)
