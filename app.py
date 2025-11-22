import streamlit as st
import pandas as pd
from docx import Document
from summarizer import summarize_text


st.title("AI Text Summarization Tool")

st.subheader("Enter Text or Upload a File")

# ----------- INPUT METHOD SELECTION -----------
input_method = st.radio(
    "Choose input method:",
    ["Upload File", "Type/Paste Text"]
)

text = ""

# ----------- TEXT INPUT OPTION -----------
if input_method == "Type/Paste Text":
    text = st.text_area("Enter your text here:", height=250)

# ----------- FILE UPLOAD OPTION -----------
elif input_method == "Upload File":
    uploaded_file = st.file_uploader("Upload a text, CSV, or Word file", type=["txt", "csv", "docx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".txt"):
            text = uploaded_file.read().decode("utf-8")

        elif uploaded_file.name.endswith(".docx"):
            doc = Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])

        elif uploaded_file.name.endswith(".csv"):
            data = pd.read_csv(uploaded_file)
            text_col = st.selectbox("Select the column to summarize", data.columns)
            text = " ".join(data[text_col].astype(str))


# ----------- IF TEXT AVAILABLE, SHOW SAMPLE + OPTIONS -----------
if text.strip():
    st.subheader("Original Text Sample")
    st.write(text[:1000] + ("..." if len(text) > 1000 else ""))

    # User options
    num_sentences = st.slider("Select number of sentences for summary", 1, 15, 5)
    correct_words = st.checkbox("Enable word correction (slow for large text)")

    # Summarize
    result = summarize_text(
        text,
        num_sentences=num_sentences,
        correct_words=correct_words
    )

    st.subheader("Summarized Text")
    # Display the HTML version on the webpage
    st.markdown(result["html"], unsafe_allow_html=True)

    # Download button
    st.download_button(
        label="Download Summary as TXT",
        data=result["text"],
        file_name="summary.txt",
        mime="text/plain"
    )
else:
    st.info("Please upload a file or enter text to summarize.")
