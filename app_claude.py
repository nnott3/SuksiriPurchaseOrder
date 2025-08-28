
# from __future__ import annotations
# from agentic_doc.parse import parse
# from agentic_doc.utils import viz_parsed_document
# from agentic_doc.config import VisualizationConfig
# from bs4 import BeautifulSoup
# import json
# import pandas as pd
# from io import StringIO
# import os
# import gspread
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
# from typing import List
# from pydantic import BaseModel, Field
# from agentic_doc.parse import parse
# from agentic_doc.connectors import LocalConnectorConfig
# import streamlit as st
# from PIL import Image, ImageOps
# import time

# from modelClass import ExtractedDocumentFieldsSchema
# from utils.utils import build_rows, update_sheet, visualize_parsing, get_store_list


# ############################### Stream-Lit ##############################

# # Initialize session state
# if 'extraction_results' not in st.session_state:
#     st.session_state.extraction_results = {}
# if 'processed_files' not in st.session_state:
#     st.session_state.processed_files = set()
# if 'approved_files' not in st.session_state:
#     st.session_state.approved_files = set()
# if 'rejected_files' not in st.session_state:
#     st.session_state.rejected_files = set()

# # ---------- APP LAYOUT ----------
# st.set_page_config(page_title="Suksiri Purchase Order App", layout="wide")
# st.title("📄 Suksiri Purchase Order App")
# st.write("Upload image files to extract purchase order data.")

# # Multiple file uploader
# uploaded_files = st.file_uploader(
#     "Choose image files", 
#     type=["png", "jpg", "jpeg"], 
#     accept_multiple_files=True
# )

# if uploaded_files:
#     st.subheader("Uploaded Images")

#     uploaded_files = sorted(uploaded_files, key=lambda x: x.name.lower())

#     # --- Step 1: Show all originals side by side ---
#     images_per_row = 4
#     image_width = 300

#     for i in range(0, len(uploaded_files), images_per_row):
#         row_files = uploaded_files[i:i+images_per_row]

#         # If the row has fewer than 4 images, append None placeholders
#         if len(row_files) < images_per_row:
#             row_files += [None] * (images_per_row - len(row_files))

#         cols = st.columns(images_per_row)
#         for col, uploaded_file in zip(cols, row_files):
#             with col:
#                 if uploaded_file is not None:
#                     img = ImageOps.exif_transpose(Image.open(uploaded_file))
#                     st.image(img, caption=uploaded_file.name, width=image_width)
#                 else:
#                     # empty placeholder
#                     st.write("")

#     # --- Step 2: Individual extraction sections ---
#     for uploaded_file in uploaded_files:
#         file_key = uploaded_file.name
        
#         with st.expander(f"Extraction for {uploaded_file.name}", expanded=True):
#             try:
#                 # Side-by-side layout: left=image, right=controls + table
#                 col_img, col_right = st.columns([1, 1])

#                 # Left column - Image display
#                 with col_img:
#                     # Show parsed visualization if available, otherwise show original
#                     if file_key in st.session_state.extraction_results and 'parsed_images' in st.session_state.extraction_results[file_key]:
#                         parsed_images = st.session_state.extraction_results[file_key]['parsed_images']
#                         for idx, img in enumerate(parsed_images):
#                             st.image(img, caption=f"Parsed visualization {idx+1} for {uploaded_file.name}", width=590)
#                     else:
#                         # Show original image (during extraction or before processing)
#                         image = ImageOps.exif_transpose(Image.open(uploaded_file))
#                         st.image(image, caption=f"Original {uploaded_file.name}", width=590)

#                 # Right column - Controls and results
#                 with col_right:
#                     # Status indicators
#                     if file_key in st.session_state.approved_files:
#                         st.success("✅ APPROVED - Data sent to Google Sheets!")
#                     elif file_key in st.session_state.rejected_files:
#                         st.warning("❌ REJECTED")
#                     elif file_key in st.session_state.processed_files:
#                         st.info("📊 Extraction completed - Ready for review")
#                     else:
#                         st.info("⏳ Ready for extraction")

#                     # Extraction button
#                     if file_key not in st.session_state.processed_files and file_key not in st.session_state.approved_files and file_key not in st.session_state.rejected_files:
#                         if st.button(f"🚀 Start Extraction", key=f"extract_{file_key}"):
#                             # Save uploaded file temporarily
#                             temp_path = f"temp_{file_key}.{uploaded_file.name.split('.')[-1]}"
#                             with open(temp_path, "wb") as f:
#                                 f.write(uploaded_file.getbuffer())

#                             # Show progress
#                             with st.spinner(f"Extracting data from {uploaded_file.name}..."):
#                                 progress_bar = st.progress(0)
                                
#                                 # Simulate progress
#                                 for i in range(5):
#                                     time.sleep(0.2)
#                                     progress_bar.progress((i+1)*20)
                                
#                                 # Run actual extraction
#                                 start_time = time.time()
#                                 results = parse(temp_path, extraction_model=ExtractedDocumentFieldsSchema)
#                                 end_time = time.time()
#                                 elapsed_time = end_time - start_time
                                
#                                 # Complete progress
#                                 progress_bar.progress(100)
                                
#                                 # Process results
#                                 fields = results[0].extraction
#                                 rows = build_rows(fields)
                                
#                                 # Visualize parsing
#                                 parsed_images = [ImageOps.exif_transpose(img) for img in visualize_parsing(temp_path, results[0])]
                                
#                                 # Store results in session state
#                                 st.session_state.extraction_results[file_key] = {
#                                     'rows': rows,
#                                     'parsed_images': parsed_images,
#                                     'elapsed_time': elapsed_time,
#                                     'fields': fields
#                                 }
#                                 st.session_state.processed_files.add(file_key)
                                
#                                 # Clean up temp file
#                                 if os.path.exists(temp_path):
#                                     os.remove(temp_path)
                            
#                             st.success(f"✅ Extraction completed in {elapsed_time:.2f} seconds!")
#                             st.rerun()

#                     # Show extraction results if available
#                     if file_key in st.session_state.extraction_results:
#                         result_data = st.session_state.extraction_results[file_key]
                        
#                         st.write(f"**Extraction time:** {result_data['elapsed_time']:.2f} seconds")
                        
#                         # Editable table
#                         if file_key not in st.session_state.approved_files and file_key not in st.session_state.rejected_files:
#                             st.write("**Extracted Data (Editable):**")
#                             edited_df = st.data_editor(
#                                 pd.DataFrame(result_data['rows']),
#                                 use_container_width=True,
#                                 num_rows="dynamic",
#                                 key=f"editor_{file_key}"
#                             )
                            
#                             # Update the stored data with edits
#                             st.session_state.extraction_results[file_key]['edited_rows'] = edited_df.to_dict()
                            
#                             # Approve/Reject buttons
#                             col1, col2 = st.columns(2)
#                             with col1:
#                                 if st.button("✅ Approve", key=f"approve_{file_key}"):
#                                     try:
#                                         # Use edited data for update
#                                         data_to_update = st.session_state.extraction_results[file_key].get('edited_rows', edited_df.to_dict())
#                                         update_sheet(data_to_update)
#                                         st.session_state.approved_files.add(file_key)
#                                         st.rerun()
#                                     except Exception as e:
#                                         st.error(f"Error updating sheet: {e}")
                                        
#                             with col2:
#                                 if st.button("❌ Reject", key=f"reject_{file_key}"):
#                                     st.session_state.rejected_files.add(file_key)
#                                     st.rerun()
                        
#                         else:
#                             # Show final data (read-only)
#                             st.write("**Final Data:**")
#                             final_data = st.session_state.extraction_results[file_key].get('edited_rows', result_data['rows'])
#                             st.dataframe(pd.DataFrame(final_data), use_container_width=True)

#             except Exception as e:
#                 st.error(f"Error during extraction for {uploaded_file.name}: {e}")

#     # Summary section
#     if uploaded_files:
#         st.subheader("📊 Processing Summary")
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric("Total Files", len(uploaded_files))
#         with col2:
#             st.metric("Processed", len(st.session_state.processed_files))
#         with col3:
#             st.metric("Approved", len(st.session_state.approved_files))
#         with col4:
#             st.metric("Rejected", len(st.session_state.rejected_files))

#         # Reset button
#         if st.button("🔄 Reset All", type="secondary"):
#             st.session_state.extraction_results = {}
#             st.session_state.processed_files = set()
#             st.session_state.approved_files = set()
#             st.session_state.rejected_files = set()
#             st.rerun()

# else:
#     st.info("No images uploaded yet.")

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

# Initialize session state
if 'extraction_results' not in st.session_state:
    st.session_state.extraction_results = {}
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = set()
if 'approved_files' not in st.session_state:
    st.session_state.approved_files = set()
if 'rejected_files' not in st.session_state:
    st.session_state.rejected_files = set()
if 'extracting' not in st.session_state:
    st.session_state.extracting = False

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

    # --- Step 2: Master extraction button ---
    st.subheader("🚀 Extraction Control")
    
    # Check if any files are not processed
    unprocessed_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files and f.name not in st.session_state.approved_files and f.name not in st.session_state.rejected_files]
    
    if unprocessed_files:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 Start All Extractions", type="primary"):
                st.session_state.extracting = True
                st.rerun()
        with col2:
            st.write(f"Ready to process {len(unprocessed_files)} image(s)")
    else:
        st.success("✅ All images have been processed!")

    # --- Step 3: Individual extraction results ---
    for uploaded_file in uploaded_files:
        file_key = uploaded_file.name
        
        with st.expander(f"Extraction for {uploaded_file.name}", expanded=True):
            try:
                # Side-by-side layout: left=image, right=controls + table
                col_img, col_right = st.columns([1, 1])

                # Left column - Image display
                with col_img:
                    # Show parsed visualization if available, otherwise show original
                    if file_key in st.session_state.extraction_results and 'parsed_images' in st.session_state.extraction_results[file_key]:
                        parsed_images = st.session_state.extraction_results[file_key]['parsed_images']
                        for idx, img in enumerate(parsed_images):
                            st.image(img, caption=f"Parsed visualization {idx+1} for {uploaded_file.name}", width=590)
                    else:
                        # Show original image (during extraction or before processing)
                        image = ImageOps.exif_transpose(Image.open(uploaded_file))
                        st.image(image, caption=f"Original {uploaded_file.name}", width=590)

                # Right column - Controls and results
                with col_right:
                    # Status indicators
                    if file_key in st.session_state.approved_files:
                        st.success("✅ APPROVED - Data sent to Google Sheets!")
                    elif file_key in st.session_state.rejected_files:
                        st.warning("❌ REJECTED")
                    elif file_key in st.session_state.processed_files:
                        st.info("📊 Extraction completed - Ready for review")
                    else:
                        st.info("⏳ Ready for extraction")

                    # Show extraction progress if currently processing this file
                    if (st.session_state.get('extracting', False) and 
                        file_key not in st.session_state.processed_files and 
                        file_key not in st.session_state.approved_files and 
                        file_key not in st.session_state.rejected_files):
                        
                        # Check if this is the file currently being processed
                        unprocessed_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files and f.name not in st.session_state.approved_files and f.name not in st.session_state.rejected_files]
                        current_file_index = None
                        for idx, f in enumerate(unprocessed_files):
                            if f.name == file_key:
                                current_file_index = idx
                                break
                        
                        if current_file_index is not None:
                            # Save uploaded file temporarily
                            temp_path = f"temp_{file_key}.{uploaded_file.name.split('.')[-1]}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Show progress
                            st.info(f"Starting extraction...")
                            progress_bar = st.progress(0)
                            
                            # Simulate progress steps
                            for i in range(10):
                                time.sleep(0.5)
                                progress_bar.progress((i+1)*10)
                            
                            # Run actual extraction
                            start_time = time.time()
                            results = parse(temp_path, extraction_model=ExtractedDocumentFieldsSchema)
                            end_time = time.time()
                            elapsed_time = end_time - start_time
                            
                            # Process results
                            fields = results[0].extraction
                            rows = build_rows(fields)
                            
                            # Visualize parsing
                            parsed_images = [ImageOps.exif_transpose(img) for img in visualize_parsing(temp_path, results[0])]
                            
                            # Store results in session state
                            st.session_state.extraction_results[file_key] = {
                                'rows': rows,
                                'parsed_images': parsed_images,
                                'elapsed_time': elapsed_time,
                                'fields': fields
                            }
                            st.session_state.processed_files.add(file_key)
                            
                            # Clean up temp file
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            
                            st.success(f"Extraction complete for {uploaded_file.name} in {elapsed_time:.2f} seconds!")

                    # Show extraction results if available
                    if file_key in st.session_state.extraction_results:
                        result_data = st.session_state.extraction_results[file_key]
                        
                        st.write(f"**Extraction time:** {result_data['elapsed_time']:.2f} seconds")
                        
                        # Editable table
                        if file_key not in st.session_state.approved_files and file_key not in st.session_state.rejected_files:
                            st.write("**Extracted Data (Editable):**")
                            edited_df = st.data_editor(
                                pd.DataFrame(result_data['rows']),
                                use_container_width=True,
                                num_rows="dynamic",
                                key=f"editor_{file_key}"
                            )
                            
                            # Update the stored data with edits
                            st.session_state.extraction_results[file_key]['edited_rows'] = edited_df.to_dict()
                            
                            # Approve/Reject buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Approve", key=f"approve_{file_key}"):
                                    try:
                                        # Use edited data for update
                                        data_to_update = st.session_state.extraction_results[file_key].get('edited_rows', edited_df.to_dict())
                                        update_sheet(data_to_update)
                                        st.session_state.approved_files.add(file_key)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating sheet: {e}")
                                        
                            with col2:
                                if st.button("❌ Reject", key=f"reject_{file_key}"):
                                    st.session_state.rejected_files.add(file_key)
                                    st.rerun()
                        
                        else:
                            # Show final data (read-only)
                            st.write("**Final Data:**")
                            final_data = st.session_state.extraction_results[file_key].get('edited_rows', result_data['rows'])
                            st.dataframe(pd.DataFrame(final_data), use_container_width=True)

            except Exception as e:
                st.error(f"Error during extraction for {uploaded_file.name}: {e}")

    # Summary section
    if uploaded_files:
        st.subheader("📊 Processing Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Files", len(uploaded_files))
        with col2:
            st.metric("Processed", len(st.session_state.processed_files))
        with col3:
            st.metric("Approved", len(st.session_state.approved_files))
        with col4:
            st.metric("Rejected", len(st.session_state.rejected_files))

        # Reset button
        if st.button("🔄 Reset All", type="secondary"):
            st.session_state.extraction_results = {}
            st.session_state.processed_files = set()
            st.session_state.approved_files = set()
            st.session_state.rejected_files = set()
            st.rerun()

else:
    st.info("No images uploaded yet.")