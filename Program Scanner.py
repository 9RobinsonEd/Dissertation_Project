import winreg
import sqlite3
import tkinter as tk
from tkinter import ttk
import subprocess

def create_database():
    # Connect to the SQLite database
    conn = sqlite3.connect('installed_apps.db')
    cursor = conn.cursor()

    # Create a new table for applications if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            app_name TEXT UNIQUE,
            last_attack_time TEXT,
            attack_type TEXT
        )
    ''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def insert_into_database(app_name, last_attack_time=None, attack_type=None):
    # Insert application information into the database
    conn = sqlite3.connect('installed_apps.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO applications (app_name, last_attack_time, attack_type)
        VALUES (?, ?, ?)
    ''', (app_name, last_attack_time, attack_type))

    conn.commit()
    conn.close()

def get_installed_applications_from_registry():
    # Fetch installed applications from the registry
    apps = []
    reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    reg_key = winreg.HKEY_LOCAL_MACHINE

    try:
        with winreg.OpenKey(reg_key, reg_path) as reg:
            for i in range(winreg.QueryInfoKey(reg)[0]):
                subkey_name = winreg.EnumKey(reg, i)
                with winreg.OpenKey(reg, subkey_name) as app_key:
                    try:
                        app_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
                        apps.append(app_name)
                    except FileNotFoundError:
                        pass
    except Exception as e:
        print("Error fetching from registry:", e)

    return apps

def display_installed_apps():
    root = tk.Tk()
    root.title("Installed Applications")

    tree = ttk.Treeview(root)
    tree['columns'] = ('ID', 'Application Name', 'Last Attack Time', 'Attack Type')
    tree.heading('ID', text='ID')
    tree.column('ID', width=50, anchor='center')
    tree.heading('Application Name', text='Application Name')
    tree.column('Application Name', width=250, anchor='w')
    tree.heading('Last Attack Time', text='Last Attack Time')
    tree.column('Last Attack Time', width=150, anchor='center')
    tree.heading('Attack Type', text='Attack Type')
    tree.column('Attack Type', width=150, anchor='w')

    installed_applications = get_installed_applications_from_registry()

    for idx, app_name in enumerate(installed_applications, start=1):
        last_attack_time, attack_type = get_attack_info_from_database(app_name)
        tree.insert('', 'end', values=(idx, app_name, last_attack_time, attack_type))

    tree.pack(expand=True, fill='both')

    root.mainloop()

def get_attack_info_from_database(app_name):
    # Fetch attack information for an application from the database
    conn = sqlite3.connect('installed_apps.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT last_attack_time, attack_type FROM applications WHERE app_name = ?
    ''', (app_name,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result
    else:
        # If no information found, prompt user for input and store in the database
        last_attack_time = input(f"Enter Last Attack Time for '{app_name}': ")
        attack_type = input(f"Enter Attack Type for '{app_name}': ")
        insert_into_database(app_name, last_attack_time, attack_type)
        return last_attack_time, attack_type

# Create the database if it doesn't exist
create_database()

# Display the installed applications in the GUI
display_installed_apps()
