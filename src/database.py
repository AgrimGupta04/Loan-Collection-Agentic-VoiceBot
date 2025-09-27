import sqlite3
import os
from datetime import datetime, timedelta
import random

class Database:
    def __init__(self, db_file="customers.db"):
        self.db_file = db_file
        self.con = None
        try:
            self.con = sqlite3.connect(db_file, check_same_thread=False)
            self.create_table()
            print(f"✓ Database initialized: {db_file}")
            
            # Only seed if no data exists
            if not self.fetch_due_customers():
                self.seed_simple_data()
                print("✓ Database seeded with sample data")
                
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            raise

    def create_table(self):
        """Create the table if not exists"""
        try:
            query = """
                CREATE TABLE IF NOT EXISTS customers(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    phone VARCHAR NOT NULL,
                    due_date DATE NOT NULL,
                    loan_amount REAL NOT NULL,
                    call_status VARCHAR DEFAULT 'Pending',
                    notes VARCHAR DEFAULT ''
                    )
                """
            self.con.execute(query)
            self.con.commit()
        except Exception as e:
            print(f"Error creating table: {e}")
            raise

    def seed_simple_data(self):
        """Add simple sample data without external dependencies"""
        try:
            customers = [
                ("John Doe", "+1234567890", "2024-01-15", 5000.0, "Pending", ""),
                ("Jane Smith", "+1234567891", "2024-01-20", 3500.0, "Pending", ""),
                ("Mike Johnson", "+1234567892", "2024-01-25", 7200.0, "Pending", ""),
                ("Sarah Wilson", "+1234567893", "2024-02-01", 2800.0, "Pending", ""),
                ("Tom Brown", "+1234567894", "2024-02-05", 4600.0, "Pending", ""),
            ]

            self.con.executemany(
                "INSERT INTO customers (name, phone, due_date, loan_amount, call_status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                customers
            )
            self.con.commit()
        except Exception as e:
            print(f"Error seeding data: {e}")
            # Don't raise here, app can work without sample data

    def seed_data(self, n=5):
        """Original seed method with faker - fallback to simple if faker not available"""
        try:
            from faker import Faker
            fake = Faker()
            customers = []
            
            for _ in range(n):
                name = fake.name()
                phone = fake.phone_number()
                due_date = (datetime.today() + timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d")
                loan_amount = round(random.uniform(500, 20000), 2)
                customers.append((name, phone, due_date, loan_amount, "Pending", ""))

            self.con.executemany(
                "INSERT INTO customers (name, phone, due_date, loan_amount, call_status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                customers
            )
            self.con.commit()
            
        except ImportError:
            print("Faker not available, using simple seed data")
            self.seed_simple_data()
        except Exception as e:
            print(f"Error in seed_data: {e}")
            self.seed_simple_data()

    def fetch_due_customers(self):
        """Return info of all customers whose status is pending"""
        try:
            cur = self.con.execute("SELECT * FROM customers WHERE call_status = 'Pending' ")
            return cur.fetchall()
        except Exception as e:
            print(f"Error fetching due customers: {e}")
            return []

    def log_call_outcome(self, customer_id, status, notes):
        """Update the status and notes for a particular customer"""
        try:
            self.con.execute(
                "UPDATE customers SET call_status = ?, notes = ? WHERE id = ?",
                (status, notes, customer_id)
            )
            self.con.commit()
            print(f"✓ Updated customer {customer_id}: {status}")
        except Exception as e:
            print(f"Error updating customer {customer_id}: {e}")

    def close(self):
        """Close database connection"""
        if self.con:
            self.con.close()


if __name__ == "__main__":
    try:
        db = Database()
        print("Database test successful!")
        
        print("\nFetching pending customers:")
        for row in db.fetch_due_customers():
            print(f"  {row}")

        # Test updating a customer
        customers = db.fetch_due_customers()
        if customers:
            customer_id = customers[0][0]
            db.log_call_outcome(customer_id, "SUCCESSFUL", "Customer agreed to pay tomorrow")
            print(f"\nUpdated customer {customer_id}")
            
        print("\nFetching updated customers:")
        for row in db.fetch_due_customers():
            print(f"  {row}")
            
    except Exception as e:
        print(f"Database test failed: {e}")