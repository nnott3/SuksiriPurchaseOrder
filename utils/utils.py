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

def get_google_credentials():
    """Get Google credentials from Streamlit secrets or local file."""
    try:
        # Try to get from Streamlit secrets first
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            credentials_dict = dict(st.secrets['gcp_service_account'])
            return Credentials.from_service_account_info(
                credentials_dict, 
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
        else:
            # Fallback to local file for development
            if os.path.exists("suksiri-purchase-test-0f09e84df6dd.json"):
                return Credentials.from_service_account_file(
                    "suksiri-purchase-test-0f09e84df6dd.json", 
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
            else:
                raise FileNotFoundError("No credentials found in secrets or local file")
    except Exception as e:
        st.error(f"Error loading Google credentials: {str(e)}")
        st.stop()

def get_spreadsheet_id():
    """Get spreadsheet ID from secrets or use default."""
    try:
        if hasattr(st, 'secrets') and 'google_sheets' in st.secrets:
            return st.secrets['google_sheets']['spreadsheet_id']
        else:
            return "17chQLsKcpyZNnJyw8Ads-WRz45kNvI1AbvwsdIlcXqs"
    except:
        return "17chQLsKcpyZNnJyw8Ads-WRz45kNvI1AbvwsdIlcXqs"


############################### Store_list ##############################
def get_store_list():
    """Fetch and process store list from Google Sheets."""
    
    try:
        # Get credentials and spreadsheet ID
        creds = get_google_credentials()
        spreadsheet_id = get_spreadsheet_id()
        
        client = gspread.authorize(creds)
        service = build("sheets", "v4", credentials=creds)

        sheets = client.open_by_key(spreadsheet_id)
        store_data = sheets.worksheet("ข้อมูลร้านค้า")
        sheet = sheets.worksheet("รายการสินค้า")

        table_range = "ข้อมูลร้านค้า!B2:G"  

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=table_range
        ).execute()

        values = result.get("values", [])

        # Convert to DataFrame
        df_table2 = pd.DataFrame(values[1:], columns=values[0])  # first row is header

        # --- Keep only rows where 'ร้านค้า' is not None or empty ---
        df_filtered = df_table2[df_table2['ร้านค้า'].notna() & (df_table2['ร้านค้า'] != '')].copy()

        # --- Convert 'ยังไม่รวม VAT' from string 'TRUE'/'FALSE' to boolean ---
        df_filtered['ยังไม่รวม VAT'] = df_filtered['ยังไม่รวม VAT'].map(lambda x: True if str(x).upper() == 'TRUE' else False)

        unique_store_list = df_filtered['ร้านค้า'].unique().tolist()

        return unique_store_list, df_filtered
    
    except Exception as e:
        st.error(f"Error fetching store list: {str(e)}")
        return [], pd.DataFrame()



############################### Build_Rows ##############################
def build_rows(fields):
    metadata = {
        "วันเดือนปี": fields.documentInfo.documentDate,
        "ร้านค้า": fields.companyInfo.companyName,
        "เลขกำกับ": fields.documentInfo.documentNumber,
        # "taxId": fields.companyInfo.taxId,
        # "customerName": fields.customerInfo.customerName,
        # "grossAmount": fields.totals.grossAmount,
        # "netAmount": fields.totals.netAmount,
        # "vat": fields.totals.vat,
        # "grandTotal": fields.totals.grandTotal,
    }
    rows = []
    # Handle items
    for i, item in enumerate(fields.items):
        row = metadata.copy()
        row["รายการสินค้า"] = item.description
        row["จำนวน"] = float(item.quantity.replace(",", ""))
        row["หน่วย"] = item.unitName
        row["ราคาต่อหน่วย"] = float(item.unitPrice.replace(",", ""))
        
        # set defaults to empty cells
        row["ลดราคา(%)"], row["ลดราคา(บาท)"] = "", ""
        if item.discountType == "บาท":
            row["ลดราคา(บาท)"] = float(item.discount.strip('฿').replace(",", ""))
        elif item.discountType == "Percentage":
            row["ลดราคา(%)"] = float(item.discount.strip('%'))

        rows.append(row)
    
    return rows

############################### update_sheet ##############################
def update_sheet(rows):
    try:
        # Get credentials and spreadsheet ID
        creds = get_google_credentials()
        spreadsheet_id = get_spreadsheet_id()
        
        client = gspread.authorize(creds)
        service = build("sheets", "v4", credentials=creds)

        sheets = client.open_by_key(spreadsheet_id)
        store_data = sheets.worksheet("ข้อมูลร้านค้า")
        sheet = sheets.worksheet("COPY รายการสินค้า")

        df = pd.DataFrame(rows)
        values = df.values.tolist()
        
        start_row = len(sheet.get_all_values()) + 1  # +1 because Sheets are 1-indexed

        for i, row in enumerate(values):
            current_row = start_row + i

            # Column J: ยอดเงิน
            row.append("=Transactions_2[จำนวน]*Transactions_2[ราคาต่อหน่วย]")

            # Column K: ยอดเงินหลังลดราคา
            row.append("=IF(Transactions_2[ลดราคา(%)], Transactions_2[ยอดเงิน]*(1-Transactions_2[ลดราคา(%)]/100), Transactions_2[ยอดเงิน]-Transactions_2[ลดราคา(บาท)])")

            # Column L: ยอดรวมต่อรายการ
            row.append(f"=SUMIF(Transactions_2[เลขกำกับ], C{current_row}, Transactions_2[ยอดเงินหลังลดราคา])")

            # Column M: ยอดรวมหลังภาษี
            row.append(
                f"=IF(XLOOKUP(B{current_row}, Table2[ร้านค้า], Table2[ยังไม่รวม VAT], FALSE), $L{current_row}*1.07, $L{current_row})"
            )

        # Append all rows to the sheet
        sheet.append_rows(values, value_input_option="USER_ENTERED")

        return pd.DataFrame(values)
    
    except Exception as e:
        st.error(f"Error updating sheet: {str(e)}")
        return pd.DataFrame()
    
############################### Visualize_parsing ##############################
def visualize_parsing(filepath, parsed_doc):
    viz_config = VisualizationConfig(
        thickness=2,  # Thicker bounding boxes
        text_bg_opacity=0.8,  # More opaque text background
        font_scale=0.7,  # Larger text
        # color_map={
        #     ChunkType.TEXT: (255, 0, 0),  
        #     ChunkType.TABLE: (255, 255, 0), }
    )

    images = viz_parsed_document(
        filepath,
        parsed_doc,
        output_dir="picsFinished",
        viz_config=viz_config
    )
    return images

############################### Integrate ##############################
# config = LocalConnectorConfig()
# results = parse(config, 
#                 connector_path="./picsToExtract", 
#                 connector_pattern="*.jpeg",
#                 extraction_model=ExtractedDocumentFieldsSchema
#                 )
# for result in results:
#     fields = result.extraction  
#     rows = build_rows(fields)
#     print(rows)
#     update_sheet(rows)
