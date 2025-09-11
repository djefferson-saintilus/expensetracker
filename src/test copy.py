import flet as ft
import sqlite3
import bcrypt
import csv
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple

# Database setup and utilities
def init_db():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')
    
    # Expenses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        is_recurring INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Budgets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, category)
    )
    ''')
    
    # Budget alerts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budget_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        threshold REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, category)
    )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_biweekly_period(date_str: Optional[str] = None) -> Tuple[str, str]:
    """Get current biweekly period dates"""
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        date = datetime.now()
    
    if date.day <= 15:
        start_date = date.replace(day=1)
        end_date = date.replace(day=15)
    else:
        start_date = date.replace(day=16)
        # Get last day of month
        next_month = date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

# Main application class
class ExpenseTracker(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.page.title = "Expense Tracker"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
        self.user_id = None
        self.route = "/login"
        
        # Initialize database
        init_db()
        
        # Setup navigation
        self.setup_navigation()
        
    def setup_navigation(self):
        """Setup navigation routes"""
        self.page.on_route_change = self.route_change
        self.page.on_view_pop = self.view_pop
        self.page.go('/login')
    
    def route_change(self, e):
        """Handle route changes"""
        troute = ft.TemplateRoute(self.page.route)
        
        if troute.match("/login"):
            self.page.views.clear()
            self.page.views.append(LoginView(self.page, self))
        elif troute.match("/register"):
            self.page.views.append(RegisterView(self.page, self))
        elif troute.match("/dashboard"):
            if self.user_id:
                self.page.views.append(DashboardView(self.page, self, self.user_id))
            else:
                self.page.go("/login")
        elif troute.match("/add_expense"):
            if self.user_id:
                self.page.views.append(AddExpenseView(self.page, self, self.user_id))
            else:
                self.page.go("/login")
        elif troute.match("/view_expenses"):
            if self.user_id:
                self.page.views.append(ViewExpensesView(self.page, self, self.user_id))
            else:
                self.page.go("/login")
        elif troute.match("/biweekly_summary"):
            if self.user_id:
                self.page.views.append(BiweeklySummaryView(self.page, self, self.user_id))
            else:
                self.page.go("/login")
        elif troute.match("/set_budget"):
            if self.user_id:
                self.page.views.append(SetBudgetView(self.page, self, self.user_id))
            else:
                self.page.go("/login")
        elif troute.match("/set_alerts"):
            if self.user_id:
                self.page.views.append(SetAlertsView(self.page, self, self.user_id))
            else:
                self.page.go("/login")
        elif troute.match("/export"):
            if self.user_id:
                self.page.views.append(ExportView(self.page, self, self.user_id))
            else:
                self.page.go("/login")
        
        self.page.update()
    
    def view_pop(self, e):
        """Handle view pop (back navigation)"""
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

# Authentication Views
class LoginView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker):
        super().__init__(route="/login")
        self.page = page
        self.app = app
        
        self.username = ft.TextField(
            label="Username",
            autofocus=True,
            prefix_icon=ft.Icons.PERSON
        )
        
        self.password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK
        )
        
        self.error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            visible=False
        )
        
        self.controls = [
            ft.AppBar(title=ft.Text("Login")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Expense Tracker", size=24, weight=ft.FontWeight.BOLD),
                        self.username,
                        self.password,
                        ft.ElevatedButton(
                            "Login",
                            on_click=self.login,
                            icon=ft.Icons.LOGIN
                        ),
                        ft.TextButton(
                            "Create Account",
                            on_click=lambda e: self.page.go("/register")
                        ),
                        self.error_text
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
    
    def login(self, e):
        """Handle login attempt"""
        username = self.username.value.strip()
        password = self.password.value
        
        if not username or not password:
            self.error_text.value = "Please enter both username and password"
            self.error_text.visible = True
            self.page.update()
            return
        
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE username = ?", 
                (username,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result and verify_password(password, result[1]):
                self.app.user_id = result[0]
                self.page.go("/dashboard")
            else:
                self.error_text.value = "Invalid username or password"
                self.error_text.visible = True
                self.page.update()
                
        except Exception as ex:
            self.error_text.value = f"Login error: {str(ex)}"
            self.error_text.visible = True
            self.page.update()

class RegisterView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker):
        super().__init__(route="/register")
        self.page = page
        self.app = app
        
        self.username = ft.TextField(
            label="Username",
            autofocus=True,
            prefix_icon=ft.Icons.PERSON
        )
        
        self.password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK
        )
        
        self.confirm_password = ft.TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK
        )
        
        self.error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            visible=False
        )
        
        self.controls = [
            ft.AppBar(title=ft.Text("Create Account")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Create Account", size=24, weight=ft.FontWeight.BOLD),
                        self.username,
                        self.password,
                        self.confirm_password,
                        ft.ElevatedButton(
                            "Register",
                            on_click=self.register,
                            icon=ft.Icons.PERSON_ADD
                        ),
                        ft.TextButton(
                            "Back to Login",
                            on_click=lambda e: self.page.go("/login")
                        ),
                        self.error_text
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
    
    def register(self, e):
        """Handle registration attempt"""
        username = self.username.value.strip()
        password = self.password.value
        confirm_password = self.confirm_password.value
        
        # Validation
        if not username or not password:
            self.error_text.value = "Please enter both username and password"
            self.error_text.visible = True
            self.page.update()
            return
        
        if password != confirm_password:
            self.error_text.value = "Passwords do not match"
            self.error_text.visible = True
            self.page.update()
            return
        
        if len(password) < 8:
            self.error_text.value = "Password must be at least 8 characters"
            self.error_text.visible = True
            self.page.update()
            return
        
        if not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            self.error_text.value = "Password must contain both letters and numbers"
            self.error_text.visible = True
            self.page.update()
            return
        
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                self.error_text.value = "Username already exists"
                self.error_text.visible = True
                self.page.update()
                conn.close()
                return
            
            # Create user
            password_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            
            self.page.go("/login")
            
        except Exception as ex:
            self.error_text.value = f"Registration error: {str(ex)}"
            self.error_text.visible = True
            self.page.update()

# Dashboard View
class DashboardView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker, user_id: int):
        super().__init__(route="/dashboard")
        self.page = page
        self.app = app
        self.user_id = user_id
        
        # Get username for display
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = cursor.fetchone()[0]
        conn.close()
        
        # Check for budget alerts
        alerts = self.check_budget_alerts()
        
        self.controls = [
            ft.AppBar(
                title=ft.Text(f"Welcome, {username}"),
                actions=[
                    ft.IconButton(
                        ft.Icons.LOGOUT,
                        on_click=self.logout
                    )
                ]
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        # Display alerts if any
                        *([ft.AlertDialog(
                            title=ft.Text("Budget Alert"),
                            content=ft.Text(alerts),
                            open=True
                        )] if alerts else []),
                        
                        ft.ElevatedButton(
                            "Add Expense",
                            on_click=lambda e: self.page.go("/add_expense"),
                            icon=ft.Icons.ADD,
                            width=250
                        ),
                        ft.ElevatedButton(
                            "View Expenses",
                            on_click=lambda e: self.page.go("/view_expenses"),
                            icon=ft.Icons.LIST,
                            width=250
                        ),
                        ft.ElevatedButton(
                            "Biweekly Summary",
                            on_click=lambda e: self.page.go("/biweekly_summary"),
                            icon=ft.Icons.SUMMARIZE,
                            width=250
                        ),
                        ft.ElevatedButton(
                            "Set Budgets",
                            on_click=lambda e: self.page.go("/set_budget"),
                            icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
                            width=250
                        ),
                        ft.ElevatedButton(
                            "Set Alerts",
                            on_click=lambda e: self.page.go("/set_alerts"),
                            icon=ft.Icons.NOTIFICATIONS,
                            width=250
                        ),
                        ft.ElevatedButton(
                            "Export to CSV",
                            on_click=lambda e: self.page.go("/export"),
                            icon=ft.Icons.FILE_DOWNLOAD,
                            width=250
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                ),
                padding=20,
                alignment=ft.alignment.center,
                expand=True
            )
        ]
    
    def logout(self, e):
        """Handle logout"""
        self.app.user_id = None
        self.page.go("/login")
    
    def check_budget_alerts(self) -> str:
        """Check if user has exceeded any budget thresholds"""
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            
            # Get current biweekly period
            start_date, end_date = get_biweekly_period()
            
            # Get expenses for current period by category
            cursor.execute('''
            SELECT category, SUM(amount) 
            FROM expenses 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            GROUP BY category
            ''', (self.user_id, start_date, end_date))
            
            expenses_by_category = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get budget alerts
            cursor.execute(
                "SELECT category, threshold FROM budget_alerts WHERE user_id = ?",
                (self.user_id,)
            )
            
            alerts = []
            for category, threshold in cursor.fetchall():
                if category in expenses_by_category and expenses_by_category[category] >= threshold:
                    alerts.append(
                        f"Budget alert for {category}: "
                        f"${expenses_by_category[category]:.2f} spent "
                        f"(threshold: ${threshold:.2f})"
                    )
            
            conn.close()
            return "\n".join(alerts) if alerts else ""
            
        except Exception as ex:
            return f"Error checking alerts: {str(ex)}"

# Expense Management Views
class AddExpenseView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker, user_id: int):
        super().__init__(route="/add_expense")
        self.page = page
        self.app = app
        self.user_id = user_id
        
        # Form fields
        self.amount = ft.TextField(
            label="Amount",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.ATTACH_MONEY
        )
        
        self.category = ft.TextField(
            label="Category",
            prefix_icon=ft.Icons.CATEGORY
        )
        
        self.description = ft.TextField(
            label="Description (optional)",
            multiline=True,
            min_lines=1,
            max_lines=3
        )
        
        self.date = ft.TextField(
            label="Date (YYYY-MM-DD)",
            value=datetime.now().strftime('%Y-%m-%d'),
            prefix_icon=ft.Icons.CALENDAR_MONTH
        )
        
        self.is_recurring = ft.Checkbox(
            label="Recurring expense (biweekly)",
            value=False
        )
        
        self.error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            visible=False
        )
        
        self.success_text = ft.Text(
            value="",
            color=ft.Colors.GREEN,
            visible=False
        )
        
        self.controls = [
            ft.AppBar(title=ft.Text("Add Expense")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.amount,
                        self.category,
                        self.description,
                        self.date,
                        self.is_recurring,
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Save",
                                    on_click=self.save_expense,
                                    icon=ft.Icons.SAVE
                                ),
                                ft.ElevatedButton(
                                    "Cancel",
                                    on_click=lambda e: self.page.go("/dashboard"),
                                    icon=ft.Icons.CANCEL
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        self.error_text,
                        self.success_text
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
    
    def save_expense(self, e):
        """Save expense to database"""
        try:
            # Validate inputs
            amount = float(self.amount.value)
            if amount <= 0:
                self.error_text.value = "Amount must be positive"
                self.error_text.visible = True
                self.page.update()
                return
            
            category = self.category.value.strip()
            if not category:
                self.error_text.value = "Category is required"
                self.error_text.visible = True
                self.page.update()
                return
            
            # Validate date format
            try:
                datetime.strptime(self.date.value, '%Y-%m-%d')
            except ValueError:
                self.error_text.value = "Date must be in YYYY-MM-DD format"
                self.error_text.visible = True
                self.page.update()
                return
            
            # Save to database
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO expenses 
                (user_id, amount, category, description, date, is_recurring)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    self.user_id, 
                    amount, 
                    category, 
                    self.description.value.strip(),
                    self.date.value,
                    1 if self.is_recurring.value else 0
                )
            )
            conn.commit()
            conn.close()
            
            # Show success message
            self.success_text.value = "Expense added successfully!"
            self.success_text.visible = True
            self.error_text.visible = False
            
            # Clear form
            self.amount.value = ""
            self.category.value = ""
            self.description.value = ""
            self.date.value = datetime.now().strftime('%Y-%m-%d')
            self.is_recurring.value = False
            
            self.page.update()
            
        except ValueError:
            self.error_text.value = "Amount must be a valid number"
            self.error_text.visible = True
            self.page.update()
        except Exception as ex:
            self.error_text.value = f"Error saving expense: {str(ex)}"
            self.error_text.visible = True
            self.page.update()

class ViewExpensesView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker, user_id: int):
        super().__init__(route="/view_expenses")
        self.page = page
        self.app = app
        self.user_id = user_id
        
        # Filter controls
        self.category_filter = ft.Dropdown(
            label="Filter by Category",
            options=[ft.dropdown.Option("All")],
            on_change=self.filter_expenses
        )
        
        self.period_filter = ft.Dropdown(
            label="Filter by Period",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Current Biweekly"),
                ft.dropdown.Option("Previous Biweekly")
            ],
            on_change=self.filter_expenses
        )
        
        # Expenses list
        self.expenses_list = ft.ListView(expand=True)
        
        # Load categories and expenses
        self.load_categories()
        self.load_expenses()
        
        self.controls = [
            ft.AppBar(title=ft.Text("View Expenses")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[self.category_filter, self.period_filter],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Divider(),
                        self.expenses_list
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
    
    def load_categories(self):
        """Load categories from database"""
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category",
                (self.user_id,)
            )
            
            categories = [ft.dropdown.Option("All")]
            categories.extend(ft.dropdown.Option(row[0]) for row in cursor.fetchall())
            
            self.category_filter.options = categories
            conn.close()
            
        except Exception as ex:
            print(f"Error loading categories: {ex}")
    
    def load_expenses(self, category_filter=None, period_filter=None):
        """Load expenses from database with optional filters"""
        try:
            # Clear current list
            self.expenses_list.controls.clear()
            
            # Build query
            query = '''
            SELECT id, amount, category, description, date, is_recurring 
            FROM expenses WHERE user_id = ?
            '''
            params = [self.user_id]
            
            # Apply category filter
            if category_filter and category_filter != "All":
                query += " AND category = ?"
                params.append(category_filter)
            
            # Apply period filter
            if period_filter and period_filter != "All":
                if period_filter == "Current Biweekly":
                    start_date, end_date = get_biweekly_period()
                elif period_filter == "Previous Biweekly":
                    # Get previous period by going back 15 days
                    prev_date = datetime.now() - timedelta(days=15)
                    start_date, end_date = get_biweekly_period(prev_date.strftime('%Y-%m-%d'))
                
                query += " AND date BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            
            query += " ORDER BY date DESC"
            
            # Execute query
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Add expenses to list
            for row in cursor.fetchall():
                expense_id, amount, category, description, date, is_recurring = row
                
                expense_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.ListTile(
                                    title=ft.Text(f"${amount:.2f} - {category}"),
                                    subtitle=ft.Text(
                                        f"{date}" + 
                                        (" (Recurring)" if is_recurring else "") +
                                        (f"\n{description}" if description else "")
                                    )
                                ),
                                ft.Row(
                                    controls=[
                                        ft.TextButton(
                                            "Edit",
                                            on_click=lambda e, id=expense_id: self.edit_expense(id)
                                        ),
                                        ft.TextButton(
                                            "Delete",
                                            on_click=lambda e, id=expense_id: self.delete_expense(id)
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.END
                                )
                            ]
                        ),
                        padding=10
                    )
                )
                
                self.expenses_list.controls.append(expense_card)
            
            conn.close()
            self.page.update()
            
        except Exception as ex:
            print(f"Error loading expenses: {ex}")
    
    def filter_expenses(self, e):
        """Apply filters to expenses list"""
        category = self.category_filter.value
        period = self.period_filter.value
        self.load_expenses(category, period)
    
    def edit_expense(self, expense_id):
        """Edit an expense (to be implemented)"""
        # Implementation for editing expenses
        pass
    
    def delete_expense(self, expense_id):
        """Delete an expense"""
        try:
            # Confirm deletion
            def confirm_delete(e):
                try:
                    conn = sqlite3.connect('expenses.db')
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                        (expense_id, self.user_id)
                    )
                    conn.commit()
                    conn.close()
                    
                    # Reload expenses
                    self.load_expenses(
                        self.category_filter.value, 
                        self.period_filter.value
                    )
                    
                    # Close dialog
                    self.page.close_dialog()
                    self.page.update()
                    
                except Exception as ex:
                    print(f"Error deleting expense: {ex}")
            
            def cancel_delete(e):
                self.page.close_dialog()
                self.page.update()
            
            # Show confirmation dialog
            self.page.dialog = ft.AlertDialog(
                title=ft.Text("Confirm Delete"),
                content=ft.Text("Are you sure you want to delete this expense?"),
                actions=[
                    ft.TextButton("Yes", on_click=confirm_delete),
                    ft.TextButton("No", on_click=cancel_delete)
                ]
            )
            self.page.dialog.open = True
            self.page.update()
            
        except Exception as ex:
            print(f"Error in delete confirmation: {ex}")

# Budget and Summary Views
class BiweeklySummaryView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker, user_id: int):
        super().__init__(route="/biweekly_summary")
        self.page = page
        self.app = app
        self.user_id = user_id
        
        # Period selection
        self.period_selector = ft.Dropdown(
            label="Select Period",
            options=[
                ft.dropdown.Option("Current"),
                ft.dropdown.Option("Previous")
            ],
            value="Current",
            on_change=self.load_summary
        )
        
        # Summary display
        self.summary_text = ft.Text()
        
        self.controls = [
            ft.AppBar(title=ft.Text("Biweekly Summary")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.period_selector,
                        ft.Divider(),
                        self.summary_text
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
        
        # Load initial summary
        self.load_summary(None)
    
    def load_summary(self, e):
        """Load biweekly summary"""
        try:
            # Get selected period dates
            if self.period_selector.value == "Current":
                start_date, end_date = get_biweekly_period()
            else:
                # Previous period
                prev_date = datetime.now() - timedelta(days=15)
                start_date, end_date = get_biweekly_period(prev_date.strftime('%Y-%m-%d'))
            
            # Get expenses for period
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute('''
            SELECT category, SUM(amount) 
            FROM expenses 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            ''', (self.user_id, start_date, end_date))
            
            expenses_by_category = cursor.fetchall()
            
            # Calculate total
            total = sum(amount for _, amount in expenses_by_category)
            
            # Format summary text
            summary_lines = [
                f"Biweekly Summary: {start_date} to {end_date}",
                f"Total: ${total:.2f}",
                "",
                "By Category:"
            ]
            
            for category, amount in expenses_by_category:
                percentage = (amount / total * 100) if total > 0 else 0
                summary_lines.append(
                    f"{category}: ${amount:.2f} ({percentage:.1f}%)"
                )
            
            self.summary_text.value = "\n".join(summary_lines)
            conn.close()
            self.page.update()
            
        except Exception as ex:
            self.summary_text.value = f"Error loading summary: {str(ex)}"
            self.page.update()

class SetBudgetView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker, user_id: int):
        super().__init__(route="/set_budget")
        self.page = page
        self.app = app
        self.user_id = user_id
        
        # Budget form
        self.category = ft.Dropdown(
            label="Category",
            options=[],
            prefix_icon=ft.Icons.CATEGORY
        )
        
        self.amount = ft.TextField(
            label="Budget Amount",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.ATTACH_MONEY
        )
        
        self.error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            visible=False
        )
        
        self.success_text = ft.Text(
            value="",
            color=ft.Colors.GREEN,
            visible=False
        )
        
        # Current budgets list
        self.budgets_list = ft.Column()
        
        self.controls = [
            ft.AppBar(title=ft.Text("Set Budgets")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.category,
                        self.amount,
                        ft.ElevatedButton(
                            "Set Budget",
                            on_click=self.set_budget,
                            icon=ft.Icons.SAVE
                        ),
                        self.error_text,
                        self.success_text,
                        ft.Divider(),
                        ft.Text("Current Budgets:", weight=ft.FontWeight.BOLD),
                        self.budgets_list
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
        
        # Load categories and current budgets
        self.load_categories()
        self.load_budgets()
    
    def load_categories(self):
        """Load categories from expenses"""
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category",
                (self.user_id,)
            )
            
            categories = [ft.dropdown.Option(row[0]) for row in cursor.fetchall()]
            self.category.options = categories
            conn.close()
            
        except Exception as ex:
            print(f"Error loading categories: {ex}")
    
    def load_budgets(self):
        """Load current budgets"""
        try:
            self.budgets_list.controls.clear()
            
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, amount FROM budgets WHERE user_id = ? ORDER BY category",
                (self.user_id,)
            )
            
            for category, amount in cursor.fetchall():
                self.budgets_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(category),
                        subtitle=ft.Text(f"${amount:.2f}"),
                        trailing=ft.IconButton(
                            ft.Icons.DELETE,
                            on_click=lambda e, cat=category: self.delete_budget(cat)
                        )
                    )
                )
            
            conn.close()
            self.page.update()
            
        except Exception as ex:
            print(f"Error loading budgets: {ex}")
    
    def set_budget(self, e):
        """Set budget for category"""
        try:
            category = self.category.value
            amount = float(self.amount.value)
            
            if not category:
                self.error_text.value = "Please select a category"
                self.error_text.visible = True
                self.page.update()
                return
            
            if amount <= 0:
                self.error_text.value = "Amount must be positive"
                self.error_text.visible = True
                self.page.update()
                return
            
            # Save to database
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE to update existing budgets
            cursor.execute(
                '''INSERT OR REPLACE INTO budgets (user_id, category, amount)
                VALUES (?, ?, ?)''',
                (self.user_id, category, amount)
            )
            
            conn.commit()
            conn.close()
            
            # Show success and reload
            self.success_text.value = f"Budget for {category} set to ${amount:.2f}"
            self.success_text.visible = True
            self.error_text.visible = False
            
            # Clear form
            self.amount.value = ""
            
            self.load_budgets()
            self.page.update()
            
        except ValueError:
            self.error_text.value = "Amount must be a valid number"
            self.error_text.visible = True
            self.page.update()
        except Exception as ex:
            self.error_text.value = f"Error setting budget: {str(ex)}"
            self.error_text.visible = True
            self.page.update()
    
    def delete_budget(self, category):
        """Delete a budget"""
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM budgets WHERE user_id = ? AND category = ?",
                (self.user_id, category)
            )
            conn.commit()
            conn.close()
            
            self.load_budgets()
            
        except Exception as ex:
            print(f"Error deleting budget: {ex}")

class SetAlertsView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker, user_id: int):
        super().__init__(route="/set_alerts")
        self.page = page
        self.app = app
        self.user_id = user_id
        
        # Alert form
        self.category = ft.Dropdown(
            label="Category",
            options=[],
            prefix_icon=ft.Icons.CATEGORY
        )
        
        self.threshold = ft.TextField(
            label="Alert Threshold ($)",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_icon=ft.Icons.WARNING
        )
        
        self.error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            visible=False
        )
        
        self.success_text = ft.Text(
            value="",
            color=ft.Colors.GREEN,
            visible=False
        )
        
        # Current alerts list
        self.alerts_list = ft.Column()
        
        self.controls = [
            ft.AppBar(title=ft.Text("Set Budget Alerts")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.category,
                        self.threshold,
                        ft.ElevatedButton(
                            "Set Alert",
                            on_click=self.set_alert,
                            icon=ft.Icons.SAVE
                        ),
                        self.error_text,
                        self.success_text,
                        ft.Divider(),
                        ft.Text("Current Alerts:", weight=ft.FontWeight.BOLD),
                        self.alerts_list
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
        
        # Load categories and current alerts
        self.load_categories()
        self.load_alerts()
    
    def load_categories(self):
        """Load categories from expenses"""
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category",
                (self.user_id,)
            )
            
            categories = [ft.dropdown.Option(row[0]) for row in cursor.fetchall()]
            self.category.options = categories
            conn.close()
            
        except Exception as ex:
            print(f"Error loading categories: {ex}")
    
    def load_alerts(self):
        """Load current alerts"""
        try:
            self.alerts_list.controls.clear()
            
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, threshold FROM budget_alerts WHERE user_id = ? ORDER BY category",
                (self.user_id,)
            )
            
            for category, threshold in cursor.fetchall():
                self.alerts_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(category),
                        subtitle=ft.Text(f"Alert at ${threshold:.2f}"),
                        trailing=ft.IconButton(
                            ft.Icons.DELETE,
                            on_click=lambda e, cat=category: self.delete_alert(cat)
                        )
                    )
                )
            
            conn.close()
            self.page.update()
            
        except Exception as ex:
            print(f"Error loading alerts: {ex}")
    
    def set_alert(self, e):
        """Set alert for category"""
        try:
            category = self.category.value
            threshold = float(self.threshold.value)
            
            if not category:
                self.error_text.value = "Please select a category"
                self.error_text.visible = True
                self.page.update()
                return
            
            if threshold <= 0:
                self.error_text.value = "Threshold must be positive"
                self.error_text.visible = True
                self.page.update()
                return
            
            # Save to database
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE to update existing alerts
            cursor.execute(
                '''INSERT OR REPLACE INTO budget_alerts (user_id, category, threshold)
                VALUES (?, ?, ?)''',
                (self.user_id, category, threshold)
            )
            
            conn.commit()
            conn.close()
            
            # Show success and reload
            self.success_text.value = f"Alert for {category} set at ${threshold:.2f}"
            self.success_text.visible = True
            self.error_text.visible = False
            
            # Clear form
            self.threshold.value = ""
            
            self.load_alerts()
            self.page.update()
            
        except ValueError:
            self.error_text.value = "Threshold must be a valid number"
            self.error_text.visible = True
            self.page.update()
        except Exception as ex:
            self.error_text.value = f"Error setting alert: {str(ex)}"
            self.error_text.visible = True
            self.page.update()
    
    def delete_alert(self, category):
        """Delete an alert"""
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM budget_alerts WHERE user_id = ? AND category = ?",
                (self.user_id, category)
            )
            conn.commit()
            conn.close()
            
            self.load_alerts()
            
        except Exception as ex:
            print(f"Error deleting alert: {ex}")

# Export View
class ExportView(ft.View):
    def __init__(self, page: ft.Page, app: ExpenseTracker, user_id: int):
        super().__init__(route="/export")
        self.page = page
        self.app = app
        self.user_id = user_id
        
        # Export options
        self.period_selector = ft.Dropdown(
            label="Select Period",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Current Biweekly"),
                ft.dropdown.Option("Previous Biweekly")
            ],
            value="All"
        )
        
        self.export_button = ft.ElevatedButton(
            "Export to CSV",
            on_click=self.export_csv,
            icon=ft.Icons.FILE_DOWNLOAD
        )
        
        self.status_text = ft.Text()
        
        self.controls = [
            ft.AppBar(title=ft.Text("Export Expenses")),
            ft.Container(
                content=ft.Column(
                    controls=[
                        self.period_selector,
                        self.export_button,
                        self.status_text
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        ]
    
    def export_csv(self, e):
        """Export expenses to CSV file"""
        try:
            # Build query based on selected period
            query = '''
            SELECT amount, category, description, date, is_recurring 
            FROM expenses WHERE user_id = ?
            '''
            params = [self.user_id]
            
            period = self.period_selector.value
            if period != "All":
                if period == "Current Biweekly":
                    start_date, end_date = get_biweekly_period()
                elif period == "Previous Biweekly":
                    prev_date = datetime.now() - timedelta(days=15)
                    start_date, end_date = get_biweekly_period(prev_date.strftime('%Y-%m-%d'))
                
                query += " AND date BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            
            query += " ORDER BY date"
            
            # Get expenses
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute(query, params)
            expenses = cursor.fetchall()
            
            # Get username for filename
            cursor.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
            username = cursor.fetchone()[0]
            conn.close()
            
            if not expenses:
                self.status_text.value = "No expenses to export for selected period"
                self.status_text.color = ft.Colors.ORANGE
                self.page.update()
                return
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"expenses_{username}_{timestamp}.csv"
            
            # Write to CSV
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Amount', 'Category', 'Description', 'Date', 'Recurring'])
                
                for expense in expenses:
                    writer.writerow(expense)
            
            self.status_text.value = f"Exported {len(expenses)} expenses to {filename}"
            self.status_text.color = ft.Colors.GREEN
            self.page.update()
            
        except Exception as ex:
            self.status_text.value = f"Error exporting: {str(ex)}"
            self.status_text.color = ft.Colors.RED
            self.page.update()

# Main application entry point
def main(page: ft.Page):
    # Create and run the expense tracker
    app = ExpenseTracker(page)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)