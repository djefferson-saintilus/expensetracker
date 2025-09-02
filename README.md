# Expense Tracker

A command-line Python application to help users track expenses, manage budgets, and monitor spending on a biweekly basis. The application supports user authentication, recurring expenses, budget alerts, and CSV export functionality.

---

## Features

* **User Authentication**

  * Register and login with username and password.
  * Passwords are securely hashed using `bcrypt`.

* **Expense Management**

  * Add, edit, and remove expenses.
  * Categorize expenses (predefined or custom categories).
  * Record recurring expenses.

* **Biweekly Summaries**

  * Automatically calculate biweekly periods (1st-15th and 16th-end of month).
  * Summarize expenses by category within a selected period.

* **Budget Management**

  * Set budgets per category.
  * Set budget alerts to notify when spending exceeds thresholds.

* **Export**

  * Export all expenses to CSV for offline analysis.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/djefferson-saintilus/expensetracker.git
   cd expense-tracker
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:

   ```bash
   pip install bcrypt
   ```

---

## Usage

1. Run the application:

   ```bash
   python3 expensetracker.py
   ```

2. Main menu:

   * **Login** or **Register** to access your dashboard.

3. User dashboard options:

   * Add Expense
   * View Expenses (filter by category or biweekly period)
   * Biweekly Summary
   * Export Expenses to CSV
   * Set/View Budgets
   * Set Budget Alerts
   * Edit/Remove Expenses
   * Logout

4. When adding expenses:

   * You can choose predefined categories or create a custom one.
   * Mark expenses as recurring if they repeat biweekly.

5. Budget alerts:

   * Receive notifications if spending exceeds the set threshold in the current biweekly period.

---

## Database

* SQLite database file: `expenses.db`
* Tables:

  * `users` – stores user credentials.
  * `expenses` – stores all expenses.
  * `budgets` – stores budgets per category.
  * `budget_alerts` – stores threshold alerts per category.
  * `budget_changes` – logs changes to budgets (optional).

---

## Dependencies

* Python 3.x
* `bcrypt` – for secure password hashing.
* `sqlite3` – built-in, used for database management.

---

## Notes

* Passwords must be at least 8 characters and include both letters and numbers.
* Dates are formatted as `YYYY-MM-DD`.
* Expenses are filtered based on biweekly periods (1st–15th, 16th–end of month).
* Exported CSV files are timestamped: `expenses_user_<user_id>_YYYYMMDD_HHMMSS.csv`.

---

## Future Improvements

* Automatically add recurring expenses each biweekly period.
* CLI table formatting for better readability.
* Graphical representation of spending trends.
* Monthly or yearly summaries.
* Multi-user support with shared budgets.

---

## License

This project is open-source and free to use.
