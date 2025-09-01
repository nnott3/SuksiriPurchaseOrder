#  SuksiriPurchaseOrder

A **Streamlit web app** to handle Purchase Orders (POs) using **Agentic Document Extraction** and integration with **Google Sheets**.

Try using the app here: [SuksiriPurchaseOrder](https://suksiripurchaseorder.streamlit.app/)

---

##  Features

- Upload or scan PO documents and extract structured data using AI-powered doc extraction, working both in English and Thai.
- Extract features including วันเดือนปี, ร้านค้า, เลขกำกับ, ชื่อรายการสินค้า,จำนวน, หน่วย, ราคาต่อหน่วย, ลดราคา(%),ลดราคา(บาท)
- Integrate with Google Sheets to store and update. Match supplier and product names with existing database
- Automatically calculate total purchase order per bill (with or without VAT)
- Review and edit extracted info with UI from Streamlit.

---
