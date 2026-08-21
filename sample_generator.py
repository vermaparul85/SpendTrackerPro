import os
import io
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_statements")

def ensure_sample_dir():
    if not os.path.exists(SAMPLE_DIR):
        os.makedirs(SAMPLE_DIR, exist_ok=True)

def generate_pdf_statement(filename: str, bank_title: str, card_title: str, account_number: str, member_name: str, transactions: list) -> str:
    """Generates a realistic multi-page PDF credit card/bank statement using ReportLab."""
    ensure_sample_dir()
    filepath = os.path.join(SAMPLE_DIR, filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{bank_title} - Monthly Account Statement")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Card/Account: {card_title} ({account_number}) | Card Member: {member_name}")
    c.drawString(50, height - 85, f"Statement Period: 01-Aug-2024 to 19-Aug-2024 | Currency: INR (₹)")
    c.line(50, height - 95, width - 50, height - 95)

    # Table Header
    y = height - 120
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Date")
    c.drawString(130, y, "Transaction Description")
    c.drawString(420, y, "Amount (INR ₹)")
    c.drawString(510, y, "Type")
    c.line(50, y - 5, width - 50, y - 5)

    # Table Rows
    y -= 25
    c.setFont("Helvetica", 9)

    for tx in transactions:
        if y < 60:  # New Page
            c.showPage()
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, height - 50, f"{bank_title} Statement (Continued)")
            y = height - 80

        c.drawString(50, y, tx["date"])
        c.drawString(130, y, tx["desc"][:45])
        c.drawString(420, y, f"{tx['amount']:,.2f}")
        c.drawString(510, y, tx["type"])
        y -= 20

    c.line(50, y - 5, width - 50, y - 5)
    c.drawString(50, y - 20, "End of Statement. Thank you for banking with us.")
    c.save()

    return filepath

def generate_sample_statements_bundle() -> list:
    """Generates a bundle of realistic sample statements for HDFC, ICICI, SBI, Axis."""
    samples = []

    # 1. HDFC Regalia Gold (Rahul - Primary Earner)
    hdfc_txs = [
        {"date": "02/08/2024", "desc": "UPI/4321908/SWIGGY FOOD GURGAON", "amount": 840.00, "type": "DR"},
        {"date": "04/08/2024", "desc": "AMAZON INDIA PAYMENTS SELLER", "amount": 4299.00, "type": "DR"},
        {"date": "06/08/2024", "desc": "BLINKIT STORE BLINKIT GROCERY", "amount": 1450.00, "type": "DR"},
        {"date": "08/08/2024", "desc": "HPCL FUEL PETROL PUMP", "amount": 2500.00, "type": "DR"},
        {"date": "10/08/2024", "desc": "NETFLIX ENTERTAINMENT SUBSCRIPTION", "amount": 649.00, "type": "DR"},
        {"date": "12/08/2024", "desc": "MAKEMYTRIP GOA FLIGHT TICKET", "amount": 18500.00, "type": "DR"},
        {"date": "14/08/2024", "desc": "REFUND MAKEMYTRIP CANCELLATION", "amount": 2500.00, "type": "CR"},
        {"date": "16/08/2024", "desc": "DMART RETAIL GROCERIES MUMBAI", "amount": 6820.00, "type": "DR"},
        {"date": "18/08/2024", "desc": "CRED PAYMENT HDFC CREDIT CARD", "amount": 25000.00, "type": "CR"}
    ]
    f1 = generate_pdf_statement("HDFC_Regalia_Rahul.pdf", "HDFC Bank", "HDFC Regalia Gold", "XXXX-XXXX-XXXX-4812", "Rahul", hdfc_txs)
    samples.append({"filename": "HDFC_Regalia_Rahul.pdf", "path": f1, "bank_code": "HDFC", "account_id": "hdfc_regalia_1", "member_id": 1})

    # 2. ICICI Amazon Pay (Ananya - Spouse)
    icici_txs = [
        {"date": "01/08/2024", "desc": "POS 4019 ZOMATO MEDIA GURGAON", "amount": 650.00, "type": "DR"},
        {"date": "03/08/2024", "desc": "AMAZON PAY FRESH GROCERIES", "amount": 3200.00, "type": "DR"},
        {"date": "05/08/2024", "desc": "ZEPTO INSTANT DELIVERY MUMBAI", "amount": 480.00, "type": "DR"},
        {"date": "07/08/2024", "desc": "MYNTRA DESIGNS FASHION", "amount": 3999.00, "type": "DR"},
        {"date": "09/08/2024", "desc": "AIRTEL BROADBAND & MOBILE BILL", "amount": 1499.00, "type": "DR"},
        {"date": "11/08/2024", "desc": "APOLLO PHARMACY HEALTHCARE", "amount": 1250.00, "type": "DR"},
        {"date": "15/08/2024", "desc": "BOOKMYSHOW MOVIE TICKETS", "amount": 920.00, "type": "DR"},
        {"date": "17/08/2024", "desc": "CULT FIT ANNUAL GYM MEMBERSHIP", "amount": 14500.00, "type": "DR"}
    ]
    f2 = generate_pdf_statement("ICICI_AmazonPay_Ananya.pdf", "ICICI Bank", "ICICI Amazon Pay Card", "XXXX-XXXX-XXXX-9102", "Ananya", icici_txs)
    samples.append({"filename": "ICICI_AmazonPay_Ananya.pdf", "path": f2, "bank_code": "ICICI", "account_id": "icici_amazon_2", "member_id": 2})

    # 3. SBI Cashback Card (Rahul - Primary Earner)
    sbi_txs = [
        {"date": "03/08/2024", "desc": "FLIPKART INTERNET ECOMMERCE", "amount": 8990.00, "type": "DR"},
        {"date": "05/08/2024", "desc": "UBER INDIA TRANSPORT RIDES", "amount": 540.00, "type": "DR"},
        {"date": "09/08/2024", "desc": "BIGBASKET SUPERMARKET", "amount": 2100.00, "type": "DR"},
        {"date": "13/08/2024", "desc": "TATA POWER ELECTRICITY BILL", "amount": 3450.00, "type": "DR"},
        {"date": "17/08/2024", "desc": "SWIGGY INSTAMART GROCERY", "amount": 890.00, "type": "DR"}
    ]
    f3 = generate_pdf_statement("SBI_Cashback_Rahul.pdf", "SBI Card", "SBI Cashback Credit Card", "XXXX-XXXX-XXXX-3341", "Rahul", sbi_txs)
    samples.append({"filename": "SBI_Cashback_Rahul.pdf", "path": f3, "bank_code": "SBI", "account_id": "sbi_cashback_1", "member_id": 1})

    # 4. Axis ACE Card (Rohan - Student)
    axis_txs = [
        {"date": "02/08/2024", "desc": "SPOTIFY MUSIC SUBSCRIPTION", "amount": 119.00, "type": "DR"},
        {"date": "05/08/2024", "desc": "SWIGGY FOOD DELIVERY", "amount": 340.00, "type": "DR"},
        {"date": "08/08/2024", "desc": "RAPIDO BIKE TAXI HYDERABAD", "amount": 85.00, "type": "DR"},
        {"date": "12/08/2024", "desc": "COLLEGE BOOKSTORE SUPPLIES", "amount": 1500.00, "type": "DR"},
        {"date": "15/08/2024", "desc": "POCKET MONEY ALLOWANCE TRANSFER", "amount": 10000.00, "type": "CR"}
    ]
    f4 = generate_pdf_statement("Axis_ACE_Rohan.pdf", "Axis Bank", "Axis ACE Card", "XXXX-XXXX-XXXX-7710", "Rohan", axis_txs)
    samples.append({"filename": "Axis_ACE_Rohan.pdf", "path": f4, "bank_code": "AXIS", "account_id": "axis_ace_3", "member_id": 3})

    return samples
