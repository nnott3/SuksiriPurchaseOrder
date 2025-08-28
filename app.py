from __future__ import annotations
from agentic_doc.parse import parse
from agentic_doc.utils import viz_parsed_document
from agentic_doc.config import VisualizationConfig
from bs4 import BeautifulSoup
import json
import pandas as pd
from io import StringIO
import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from typing import List
from pydantic import BaseModel, Field
from agentic_doc.parse import parse
from agentic_doc.connectors import LocalConnectorConfig
import streamlit as st
from PIL import Image, ImageOps
import time

from modelClass import ExtractedDocumentFieldsSchema
from utils.utils import build_rows, update_sheet, visualize_parsing, get_store_list


############################### Stream-Lit ##############################

# ---------- APP LAYOUT ----------
st.set_page_config(page_title="Suksiri Purchase Order App", layout="wide")
st.title("📄 Suksiri Purchase Order App")
st.write("Upload image files to extract purchase order data.")

# Multiple file uploader
uploaded_files = st.file_uploader(
    "Choose image files", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)
if uploaded_files:
    st.subheader("Uploaded Images")

    uploaded_files = sorted(uploaded_files, key=lambda x: x.name.lower())

    # --- Step 1: Show all originals side by side ---
    images_per_row = 4
    image_width = 300

    for i in range(0, len(uploaded_files), images_per_row):
        row_files = uploaded_files[i:i+images_per_row]

        # If the row has fewer than 4 images, append None placeholders
        if len(row_files) < images_per_row:
            row_files += [None] * (images_per_row - len(row_files))

        cols = st.columns(images_per_row)
        for col, uploaded_file in zip(cols, row_files):
            with col:
                if uploaded_file is not None:
                    img = ImageOps.exif_transpose(Image.open(uploaded_file))
                    st.image(img, caption=uploaded_file.name, width=image_width)
                else:
                    # empty placeholder
                    st.write("")


    for uploaded_file in uploaded_files:

        with st.expander(f"Extraction for {uploaded_file.name}", expanded=True):
            try:
                # Save uploaded file temporarily
                temp_path = f"temp_uploaded_image.{uploaded_file.name.split('.')[-1]}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())


                    # Side-by-side layout: left=image, right=progress + table
                    col_img, col_right = st.columns([1,1])

                    # Placeholder for left image (original → parsed later)
                    img_placeholder = col_img.empty()
                    image = ImageOps.exif_transpose(Image.open(uploaded_file))
                    img_placeholder.image(image, caption=f"Original {uploaded_file.name}", width=590)

                    # Placeholder for progress bar + table
                    with col_right:
                        st.info("Starting extraction...")
                        progress_placeholder = st.empty()
                        table_placeholder = st.empty()
                        

                    # Run actual extraction
                    start_time = time.time()
                    results = parse(temp_path, extraction_model=ExtractedDocumentFieldsSchema)
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    
                
                    # Show progress bar
                    with progress_placeholder.container():
                        progress_bar = st.progress(0)
                        for i in range(10):  # simulate extraction steps
                            time.sleep(0.5)
                            progress_bar.progress((i+1)*100//10)

                        st.success(f"Extraction complete for {uploaded_file.name} in {elapsed_time:.2f} seconds!")

                    fields = results[0].extraction
                    rows = build_rows(fields)
                    

                    # Visualize parsing
                    parsed_images = [ImageOps.exif_transpose(img) for img in visualize_parsing(temp_path, results[0])]
                    # parsed_images = [temp_path]
                    with img_placeholder.container():
                        for idx, img in enumerate(parsed_images):
                            st.image(img, caption=f"Parsed visualization {idx+1} for {uploaded_file.name}", width=590)
            
                    # Editable table
                    with table_placeholder.container():
                        edited_df = st.data_editor(pd.DataFrame(rows),
                                                    use_container_width=True,
                                                    num_rows="dynamic",
                                                    key=f"editor_{uploaded_file.name}"  # unique key per file
                                                    )
                        # Approve/Reject inside a form to prevent rerun issues
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Approve", key=f"approve_{uploaded_file.name}"):
                                update_sheet(edited_df.to_dict())
                                st.success(f"✅ Data sent to Google Sheets for {uploaded_file.name}!")
                        with col2:
                            if st.button("❌ Reject", key=f"reject_{uploaded_file.name}"):
                                st.warning(f"Rejected {uploaded_file.name}")

            except Exception as e:
                st.error(f"Error during extraction for {uploaded_file.name}: {e}")
    
else:
    st.info("No images uploaded yet.")
# # ---------- END OF APP ----------
# # rows = [
#                 # {
#                 #         "วันเดือนปี": "01/08/2025",
#                 #         "ร้านค้า": "ร้านสมาร์ทมาร์ท",
#                 #         "เลขกำกับ": "INV001",
#                 #         "รายการสินค้า": "นมสด",
#                 #         "จำนวน": 2,
#                 #         "หน่วย": "ขวด",
#                 #         "ราคาต่อหน่วย": 45.0,
#                 #         "ลดราคา(%)": 10,
#                 #         "ลดราคา(บาท)": 9.0
#                 #     },
#                 #     {
#                 #         "วันเดือนปี": "02/08/2025",
#                 #         "ร้านค้า": "ร้านสมาร์ทมาร์ท",
#                 #         "เลขกำกับ": "INV002",
#                 #         "รายการสินค้า": "ขนมปัง",
#                 #         "จำนวน": 1,
#                 #         "หน่วย": "ชิ้น",
#                 #         "ราคาต่อหน่วย": 25.0,
#                 #         "ลดราคา(%)": 0,
#                 #         "ลดราคา(บาท)": 0.0
#                 #     },
#                 #     {
#                 #         "วันเดือนปี": "02/08/2025",
#                 #         "ร้านค้า": "ร้านฟู้ดแลนด์",
#                 #         "เลขกำกับ": "INV003",
#                 #         "รายการสินค้า": "ไข่ไก่",
#                 #         "จำนวน": 12,
#                 #         "หน่วย": "ฟอง",
#                 #         "ราคาต่อหน่วย": 5.0,
#                 #         "ลดราคา(%)": 5,
#                 #         "ลดราคา(บาท)": 0.6
#                 #     },
#                 #     {
#                 #         "วันเดือนปี": "03/08/2025",
#                 #         "ร้านค้า": "ร้านฟู้ดแลนด์",
#                 #         "เลขกำกับ": "INV004",
#                 #         "รายการสินค้า": "ข้าวสาร",
#                 #         "จำนวน": 5,
#                 #         "หน่วย": "กก.",
#                 #         "ราคาต่อหน่วย": 40.0,
#                 #         "ลดราคา(%)": 0,
#                 #         "ลดราคา(บาท)": 0.0
#                 #     }
#                 # ]