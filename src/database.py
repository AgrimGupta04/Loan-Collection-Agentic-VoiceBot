import sqlite3
from faker import Faker 
from datetime import datetime, timedelta
import random

class Database:
    def __init__(self, db_file = "customers.db"):
        
        self.con = sqlite3.connect(db_file, check_same_thread=False)
        self.create_table()

    def create_table(self):
        ## Creating the table if not created 
        query = """
            CREATE TABLE IF NOT EXISTS customers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                phone INT,
                due_date DATE,
                loan_amount VARCHAR,
                call_status VARCHAR DEFAULT 'Pending',
                notes VARCHAR
                )
            """
        self.con.execute(query)
        self.con.commit()

    def seed_data(self, n):
        fake = Faker()
        customers = [] 
        for _ in range(n):
            name = fake.name()
            phone = fake.phone_number()

            due_date = (datetime.today() + timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d")
            loan_amount = round(random.uniform(500 ,20000), 2)
            customers.append((name, phone, due_date, loan_amount, "Pending", ""))

        self.con.executemany(
            "INSERT INTO customers (name, phone, due_date, loan_amount, call_status, notes) VALUES (?, ?, ?, ?, ?, ?)",
            customers
        )
        self.con.commit()

    def fetch_due_customers(self):  ## To return the info of all customers whose status is pending
        cur = self.con.execute("SELECT * FROM customers WHERE call_status = 'Pending' ")
        return cur.fetchall()

    def log_call_outcome(self, customer_id, status, notes):  ## To update the status and notes for a particular customer
        self.con.execute(
            "UPDATE customers SET call_status = ?, notes=? WHERE id=?",
            (status, notes, customer_id)
        )
        self.con.commit()


if __name__ == "__main__":

    db = Database()
    db.seed_data(n=5)

    print("Fetching pending customers:")
    for row in db.fetch_due_customers():
        print(row)

    print("\nOutcome for customers:\n")
    db.log_call_outcome(1, "SUCCESSFUL", "Customer agreed to pay tommorow")

    print("\nFetching updated customers:")
    for row in db.fetch_due_customers():
        print(row)