import winreg
import sqlite3
import tkinter as tk
from tkinter import ttk
import subprocess
import matplotlib.pyplot as plt


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
            attack_type TEXT,
            vulnerabilities TEXT
        )
    ''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def insert_into_database(app_name, last_attack_time=None, attack_type=None, vulnerabilities=None):
    # Insert application information into the database
    conn = sqlite3.connect('installed_apps.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO applications (app_name, last_attack_time, attack_type, vulnerabilities)
        VALUES (?, ?, ?, ?)
    ''', (app_name, last_attack_time, attack_type, vulnerabilities))

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

    # Sort the list of applications alphabetically
    apps.sort()

    return apps


def display_installed_apps():
    root = tk.Tk()
    root.title("Installed Applications")

    tree = ttk.Treeview(root)
    tree['columns'] = ('ID', 'Application Name', 'Last Attack Time', 'Attack Type', 'Vulnerabilities')
    tree.heading('ID', text='ID')
    tree.column('ID', width=50, anchor='center')
    tree.heading('Application Name', text='Application Name')
    tree.column('Application Name', width=200, anchor='w')
    tree.heading('Last Attack Time', text='Last Attack Time')
    tree.column('Last Attack Time', width=150, anchor='center')
    tree.heading('Attack Type', text='Attack Type')
    tree.column('Attack Type', width=150, anchor='w')
    tree.heading('Vulnerabilities', text='Vulnerabilities')
    tree.column('Vulnerabilities', width=150, anchor='w')

    installed_applications = get_installed_applications_from_registry()

    for idx, app_name in enumerate(installed_applications, start=1):
        last_attack_time, attack_type, vulnerabilities = get_attack_info_from_database(app_name)
        tree.insert('', 'end', values=(idx, app_name, last_attack_time, attack_type, vulnerabilities))

    tree.pack(expand=True, fill='both')

    # Add a button to display pie chart
    pie_chart_button = ttk.Button(root, text="Show Pie Chart", command=display_pie_chart)
    pie_chart_button.pack(pady=10)

    root.mainloop()


def get_attack_info_from_database(app_name):
    # Fetch attack information for an application from the database
    conn = sqlite3.connect('installed_apps.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT last_attack_time, attack_type, vulnerabilities FROM applications WHERE app_name = ?
    ''', (app_name,))
    result = cursor.fetchone()

    if result:
        conn.close()
        return result

    # If no information found, prompt user for input and store in the database
    last_attack_time = input(f"Enter Last Attack Time for '{app_name}': ")
    attack_type = input(f"Enter Attack Type for '{app_name}': ")
    vulnerabilities = input(f"Enter Vulnerabilities for '{app_name}': ")
    insert_into_database(app_name, last_attack_time, attack_type, vulnerabilities)
    conn.close()
    return last_attack_time, attack_type, vulnerabilities


def display_pie_chart():
    vulnerabilities_data = get_vulnerabilities_data()

    if not vulnerabilities_data:
        tk.messagebox.showinfo("No Data", "No data available to display a pie chart.")
        return

    labels = list(vulnerabilities_data.keys())
    sizes = list(vulnerabilities_data.values())

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("Vulnerabilities Distribution")
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.show()


def get_vulnerabilities_data():
    # Fetch vulnerabilities data from the database and calculate distribution
    conn = sqlite3.connect('installed_apps.db')
    cursor = conn.cursor()

    cursor.execute('SELECT vulnerabilities FROM applications')
    vulnerabilities_list = cursor.fetchall()

    conn.close()

    vulnerabilities_count = {}
    for vulnerabilities in vulnerabilities_list:
        vulnerabilities = vulnerabilities[0].split(', ')  # Assuming vulnerabilities are separated by comma
        for vulnerability in vulnerabilities:
            vulnerabilities_count[vulnerability] = vulnerabilities_count.get(vulnerability, 0) + 1

    return vulnerabilities_count


# Create the database if it doesn't exist
create_database()

# Display the installed applications in the GUI
display_installed_apps()
