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

from utils.utils import get_store_list, update_sheet, build_rows, visualize_parsing

unique_store_list, _ = get_store_list()
####################### ExtractedDocumentFieldsSchema Class ##############################
class CompanyInfo(BaseModel):
    companyName: str = Field(
        ...,
        description=f'Identify the official name of the seller/supplier company as stated in the document. Compare it to the following list of known companies: [{", ".join(unique_store_list)}]. Return the closest match, ignoring common words like ["ห้างหุ้นส่วนจำกัด", "บริษัท", "จำกัด", "บจก.", "หจก.", "จํากัด", "ก้าวไกล"] for matching purposes. If no sufficiently similar match is found, retain the original text from the document.',
        title='Company Name',
    )
    taxId: str = Field(
        ...,
        description="The seller/supplier company's tax identification number.",
        title='Tax Identification Number',
    )


class CustomerInfo(BaseModel):
    customerName: str = Field(
        ..., description='The name of the customer or recipient.', title='Customer Name'
    )
    

class DocumentInfo(BaseModel):
    documentNumber: str = Field(
        ...,
        description='Unique identifier or reference number(เลขที่กำกับ) for the document.',
        title='Document Number',
    )
    documentDate: str = Field(
        ..., description='Date the document was issued with Year formatted in คริสต์ศักราช (ค.ศ.)/AD (Anno Domini) if it was initially written in the format of พุทธศักราช (พ.ศ.)/BE (Buddhist Era)', title='Document Date'
    )
    


class Item(BaseModel):
    description: str = Field(
        ..., description='Description of the item or service.', title='Description'
    )
    quantity: str = Field(..., description='Quantity of the item.', title='Quantity')
    unitPrice: str = Field(
        ..., description='Price per unit of the item.', title='Unit Price'
    )
    unitName: str = Field(..., description='Unit of measurement for the item, for example, meter, Pcs, ea, kg, box, อัน, ใบ, เส้น, ท่อน, ตัว, กระป๋อง, หลอด, ม้วน', title='Unit Name')
    amount: str = Field(..., description='Total amount for the item.', title='Amount')
    discount: str = Field(..., description='Discount applied to the item.', title='Item Discount')
    discountType: str = Field(..., description='Type of discount applied in Thai Baht or in Percentage or No Discount', title='Discount Type')

class Totals(BaseModel):
    grossAmount: str = Field(
        ...,
        description='Total gross amount before discounts and taxes.',
        title='Gross Amount',
    )
    netAmount: str = Field(
        ..., description='Net amount after discounts.', title='Net Amount'
    )
    vat: str = Field(..., description='Value-added tax amount.', title='VAT')
    grandTotal: str = Field(
        ...,
        description='Total amount payable including all taxes.',
        title='Grand Total',
    )


class ExtractedDocumentFieldsSchema(BaseModel):
    
    companyInfo: CompanyInfo = Field(
        ...,
        description='Key company details from headers and form fields.',
        title='Company Information',
    )
    customerInfo: CustomerInfo = Field(
        ...,
        description='Details about the customer or recipient of the invoice/delivery.',
        title='Customer Information',
    )
    documentInfo: DocumentInfo = Field(
        ...,
        description='Key identifiers and dates for the document.',
        title='Document Information',
    )
    items: List[Item] = Field(
        ...,
        description='List of items, products, or services from the main table(s) in the document.',
        title='Itemized Table',
    )
    totals: Totals = Field(
        ...,
        description='Summary of financial totals from the document.',
        title='Totals and Summary',
    )
    