import tkinter as tk
from tkinter import ttk, Menu, filedialog, messagebox
import obd

class OBDIITool:
    def __init__(self, root):
        # Create the main application window
        self.root = root
        self.root.title("Python OBDScanner")
        self.root.geometry("800x600")

        # OBD Connection Setup
        self.connection = None

        # Create the menubar
        self.menu_bar = Menu(root)
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Quit", command=root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.root.config(menu=self.menu_bar)

        # Create the notebook container for tabs
        self.notebook = ttk.Notebook(root)

        # Add spacing to notebook tab names
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", padding=[10,5])

        # Create tab1
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="DTCs")

        # Create tab2
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Live Data")

        # Create tab3
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="Scope")

        # Tab1 - Treeview for DTCs
        self.dtc_tree = ttk.Treeview(self.tab1, columns=("Code", "Description"), show="headings")
        self.dtc_tree.heading("Code", text="Code")
        self.dtc_tree.heading("Description", text="Description")
        self.dtc_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1 - Clear DTC Button
        self.button_clear_dtcs = tk.Button(self.tab1, text="Clear All", command=self.clear_dtcs)
        self.button_clear_dtcs.pack(pady=10)

        # Tab2 - Treeview Live Data
        self.live_data_tree = ttk.Treeview(self.tab2, columns=("Parameter", "Value", "Unit"), show="headings")
        self.live_data_tree.heading("Parameter", text="Paramater")
        self.live_data_tree.heading("Value", text="Value")
        self.live_data_tree.heading("Unit", text="Unit")
        self.live_data_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab2 - Start/Stop Live Data
        self.button_toggle_livedata = tk.Button(self.tab2, text="Start Live Data", command=self.start_live_data)
        self.button_toggle_livedata.pack(pady=10)

        # Notebook layout pack
        self.notebook.pack(expand=True, fill=tk.BOTH)

        # Create a status bar (bottom of window)
        self.status_bar = tk.Frame(root, bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Add a connect button to connect
        self.button_connect = tk.Button(self.status_bar, text="<->", command=self.connect_to_obd)
        self.button_connect.pack(side=tk.LEFT, padx=10, pady=5)

        # Add connection information to the status bar
        self.status_label = tk.Label(self.status_bar, text="Disconnected", anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

    def connect_to_obd(self):
        try:
            self.connection = obd.OBD()  # connect to adapter
            if self.connection.is_connected():
                self.status_label.config(text="Connected", fg="green")
                self.get_dtcs()
            else:
                self.status_label.config(text="Failed to connect", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to OBD-II adapter: {e}")

    def get_dtcs(self):
        if self.connection and self.connection.is_connected():
            # Fetch DTCs
            dtcs = self.connection.query(obd.commands.GET_DTC)
            if dtcs and dtcs.value:
                for code, description in dtcs.value:
                    self.dtc_tree.insert("", "end", values=(code, description))
            else:
                self.dtc_tree.insert("", "end", values=("No DTCs", "No trouble codes found"))

    def clear_dtcs(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.clear_dtc()
                messagebox.showinfo("Success", "DTCs Cleared!")
                self.get_dtcs()  # Refresh the list after clear
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear DTCs: {e}")

    def start_live_data(self):
        pid_ranges = [obd.commands.PIDS_A, obd.commands.PIDS_B, obd.commands.PIDS_C]
        self.supported_pids = []  # Create empty list

        for pid_range in pid_ranges:   # Breakdown individual PIDS_X
            response = self.connection.query(pid_range)   # ex. Query PIDS_A
            if not response.is_null():
                bit_array = response.value
                print("DEBUG response.value: ", bit_array)
                for i, bit in enumerate(bit_array.bin):
                    if bit == "1":
                        pid_num = i + 1
                        pid_command = obd.commands.get(f"PID_{pid_num:02X}")
                        if pid_command:
                            self.supported_pids.append(pid_command)

        for pid_command in self.supported_pids:
            self.live_data_tree.insert("", tk.END, values=(pid_command.command, pid_command.name, "Waiting..."))
            
        self.update_live_data()

    def update_live_data(self):
        for i, pid_command in enumerate(self.supported_pids):
            response = self.connection.query(pid_command)
            if not response.is_null():
                value = response.value
                # update the treeview row
                self.live_data_tree.set(self.live_data_tree.get_children()[i], "Value", f"{value}")

        self.root.after(1000, self.update_live_data)

# Run the application
if __name__ == "__main__":
#root.protocol("WM_DELETE_WINDOW", on_closing)
    root = tk.Tk()
    app = OBDIITool(root)
    root.mainloop()
