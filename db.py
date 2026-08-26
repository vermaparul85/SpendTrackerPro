import os
import sqlite3
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from config import DEFAULT_MEMBERS, DEFAULT_BANKS, DEFAULT_CATEGORIES, DEFAULT_CARDS

DB_FILE = os.path.join(os.path.dirname(__file__), "spend_tracker.db")

class SpendTrackerDB:
    def __init__(self, mode: str = "local", gcp_project: str = "", dataset_id: str = "spend_tracker"):
        self.mode = mode
        self.gcp_project = gcp_project
        self.dataset_id = dataset_id
        self.init_db()

    def get_connection(self):
        """Returns SQLite connection for local mode."""
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes database schema and seeds default reference records."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY,
                member_name TEXT NOT NULL,
                role TEXT NOT NULL,
                budget_target REAL DEFAULT 0.0,
                avatar_color TEXT DEFAULT '#3B82F6',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Banks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS banks (
                bank_id INTEGER PRIMARY KEY,
                bank_name TEXT NOT NULL,
                bank_code TEXT NOT NULL UNIQUE,
                icon TEXT DEFAULT '🏛️',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Accounts & Cards
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts_cards (
                account_id TEXT PRIMARY KEY,
                account_name TEXT NOT NULL,
                bank_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                account_type TEXT NOT NULL,
                last4 TEXT,
                credit_limit REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bank_id) REFERENCES banks(bank_id),
                FOREIGN KEY (member_id) REFERENCES members(member_id)
            )
        """)

        # 4. Categories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY,
                category_name TEXT NOT NULL,
                category_group TEXT NOT NULL,
                icon TEXT DEFAULT '🏷️',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Rules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                category_id INTEGER NOT NULL,
                clean_merchant TEXT,
                member_id INTEGER,
                priority INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """)

        # 6. Statement Upload Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statements_log (
                upload_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                bank_code TEXT NOT NULL,
                member_id INTEGER,
                record_count INTEGER DEFAULT 0,
                total_debit REAL DEFAULT 0.0,
                total_credit REAL DEFAULT 0.0,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. Transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                upload_id TEXT,
                transaction_date TEXT NOT NULL,
                merchant_description TEXT NOT NULL,
                clean_merchant TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                account_id TEXT NOT NULL,
                member_id INTEGER NOT NULL,
                bank_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                is_shared INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts_cards(account_id),
                FOREIGN KEY (member_id) REFERENCES members(member_id),
                FOREIGN KEY (bank_id) REFERENCES banks(bank_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """)

        conn.commit()

        # Seed Defaults if tables empty
        cursor.execute("SELECT COUNT(*) FROM members")
        if cursor.fetchone()[0] == 0:
            for m in DEFAULT_MEMBERS:
                cursor.execute("""
                    INSERT INTO members (member_id, member_name, role, avatar_color)
                    VALUES (?, ?, ?, ?)
                """, (m["id"], m["name"], m["role"], m["color"]))

        cursor.execute("SELECT COUNT(*) FROM banks")
        if cursor.fetchone()[0] == 0:
            for b in DEFAULT_BANKS:
                cursor.execute("""
                    INSERT INTO banks (bank_id, bank_name, bank_code, icon)
                    VALUES (?, ?, ?, ?)
                """, (b["id"], b["name"], b["code"], b["icon"]))

        for c in DEFAULT_CATEGORIES:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (category_id, category_name, category_group, icon)
                VALUES (?, ?, ?, ?)
            """, (c["id"], c["name"], c["group"], c["icon"]))

        cursor.execute("SELECT COUNT(*) FROM accounts_cards")
        if cursor.fetchone()[0] == 0:
            for c in DEFAULT_CARDS:
                cursor.execute("""
                    INSERT INTO accounts_cards (account_id, account_name, bank_id, member_id, account_type, last4, credit_limit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (c["id"], c["name"], c["bank_id"], c["member_id"], c["type"], c["last4"], c["limit"]))

        # Seed default merchant rules, keeping existing data intact with IGNORE semantics.
        default_rules = [
            ("SWIGGY", 2, "Swiggy"),
            ("ZOMATO", 2, "Zomato"),
            ("BLINKIT", 1, "Blinkit"),
            ("ZEPTO", 1, "Zepto"),
            ("BIGBASKET", 1, "BigBasket"),
            ("AMAZON", 3, "Amazon"),
            ("FLIPKART", 3, "Flipkart"),
            ("MYNTRA", 3, "Myntra"),
            ("UBER", 5, "Uber"),
            ("OLA", 5, "Ola"),
            ("RAPIDO", 5, "Rapido"),
            ("BOOKMYSHOW", 7, "BookMyShow"),
            ("NETFLIX", 7, "Netflix"),
            ("SPOTIFY", 7, "Spotify"),
            ("PRIME VIDEO", 7, "Amazon Prime"),
            ("AIRTEL", 4, "Airtel"),
            ("JIO", 4, "Jio"),
            ("TATA POWER", 4, "Tata Power"),
            ("BESCOM", 4, "Electricity Bill"),
            ("CRED", 9, "CRED Payment"),
            ("CREDIT CARD PAYMENT", 11, "Credit Card Payment"),
            ("CRED PAYMENT", 11, "CRED Payment"),
            ("CREDIT CARD BILL", 11, "Credit Card Bill"),
            ("PETROL", 5, "Fuel Station"),
            ("HPCL", 5, "HP Fuel"),
            ("BPCL", 5, "Bharat Petroleum"),
            ("IOCL", 5, "Indian Oil"),
            ("DMART", 1, "D-Mart"),
            ("APOLLO PHARMA", 8, "Apollo Pharmacy"),
            ("PHARMEASY", 8, "PharmEasy"),
            ("MAKEMYTRIP", 6, "MakeMyTrip"),
            ("INDIGO", 6, "IndiGo Airlines"),
            ("CULT FIT", 8, "Cult.fit")
        ]
        for kw, cat_id, clean_m in default_rules:
            cursor.execute("""
                INSERT OR IGNORE INTO rules (keyword, category_id, clean_merchant)
                VALUES (?, ?, ?)
            """, (kw, cat_id, clean_m))

        conn.commit()
        conn.close()

    # -----------------------------
    # Query Methods
    # -----------------------------
    def get_members(self) -> pd.DataFrame:
        conn = self.get_connection()
        query = """
            SELECT m.*,
                   (SELECT COUNT(*) FROM transactions t WHERE t.member_id = m.member_id) AS transaction_count
            FROM members m
            ORDER BY m.member_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_banks(self) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM banks ORDER BY bank_id", conn)
        conn.close()
        return df

    def get_cards(self) -> pd.DataFrame:
        conn = self.get_connection()
        query = """
            SELECT c.*, b.bank_name, b.bank_code, b.icon as bank_icon, m.member_name,
                   (SELECT COUNT(*) FROM transactions t WHERE t.account_id = c.account_id) as tx_count
            FROM accounts_cards c
            JOIN banks b ON c.bank_id = b.bank_id
            JOIN members m ON c.member_id = m.member_id
            ORDER BY c.account_name
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_categories(self) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM categories ORDER BY category_id", conn)
        conn.close()
        return df

    def get_rules(self) -> pd.DataFrame:
        conn = self.get_connection()
        query = """
            SELECT r.*, c.category_name, m.member_name
            FROM rules r
            JOIN categories c ON r.category_id = c.category_id
            LEFT JOIN members m ON r.member_id = m.member_id
            ORDER BY r.priority DESC, r.keyword
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_statements_log(self) -> pd.DataFrame:
        conn = self.get_connection()
        query = """
            SELECT s.*, m.member_name
            FROM statements_log s
            LEFT JOIN members m ON s.member_id = m.member_id
            ORDER BY s.uploaded_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_transactions(self, filters: Dict[str, Any] = None, sort_by: str = "date", sort_dir: str = "desc") -> pd.DataFrame:
        conn = self.get_connection()
        query = """
            SELECT t.*, 
                   m.member_name, m.avatar_color,
                   b.bank_name, b.bank_code, b.icon as bank_icon,
                   c.category_name, c.category_group, c.icon as category_icon,
                   a.account_name, a.account_type, a.last4
            FROM transactions t
            JOIN members m ON t.member_id = m.member_id
            JOIN banks b ON t.bank_id = b.bank_id
            JOIN categories c ON t.category_id = c.category_id
            JOIN accounts_cards a ON t.account_id = a.account_id
            WHERE 1=1
        """
        params = []
        if filters:
            if filters.get("member_id"):
                query += " AND t.member_id = ?"
                params.append(filters["member_id"])
            if filters.get("bank_id"):
                query += " AND t.bank_id = ?"
                params.append(filters["bank_id"])
            if filters.get("category_id"):
                query += " AND t.category_id = ?"
                params.append(filters["category_id"])
            if filters.get("account_id"):
                query += " AND t.account_id = ?"
                params.append(filters["account_id"])
            if filters.get("transaction_type"):
                query += " AND t.transaction_type = ?"
                params.append(filters["transaction_type"])
            if filters.get("search_text"):
                query += " AND (t.merchant_description LIKE ? OR t.clean_merchant LIKE ?)"
                kw = f"%{filters['search_text']}%"
                params.extend([kw, kw])
            if filters.get("start_date"):
                query += " AND t.transaction_date >= ?"
                params.append(filters["start_date"])
            if filters.get("end_date"):
                query += " AND t.transaction_date <= ?"
                params.append(filters["end_date"])

        sort_field_map = {
            "date": "t.transaction_date",
            "merchant": "t.clean_merchant",
            "amount": "CAST(t.amount AS REAL)",
            "type": "t.transaction_type",
            "category": "c.category_name",
            "member": "m.member_name",
            "bank": "b.bank_name",
        }

        sort_field = sort_field_map.get(sort_by, "t.transaction_date")
        query += f" ORDER BY {sort_field} {sort_dir.upper()}, t.transaction_date DESC, t.created_at DESC"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    # -----------------------------
    # Insert & Update Operations
    # -----------------------------
    def is_statement_uploaded(self, upload_id: str) -> bool:
        """Checks if file hash already exists in upload log."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM statements_log WHERE upload_id = ?", (upload_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def filter_existing_transaction_hashes(self, transaction_hashes: List[str]) -> set:
        """Returns set of transaction hashes that already exist in database."""
        if not transaction_hashes:
            return set()
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(transaction_hashes))
        cursor.execute(f"SELECT transaction_id FROM transactions WHERE transaction_id IN ({placeholders})", transaction_hashes)
        existing = {row[0] for row in cursor.fetchall()}
        conn.close()
        return existing

    def log_statement_upload(self, upload_id: str, filename: str, file_type: str, bank_code: str,
                             member_id: int, record_count: int, total_debit: float, total_credit: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO statements_log 
            (upload_id, filename, file_type, bank_code, member_id, record_count, total_debit, total_credit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (upload_id, filename, file_type, bank_code, member_id, record_count, total_debit, total_credit))
        conn.commit()
        conn.close()

    def insert_transactions(self, records: List[Dict[str, Any]]) -> int:
        """Inserts unique transactions into DB. Returns count inserted."""
        if not records:
            return 0

        conn = self.get_connection()
        cursor = conn.cursor()
        inserted_count = 0

        for r in records:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO transactions 
                    (transaction_id, upload_id, transaction_date, merchant_description, clean_merchant,
                     amount, transaction_type, account_id, member_id, bank_id, category_id, is_shared)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r["transaction_id"], r.get("upload_id"), r["transaction_date"],
                    r["merchant_description"], r["clean_merchant"], r["amount"],
                    r["transaction_type"], r["account_id"], r["member_id"],
                    r["bank_id"], r["category_id"], r.get("is_shared", 1)
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1
            except Exception as e:
                print(f"[DB Error] Failed to insert transaction {r.get('transaction_id')}: {e}")

        conn.commit()
        conn.close()
        return inserted_count

    def update_transaction_category(self, transaction_id: str, category_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET category_id = ? WHERE transaction_id = ?", (category_id, transaction_id))
        conn.commit()
        conn.close()

    def update_transaction_member(self, transaction_id: str, member_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET member_id = ? WHERE transaction_id = ?", (member_id, transaction_id))
        conn.commit()
        conn.close()

    def add_member(self, name: str, role: str, color: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO members (member_name, role, avatar_color)
            VALUES (?, ?, ?)
        """, (name, role, color))
        conn.commit()
        conn.close()

    def update_member(self, member_id: int, name: str, role: str, color: Optional[str] = None):
        conn = self.get_connection()
        cursor = conn.cursor()

        updates = ["member_name = ?", "role = ?"]
        values = [name, role or "Member"]

        if color is not None:
            updates.append("avatar_color = ?")
            values.append(color)

        values.append(member_id)
        cursor.execute(f"UPDATE members SET {', '.join(updates)} WHERE member_id = ?", values)
        conn.commit()
        conn.close()

    def delete_member(self, member_id: int):
        """Deletes a member only when no transactions are attached to that member."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM transactions WHERE member_id = ?", (member_id,))
        tx_count = cursor.fetchone()[0]
        if tx_count > 0:
            conn.close()
            raise ValueError(f"Cannot delete member: {tx_count} transaction{'s are' if tx_count != 1 else ' is'} linked to this member.")

        cursor.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
        conn.commit()
        conn.close()

    def add_card(self, account_id: str, name: str, bank_id: int, member_id: int, acc_type: str, last4: str, limit: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO accounts_cards (account_id, account_name, bank_id, member_id, account_type, last4, credit_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (account_id, name, bank_id, member_id, acc_type, last4, limit))
        conn.commit()
        conn.close()

    def update_card(self, account_id: str, updates: Dict[str, Any]) -> bool:
        """Updates card fields: account_name, last4, bank_id, member_id, account_type, credit_limit."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        allowed = ["account_name", "last4", "bank_id", "member_id", "account_type", "credit_limit"]
        for k in allowed:
            if k in updates and updates[k] is not None:
                fields.append(f"{k} = ?")
                values.append(updates[k])
        
        if not fields:
            conn.close()
            return False
            
        values.append(account_id)
        cursor.execute(f"UPDATE accounts_cards SET {', '.join(fields)} WHERE account_id = ?", values)
        
        # If member was updated, also update member on linked transactions
        if "member_id" in updates and updates["member_id"] is not None:
            cursor.execute("UPDATE transactions SET member_id = ? WHERE account_id = ?", (updates["member_id"], account_id))
            
        conn.commit()
        conn.close()
        return True

    def delete_card(self, account_id: str) -> Tuple[bool, str]:
        """Deletes a card/account only if no transactions/statements are linked to it."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE account_id = ?", (account_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return False, f"Cannot delete card: {count} transaction{'s are' if count > 1 else ' is'} linked to this card."
        
        cursor.execute("DELETE FROM accounts_cards WHERE account_id = ?", (account_id,))
        conn.commit()
        conn.close()
        return True, "Card deleted successfully."

    def add_rule(self, keyword: str, category_id: int, clean_merchant: str, member_id: Optional[int] = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO rules (keyword, category_id, clean_merchant, member_id)
            VALUES (?, ?, ?, ?)
        """, (keyword.upper(), category_id, clean_merchant, member_id))
        conn.commit()
        conn.close()

    def reassign_statement_member(self, upload_id: str, new_member_id: int):
        """Reassigns a statement and ALL its transactions to a different member."""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Reassign in statements_log
        cursor.execute(
            "UPDATE statements_log SET member_id = ? WHERE upload_id = ?",
            (new_member_id, upload_id)
        )
        # Reassign all transactions that belong to this statement upload
        cursor.execute(
            "UPDATE transactions SET member_id = ? WHERE upload_id = ?",
            (new_member_id, upload_id)
        )
        conn.commit()
        conn.close()

    def delete_statement(self, upload_id: str) -> int:
        """Deletes one statement log and all transactions belonging to it."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE upload_id = ?", (upload_id,))
        deleted_count = cursor.rowcount
        cursor.execute("DELETE FROM statements_log WHERE upload_id = ?", (upload_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            raise ValueError("Statement not found")
        conn.commit()
        conn.close()
        return deleted_count

    def reset_database(self):
        """Resets transactions and upload logs for fresh start."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM statements_log")
        conn.commit()
        conn.close()

# Singleton DB Instance
db = SpendTrackerDB()
