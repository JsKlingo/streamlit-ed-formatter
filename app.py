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

