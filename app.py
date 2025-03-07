import re
import streamlit as st

# Pre-defined section labels for the ED note
SECTION_LABELS = [
    "Chief Complaint", "HPI", "ROS", "ED Vitals", "Physical Exam",
    "Labs & Imaging", "MDM", "Prior to Admission", "Uncategorized"
]

# Title of the Streamlit app
st.title("ED Note Formatter")

# Text area for inputting raw ED note data
raw_text = st.text_area("Paste your raw ED note data here:")

# Hardcoded abbreviation mappings (term -> abbreviation or expanded form)
abbreviations = {
    "myocardial infarction": "MI",
    "hypertension": "HTN",
    "c/o": "complains of",
    "SOB": "shortness of breath",
    # Add more abbreviations or expansions as needed
}

def classify_segment(segment: str) -> str:
    """
    Classify a text segment into an ED note section using keyword-based rules.
    Returns the section label or "Uncategorized" if no rule matches.
    """
    text = segment.lower()
    # Rule-based keywords for each section:
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
    if any(kw in text for kw in ["lab", "labs", "wbc", "hgb", "x-ray", "ct scan", "mri", "imaging", "blood culture", "ekg"]):
        return "Labs & Imaging"
    if any(kw in text for kw in ["mdm", "medical decision", "plan", "assessment", "will monitor", "differential"]):
        return "MDM"
    if any(kw in text for kw in ["prior to admission", "pta", "before arrival", "prior treatment"]):
        return "Prior to Admission"
    return "Uncategorized"

def split_text_into_segments(text: str) -> list:
    """
    Split the input text into segments (e.g., sentences or paragraphs) for classification.
    """
    # Split by sentence-ending punctuation (., ?, !) followed by whitespace
    segments = re.split(r'(?<=[\.!?])\s+', text)
    return [seg.strip() for seg in segments if seg.strip()]

def format_ed_data(text: str, abbr_dict: dict) -> dict:
    """
    Format ED note data by classifying segments and replacing terms with abbreviations.
    Returns a dictionary of section labels to formatted text.
    """
    if not text or not text.strip():
        return {"Error": "No data provided"}

    # Initialize all sections with empty strings
    structured_data = {section: "" for section in SECTION_LABELS}

    # Split the input text into meaningful segments
    segments = split_text_into_segments(text)

    # Classify each segment and append to the appropriate section
    for segment in segments:
        section = classify_segment(segment)
        structured_data[section] += segment.strip() + "\n\n"

    # Apply abbreviation replacements in each section's content
    for section, content in structured_data.items():
        for term, abbr in abbr_dict.items():
            # Use case-insensitive replacement for whole words
            content = re.sub(rf"(?i)\b{re.escape(term)}\b", abbr, content)
        structured_data[section] = content.strip()  # Remove trailing newlines/spaces

    return structured_data

# Process the data when the user clicks the format button
if st.button("Format Data"):
    result = format_ed_data(raw_text, abbreviations)

    if "Error" in result:
        st.error(result["Error"])
    else:
        st.subheader("Structured ED Note")
        # Display each section with its content as plain text
        for section in SECTION_LABELS:
            content = result.get(section, "")
            if content:  # Only display sections that have content
                st.markdown(f"**{section}:**")
                st.write(content)
