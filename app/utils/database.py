import psycopg2
from psycopg2 import sql
import os
from typing import List, Dict

class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "streaver_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                port=os.getenv("DB_PORT", "5432")
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def create_tables(self):
        """Create the original and normalized data tables"""
        try:
            # Table for original data
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS original_data (
                    id SERIAL PRIMARY KEY,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data JSONB NOT NULL
                )
            """)
            
            # Table for normalized data
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS normalized_data (
                    id SERIAL PRIMARY KEY,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    firstname VARCHAR(255),
                    lastname VARCHAR(255),
                    phonenumber VARCHAR(20),
                    zipcode VARCHAR(10),
                    color VARCHAR(50),
                    original_id INTEGER REFERENCES original_data(id)
                )
            """)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            return False
    
    def insert_original_data(self, data: List[Dict]) -> int:
        """Insert original CSV data"""
        try:
            import json
            self.cursor.execute(
                "INSERT INTO original_data (raw_data) VALUES (%s) RETURNING id",
                (json.dumps(data),)
            )
            original_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return original_id
        except Exception as e:
            print(f"Error inserting original data: {e}")
            self.conn.rollback()
            return None
    
    def insert_normalized_data(self, entries: List[Dict], original_id: int):
        """Insert normalized data"""
        try:
            for entry in entries:
                self.cursor.execute("""
                    INSERT INTO normalized_data 
                    (firstname, lastname, phonenumber, zipcode, color, original_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    entry.get('firstname'),
                    entry.get('lastname'),
                    entry.get('phonenumber'),
                    entry.get('zipcode'),
                    entry.get('color'),
                    original_id
                ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting normalized data: {e}")
            self.conn.rollback()
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
