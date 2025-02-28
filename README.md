# Expense Management Application

This is a simple expense management application that allows users to register, log in, add expenses, view expenses, generate monthly summaries, export expenses to CSV, set budgets, and set budget alerts.

## Features

- User Registration and Login
- Add Expenses
- View Expenses with Filtering Options
- Monthly Expense Summary
- Export Expenses to CSV
- Set Budgets for Categories
- Set Budget Alerts

## Installation

1. Clone the repository or download the source code.
2. Ensure you have Python installed on your system.
3. Install the required packages using pip:
    ```sh
    pip install bcrypt
    ```

## Creating a Standalone Executable

To create a standalone executable for the Expense Tracker script, follow these steps:

1. **Install PyInstaller**:
   ```sh
   pip install pyinstaller
   ```

2. **Generate the Executable**:
   Navigate to the directory containing `expense.py` and run:
   ```sh
   pyinstaller --onefile expense.py
   ```

3. **Run the Executable**:
   Navigate to the `dist` directory and run the executable:
   ```sh
   cd dist
   ./expense   # On Windows, use expense.exe
   ```

This will create a standalone executable that you can run without needing to have Python installed on the target machine.

## Usage

1. Initialize the database by running the application:
    ```sh
    python expense.py
    ```

2. Follow the on-screen instructions to register a new user or log in with an existing account.

3. Once logged in, you can access the user dashboard to manage your expenses and budgets.

## Database Schema

The application uses SQLite for data storage. The following tables are created:

- `users`: Stores user information (username and password).
- `expenses`: Stores expense records with details such as category, amount, description, date, and recurring status.
- `budgets`: Stores budget information for each category.
- `budget_alerts`: Stores budget alert thresholds for each category.
- `budget_changes`: Stores changes made to budgets with timestamps.

## Functions

### User Authentication

- `register()`: Registers a new user.
- `login()`: Logs in an existing user.

### Expense Management

- `add_expense(user_id)`: Adds a new expense for the logged-in user.
- `view_expenses(user_id)`: Views expenses with optional filtering by category or date range.
- `monthly_summary(user_id)`: Generates a monthly summary of expenses by category.
- `export_to_csv(user_id)`: Exports expenses to a CSV file.

### Budget Management

- `set_budget(user_id)`: Sets a budget for a specific category.
- `set_budget_alert(user_id, category, threshold_percentage)`: Sets a budget alert for a specific category.
- `check_budget_alert(user_id)`: Checks if any budget alerts have been triggered.

## Main Function

- `main()`: Initializes the database and provides the main menu for user registration, login, and exit.
- `user_dashboard(user_id)`: Provides the user dashboard for managing expenses and budgets after login.

## License

This project is licensed under the MIT License.