import streamlit as st
import re
import json

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
    "pulmonary embolism": "PE"
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
    # Define common section headers (allowing variations in spacing/capitalization)
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

    # Remove extra spaces and line breaks
    text = re.sub(r"\n+", "\n", text.strip())

    # Search for section headers and extract content dynamically
    for section, pattern in section_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_index = match.start()
            next_section_index = len(text)

            # Find the next section header
            for other_pattern in section_patterns.values():
                next_match = re.search(other_pattern, text[start_index + 1:], re.IGNORECASE)
                if next_match:
                    next_section_index = min(next_section_index, start_index + 1 + next_match.start())

            # Extract section content and clean formatting
            section_content = text[start_index:next_section_index].strip()
            structured_data[section] = re.sub(pattern, "", section_content, flags=re.IGNORECASE).strip()

    # Detect and insert missing sections
    for section in section_patterns.keys():
        if section not in structured_data:
            structured_data[section] = "[Missing Data]"

    # Automatically replace long medical terms with abbreviations
    formatted_output = ""
    for section, content in structured_data.items():
        for term, abbr in abbreviations.items():
            content = re.sub(rf"\b{term}\b", abbr, content, flags=re.IGNORECASE)
        formatted_output += f"**{section}**:\n{content}\n\n"
    
    return formatted_output if formatted_output else "No structured data detected."

# Button to process the data
if st.button("Format Data"):
    structured_text = format_ed_data(raw_text, user_abbreviations)
    st.text_area("Formatted Output:", structured_text, height=400)

