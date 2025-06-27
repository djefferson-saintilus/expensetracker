#!/usr/bin/env python3
import sqlite3
import getpass
import datetime
import bcrypt
import csv

# Database Initialization
def init_db():
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    amount REAL,
                    description TEXT,
                    date TEXT,
                    recurring INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    budget REAL,
                    UNIQUE(user_id, category),
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS budget_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    threshold_amount REAL,
                    UNIQUE(user_id, category),
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS budget_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    new_budget REAL,
                    timestamp TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def print_header(title):
    print("\n" + "-" * 50)
    print(f"{title}".center(50))
    print("-" * 50)

def print_footer():
    print("\n" + "-" * 50)

# User Authentication
def register():
    print_header("Register")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    username = input("Enter username: ").strip()
    password = getpass.getpass("Enter password: ").strip()

    if len(password) < 8 or password.isalpha() or password.isnumeric():
        print("Password must be at least 8 characters and include both letters and numbers.")
        conn.close()
        return

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash.decode())) 
        conn.commit()
        print("Registration successful!")
    except sqlite3.IntegrityError:
        print("Username already taken.")
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def login():
    print_header("Login")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    username = input("Enter username: ").strip()
    password = getpass.getpass("Enter password: ").strip()
    
    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        user_id, stored_password_hash = user
        if bcrypt.checkpw(password.encode(), stored_password_hash.encode('utf-8')):

            print("Login successful!")
            return user_id
        else:
            print("Invalid credentials.")
    else:
        print("User not found.")
    return None

# Expense Management
def add_expense(user_id):
    print_header("Add Expense")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    categories = ["Rent", "Haircuts", "Transportation", "Food", "Cleaning", 
                  "Gift", "Hobbies", "Healthcare", "Electric", "Internet", 
                  "Drink", "Shopping", "Clothes"]

    print("Predefined Categories:", ", ".join(categories))
    category = input("Enter category (or press Enter to select a predefined category): ").capitalize().strip()
    while not category:
        category = input("Category cannot be empty. Enter category: ").capitalize().strip()

    while True:
        amount_input = input("Enter amount: $").strip()
        try:
            amount = float(amount_input)
            break
        except ValueError:
            print("Invalid amount. Please enter a numeric value.")

    description = input("Enter description: ").strip()
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    recurring = input("Is this a recurring expense? (yes/no): ").strip().lower()
    recurring_flag = 1 if recurring == "yes" else 0

    c.execute("INSERT INTO expenses (user_id, category, amount, description, date, recurring) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, category, amount, description, date, recurring_flag))
    conn.commit()
    conn.close()

    print(f"\nExpense added successfully! Category: {category}, Amount: ${amount:.2f}")
    check_budget_alert(user_id)
    print_footer()

def view_expenses(user_id):
    print_header("View Expenses")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    filter_choice = input("Filter by category (1), date range (2), or view all (Enter)? ").strip()

    if filter_choice == "1":
        category = input("Enter category to filter: ").capitalize()
        c.execute("SELECT category, amount, description, date, recurring FROM expenses WHERE user_id = ? AND category = ?", (user_id, category))
    elif filter_choice == "2":
        start_date = input("Start date (YYYY-MM-DD): ").strip() or "1900-01-01"
        end_date = input("End date (YYYY-MM-DD): ").strip() or "9999-12-31"
        c.execute("SELECT category, amount, description, date, recurring FROM expenses WHERE user_id = ? AND date BETWEEN ? AND ?", (user_id, start_date, end_date))
    else:
        c.execute("SELECT category, amount, description, date, recurring FROM expenses WHERE user_id = ?", (user_id,))

    expenses = c.fetchall()
    conn.close()

    if expenses:
        print("\n--- Expense List ---")
        for expense in expenses:
            recurring_text = "(Recurring)" if expense[4] else ""
            print(f"{expense[3]} - {expense[0]}: ${expense[1]:.2f} ({expense[2]}) {recurring_text}")
    else:
        print("No expenses found.")
    print_footer()

def monthly_summary(user_id):
    print_header("Monthly Summary")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    month = input("Enter the month for summary (YYYY-MM): ").strip()

    c.execute('''
        SELECT category, SUM(amount) 
        FROM expenses 
        WHERE user_id = ? AND date LIKE ?
        GROUP BY category
    ''', (user_id, f"{month}%"))

    summary = c.fetchall()
    conn.close()

    if summary:
        print(f"\nMonthly Summary for {month}:")
        for category, total in summary:
            print(f"Category: {category}, Total: ${total:.2f}")
    else:
        print("No expenses found for this month.")
    print_footer()

def export_to_csv(user_id):
    print_header("Export to CSV")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("SELECT category, amount, description, date, recurring FROM expenses WHERE user_id = ?", (user_id,))
    expenses = c.fetchall()
    conn.close()

    if expenses:
        filename = input("Enter the filename (e.g., expenses.csv): ").strip()
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Category", "Amount", "Description", "Date", "Recurring"])
            for expense in expenses:
                recurring_text = "Yes" if expense[4] else "No"
                writer.writerow([expense[0], expense[1], expense[2], expense[3], recurring_text])
        print(f"Expenses exported to {filename} successfully!")
    else:
        print("No expenses to export.")
    print_footer()

# Budget Management
def set_budget(user_id):
    print_header("Set Budget")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    category = input("Enter category for budget: ").capitalize().strip()

    while True:
        try:
            budget = float(input(f"Enter budget for {category}: "))
            break
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    c.execute("INSERT OR REPLACE INTO budgets (user_id, category, budget) VALUES (?, ?, ?)", (user_id, category, budget))
    conn.commit()
    conn.close()
    print(f"Budget for {category} set to ${budget:.2f}.")
    print_footer()

def set_budget_alert(user_id, category, threshold_percentage):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    
    c.execute("SELECT budget FROM budgets WHERE user_id = ? AND category = ?", (user_id, category))
    result = c.fetchone()

    if result:
        budget = result[0]
        threshold_amount = budget * (threshold_percentage / 100)
        c.execute("INSERT OR REPLACE INTO budget_alerts (user_id, category, threshold_amount) VALUES (?, ?, ?)",
                  (user_id, category, threshold_amount))
        conn.commit()
        print(f"Alert set for {category} at {threshold_percentage}% (${threshold_amount:.2f}).")
    else:
        print("Budget not found for this category.")
    conn.close()
    print_footer()

def check_budget_alert(user_id):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    try:
        c.execute('''
            SELECT e.category, a.threshold_amount, SUM(e.amount)
            FROM expenses e
            JOIN budget_alerts a ON e.user_id = a.user_id AND e.category = a.category
            WHERE e.user_id = ?
            GROUP BY e.category
        ''', (user_id,))
        alerts = c.fetchall()
        for category, threshold, total in alerts:
            if total >= threshold:
                print(f"⚠️ Alert: Spending in {category} is ${total:.2f}, exceeding threshold of ${threshold:.2f}")
    except sqlite3.Error as e:
        print(f"Error while checking budget alert: {e}")
    finally:
        conn.close()

# Main Execution
def user_dashboard(user_id):
    while True:
        print_header("User Dashboard")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Monthly Summary")
        print("4. Export to CSV")
        print("5. Set Budget")
        print("6. Set Budget Alert")
        print("7. Logout")
        action = input("Choose an option: ").strip()

        if action == "1":
            add_expense(user_id)
        elif action == "2":
            view_expenses(user_id)
        elif action == "3":
            monthly_summary(user_id)
        elif action == "4":
            export_to_csv(user_id)
        elif action == "5":
            set_budget(user_id)
        elif action == "6":
            category = input("Enter category for alert: ").capitalize()
            while True:
                try:
                    threshold_percentage = float(input("Enter threshold percentage: "))
                    break
                except ValueError:
                    print("Enter a valid percentage.")
            set_budget_alert(user_id, category, threshold_percentage)
        elif action == "7":
            print("Logging out...")
            break
        else:
            print("Invalid choice, please try again.")

def main():
    init_db()
    while True:
        print_header("Main Menu")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            register()
        elif choice == "2":
            user_id = login()
            if user_id:
                user_dashboard(user_id)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
