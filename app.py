import json
import re
import streamlit as st
from datetime import datetime, timezone
import spacy  # For Named Entity Recognition (NER)

# Load spaCy's English model for NER with caching to avoid repeated downloads
@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        st.warning("Downloading 'en_core_web_sm' model... This may take a few minutes.")
        spacy.cli.download("en_core_web_sm")
        return spacy.load("en_core_web_sm")

nlp = load_spacy_model()

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

def remove_names(text: str) -> str:
    """
    Remove names from the text using spaCy's Named Entity Recognition (NER).
    """
    doc = nlp(text)
    cleaned_text = []
    for token in doc:
        if token.ent_type_ != "PERSON":  # Filter out PERSON entities
            cleaned_text.append(token.text)
    return " ".join(cleaned_text)

def classify_segment(segment: str) -> str:
    """
    Classify a text segment into an ED note section using rule-based keyword matching.
    """
    text = segment.lower()
    keyword_map = {
        "Chief Complaint": ["chief complaint", "c/o", "complains of"],
        "HPI": ["hpi", "history of present illness"],
        "ROS": ["ros", "review of systems", "denies", "reports no"],
        "ED Vitals": ["blood pressure", "bp", "heart rate", "hr", "o2 sat", "temperature", "vitals"],
        "Physical Exam": ["physical exam", "exam", "heent", "lungs", "extremities", "no edema"],
        "Labs & Imaging": ["lab", "labs", "wbc", "hgb", "x-ray", "ct scan", "mri", "imaging", "ekg"],
        "Medications": ["medications:", "infusion", "scheduled meds", "prn meds"],
        "MDM": ["mdm", "medical decision", "plan", "assessment", "differential"],
        "Prior to Admission": ["prior to admission", "pta", "before arrival", "prior treatment"]
    }
    for section, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            return section
    return "Uncategorized"

def split_text_into_segments(text: str) -> list:
    """
    Split the input text into sentences without breaking abbreviations.
    Uses word-based splitting instead of regex look-behind.
    """
    known_abbreviations = {"Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "Sr.", "Jr."}
    words = text.split()
    segments = []
    current_sentence = []
    for word in words:
        current_sentence.append(word)
        # End segment at sentence-ending punctuation if not an abbreviation
        if word.endswith((".", "!", "?")) and word not in known_abbreviations:
            segments.append(" ".join(current_sentence))
            current_sentence = []
    if current_sentence:
        segments.append(" ".join(current_sentence))
    return [s.strip() for s in segments if s.strip()]

def format_ed_data(text: str, abbr_dict: dict) -> dict:
    """
    Format ED note data with abbreviation replacement.
    """
    if not text or not text.strip():
        return {"Error": "No data provided"}
    # Remove personal names using NER
    text = remove_names(text)
    structured_data = {section: "" for section in SECTION_LABELS}
    # Split text into sentence segments
    segments = split_text_into_segments(text)
    for segment in segments:
        section = classify_segment(segment)
        structured_data[section] += segment.strip() + "\n\n"
    # Replace full terms with abbreviations (case-insensitive whole-word matches)
    for section, content in structured_data.items():
        for term, abbr in abbr_dict.items():
            pattern = re.compile(rf'\b{re.escape(term)}\b', flags=re.IGNORECASE)
            content = pattern.sub(abbr, content)
        structured_data[section] = content.strip()
    return structured_data

def convert_to_soap(structured_data: dict) -> dict:
    """
    Convert the structured data into a nested JSON (SOAP format) for output.
    """
    soap_data = {"Subjective": {}, "Objective": {}, "Assessment": {}, "Plan": {}, "Other": {}}
    for section, content in structured_data.items():
        if content.strip():
            soap_category = section_to_soap.get(section, "Other")
            soap_data[soap_category][section] = content.strip()
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "note_version": "1.1"
    }
    return {"metadata": metadata, "note": soap_data}

# Run processing when button is clicked
if st.button("Format Data to Enhanced SOAP JSON"):
    result = format_ed_data(raw_text, abbreviations)
    if "Error" in result:
        st.error(result["Error"])
    else:
        soap_result = convert_to_soap(result)
        st.subheader("Structured ED Note (Optimized for GPT-Based H&P)")
        st.json(soap_result)
