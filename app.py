import streamlit as st
import os
import io
import zipfile
import json

# ---------- Step 1: Remove commas (preserve speaker labels like "Agent:") ----------
def clean_text(content: str) -> str:
    lines = content.splitlines()
    cleaned = [line.replace(",", "") for line in lines if ':' in line]
    return "\n".join(cleaned)

# ---------- Step 2: Convert cleaned text to JSON (full string, not split) ----------
def text_to_json(text: str) -> dict:
    return {"transcript": text}

# ---------- Step 3: Reformat JSON into transcript string with metadata ----------
def reformat_json_transcript(data: dict) -> dict:
    transcript = data["transcript"]
    turns = [t.strip() for t in transcript.split('\n') if t.strip()]
    formatted_turns = []
    start_offset = 0

    for turn_id, turn in enumerate(turns):
        if ':' not in turn:
            continue
        speaker_id, words = turn.split(':', 1)
        word_count = len(words.strip().split())
        end_offset = start_offset + word_count
        line = f"{turn_id}, {start_offset:.2f}, {end_offset:.2f}, {speaker_id.strip()}, {words.strip()}"
        formatted_turns.append(line)
        start_offset = end_offset

    final_transcript = "turn ID, start time, end time, speaker ID, words\n" + "\n".join(formatted_turns)
    return {"transcript": final_transcript}

# ---------- ZIP Creator: Combines all outputs into one ZIP with folders ----------
def create_combined_zip(cleaned_dict, json_dict, formatted_dict):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zipf:
        for filename, content in cleaned_dict.items():
            zipf.writestr(f"cleaned_txt/{filename}", content)

        for filename, content in json_dict.items():
            zipf.writestr(f"Text_json/{filename}", content)

        for filename, content in formatted_dict.items():
            zipf.writestr(f"json_timestamps/{filename}", content)

    buffer.seek(0)
    st.download_button(
        label="⬇️ Download Output.zip",
        data=buffer,
        file_name="Output.zip",
        mime="application/zip"
    )

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Transcript Processor", layout="centered")
st.title("📁 Upload Files:")

st.info("""
### 📝 Instructions:
1. Upload `zip` files containing `.txt` files.  
2. `.txt` files must start with speaker labels like `Agent:` or `Customer:`.   
3. This app will:
   -  Remove commas
   -  Convert cleaned text to JSON
   -  Format transcript with **turn ID**, **start time**, **end time**, **speaker ID**, and **words**
4. You will be able to **download the output** as ZIP files.
""")

uploaded_zip = st.file_uploader("Upload a ZIP file containing .txt files", type=["zip"])

if uploaded_zip:
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        st.success("📂 ZIP uploaded successfully. Processing files...")
        output_cleaned_texts = {}
        output_json_files = {}
        output_formatted_jsons = {}

        for file_name in zip_ref.namelist():
            if file_name.endswith(".txt") and not file_name.startswith("__MACOSX/"):
                with zip_ref.open(file_name) as file:
                    content = file.read().decode("utf-8")
                    
                    # Step 1: Clean text
                    cleaned_text = clean_text(content)
                    output_cleaned_texts[file_name] = cleaned_text
                    
                    # Step 2: Convert to JSON
                    json_data = text_to_json(cleaned_text)
                    json_string = json.dumps(json_data, ensure_ascii=False, indent=4)
                    output_json_files[file_name.replace(".txt", ".json")] = json_string
                    
                    # Step 3: Reformat JSON
                    reformatted = reformat_json_transcript(json_data)
                    reformatted_string = json.dumps(reformatted, ensure_ascii=False, indent=4)
                    output_formatted_jsons[file_name.replace(".txt", ".json")] = reformatted_string

    # Final Combined ZIP
    st.subheader("✅ Download Output Files")
    create_combined_zip(output_cleaned_texts, output_json_files, output_formatted_jsons)
