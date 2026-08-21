import io
import re
import hashlib
import pandas as pd
from datetime import datetime
from typing import Tuple, List, Dict, Optional, Any

class IndianStatementParser:
    """
    Statement Parser for Indian Bank & Credit Card PDF/CSV Statements.
    Normalizes disparate statement layouts (HDFC, ICICI, SBI, Axis, AMEX, Kotak, CRED, BOB, IndusInd, RBL, etc.)
    into a unified transaction format with clean merchant strings and cryptographic deduplication.
    Supports password-protected encrypted PDFs and automatic detection of bank, member, and account details.
    """

    @staticmethod
    def calculate_file_hash(file_bytes: bytes) -> str:
        """MD5 hash of file content for statement duplicate detection."""
        return hashlib.md5(file_bytes).hexdigest()

    @staticmethod
    def calculate_transaction_hash(account_id: str, date_str: str, amount: float, description: str) -> str:
        """SHA256 composite hash for exact transaction deduplication."""
        raw_key = f"{account_id.strip().lower()}|{date_str.strip()}|{amount:.2f}|{description.strip().lower()}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    @staticmethod
    def clean_merchant_name(description: str) -> str:
        """
        Normalizes noisy Indian payment descriptors into clean merchant names.
        e.g., 'UPI/4321908/SWIGGY BANGALORE' -> 'Swiggy'
              'POS 9012 ZOMATO MEDIA GURGAON' -> 'Zomato'
              'NEFT-UTIB00001-AIRTEL BILL' -> 'Airtel'
        """
        text = str(description).upper().strip()

        # Common Indian Payment Prefix Removal (UPI, POS, NEFT, RTGS, IMPS, ATM, NACH, ECS)
        text = re.sub(r'^(?:UPI|POS|NEFT|RTGS|IMPS|ATM|ACH|NACH|ECS|INB|BIL|TPV|IPS|BBPS)[/\s:-]+', '', text)
        text = re.sub(r'\b\d{6,}\b', '', text) # Remove reference/terminal numbers
        text = re.sub(r'\b(?:BANGALORE|MUMBAI|GURGAON|DELHI|NOIDA|HYDERABAD|CHENNAI|PUNE|KOLKATA|AHMEDABAD|JAIPUR|INDIA|PVT LTD|LTD|IN)\b', '', text)
        text = re.sub(r'\b(?:STORE|TERMINAL|BRANCH|CHECK|DEBIT|CREDIT|PURCHASE|PAYMENT|ONLINE|RECURRING|REF|TXN|TRF)\b', '', text)
        text = re.sub(r'[#\*@!&%]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Known Merchant Mapping overrides
        mapping = {
            "SWIGGY": "Swiggy",
            "ZOMATO": "Zomato",
            "BLINKIT": "Blinkit",
            "ZEPTO": "Zepto",
            "BIGBASKET": "BigBasket",
            "AMAZON": "Amazon",
            "FLIPKART": "Flipkart",
            "MYNTRA": "Myntra",
            "UBER": "Uber",
            "OLA": "Ola",
            "RAPIDO": "Rapido",
            "BOOKMYSHOW": "BookMyShow",
            "NETFLIX": "Netflix",
            "SPOTIFY": "Spotify",
            "AIRTEL": "Airtel",
            "JIO": "Jio",
            "CRED": "CRED",
            "DMART": "D-Mart",
            "MAKEMYTRIP": "MakeMyTrip",
            "INDIGO": "IndiGo Airlines",
            "APOLLO": "Apollo Pharmacy",
            "PHARMEASY": "PharmEasy",
            "CULT FIT": "Cult.fit",
            "TATA POWER": "Tata Power",
            "BESCOM": "Electricity Bill",
            "PETROL": "Fuel Station",
            "HPCL": "HP Fuel",
            "BPCL": "Bharat Petroleum",
            "IOCL": "Indian Oil"
        }

        for kw, clean in mapping.items():
            if kw in text:
                return clean

        return text.title() if text else str(description).strip()

    @staticmethod
    def is_pdf_encrypted(file_bytes: bytes) -> bool:
        """Checks if a PDF is password-protected without throwing an exception."""
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            return bool(reader.is_encrypted)
        except Exception:
            return False

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str, password: Optional[str] = None) -> Tuple[str, bool, str]:
        """
        Extracts raw text from PDF or CSV file for bank and member recognition.
        Returns: (extracted_text, is_encrypted, status_code)
        status_code: 'OK' | 'PASSWORD_REQUIRED' | 'INCORRECT_PASSWORD' | 'EMPTY' | 'ERROR'
        """
        if not filename.lower().endswith(".pdf"):
            try:
                text = file_bytes.decode("utf-8", errors="ignore")
                return text, False, "OK"
            except Exception as e:
                return "", False, f"CSV_DECODE_ERROR: {e}"

        # 1. Check encryption status using pypdf
        is_encrypted = False
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            if reader.is_encrypted:
                is_encrypted = True
                if not password:
                    return "", True, "PASSWORD_REQUIRED"
                # Test decryption
                dec_res = reader.decrypt(password)
                if dec_res == 0:  # Failed decryption in pypdf
                    return "", True, "INCORRECT_PASSWORD"
        except Exception as e:
            err_str = str(e).lower()
            if "password" in err_str or "encrypted" in err_str:
                return "", True, "INCORRECT_PASSWORD" if password else "PASSWORD_REQUIRED"

        text = ""

        # 2. Extract using pdfplumber (preserves layout best)
        try:
            import pdfplumber
            kwargs = {}
            if password:
                kwargs["password"] = password
            with pdfplumber.open(io.BytesIO(file_bytes), **kwargs) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
        except Exception as e:
            err_str = str(e).lower()
            if "password" in err_str or "encrypted" in err_str:
                return "", True, "INCORRECT_PASSWORD" if password else "PASSWORD_REQUIRED"

        # 3. Fallback extraction using pypdf if pdfplumber was empty
        if not text:
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                if reader.is_encrypted:
                    if password:
                        reader.decrypt(password)
                    else:
                        return "", True, "PASSWORD_REQUIRED"
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            except Exception as e:
                err_str = str(e).lower()
                if "password" in err_str or "encrypted" in err_str:
                    return "", True, "INCORRECT_PASSWORD" if password else "PASSWORD_REQUIRED"

        if not text and is_encrypted:
            return "", True, "INCORRECT_PASSWORD" if password else "PASSWORD_REQUIRED"

        if not text:
            return "", False, "EMPTY"

        return text, is_encrypted, "OK"

    @staticmethod
    def detect_bank_and_member(
        file_bytes: bytes,
        filename: str,
        members_df: pd.DataFrame,
        banks_df: pd.DataFrame,
        cards_df: Optional[pd.DataFrame] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scans statement text & filename to automatically recognize:
        1. Encryption status (is_encrypted, is_unlocked)
        2. Bank Code & Bank Details (HDFC, ICICI, SBI, AXIS, AMEX, KOTAK, CRED, BOB, INDUSIND, RBL, etc.)
        3. Household Member Name & ID
        4. Card / Account Details (e.g. last4 digits, matching card from accounts_cards)
        """
        text, is_encrypted, status = IndianStatementParser.extract_text(file_bytes, filename, password)
        combined_text = (text + " " + filename).upper()

        if status in ["PASSWORD_REQUIRED", "INCORRECT_PASSWORD"]:
            combined_text = filename.upper()

        # ── 1. Recognize Bank Code ──────────────────────────────────────────
        detected_bank_code = None
        detected_bank_name = None
        detected_bank_id = None
        detected_bank_icon = "🏛️"

        bank_signatures = [
            ("HDFC", "HDFC", "HDFC Bank", "💳", ["HDFC", "HDFCBANK.COM", "REGALIA", "MILLENNIA", "INFINIA", "DINERS CLUB", "TATA NEU HDFC", "HDFC0"]),
            ("ICICI", "ICICI", "ICICI Bank", "🟧", ["ICICI", "AMAZON PAY ICICI", "ICICIBANK.COM", "SAPPHIRO", "RUBYX", "CORAL", "EMERALDE", "ICIC0"]),
            ("SBI", "SBI", "State Bank of India (SBI)", "🔷", ["STATE BANK OF INDIA", "SBI CARD", "SBICARD.COM", "SBI.CO.IN", "SIMPLYCLICK", "SIMPLYSAVE", "AURUM", "SBIN0"]),
            ("AXIS", "AXIS", "Axis Bank", "🔺", ["AXIS BANK", "AXIS", "AXISBANK.COM", "FLIPKART AXIS", "AXIS ACE", "MAGNUS", "ATLAS", "MY ZONE", "NEO", "UTIB0"]),
            ("AMEX", "AMEX", "American Express (AMEX)", "✈️", ["AMERICAN EXPRESS", "AMEX", "AMERICANEXPRESS.COM", "MEMBERSHIP REWARDS", "PLATINUM TRAVEL", "SMART EARN"]),
            ("KOTAK", "KOTAK", "Kotak Mahindra Bank", "🔴", ["KOTAK MAHINDRA", "KOTAK", "KOTAK.COM", "811", "WHITE CARD", "LEAGUE PLATINUM", "KKBK0"]),
            ("CRED", "CRED", "CRED Consolidated", "⚡", ["CRED", "DREAMPLUG", "CRED CONSOLIDATED", "CRED PAY"]),
            ("BOB", "BOB", "Bank of Baroda (BOB)", "🔶", ["BANK OF BARODA", "BOBCARD", "BOB", "BARB0"]),
            ("INDUSIND", "INDUSIND", "IndusInd Bank", "🟣", ["INDUSIND", "INDUSINDBANK.COM", "PIONEER", "LEGEND", "PINNACLE", "INDB0"]),
            ("RBL", "RBL", "RBL Bank", "🔷", ["RBL BANK", "RBL", "RBLBANK.COM", "BAJAJ FINSERV RBL", "RATN0"]),
            ("IDFC", "IDFC", "IDFC FIRST Bank", "🔴", ["IDFC FIRST", "IDFC", "IDFCFIRSTBANK.COM", "FIRST WOW", "FIRST CLASSIC", "IDFB0"]),
            ("YES", "YES", "Yes Bank", "🟦", ["YES BANK", "YESBANK.IN", "YES FIRST", "YESB0"]),
        ]

        for code, b_code, b_name, b_icon, kws in bank_signatures:
            if any(kw in combined_text for kw in kws):
                detected_bank_code = b_code
                detected_bank_name = b_name
                detected_bank_icon = b_icon
                break

        if not banks_df.empty:
            for _, b in banks_df.iterrows():
                b_code = str(b.get("bank_code", "")).upper()
                b_name = str(b.get("bank_name", "")).upper()
                if b_code in combined_text or b_name in combined_text:
                    detected_bank_code = b.get("bank_code")
                    detected_bank_name = b.get("bank_name")
                    detected_bank_id = int(b.get("bank_id"))
                    detected_bank_icon = b.get("icon", "🏛️")
                    break

            if not detected_bank_id and detected_bank_code:
                match = banks_df[banks_df["bank_code"] == detected_bank_code]
                if not match.empty:
                    detected_bank_id = int(match.iloc[0]["bank_id"])
                    detected_bank_name = str(match.iloc[0]["bank_name"])
                    detected_bank_icon = str(match.iloc[0].get("icon", "🏛️"))

            if not detected_bank_id:
                detected_bank_id = int(banks_df.iloc[0]["bank_id"])
                detected_bank_code = str(banks_df.iloc[0]["bank_code"])
                detected_bank_name = str(banks_df.iloc[0]["bank_name"])
                detected_bank_icon = str(banks_df.iloc[0].get("icon", "💳"))
        else:
            detected_bank_id = 1
            detected_bank_code = detected_bank_code or "HDFC"
            detected_bank_name = detected_bank_name or "HDFC Bank"

        # ── 2. Recognize Member Name & ID ───────────────────────────────────
        detected_member_id = None
        detected_member_name = None
        is_new_member = False

        # First pass: check existing household members in DB (prioritize exact full name match, then first name with word boundary)
        if not members_df.empty:
            # 1a. Check full name match
            for _, m in members_df.iterrows():
                raw_name = str(m["member_name"])
                clean_name = raw_name.split("(")[0].strip().upper()
                parts = clean_name.split()
                if len(parts) >= 2:
                    pat = r'\b' + re.escape(parts[0]) + r'\s+' + re.escape(parts[-1]) + r'\b'
                    if re.search(pat, combined_text):
                        detected_member_id = int(m["member_id"])
                        detected_member_name = raw_name
                        break
                elif len(clean_name) >= 3 and clean_name in combined_text:
                    detected_member_id = int(m["member_id"])
                    detected_member_name = raw_name
                    break

            # 1b. If no full name match, check unique first names with word boundary
            if not detected_member_id:
                for _, m in members_df.iterrows():
                    raw_name = str(m["member_name"])
                    clean_name = raw_name.split("(")[0].strip().upper()
                    first_name = clean_name.split()[0] if clean_name.split() else clean_name
                    if len(first_name) >= 3 and re.search(r'\b' + re.escape(first_name) + r'\b', combined_text):
                        detected_member_id = int(m["member_id"])
                        detected_member_name = raw_name
                        break

        # Second pass: scan statement text for customer name patterns
        if not detected_member_id and text:
            name_patterns = [
                re.compile(r'(?:Card\s*Member|Cardholder(?:\s*Name)?|Account\s*Holder|Customer\s*Name|Name)\s*[:\-]\s*([A-Za-z\s]{3,35}?)(?:\s*\||\s*\n|\s*,|\s*Statement|\s*Period|\s*Currency|$)', re.IGNORECASE),
                re.compile(r'(?:Dear|Mr\.|Mrs\.|Ms\.|Shri|Smt\.)\s+([A-Za-z\s]{3,30}?)(?:\s*[,|\n]|$)', re.IGNORECASE),
            ]
            for pat in name_patterns:
                m_match = pat.search(text)
                if m_match:
                    candidate = m_match.group(1).strip()
                    if candidate.upper() not in ["CUSTOMER", "CARDMEMBER", "ACCOUNT", "STATEMENT", "BANK", "SIR", "MADAM", "VALUED CUSTOMER"]:
                        candidate_clean = " ".join(candidate.split()[:2]).title()
                        if len(candidate_clean) >= 3:
                            # Check if candidate matches any member in DB
                            if not members_df.empty:
                                for _, m in members_df.iterrows():
                                    raw_m = str(m["member_name"]).split("(")[0].strip().upper()
                                    if raw_m in candidate_clean.upper() or candidate_clean.upper() in raw_m:
                                        detected_member_id = int(m["member_id"])
                                        detected_member_name = str(m["member_name"])
                                        break
                            if not detected_member_id:
                                detected_member_name = candidate_clean
                                is_new_member = True
                            break

        # Default fallback to primary member if none matched
        if not detected_member_id:
            if not members_df.empty:
                detected_member_id = int(members_df.iloc[0]["member_id"])
                if not detected_member_name:
                    detected_member_name = str(members_df.iloc[0]["member_name"])
            else:
                detected_member_id = 1
                detected_member_name = detected_member_name or "Rahul (Self)"

        # ── 3. Extract Card / Account Number (Last 4 Digits) ────────────────
        detected_last4 = None
        combined_for_card = (text or "") + " \n " + (filename or "")

        # Tier 1: Unicode masked bullet formats (e.g. •••• 1234, ●●●● 1234, **** 1234)
        if not detected_last4:
            m_bullet = re.search(r'[•●∙*]{3,16}[\s.\-_]*(\d{4})\b', combined_for_card)
            if m_bullet:
                detected_last4 = m_bullet.group(1)

        # Tier 2: Explicit 'Ending in / with' patterns (e.g. Card Ending in 1120, ends with 2002)
        if not detected_last4:
            m_ending = re.search(r'(?:ending\s+(?:in|with)|last\s+4\s+digits?|ends\s+with|ending)\s*[:\-]?\s*[x*.\s]*(\d{4})\b', combined_for_card, re.IGNORECASE)
            if m_ending:
                detected_last4 = m_ending.group(1)

        # Tier 3: Standard Masked card formats (e.g. 4315-XXXX-XXXX-2002, 4315XXXXXXXX2002, XXXX-XXXX-XXXX-3341, ************9102)
        if not detected_last4:
            masked_patterns = [
                r'(?:\b\d{4}|\b[X*]{4})[\s.\-_]*(?:[X*]{4,10}|\d{2}[X*]{2,8})[\s.\-_]*(?:[X*]{4})?[\s.\-_]*(\d{4})\b',
                r'(?:[X*]{4}[\s.\-_]*){2,3}(\d{4})\b',
                r'(?:[X*]{6,16}|(?:\*{4}\s*){2,3})(\d{4})\b',
                r'\d{4}[X*x]{4,12}(\d{4})',
            ]
            for pat in masked_patterns:
                m_masked = re.search(pat, combined_for_card, re.IGNORECASE)
                if m_masked:
                    detected_last4 = m_masked.group(1)
                    break

        # Tier 4: Explicit Card Number / Account Number label followed by values
        if not detected_last4:
            m_lbl = re.search(r'(?:Card\s*(?:No\.?|Number|#)?|Credit\s*Card\s*(?:No\.?|Number|#)?|Primary\s*Card|Account\s*(?:No\.?|Number|#)?)\s*[:\-]?\s*([0-9X*x\s\-_.]{8,35})', combined_for_card, re.IGNORECASE)
            if m_lbl:
                raw_val = m_lbl.group(1).strip()
                # Find trailing 4 consecutive digits
                digits_blocks = re.findall(r'\b\d{4}\b', raw_val)
                if digits_blocks:
                    detected_last4 = digits_blocks[-1]
                else:
                    all_digits = re.findall(r'\d', raw_val)
                    if len(all_digits) >= 4:
                        detected_last4 = ''.join(all_digits[-4:])

        # Tier 5: 16-digit unmasked standard card number (e.g. 3633 0243 5611 2025 or 3633024356112025)
        if not detected_last4:
            m_spaced = re.search(r'\b(?:\d{4}[\s-]){3}(\d{4})\b', combined_for_card)
            if m_spaced:
                detected_last4 = m_spaced.group(1)
            else:
                m_continuous = re.search(r'\b\d{12}(\d{4})\b', combined_for_card)
                if m_continuous:
                    detected_last4 = m_continuous.group(1)

        # Tier 6: Filename fallback patterns
        if not detected_last4 and filename:
            m_fn_masked = re.search(r'\d{4}[X*x]{4,12}(\d{4})', filename, re.IGNORECASE)
            if m_fn_masked:
                detected_last4 = m_fn_masked.group(1)
            else:
                m_fn_digits = re.search(r'(\d{16})', filename)
                if m_fn_digits:
                    detected_last4 = m_fn_digits.group(1)[-4:]
                else:
                    m_fn_suffix = re.search(r'(?:XXXX|xxxx|_|-)(\d{4})\b', filename)
                    if m_fn_suffix:
                        detected_last4 = m_fn_suffix.group(1)

        # ── 4. Identify Card Name & Account ID ──────────────────────────────
        card_variant_signatures = [
            ("AMAZON PAY", "ICICI", "ICICI Amazon Pay Credit Card", "icici_amazon"),
            ("SAPPHIRO", "ICICI", "ICICI Sapphiro Card", "icici_sapphiro"),
            ("RUBYX", "ICICI", "ICICI Rubyx Card", "icici_rubyx"),
            ("CORAL", "ICICI", "ICICI Coral Card", "icici_coral"),
            ("EMERALDE", "ICICI", "ICICI Emeralde Card", "icici_emeralde"),
            ("PLATINUM CHIP", "ICICI", "ICICI Platinum Card", "icici_plat"),
            ("CASHBACK", "SBI", "SBI Cashback Credit Card", "sbi_cashback"),
            ("SIMPLYCLICK", "SBI", "SBI SimplyCLICK Credit Card", "sbi_simplyclick"),
            ("SIMPLYSAVE", "SBI", "SBI SimplySAVE Credit Card", "sbi_simplysave"),
            ("AURUM", "SBI", "SBI Aurum Card", "sbi_aurum"),
            ("PRIME", "SBI", "SBI Card PRIME", "sbi_prime"),
            ("ELITE", "SBI", "SBI Card ELITE", "sbi_elite"),
            ("PULSE", "SBI", "SBI Card PULSE", "sbi_pulse"),
            ("REGALIA GOLD", "HDFC", "HDFC Regalia Gold", "hdfc_regalia"),
            ("REGALIA", "HDFC", "HDFC Regalia Card", "hdfc_regalia"),
            ("MILLENNIA", "HDFC", "HDFC Millennia Card", "hdfc_millennia"),
            ("INFINIA", "HDFC", "HDFC Infinia Metal", "hdfc_infinia"),
            ("DINERS CLUB BLACK", "HDFC", "HDFC Diners Club Black", "hdfc_diners_black"),
            ("DINERS CLUB", "HDFC", "HDFC Diners Club", "hdfc_diners"),
            ("TATA NEU INFINITY", "HDFC", "Tata Neu Infinity HDFC", "hdfc_tata_neu_inf"),
            ("TATA NEU", "HDFC", "Tata Neu HDFC Card", "hdfc_tata_neu"),
            ("MONEYBACK", "HDFC", "HDFC MoneyBack+ Card", "hdfc_moneyback"),
            ("FLIPKART", "AXIS", "Flipkart Axis Bank Card", "axis_flipkart"),
            ("ACE", "AXIS", "Axis Bank ACE Card", "axis_ace"),
            ("MAGNUS", "AXIS", "Axis Magnus Card", "axis_magnus"),
            ("ATLAS", "AXIS", "Axis Atlas Card", "axis_atlas"),
            ("MY ZONE", "AXIS", "Axis My Zone Card", "axis_myzone"),
            ("NEO", "AXIS", "Axis Neo Card", "axis_neo"),
            ("VISTARA", "AXIS", "Axis Vistara Card", "axis_vistara"),
            ("PLATINUM TRAVEL", "AMEX", "Amex Platinum Travel", "amex_plat_travel"),
            ("SMART EARN", "AMEX", "Amex SmartEarn Card", "amex_smartearn"),
            ("MEMBERSHIP REWARDS", "AMEX", "Amex Membership Rewards", "amex_mrcc"),
            ("LEAGUE PLATINUM", "KOTAK", "Kotak League Platinum", "kotak_league"),
            ("WHITE CARD", "KOTAK", "Kotak White Card", "kotak_white"),
            ("811", "KOTAK", "Kotak 811 Account", "kotak_811"),
            ("FIRST WOW", "IDFC", "IDFC FIRST WOW! Card", "idfc_wow"),
            ("FIRST CLASSIC", "IDFC", "IDFC FIRST Classic", "idfc_classic"),
        ]

        matched_variant_name = None
        matched_slug = None
        for sig_kw, sig_bank, card_name, slug in card_variant_signatures:
            if sig_bank == detected_bank_code and sig_kw in combined_text:
                matched_variant_name = card_name
                matched_slug = slug
                break

        detected_account_name = matched_variant_name or f"{detected_bank_name} Credit Card"
        slug_prefix = matched_slug or f"{detected_bank_code.lower()}_card"
        detected_account_id = f"{slug_prefix}_{detected_last4 or '1'}"

        # If a card already matches this bank + last4 in DB, use its existing account_id
        if cards_df is not None and not cards_df.empty:
            subset = cards_df[cards_df["bank_id"] == detected_bank_id]
            if detected_last4:
                card_last4_match = subset[subset["last4"] == detected_last4]
                if not card_last4_match.empty:
                    detected_account_id = card_last4_match.iloc[0]["account_id"]
                    detected_account_name = card_last4_match.iloc[0]["account_name"]

        masked_last4 = f"•••• {detected_last4}" if detected_last4 else "•••• ••••"

        return {
            "status": status,
            "is_encrypted": is_encrypted,
            "is_unlocked": status == "OK",
            "bank_id": detected_bank_id,
            "bank_code": detected_bank_code,
            "bank_name": detected_bank_name,
            "bank_icon": detected_bank_icon,
            "member_id": detected_member_id,
            "member_name": detected_member_name,
            "is_new_member": is_new_member,
            "last4": detected_last4,
            "masked_last4": masked_last4,
            "account_id": detected_account_id,
            "account_name": detected_account_name,
            "confidence": "HIGH" if status == "OK" and detected_bank_code else "MEDIUM"
        }

    def parse_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        account_id: str,
        bank_code: str = "GENERIC",
        password: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Parses Indian PDF bank/credit card statement with password decryption support.
        Returns: (DataFrame, status_message)
        """
        extracted_text, is_encrypted, status = self.extract_text(file_bytes, filename, password)

        if status == "PASSWORD_REQUIRED":
            return pd.DataFrame(), "LOCKED_PDF_PASSWORD_REQUIRED"
        if status == "INCORRECT_PASSWORD":
            return pd.DataFrame(), "INCORRECT_PASSWORD"
        if status == "EMPTY" or not extracted_text.strip():
            return pd.DataFrame(), "EMPTY_OR_UNPARSABLE_PDF"

        records = []

        # ── Method 1: Single-line regex patterns ────────────────────────────
        patterns = [
            # Pattern 1: Date (DD/MM/YYYY or DD-MM-YYYY) + Description + Amount + optional Cr/Dr
            re.compile(r'(\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4})\s+(.+?)\s+(?:₹|Rs\.?|INR)?\s*([\d,]+\.\d{2})\s*(CR|DR|CR\.|DR\.|DEBIT|CREDIT)?', re.IGNORECASE),
            
            # Pattern 2: Date (DD MMM YYYY e.g. 15 Aug 2024) + Description + Amount
            re.compile(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})\s+(.+?)\s+(?:₹|Rs\.?|INR)?\s*([\d,]+\.\d{2})\s*(CR|DR|DEBIT|CREDIT)?', re.IGNORECASE),

            # Pattern 3: Date (MMM DD, YYYY e.g. Aug 15, 2024) + Description + Amount
            re.compile(r'([A-Za-z]{3}\s+\d{1,2},?\s+\d{2,4})\s+(.+?)\s+(?:₹|Rs\.?|INR)?\s*([\d,]+\.\d{2})\s*(CR|DR)?', re.IGNORECASE)
        ]

        lines = extracted_text.splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) < 8:
                continue

            for pat in patterns:
                match = pat.search(line_str)
                if match:
                    groups = match.groups()
                    date_part = groups[0]
                    desc_part = groups[1]
                    amt_part = groups[2]
                    type_part = groups[3] if len(groups) > 3 else None

                    parsed_date = self._normalize_date(date_part)
                    if not parsed_date:
                        continue

                    clean_amt_str = amt_part.replace(',', '').strip()
                    try:
                        amount = float(clean_amt_str)
                    except ValueError:
                        continue

                    if amount <= 0:
                        continue

                    t_type = "Debit"
                    if type_part and str(type_part).upper() in ['CR', 'CR.', 'CREDIT']:
                        t_type = "Credit"
                    elif type_part and str(type_part).upper() in ['DR', 'DR.', 'DEBIT']:
                        t_type = "Debit"
                    else:
                        if any(k in desc_part.upper() for k in ['PAYMENT RECEIVED', 'REFUND', 'DEPOSIT', 'SALARY', 'CREDIT', 'CASHBACK']):
                            t_type = "Credit"

                    clean_m = self.clean_merchant_name(desc_part)
                    t_hash = self.calculate_transaction_hash(account_id, parsed_date, amount, desc_part)

                    records.append({
                        "transaction_id": t_hash,
                        "transaction_date": parsed_date,
                        "merchant_description": desc_part.strip(),
                        "clean_merchant": clean_m,
                        "amount": round(amount, 2),
                        "transaction_type": t_type,
                        "account_id": account_id
                    })
                    break

        # ── Method 2: Multi-line sequence parser (for statements where each column is its own line) ──
        if not records:
            date_re = re.compile(r'^\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4}$')
            amt_re = re.compile(r'^[\d,]+\.\d{2}$')
            type_re = re.compile(r'^(?:CR|DR|DEBIT|CREDIT)$', re.IGNORECASE)

            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if date_re.match(line):
                    parsed_date = self._normalize_date(line)
                    if parsed_date and i + 2 < len(lines):
                        desc = lines[i + 1].strip()
                        amt_line = lines[i + 2].strip()
                        if amt_re.match(amt_line):
                            try:
                                amount = float(amt_line.replace(',', ''))
                                t_type = "Debit"
                                offset = 3
                                if i + 3 < len(lines) and type_re.match(lines[i + 3].strip()):
                                    if lines[i + 3].strip().upper() in ['CR', 'CREDIT']:
                                        t_type = "Credit"
                                    offset = 4

                                clean_m = self.clean_merchant_name(desc)
                                t_hash = self.calculate_transaction_hash(account_id, parsed_date, amount, desc)
                                records.append({
                                    "transaction_id": t_hash,
                                    "transaction_date": parsed_date,
                                    "merchant_description": desc,
                                    "clean_merchant": clean_m,
                                    "amount": round(amount, 2),
                                    "transaction_type": t_type,
                                    "account_id": account_id
                                })
                                i += offset
                                continue
                            except ValueError:
                                pass
                i += 1

        if not records:
            return pd.DataFrame(), "NO_TRANSACTIONS_FOUND_IN_PDF"

        return pd.DataFrame(records), "SUCCESS"

    @staticmethod
    def _normalize_date(date_str: str) -> Optional[str]:
        """Normalizes date string to YYYY-MM-DD format."""
        clean_d = date_str.replace('.', '/').replace('-', '/')
        for date_fmt in ['%d/%m/%Y', '%d/%m/%y', '%d %b %Y', '%b %d, %Y', '%b %d %Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(clean_d, date_fmt).strftime('%Y-%m-%d')
            except Exception:
                pass
        try:
            return pd.to_datetime(date_str).strftime('%Y-%m-%d')
        except Exception:
            return None

    def parse_csv(self, file_bytes: bytes, filename: str, account_id: str) -> Tuple[pd.DataFrame, str]:
        """Parses CSV bank/credit card statements with automatic column mapping."""
        try:
            try:
                df_raw = pd.read_csv(io.BytesIO(file_bytes))
            except Exception:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), encoding='latin1')

            cols_lower = {col: str(col).strip().lower().replace(" ", "_") for col in df_raw.columns}
            df_raw = df_raw.rename(columns=cols_lower)

            date_col = next((c for c in df_raw.columns if any(k in c for k in ['date', 'time', 'trans_date'])), None)
            desc_col = next((c for c in df_raw.columns if any(k in c for k in ['description', 'payee', 'merchant', 'details', 'particulars', 'memo'])), None)
            amount_col = next((c for c in df_raw.columns if 'amount' in c or 'value' in c), None)
            debit_col = next((c for c in df_raw.columns if 'debit' in c or 'withdraw' in c or 'dr' in c), None)
            credit_col = next((c for c in df_raw.columns if 'credit' in c or 'deposit' in c or 'cr' in c), None)
            type_col = next((c for c in df_raw.columns if 'type' in c or 'dr/cr' in c), None)

            records = []
            for _, row in df_raw.iterrows():
                raw_date = row.get(date_col) if date_col else None
                if pd.isna(raw_date):
                    continue

                try:
                    parsed_date = pd.to_datetime(raw_date).strftime('%Y-%m-%d')
                except Exception:
                    continue

                description = str(row.get(desc_col, "Bank Transaction")).strip()
                amount = 0.0
                t_type = "Debit"

                if amount_col and not pd.isna(row.get(amount_col)):
                    raw_amt = str(row.get(amount_col)).replace('₹', '').replace('Rs', '').replace(',', '').strip()
                    try:
                        val = float(raw_amt)
                        if val < 0:
                            amount = abs(val)
                            t_type = "Debit"
                        else:
                            amount = val
                            t_type = "Credit" if (type_col and 'credit' in str(row.get(type_col)).lower()) else "Debit"
                    except ValueError:
                        continue
                elif debit_col or credit_col:
                    raw_deb = str(row.get(debit_col, '')).replace('₹', '').replace(',', '').strip()
                    raw_cred = str(row.get(credit_col, '')).replace('₹', '').replace(',', '').strip()
                    try:
                        if raw_deb and raw_deb != 'nan' and float(raw_deb) > 0:
                            amount = float(raw_deb)
                            t_type = "Debit"
                        elif raw_cred and raw_cred != 'nan' and float(raw_cred) > 0:
                            amount = float(raw_cred)
                            t_type = "Credit"
                    except ValueError:
                        continue

                if amount <= 0:
                    continue

                clean_m = self.clean_merchant_name(description)
                t_hash = self.calculate_transaction_hash(account_id, parsed_date, amount, description)

                records.append({
                    "transaction_id": t_hash,
                    "transaction_date": parsed_date,
                    "merchant_description": description,
                    "clean_merchant": clean_m,
                    "amount": round(amount, 2),
                    "transaction_type": t_type,
                    "account_id": account_id
                })

            if not records:
                return pd.DataFrame(), "NO_TRANSACTIONS_FOUND_IN_CSV"

            return pd.DataFrame(records), "SUCCESS"

        except Exception as e:
            return pd.DataFrame(), f"CSV Parsing Error: {e}"

# Singleton Parser Instance
parser = IndianStatementParser()
