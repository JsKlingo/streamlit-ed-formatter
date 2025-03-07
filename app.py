import streamlit as st

st.title("ED Note Formatter")  # App title

# Text input area for raw ED data
raw_text = st.text_area("Paste your raw ED data here:")

if st.button("Format Data"):
    # Simulated cleaning function
    structured_text = raw_text.replace("\n", " ").replace("CC:", "\nChief Complaint:")
    st.text_area("Structured Output:", structured_text, height=300)

