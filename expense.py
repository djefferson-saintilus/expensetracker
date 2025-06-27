#!/usr/bin/env python3
import sqlite3
import getpass
import datetime
import bcrypt
import csv
import fixDatepython

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

# Helper function for biweekly periods
def get_biweekly_period(date_obj):
    # date_obj is datetime.date or datetime.datetime
    day = date_obj.day
    if day <= 15:
        start_date = datetime.date(date_obj.year, date_obj.month, 1)
        end_date = datetime.date(date_obj.year, date_obj.month, 15)
    else:
        # Calculate last day of the month
        if date_obj.month == 12:
            next_month = datetime.date(date_obj.year + 1, 1, 1)
        else:
            next_month = datetime.date(date_obj.year, date_obj.month + 1, 1)
        last_day = (next_month - datetime.timedelta(days=1)).day
        start_date = datetime.date(date_obj.year, date_obj.month, 16)
        end_date = datetime.date(date_obj.year, date_obj.month, last_day)
    return start_date, end_date

def get_biweekly_periods_for_month(year_month):
    # year_month: YYYY-MM string
    year, month = map(int, year_month.split('-'))
    first_period = (datetime.date(year, month, 1), datetime.date(year, month, 15))
    if month == 12:
        next_month_first = datetime.date(year + 1, 1, 1)
    else:
        next_month_first = datetime.date(year, month + 1, 1)
    last_day = (next_month_first - datetime.timedelta(days=1)).day
    second_period = (datetime.date(year, month, 16), datetime.date(year, month, last_day))
    return [first_period, second_period]

def select_biweekly_period(year_month_input):
    """
    If user inputs "current" return biweekly period of today.
    Else, return user selected biweekly period for given year-month.
    Returns (start_date, end_date) tuple.
    """
    if year_month_input.lower() == "current":
        today = datetime.date.today()
        return get_biweekly_period(today)

    try:
        periods = get_biweekly_periods_for_month(year_month_input)
    except Exception:
        print("Invalid date format. Expected YYYY-MM or 'current'.")
        return None, None

    print(f"Select biweekly period for {year_month_input}:")
    print("1. 1st - 15th")
    print(f"2. 16th - {periods[1][1].day}th")
    choice = input("Choose 1 or 2: ").strip()
    if choice == "1":
        return periods[0]
    elif choice == "2":
        return periods[1]
    else:
        print("Invalid choice. Defaulting to first period.")
        return periods[0]

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

    filter_choice = input("Filter by category (1), biweekly period (2), or view all (Enter)? ").strip()

    if filter_choice == "1":
        category = input("Enter category to filter: ").capitalize()
        c.execute("SELECT category, amount, description, date, recurring FROM expenses WHERE user_id = ? AND category = ?", (user_id, category))
    elif filter_choice == "2":
        year_month_input = input("Enter year and month (YYYY-MM) or 'current' for current biweekly: ").strip()
        start_date, end_date = select_biweekly_period(year_month_input)
        if not start_date or not end_date:
            print("Invalid period selection.")
            conn.close()
            print_footer()
            return
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

def biweekly_summary(user_id):
    print_header("Biweekly Summary")
    year_month_input = input("Enter the year and month for summary (YYYY-MM) or 'current' for current biweekly: ").strip()
    start_date, end_date = select_biweekly_period(year_month_input)
    if not start_date or not end_date:
        print("Invalid period selection.")
        print_footer()
        return

    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute('''SELECT category, SUM(amount) FROM expenses 
                 WHERE user_id = ? AND date BETWEEN ? AND ? 
                 GROUP BY category''', (user_id, start_date, end_date))
    results = c.fetchall()
    conn.close()

    print(f"\nSummary for period {start_date} to {end_date}:")
    total = 0
    if results:
        for category, amount_sum in results:
            print(f"{category}: ${amount_sum:.2f}")
            total += amount_sum
    else:
        print("No expenses recorded in this period.")

    print(f"Total expenses: ${total:.2f}")
    print_footer()

# Budget Management and Alerts
def set_budget(user_id):
    print_header("Set Budget")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    category = input("Enter category for budget: ").capitalize()
    while True:
        budget_input = input("Enter budget amount: $").strip()
        try:
            budget = float(budget_input)
            break
        except ValueError:
            print("Invalid amount, please enter a numeric value.")

    c.execute("INSERT OR REPLACE INTO budgets (user_id, category, budget) VALUES (?, ?, ?)", (user_id, category, budget))
    conn.commit()
    conn.close()
    print(f"Budget set for category {category}: ${budget:.2f}")
    print_footer()

def view_budget(user_id):
    print_header("View Budgets")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("SELECT category, budget FROM budgets WHERE user_id = ?", (user_id,))
    budgets = c.fetchall()
    conn.close()

    if budgets:
        for category, budget in budgets:
            print(f"Category: {category}, Budget: ${budget:.2f}")
    else:
        print("No budgets set.")
    print_footer()

def set_budget_alert(user_id):
    print_header("Set Budget Alert")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    category = input("Enter category for budget alert: ").capitalize()
    while True:
        threshold_input = input("Enter alert threshold amount: $").strip()
        try:
            threshold = float(threshold_input)
            break
        except ValueError:
            print("Invalid amount, please enter a numeric value.")

    c.execute("INSERT OR REPLACE INTO budget_alerts (user_id, category, threshold_amount) VALUES (?, ?, ?)",
              (user_id, category, threshold))
    conn.commit()
    conn.close()
    print(f"Budget alert set for category {category} at ${threshold:.2f}")
    print_footer()

def check_budget_alert(user_id):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    today = datetime.date.today()
    start_date, end_date = get_biweekly_period(today)

    c.execute("SELECT category, threshold_amount FROM budget_alerts WHERE user_id = ?", (user_id,))
    alerts = c.fetchall()

    for category, threshold in alerts:
        c.execute('''
            SELECT SUM(amount) FROM expenses 
            WHERE user_id = ? AND category = ? AND date BETWEEN ? AND ?
        ''', (user_id, category, start_date, end_date))
        total_expenses = c.fetchone()[0] or 0

        if total_expenses >= threshold:
            print(f"*** ALERT: Expenses in '{category}' have reached ${total_expenses:.2f}, exceeding your threshold of ${threshold:.2f} ***")

    conn.close()

# Remove Expense
def remove_expense(user_id):
    print_header("Remove Expense")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    c.execute("SELECT id, category, amount, description, date FROM expenses WHERE user_id = ?", (user_id,))
    expenses = c.fetchall()

    if not expenses:
        print("No expenses to remove.")
        conn.close()
        print_footer()
        return

    print("Your expenses:")
    for exp in expenses:
        print(f"ID: {exp[0]} | {exp[4]} - {exp[1]}: ${exp[2]:.2f} ({exp[3]})")

    while True:
        try:
            expense_id = int(input("Enter the ID of the expense you want to remove: ").strip())
            if any(exp[0] == expense_id for exp in expenses):
                break
            else:
                print("Invalid ID. Please try again.")
        except ValueError:
            print("Please enter a valid numeric ID.")

    confirm = input(f"Are you sure you want to delete expense ID {expense_id}? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Delete cancelled.")
        conn.close()
        print_footer()
        return

    c.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    conn.commit()
    conn.close()

    print(f"Expense ID {expense_id} removed successfully.")
    print_footer()

# Edit Expense
def edit_expense(user_id):
    print_header("Edit Expense")
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    c.execute("SELECT id, category, amount, description, date, recurring FROM expenses WHERE user_id = ?", (user_id,))
    expenses = c.fetchall()

    if not expenses:
        print("No expenses available to edit.")
        conn.close()
        print_footer()
        return

    print("Your expenses:")
    for exp in expenses:
        recurring_text = "Yes" if exp[5] else "No"
        print(f"ID: {exp[0]} | {exp[4]} - {exp[1]}: ${exp[2]:.2f} ({exp[3]}) Recurring: {recurring_text}")

    while True:
        try:
            expense_id = int(input("Enter the ID of the expense you want to edit: ").strip())
            if any(exp[0] == expense_id for exp in expenses):
                break
            else:
                print("Invalid expense ID. Try again.")
        except ValueError:
            print("Enter a valid numeric ID.")

    c.execute("SELECT category, amount, description, date, recurring FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    expense = c.fetchone()

    if not expense:
        print("Expense not found.")
        conn.close()
        print_footer()
        return

    current_category, current_amount, current_description, current_date, current_recurring = expense

    new_category = input(f"Enter new category [{current_category}]: ").capitalize().strip() or current_category

    while True:
        new_amount_input = input(f"Enter new amount [{current_amount}]: ").strip()
        if not new_amount_input:
            new_amount = current_amount
            break
        try:
            new_amount = float(new_amount_input)
            break
        except ValueError:
            print("Invalid amount. Please enter a numeric value.")

    new_description = input(f"Enter new description [{current_description}]: ").strip() or current_description

    new_date_input = input(f"Enter new date (YYYY-MM-DD) [{current_date}]: ").strip()
    if new_date_input:
        try:
            datetime.datetime.strptime(new_date_input, "%Y-%m-%d")
            new_date = new_date_input
        except ValueError:
            print("Invalid date format. Using current date.")
            new_date = current_date
    else:
        new_date = current_date

    new_recurring_input = input(f"Is this a recurring expense? (yes/no) [{'yes' if current_recurring else 'no'}]: ").strip().lower()
    if new_recurring_input in ("yes", "no"):
        new_recurring = 1 if new_recurring_input == "yes" else 0
    else:
        new_recurring = current_recurring

    c.execute('''
        UPDATE expenses
        SET category = ?, amount = ?, description = ?, date = ?, recurring = ?
        WHERE id = ? AND user_id = ?
    ''', (new_category, new_amount, new_description, new_date, new_recurring, expense_id, user_id))
    conn.commit()
    conn.close()

    print(f"Expense ID {expense_id} updated successfully.")
    print_footer()

# Export to CSV
def export_to_csv(user_id):
    print_header("Export Expenses to CSV")
    filename = f"expenses_user_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    c.execute("SELECT category, amount, description, date, recurring FROM expenses WHERE user_id = ?", (user_id,))
    expenses = c.fetchall()
    conn.close()

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Category", "Amount", "Description", "Date", "Recurring"])
        for exp in expenses:
            writer.writerow(exp)

    print(f"Expenses exported to {filename}")
    print_footer()

# User Dashboard
def user_dashboard(user_id):
    while True:
        print_header("User Dashboard")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Biweekly Summary")
        print("4. Export Expenses to CSV")
        print("5. Set Budget")
        print("6. View Budgets")
        print("7. Set Budget Alert")
        print("8. Remove Expense")
        print("9. Edit Expense")
        print("0. Logout")

        action = input("Choose an action: ").strip()

        if action == "1":
            add_expense(user_id)
        elif action == "2":
            view_expenses(user_id)
        elif action == "3":
            biweekly_summary(user_id)
        elif action == "4":
            export_to_csv(user_id)
        elif action == "5":
            set_budget(user_id)
        elif action == "6":
            view_budget(user_id)
        elif action == "7":
            set_budget_alert(user_id)
        elif action == "8":
            remove_expense(user_id)
        elif action == "9":
            edit_expense(user_id)
        elif action == "0":
            print("Logging out...")
            break
        else:
            print("Invalid choice, please try again.")

# Main Program Loop
def main():
    init_db()
    while True:
        print_header("Welcome to the Biweekly Expense Tracker")
        print("1. Login")
        print("2. Register")
        print("0. Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            user_id = login()
            if user_id:
                user_dashboard(user_id)
        elif choice == "2":
            register()
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()
