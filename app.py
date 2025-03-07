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
st.title("ED Note Formatter - Optimized for GPT-Based H&P Generation")

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
    keyword_map = {
        "Chief Complaint": [r"\bchief complaint\b", r"\bc/o\b", r"\bcomplains of\b"],
        "HPI": [r"\bhpi\b", r"\bhistory of present illness\b"],
        "ROS": [r"\bros\b", r"\breview of systems\b", r"\bdenies\b", r"\breports no\b"],
        "ED Vitals": [r"\bblood pressure\b", r"\bbp\b", r"\bheart rate\b", r"\bhr\b", r"\bo2 sat\b", r"\btemperature\b", r"\bvitals\b"],
        "Physical Exam": [r"\bphysical exam\b", r"\bexam\b", r"\bheent\b", r"\blungs\b", r"\bextremities\b", r"\bno edema\b"],
        "Labs & Imaging": [r"\blab\b", r"\blabs\b", r"\bwbc\b", r"\bhgb\b", r"\bx-ray\b", r"\bct scan\b", r"\bmri\b", r"\bimaging\b", r"\bekg\b"],
        "Medications": [r"\bmedications?:\b", r"\binfusion\b", r"\bscheduled meds\b", r"\bprn meds\b"],
        "MDM": [r"\bmdm\b", r"\bmedical decision\b", r"\bplan\b", r"\bassessment\b", r"\bdifferential\b"],
        "Prior to Admission": [r"\bprior to admission\b", r"\bpta\b", r"\bbefore arrival\b", r"\bprior treatment\b"]
    }
    for section, patterns in keyword_map.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return section
    return "Uncategorized"

def split_text_into_segments(text: str) -> list:
    """
    Split the input text into segments while avoiding incorrect splits on abbreviations.
    """
    known_abbreviations = ["Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "Sr.", "Jr."]
    
    raw_segments = re.split(r'(?<!\b(?:' + '|'.join(map(re.escape, known_abbreviations)) + r'))(?<=[.!?])\s+', text)
    
    return [seg.strip() for seg in raw_segments if seg.strip()]

def format_ed_data(text: str, abbr_dict: dict) -> dict:
    """
    Format ED note data by classifying segments and applying abbreviation replacements efficiently.
    """
    if not text or not text.strip():
        return {"Error": "No data provided"}

    structured_data = {section: "" for section in SECTION_LABELS}
    segments = split_text_into_segments(text)
    
    for segment in segments:
        section = classify_segment(segment)
        structured_data[section] += segment.strip() + "\n\n"

    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, abbr_dict.keys())) + r')\b', re.IGNORECASE)
    
    for section, content in structured_data.items():
        structured_data[section] = pattern.sub(lambda match: abbr_dict[match.group(0).lower()], content).strip()

    return structured_data

def convert_to_soap(structured_data: dict) -> dict:
    """
    Convert the structured data into a nested JSON format optimized for GPT-based H&P generation.
    """
    soap_data = {
        "Subjective": {},
        "Objective": {},
        "Assessment": {},
        "Plan": {},
        "Other": {}
    }
    
    for section, content in structured_data.items():
        if content:
            soap_category = section_to_soap.get(section, "Other")
            soap_data[soap_category][section] = content.strip()

    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "note_version": "1.1"
    }
    
    return {"metadata": metadata, "note": soap_data}

# Process and output the JSON when the user clicks the button
if st.button("Format Data to Enhanced SOAP JSON"):
    result = format_ed_data(raw_text, abbreviations)
    if "Error" in result:
        st.error(result["Error"])
    else:
        soap_result = convert_to_soap(result)
        st.subheader("Structured ED Note (Optimized for GPT-Based H&P)")
        st.json(soap_result)
