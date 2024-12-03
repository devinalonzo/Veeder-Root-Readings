import tkinter as tk
from tkinter import ttk, messagebox
import telnetlib
import threading
import os
import json
import time

CONFIG_FILE = "telnet_logger_config.json"


def save_config(data):
    """Save input data to a configuration file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def load_config():
    """Load input data from the configuration file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def get_unique_filename(base_filename):
    """Generate a unique filename for second readings."""
    if not os.path.exists(base_filename):
        return base_filename

    # Append `- 2nd Reading` before the file extension
    name, ext = os.path.splitext(base_filename)
    second_reading_filename = f"{name} - 2nd Reading{ext}"
    return second_reading_filename


def connect_and_log():
    ip = ip_entry.get().strip()
    tank = tank_entry.get().strip()
    site_name = site_name_entry.get().strip()
    site_number = site_number_entry.get().strip()

    if not ip or not tank or not site_name or not site_number:
        messagebox.showerror("Input Error", "All fields must be filled out.")
        return

    # Save inputs to config
    config = {"ip": ip, "tank": tank, "site_name": site_name, "site_number": site_number}
    save_config(config)

    # Disable button and start progress bar
    connect_button.config(state="disabled")

    # Define commands
    commands = [
        f"\x01I11300",
        f"\x01I20C0{tank}",
        f"\x01IA540{tank}",
        f"\x01I2030{tank}",
        f"\x01I2070{tank}",
        f"\x01I2080{tank}",
    ]

    # Set progress bar
    progress_bar["value"] = 0
    progress_bar["maximum"] = len(commands)

    # Generate the base filename
    base_filename = os.path.expanduser(f"~/Desktop/{site_name} - {site_number} - Tank {tank}.txt")
    unique_filename = get_unique_filename(base_filename)

    def log_responses():
        try:
            # Connect to the device using Telnet on port 4004
            tn = telnetlib.Telnet(ip, port=4004, timeout=10)
            log_text = f"Connected to {ip}\n"

            with open(unique_filename, "w") as logfile:
                logfile.write(log_text)

                for i, command in enumerate(commands, start=1):
                    tn.write(command.encode("ascii") + b"\n")
                    time.sleep(0.5)  # Allow time for response to start arriving

                    command_responses = []
                    while True:
                        try:
                            response = tn.read_until(b"\x03", timeout=2).decode("ascii")  # End with ETX
                            if response:
                                command_responses.append(response)
                            else:
                                break
                        except EOFError:
                            break

                    # Log the command and its responses
                    log_text += f"Command: {command}\n"
                    log_text += "Response:\n" + "".join(command_responses) + "\n\n"
                    logfile.write(f"Command: {command}\n")
                    logfile.write("Response:\n" + "".join(command_responses) + "\n\n")

                    # Update progress bar
                    progress_bar["value"] = i

            tn.close()
            messagebox.showinfo("Success", f"Logs saved to {unique_filename}")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
        finally:
            # Re-enable button and reset progress bar
            connect_button.config(state="normal")
            progress_bar["value"] = 0

    threading.Thread(target=log_responses).start()


# GUI setup
root = tk.Tk()
root.title("Telnet Logger")

# Load saved config
config = load_config()
ip_default = config.get("ip", "")
tank_default = config.get("tank", "")
site_name_default = config.get("site_name", "")
site_number_default = config.get("site_number", "")

# Input labels and fields
tk.Label(root, text="IP Address:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
ip_entry = tk.Entry(root, width=30)
ip_entry.insert(0, ip_default)
ip_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Tank #:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
tank_entry = tk.Entry(root, width=30)
tank_entry.insert(0, tank_default)
tank_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Site Name:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
site_name_entry = tk.Entry(root, width=30)
site_name_entry.insert(0, site_name_default)
site_name_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Site #:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
site_number_entry = tk.Entry(root, width=30)
site_number_entry.insert(0, site_number_default)
site_number_entry.grid(row=3, column=1, padx=10, pady=5)

# Progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.grid(row=4, column=0, columnspan=2, pady=10)

# Connect button
connect_button = tk.Button(root, text="Connect and Log", command=connect_and_log)
connect_button.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
