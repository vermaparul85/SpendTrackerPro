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

def generate_pdf_statement(filename: str, bank_title: str, card_title: str, account_number: str, member_name: str, transactions: list, period_label: str = "01-Aug-2024 to 19-Aug-2024") -> str:
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
    c.drawString(50, height - 85, f"Statement Period: {period_label} | Currency: INR (₹)")
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
    """Generate monthly reference-style statements for Jan-Aug 2026."""
    reference_statements = [
        # Rahul - Primary Earner
        {
            "filename": "HDFC_Regalia_Rahul",
            "bank_title": "HDFC Bank",
            "card_title": "HDFC Regalia Gold",
            "account_number": "XXXX-XXXX-XXXX-4812",
            "member_name": "Rahul",
            "bank_code": "HDFC",
            "account_id": "hdfc_regalia_1",
            "member_id": 1,
            "cycle_day": 19,
            "monthly_extras": ["SWIGGY ONE MEMBERSHIP", "AMAZON INDIA HOME ESSENTIALS", "BLINKIT WEEKEND GROCERIES", "HPCL FUEL TOP-UP", "NETFLIX PREMIUM RENEWAL", "MAKEMYTRIP HOTEL BOOKING", "DMART MONTHLY GROCERIES", "CRED HDFC CARD PAYMENT"],
            "transactions": [
        {"date": "02/08/2024", "desc": "UPI/4321908/SWIGGY FOOD GURGAON", "amount": 840.00, "type": "DR"},
        {"date": "04/08/2024", "desc": "AMAZON INDIA PAYMENTS SELLER", "amount": 4299.00, "type": "DR"},
        {"date": "06/08/2024", "desc": "BLINKIT STORE BLINKIT GROCERY", "amount": 1450.00, "type": "DR"},
        {"date": "08/08/2024", "desc": "HPCL FUEL PETROL PUMP", "amount": 2500.00, "type": "DR"},
        {"date": "10/08/2024", "desc": "NETFLIX ENTERTAINMENT SUBSCRIPTION", "amount": 649.00, "type": "DR"},
        {"date": "12/08/2024", "desc": "MAKEMYTRIP GOA FLIGHT TICKET", "amount": 18500.00, "type": "DR"},
        {"date": "14/08/2024", "desc": "REFUND MAKEMYTRIP CANCELLATION", "amount": 2500.00, "type": "CR"},
        {"date": "16/08/2024", "desc": "DMART RETAIL GROCERIES MUMBAI", "amount": 6820.00, "type": "DR"},
        {"date": "18/08/2024", "desc": "CRED PAYMENT HDFC CREDIT CARD", "amount": 25000.00, "type": "CR"}
            ],
        },
        # Ananya - Spouse
        {
            "filename": "ICICI_AmazonPay_Ananya",
            "bank_title": "ICICI Bank",
            "card_title": "ICICI Amazon Pay Card",
            "account_number": "XXXX-XXXX-XXXX-9102",
            "member_name": "Ananya",
            "bank_code": "ICICI",
            "account_id": "icici_amazon_2",
            "member_id": 2,
            "cycle_day": 12,
            "monthly_extras": ["ZOMATO WEEKEND DINNER", "AMAZON PAY HOUSEHOLD ITEMS", "ZEPTO EXPRESS GROCERIES", "MYNTRA SEASONAL SHOPPING", "AIRTEL FIBRE BILL", "APOLLO PHARMACY WELLNESS", "BOOKMYSHOW CONCERT TICKETS", "CULT FIT MONTHLY CLASS"],
            "transactions": [
        {"date": "01/08/2024", "desc": "POS 4019 ZOMATO MEDIA GURGAON", "amount": 650.00, "type": "DR"},
        {"date": "03/08/2024", "desc": "AMAZON PAY FRESH GROCERIES", "amount": 3200.00, "type": "DR"},
        {"date": "05/08/2024", "desc": "ZEPTO INSTANT DELIVERY MUMBAI", "amount": 480.00, "type": "DR"},
        {"date": "07/08/2024", "desc": "MYNTRA DESIGNS FASHION", "amount": 3999.00, "type": "DR"},
        {"date": "09/08/2024", "desc": "AIRTEL BROADBAND & MOBILE BILL", "amount": 1499.00, "type": "DR"},
        {"date": "11/08/2024", "desc": "APOLLO PHARMACY HEALTHCARE", "amount": 1250.00, "type": "DR"},
        {"date": "15/08/2024", "desc": "BOOKMYSHOW MOVIE TICKETS", "amount": 920.00, "type": "DR"},
        {"date": "17/08/2024", "desc": "CULT FIT ANNUAL GYM MEMBERSHIP", "amount": 14500.00, "type": "DR"}
            ],
        },
        # Rahul - Primary Earner
        {
            "filename": "SBI_Cashback_Rahul",
            "bank_title": "SBI Card",
            "card_title": "SBI Cashback Credit Card",
            "account_number": "XXXX-XXXX-XXXX-3341",
            "member_name": "Rahul",
            "bank_code": "SBI",
            "account_id": "sbi_cashback_1",
            "member_id": 1,
            "cycle_day": 5,
            "monthly_extras": ["FLIPKART HOUSEHOLD PURCHASE", "UBER AIRPORT RIDE", "BIGBASKET MONTHLY ORDER", "TATA POWER ELECTRICITY BILL", "SWIGGY INSTAMART ORDER", "FLIPKART ELECTRONICS PURCHASE", "UBER OFFICE COMMUTE", "BIGBASKET FESTIVE GROCERIES"],
            "transactions": [
        {"date": "03/08/2024", "desc": "FLIPKART INTERNET ECOMMERCE", "amount": 8990.00, "type": "DR"},
        {"date": "05/08/2024", "desc": "UBER INDIA TRANSPORT RIDES", "amount": 540.00, "type": "DR"},
        {"date": "09/08/2024", "desc": "BIGBASKET SUPERMARKET", "amount": 2100.00, "type": "DR"},
        {"date": "13/08/2024", "desc": "TATA POWER ELECTRICITY BILL", "amount": 3450.00, "type": "DR"},
        {"date": "17/08/2024", "desc": "SWIGGY INSTAMART GROCERY", "amount": 890.00, "type": "DR"}
            ],
        },
        # Rohan - Student
        {
            "filename": "Axis_ACE_Rohan",
            "bank_title": "Axis Bank",
            "card_title": "Axis ACE Card",
            "account_number": "XXXX-XXXX-XXXX-7710",
            "member_name": "Rohan",
            "bank_code": "AXIS",
            "account_id": "axis_ace_3",
            "member_id": 3,
            "cycle_day": 22,
            "monthly_extras": ["SPOTIFY STUDENT PLAN", "SWIGGY CAMPUS MEAL", "RAPIDO METRO CONNECT", "COLLEGE BOOKSTORE TEXTBOOK", "ONLINE COURSE SUBSCRIPTION", "SWIGGY EXAM WEEK MEAL", "RAPIDO WEEKEND RIDE", "COLLEGE FEST REGISTRATION"],
            "transactions": [
        {"date": "02/08/2024", "desc": "SPOTIFY MUSIC SUBSCRIPTION", "amount": 119.00, "type": "DR"},
        {"date": "05/08/2024", "desc": "SWIGGY FOOD DELIVERY", "amount": 340.00, "type": "DR"},
        {"date": "08/08/2024", "desc": "RAPIDO BIKE TAXI HYDERABAD", "amount": 85.00, "type": "DR"},
        {"date": "12/08/2024", "desc": "COLLEGE BOOKSTORE SUPPLIES", "amount": 1500.00, "type": "DR"},
        {"date": "15/08/2024", "desc": "POCKET MONEY ALLOWANCE TRANSFER", "amount": 10000.00, "type": "CR"}
            ],
        },
    ]

    samples = []
    for month in range(1, 9):
        for reference in reference_statements:
            month_start = datetime(2026, month, reference["cycle_day"])
            next_month = month_start.replace(day=28) + timedelta(days=4)
            next_month = next_month.replace(day=1)
            month_end = next_month.replace(day=reference["cycle_day"]) - timedelta(days=1)
            period_label = f"{month_start.strftime('%d-%b-%Y')} to {month_end.strftime('%d-%b-%Y')}"
            transactions = []
            for index, tx in enumerate(reference["transactions"]):
                reference_day = int(tx["date"].split("/")[0])
                transaction_date = month_start + timedelta(days=reference_day - 1)
                amount_variation = 1 + (((month + index) % 5) - 2) / 100
                transactions.append({
                    **tx,
                    "date": transaction_date.strftime("%d/%m/%Y"),
                    "desc": f"{tx['desc']} REF{month:02d}{index + 1:02d}",
                    "amount": round(tx["amount"] * amount_variation, 2),
                })

            extra_index = month - 1
            extra_date = month_start + timedelta(days=10 + (month % 9))
            transactions.append({
                "date": extra_date.strftime("%d/%m/%Y"),
                "desc": f"{reference['monthly_extras'][extra_index]} REF{month:02d}99",
                "amount": round(750 + (month * 137) + (reference["cycle_day"] * 11), 2),
                "type": "DR",
            })

            filename = f"{reference['filename']}_{month_start.strftime('%Y_%m')}.pdf"
            path = generate_pdf_statement(
                filename,
                reference["bank_title"],
                reference["card_title"],
                reference["account_number"],
                reference["member_name"],
                transactions,
                period_label,
            )
            samples.append({
                "filename": filename,
                "path": path,
                "bank_code": reference["bank_code"],
                "account_id": reference["account_id"],
                "member_id": reference["member_id"],
            })

    return samples
