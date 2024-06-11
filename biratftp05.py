import tkinter as tk
from tkinter import Listbox, Label, Entry, Button, PhotoImage, StringVar, messagebox, Scrollbar, filedialog, Tk
from tkinter import ttk
from ftplib import FTP
import json
import os
from tkinter import simpledialog
from tkinter.simpledialog import askstring
from PIL import Image, ImageTk
import webbrowser
import ftplib
import tempfile
import posixpath 
import threading
import time
from tkinter import filedialog, messagebox
from threading import Timer
from tkinter import simpledialog, ttk
from cryptography.fernet import Fernet





class FTPClient:
    def __init__(self, root):
        self.root = root
        self.ftp = None
        self.root.title('bitratFTP v0.5')
        self.root.geometry('900x500')
        self.current_directory = '/'
        self.key = self.load_key()
        self.cipher_suite = Fernet(self.key)
        self.create_menu()  
        self.create_context_menu() 
        self.setup_treeview()  # Setup Treeview and load icons
        self.last_activity_time = time.time()
        self.activity_lock = threading.Lock()
        self.timeout_seconds = 300  # 5 minutes
        self.timeout_timer = None
        self.is_logged_in = False
        self.start_timeout_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Track connection status
        self.create_widgets()
        self.create_context_menu()
        self.update_buttons_state(False)

        # Set the window icon
        self.root.iconbitmap('ftpclient.ico')
        self.login_button = Button(self.root, text="Login", command=self.login, width=15, height=2)
        self.login_button.grid(row=6, column=0, padx=5, pady=5)


        ##############
        #Button setup#
        ##############
        # Place all buttons in the same row, next to each other
 
    def load_key(self):
        """Generate a key for encryption if it doesn't exist and load it."""
        key_file = "secret.key"
        if not os.path.exists(key_file):
            key = Fernet.generate_key()
            with open(key_file, 'wb') as key_out:
                key_out.write(key)
        else:
            with open(key_file, 'rb') as key_in:
                key = key_in.read()
        return key


    def create_widgets(self):
        button_width = 15  # Width in character units
        button_height = 2  # Height in lines (text lines)

        self.btn_login = Button(self.root, text="Login", command=self.login, width=button_width, height=button_height)
        self.btn_login.grid(row=6, column=0, padx=5, pady=5)

        self.btn_downloadfiles = Button(self.root, text="Download File(s)", command=self.download_files, width=button_width, height=button_height)
        self.btn_downloadfiles.grid(row=6, column=1, padx=5, pady=5)

        self.btn_uploadfiles = Button(self.root, text="Upload File(s)", command=self.upload_files, width=button_width, height=button_height)
        self.btn_uploadfiles.grid(row=6, column=2, padx=5, pady=5)

        self.btn_downloadfolders = Button(self.root, text="Download Folder(s)", command=self.download_selected_folder, width=button_width, height=button_height)
        self.btn_downloadfolders.grid(row=6, column=4, padx=5, pady=5)

        self.btn_uploadfolders = Button(self.root, text="Upload Folder", command=self.upload_selected_folder, width=button_width, height=button_height)
        self.btn_uploadfolders.grid(row=6, column=5, padx=5, pady=5)

        self.btn_movefolders = Button(self.root, text="Move Folder(s)", command=self.move_folders, width=button_width, height=button_height)
        self.btn_movefolders.grid(row=7, column=5, padx=5, pady=5)

        self.btn_enterfolder = Button(self.root, text="Enter Folder", command=self.enter_directory, width=button_width, height=button_height)
        self.btn_enterfolder.grid(row=7, column=0, padx=5, pady=5)

        self.btn_goup = Button(self.root, text="Go Up", command=self.go_up, width=button_width, height=button_height)
        self.btn_goup.grid(row=7, column=1, padx=5, pady=5)

        self.btn_movefiles = Button(self.root, text="Move File(s)", command=self.move_files, width=button_width, height=button_height)
        self.btn_movefiles.grid(row=7, column=2, padx=5, pady=5)

        self.btn_logout = Button(self.root, text="Log Out", command=self.logout, width=button_width, height=button_height)
        self.btn_logout.grid(row=7, column=3, padx=5, pady=5)

        self.btn_deletefiles = Button(self.root, text="Delete File(s)", command=self.delete_file, width=button_width, height=button_height)
        self.btn_deletefiles.grid(row=7, column=4, padx=5, pady=5)

        self.btn_deletefolders = Button(self.root, text="Delete Folder(s)", command=self.delete_folder, width=button_width, height=button_height)
        self.btn_deletefolders.grid(row=6, column=4, padx=5, pady=5)

        self.new_folder_button = Button(self.root, text="New Folder", command=self.create_new_folder, width=button_width, height=button_height)
        self.new_folder_button.grid(row=6, column=3, padx=5, pady=5)

        self.tree.bind("<Button-3>", self.show_context_menu)  # Button-3 is the right-click button on most mice
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=200, mode='determinate')
        self.progress.grid(row=9, columnspan=6, sticky='ew')

        self.tree.bind("<Button-3>", self.show_context_menu)  # Button-3 is the right-click button on most mice
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=200, mode='determinate')
        self.progress.grid(row=9, columnspan=6, sticky='ew')

        self.create_context_menu()  # Initialize the context menu

        # Configure grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Rows configuration where necessary
        for i in range(8):  # Adjust the range as necessary for your rows
            self.root.grid_rowconfigure(i, weight=1)

        # Setup labels and entries
        Label(self.root, text="Host:").grid(row=0, column=0, sticky='e', padx=10, pady=5)
        self.host_entry = Entry(self.root)
        self.host_entry.grid(row=0, column=1, sticky='ew', padx=10)

        Label(self.root, text="Port:").grid(row=1, column=0, sticky='e', padx=10, pady=5)
        self.port_entry = Entry(self.root)
        self.port_entry.insert(0, '21')  # Default FTP port
        self.port_entry.grid(row=1, column=1, sticky='ew', padx=10)

        Label(self.root, text="Username:").grid(row=2, column=0, sticky='e', padx=10, pady=5)
        self.username_entry = Entry(self.root)
        self.username_entry.grid(row=2, column=1, sticky='ew', padx=10)

        Label(self.root, text="Password:").grid(row=3, column=0, sticky='e', padx=10, pady=5)
        self.password_entry = Entry(self.root, show="*")
        self.password_entry.grid(row=3, column=1, sticky='ew', padx=10)

        # Status label setup
        self.status_var = StringVar()
        self.status_label = Label(self.root, textvariable=self.status_var, fg='red')
        self.status_label.grid(row=8, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        # Configure Treeview layout not to overlap
        self.tree.grid(row=4, column=0, columnspan=5, rowspan=2, sticky='nsew', padx=10, pady=10)

        # Scrollbar for the Treeview
        scroll = tk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        scroll.grid(row=4, column=5, sticky='ns', pady=10)
        self.tree.configure(yscrollcommand=scroll.set)


    def encrypt_data(self, data):
        """Encrypt data using the cipher suite."""
        return self.cipher_suite.encrypt(data.encode())

    def decrypt_data(self, encrypted_data):
        """Decrypt data using the cipher suite."""
        return self.cipher_suite.decrypt(encrypted_data).decode()

    def update_buttons_state(self, connected):
        state = 'normal' if connected else 'disabled'
        self.btn_downloadfiles.config(state=state)
        self.btn_uploadfiles.config(state=state)
        self.btn_downloadfolders.config(state=state)
        self.btn_uploadfolders.config(state=state)
        self.btn_movefolders.config(state=state)
        self.btn_enterfolder.config(state=state)
        self.btn_goup.config(state=state)
        self.btn_movefiles.config(state=state)
        self.btn_logout.config(state=state) 
        self.btn_deletefiles.config(state=state)
        self.btn_deletefolders.config(state=state)
        self.new_folder_button.config(state=state) 

        # Update context menu items
        for index in range(self.context_menu.index('end') + 1):
            try:
                label = self.context_menu.entrycget(index, 'label')
                if label != "Refresh":
                    self.context_menu.entryconfig(index, state=state)
            except tk.TclError:
                continue  # Handle exceptions for non-standard menu items or separators

        # Update File menu items
        self.profile_menu.entryconfig("Login", state='disabled' if connected else 'normal')
        self.profile_menu.entryconfig("Log out", state=state)
        for label in ["Create new folder..", "Upload files..", "Upload folder..", "Move files", "Move folder..",
                      "Download selected files..", "Download selected folder..", "Delete selected folder..",
                      "Delete selected files..", "Rename"]:
            self.profile_menu.entryconfig(label, state=state)


    def setup_treeview(self):
        # Load and resize icons
        folder_img = Image.open('folder.ico')  # Ensure this path is correct
        file_img = Image.open('file.ico')      # Ensure this path is correct

        # Resize icons and convert to PhotoImage
        self.folder_icon = ImageTk.PhotoImage(folder_img.resize((12, 12), Image.Resampling.LANCZOS))
        self.file_icon = ImageTk.PhotoImage(file_img.resize((12, 12), Image.Resampling.LANCZOS))

        # Setup the Treeview with columns
        self.tree = ttk.Treeview(self.root, selectmode="extended", columns=("Filetype"), show="tree headings")
        self.tree.heading("#0", text="Name", anchor='w', command=lambda: self.treeview_sort_column(self.tree, "#0", False))
        self.tree.column("#0", anchor="w", width=200)
        self.tree.heading("Filetype", text="File Type", anchor='w', command=lambda: self.treeview_sort_column(self.tree, "Filetype", False))
        self.tree.column("Filetype", anchor="w", width=150)

        # Set grid and configure weights
        self.tree.grid(row=1, column=0, sticky='nsew', padx=(10, 10), pady=(10, 10))
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # Bindings for drag and double-click actions
        self.tree.bind("<Button-1>", self.start_drag)
        self.tree.bind("<B1-Motion>", self.on_drag)
        self.tree.bind("<ButtonRelease-1>", self.stop_drag)
        self.dragging = False
        self.tree.bind("<Double-1>", self.on_tree_double_click)


    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)

        # Common options
        self.context_menu.add_command(label="Copy", command=self.copy_item, state="disabled")
        self.context_menu.add_command(label="Paste", command=self.paste_item, state="disabled")
        self.context_menu.add_command(label="Create new folder", command=self.create_new_folder, state="disabled")
        self.context_menu.add_command(label="Rename", command=self.start_rename, state="disabled")

        # Refresh option
        self.context_menu.add_command(label="Refresh", command=self.refresh_view)  # Always enabled

        # Separator
        self.context_menu.add_separator()

        # File-specific options
        self.context_menu.add_command(label="Download File", command=self.download_files, state="disabled")
        self.context_menu.add_command(label="Move File(s)", command=self.move_files, state="disabled")
        self.context_menu.add_command(label="Delete File", command=self.delete_file, state="disabled")

        # Separator
        self.context_menu.add_separator()

        # Folder-specific options
        self.context_menu.add_command(label="Enter Directory", command=self.enter_directory, state="disabled")
        self.context_menu.add_command(label="Download Folder", command=self.download_selected_folder, state="disabled")
        self.context_menu.add_command(label="Move Folder(s)", command=self.move_folders, state="disabled")
        self.context_menu.add_command(label="Delete Folder", command=self.delete_folder, state="disabled")


        # Initially disable all as nothing is selected yet
        # Use exception handling to skip separators
        for index in range(self.context_menu.index('end')+1):
            try:
                self.context_menu.entryconfig(index, state='disabled')
            except tk.TclError:
                continue  # This skips the separator entries


    def show_context_menu(self, event):
        if self.ftp is None:
            # If not connected, disable all except "Refresh"
            for index in range(self.context_menu.index('end') + 1):
                try:
                    label = self.context_menu.entrycget(index, 'label')
                    if label == "Refresh":
                        self.context_menu.entryconfig(index, state='normal')
                    else:
                        self.context_menu.entryconfig(index, state='disabled')
                except tk.TclError:
                    continue
        else:
            # If connected, configure the context menu based on the selection
            item_id = self.tree.identify_row(event.y)
            if item_id:
                if item_id not in self.tree.selection():
                    self.tree.selection_set(item_id)  # Set the selection to just this item

                item = self.tree.item(item_id)
                item_type = item['values'][1] if len(item['values']) > 1 else None

                # Reset all items to disabled to avoid erroneous enabling
                for index in range(self.context_menu.index('end') + 1):
                    try:
                        self.context_menu.entryconfig(index, state='disabled')
                    except tk.TclError:
                        continue  # Ignore errors, likely due to separators or non-configurable items

                if item_type == "Directory":
                    actions_to_enable = ["Copy", "Paste", "Rename", "Enter Directory", "Download Folder", "Move Folder(s)", "Delete Folder"]
                elif item_type == "File":
                    actions_to_enable = ["Copy", "Paste", "Rename", "Download File", "Move File(s)", "Delete File"]
                else:
                    actions_to_enable = []

                for index in range(self.context_menu.index('end') + 1):
                    try:
                        label = self.context_menu.entrycget(index, 'label')
                        if label in actions_to_enable or label == "Refresh":
                            self.context_menu.entryconfig(index, state='normal')
                    except tk.TclError:
                        continue  # Handle exceptions for non-standard menu items or separators
            else:
                # When no specific item is selected, enable/disable based on general conditions
                for index in range(self.context_menu.index('end') + 1):
                    try:
                        label = self.context_menu.entrycget(index, 'label')
                        if label in ["Create new folder", "Paste", "Refresh"]:
                            self.context_menu.entryconfig(index, state='normal')
                        else:
                            self.context_menu.entryconfig(index, state='disabled')
                    except tk.TclError:
                        continue

        self.context_menu.post(event.x_root, event.y_root)

            
    def refresh_view(self):
        """Refresh the current view by re-listing files in the current directory."""
        self.list_files(self.current_directory)
        self.update_status("View refreshed.")
        self.reset_activity_timer()
        


    def find_menu_index(self, label):
        """Utility function to find the index of a menu item by label."""
        for index in range(self.context_menu.index('end') + 1):
            if self.context_menu.entrycget(index, "label") == label:
                return index
        return None


        # Show the menu at the cursor position
        self.context_menu.post(event.x_root, event.y_root)

    def copy_item(self):
        selected = self.tree.selection()
        if not selected:
            self.update_status("No items selected to copy.", error=True)
            return

        # Store all selected items along with their types
        self.copied_items = []
        for item_id in selected:
            item = self.tree.item(item_id)
            item_name = item['text']
            is_directory = item['values'][0] == "Directory"
            self.copied_items.append((item_name, is_directory))
        self.reset_activity_timer()
        self.update_status(f"Copied {len(self.copied_items)} items.", error=False)

    def paste_item(self):
        if not self.copied_items:
            self.update_status("No items to paste.", error=True)
            return

        target_directory = self.ftp.pwd()  # Get the current directory as the target
        errors = []

        for item_name, is_directory in self.copied_items:
            try:
                if is_directory:
                    # Implement directory copy logic (more complex, often needs recursion)
                    self.copy_directory(item_name, target_directory)
                    self.reset_activity_timer()
                else:
                    # Simple file copy logic
                    self.copy_file(item_name, target_directory)
                self.update_status(f"Pasted '{item_name}' to '{target_directory}'.", error=False)
                self.reset_activity_timer()
            except Exception as e:
                errors.append(str(e))
                self.reset_activity_timer()
        if errors:
            self.update_status("Failed to paste some items: " + ", ".join(errors), error=True)

        self.list_files()  # Refresh the listing

    def upload_file(self, local_path, remote_path):
        """Upload a file to an FTP server."""
        with open(local_path, 'rb') as f:
            self.ftp.storbinary(f'STOR {remote_path}', f)
        self.reset_activity_timer()

    def copy_file(self, src_file, target_directory):
        # Normalize paths using posixpath
        src_directory, filename = posixpath.split(src_file)
        src_directory = '/' + src_directory.strip('/')  # Ensure absolute path
        target_directory = '/' + target_directory.strip('/')  # Ensure absolute path

        # Download the file to a temporary location
        local_temp_file = posixpath.join(tempfile.gettempdir(), filename)
        try:
            with open(local_temp_file, 'wb') as local_file:
                self.ftp.retrbinary('RETR ' + src_file, local_file.write)
        except ftplib.error_perm as e:
            self.update_status(f"Download failed: {e}", error=True)
            return

        # Ensure the target directory exists on the server
        try:
            self.ftp.cwd(target_directory)
        except ftplib.error_perm:
            # If the directory doesn't exist, try to create it
            try:
                self.ftp.mkd(target_directory)
                self.ftp.cwd(target_directory)
            except ftplib.error_perm as e:
                self.update_status(f"Failed to create directory {target_directory}: {e}", error=True)
                return

        # Upload the file to the new location
        new_path = posixpath.join(target_directory, filename)
        try:
            with open(local_temp_file, 'rb') as local_file:
                self.ftp.storbinary('STOR ' + new_path, local_file)
            self.update_status(f"Pasted '{filename}' to '{new_path}'.", error=False)
            self.list_files()
        except ftplib.error_perm as e:
            self.update_status(f"Upload failed: {e}", error=True)
        finally:
            os.remove(local_temp_file)  # Clean up the temporary file
        self.reset_activity_timer()
    def start_drag(self, event):
        # Start drag operation
        self.dragging = True
        self.tree.selection_remove(self.tree.selection())  # Optionally clear existing selection
        self.reset_activity_timer()     
    def on_drag(self, event):
        if not self.dragging:
            return

        # Identify the item on current drag position
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # Select the item as part of the drag selection
            self.tree.selection_add(item_id)

    def stop_drag(self, event):
        # Stop drag operation
        self.dragging = False




        # File list box setup below the login form

    def create_new_folder(self):
        # Prompt user to enter the name of the new folder
        folder_name = simpledialog.askstring("New Folder", "Enter name for new folder:")
        if folder_name:
            try:
                self.ftp.mkd(folder_name)  # Attempt to create new directory on the FTP server
                self.update_status(f"Folder '{folder_name}' created successfully.", error=False)
                self.list_files()  # Refresh the list to show the new folder
            except Exception as e:
                self.update_status(f"Failed to create folder: {str(e)}", error=True)
        else:
            self.update_status("Folder creation cancelled.", error=True)
        self.reset_activity_timer()




    def upload_selected_folder(self):
        local_dir = filedialog.askdirectory(title="Select Local Directory to Upload")
        if not local_dir:
            return  # User cancelled the dialog

        remote_dir = simpledialog.askstring("Upload", "Enter the remote directory path:")
        if not remote_dir:
            return  # User cancelled or entered an invalid path

        try:
            self.update_status("Starting folder upload...", error=False)
            upload_folder(self.ftp, local_dir, remote_dir)
            self.update_status("Folder uploaded successfully.", error=False)
            self.list_files
        except Exception as e:
            self.update_status(f"Failed to upload folder: {str(e)}", error=True)
        self.reset_activity_timer()
        
    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Create "File" menu
        self.profile_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=self.profile_menu)

        self.menu_login = self.profile_menu.add_command(label="Login", command=self.login)
        self.profile_menu.add_separator()

        self.menu_create_new_folder = self.profile_menu.add_command(label="Create new folder..", command=self.create_new_folder)
        self.profile_menu.add_separator()

        self.menu_upload_files = self.profile_menu.add_command(label="Upload files..", command=self.upload_files)
        self.menu_upload_folder = self.profile_menu.add_command(label="Upload folder..", command=self.upload_selected_folder)
        self.profile_menu.add_separator()

        self.menu_move_files = self.profile_menu.add_command(label="Move files", command=self.move_files)
        self.menu_move_folder = self.profile_menu.add_command(label="Move folder..", command=self.move_folders)
        self.profile_menu.add_separator()

        self.menu_download_files = self.profile_menu.add_command(label="Download selected files..", command=self.download_files)
        self.menu_download_folder = self.profile_menu.add_command(label="Download selected folder..", command=self.download_selected_folder)
        self.profile_menu.add_separator()

        self.menu_delete_folder = self.profile_menu.add_command(label="Delete selected folder..", command=self.delete_folder)
        self.menu_delete_files = self.profile_menu.add_command(label="Delete selected files..", command=self.delete_file)
        self.profile_menu.add_separator()

        self.menu_refresh = self.profile_menu.add_command(label="Refresh", command=self.refresh_view)
        self.menu_rename = self.profile_menu.add_command(label="Rename", command=self.start_rename)
        self.profile_menu.add_separator()

        self.menu_logout = self.profile_menu.add_command(label="Log out", command=self.logout)


        # Create "Settings" menu
        profile_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=profile_menu)
            # Variable to hold the download directory setting
        self.download_option = tk.StringVar(value="prompt")
        # Add radio buttons to choose the download directory behavior
        profile_menu.add_radiobutton(label="Prompt for download directory on download", variable=self.download_option, value="prompt")
        profile_menu.add_radiobutton(label="Set default download directory...", variable=self.download_option, value="default", command=self.set_download_directory)


        # Create "Profile" menu
        profile_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Profile", menu=profile_menu)

        profile_menu.add_command(label="Save Profile", command=self.save_profile)
        profile_menu.add_command(label="Load Profile", command=self.load_profile)
        profile_menu.add_command(label="Delete Profile", command=self.delete_profile)

        # Create "Help" menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)

    def show_about(self):
    # Show about dialog or information
        tk.messagebox.showinfo("About", "bitratFTP version 0.5. Developed by Karl Olav Edland.")
        self.reset_activity_timer() 
    def show_docs(self):
    # Show documentation or open a URL
        webbrowser.open('https://bitrat.org/bitratftp.html')

    def save_profile(self):
        profile = {
            "host": self.host_entry.get(),
            "port": self.port_entry.get(),
            "username": self.username_entry.get(),
            "password": self.password_entry.get()
        }
        profile_name = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if profile_name:
            encrypted_profile = self.encrypt_data(json.dumps(profile))
            with open(profile_name, 'wb') as file:
                file.write(encrypted_profile)
            self.update_status("Profile saved successfully.", error=False)
        self.reset_activity_timer()


        self.reset_activity_timer()


    def load_profile(self):
        profile_name = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if profile_name:
            with open(profile_name, 'rb') as file:
                encrypted_profile = file.read()
            profile = json.loads(self.decrypt_data(encrypted_profile))
            self.host_entry.delete(0, tk.END)
            self.host_entry.insert(0, profile.get('host', ''))
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, profile.get('port', '21'))
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, profile.get('username', ''))
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, profile.get('password', ''))
            self.update_status("Profile loaded successfully.", error=False)
        self.reset_activity_timer()


    def delete_profile(self):
        profile_name = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if profile_name and messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this profile?"):
            os.remove(profile_name)
            self.update_status("Profile deleted successfully.", error=False)
        self.reset_activity_timer()


    def load_profiles(self):
        # This method could list existing profiles or handle them; simplified here
        profiles = {}
        return profiles
        self.reset_activity_timer()

    def login(self):
        if self.is_logged_in:
            self.update_status("Already logged in.", error=True)
            return

        host = self.host_entry.get()
        port = self.port_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()  # Password can be optional depending on the server configuration

        # Validate the necessary information
        if not host:
            self.update_status("Host field is required.", error=True)
            return
        if not port:
            self.update_status("Port field is required.", error=True)
            return
        if not username:
            self.update_status("Username field is required.", error=True)
            return

        # If all fields are filled, attempt to connect
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(host, int(port))  # Convert port to integer
            self.ftp.login(username, password)
            # Check for supported features right after login
            self.supported_features = self.check_features()
            print("Supported FTP features:", self.supported_features)
            self.update_status("Connected to FTP server.", error=False)
            self.update_buttons_state(True)
            self.list_files('/')
            self.is_logged_in = True  # Update login status to True
            self.login_button.config(state='disabled')  # Disable login button
        except Exception as e:
            self.update_status(f"Connection failed: {str(e)}", error=True)
            return

        self.reset_activity_timer()



    def update_progress(self, block):
        self.progress['value'] += len(block)
        self.root.update_idletasks()  # Update the GUI to reflect changes
        self.reset_activity_timer()

    def update_status(self, message, error=False):
        """Update the status label with the message and set the color based on error status."""
        self.status_var.set(message)
        if error:
            self.status_label.config(fg='red')  # Error messages in red
        else:
            self.status_label.config(fg='green')  # Success messages in green
        self.reset_activity_timer()
    def connect_to_ftp(self, host, port, username, password):
        try:
            self.ftp = FTP()
            self.ftp.connect(host, int(port))
            self.ftp.login(username, password)
            self.ftp.set_debuglevel(2)  # Set detailed debug output
            self.update_status("Connected to FTP server.", error=False)
            self.list_files()
            self.enable_interface()
        except Exception as e:
            self.update_status(f"Connection failed: {str(e)}", error=True)
            self.list_files()
            self.reset_activity_timer()


    def enable_interface(self):
        # Re-enable elements that were disabled
        self.file_listbox.config(state='normal')

    def check_features(self):
        """Check for supported features by sending the FEAT command and return a list of supported features."""
        try:
            response = self.ftp.sendcmd('FEAT')
            features = response.splitlines()
            # Process the feature list to make it more accessible, typically features start from the second line
            return [feature.strip().split()[0] for feature in features[1:]] if len(features) > 1 else []
        except ftplib.all_errors as e:
            print(f"Error retrieving server features: {str(e)}")
            return []
        self.reset_activity_timer()
    def ftp_has_feature(self, feature):
        """Check if the FTP server has a specific feature by issuing the FEAT command."""
        try:
            response = self.ftp.sendcmd('FEAT')  # Sends the FEAT command to the FTP server
            features = response.splitlines()
            # Check if the desired feature is in the list of features returned by the server
            for feat in features:
                if feature in feat:
                    return True
            return False
        except ftplib.error_perm as e:
            # Handle the case where FEAT command is not supported or failed
            print(f"Debug: FEAT command failed with error {e}")
            return False

    def is_directory(self, path):
        original_dir = self.ftp.pwd()
        try:
            self.ftp.cwd(path)
            return True
        except ftplib.error_perm:
            return False
        finally:
            self.ftp.cwd(original_dir)
            self.reset_activity_timer()
                    
    def safe_change_dir(self, path):
        print(f"Attempting to change directory to {path}")
        current_dir = self.ftp.pwd()
        self.ftp.cwd(path)
        new_dir = self.ftp.pwd()
        print(f"Changed from {current_dir} to {new_dir}")
        if new_dir != path:
            raise Exception(f"Mismatch in directory change: expected {path}, but current is {new_dir}")
    

    def list_files(self, directory=None):
        try:
            if directory is None:
                directory = self.current_directory

            self.ftp.cwd(directory)
            self.tree.delete(*self.tree.get_children())

            # Add the ".." (parent directory) entry if not at the root
            if directory != '/':  # Adjust this check based on your FTP root path handling
                self.tree.insert("", 'end', text="..", values=("Navigate Up",), image=self.folder_icon)

            for entry in self.ftp.mlsd():  # Using MLSD for accurate directory listing
                name, facts = entry
                if name in ['.', '..']:
                    continue

                item_type = facts['type']
                file_type = facts.get('kind', 'unknown').title() + " File"

                if item_type == 'dir':
                    self.tree.insert("", 'end', text=name, values=("Folder", "Directory"), image=self.folder_icon)
                else:
                    file_extension = posixpath.splitext(name)[1][1:].upper() or "Unknown"
                    self.tree.insert("", 'end', text=name, values=(f"{file_extension} File", "File"), image=self.file_icon)

            self.update_status(f"Files listed successfully in '{directory}'.")
        except Exception as e:
            self.update_status(f"Failed to list files in '{directory}': {str(e)}", error=True)
            self.reset_activity_timer()


    def delete_file(self):
        selected_items = self.tree.selection()
        if not selected_items:
            self.update_status("No file selected for deletion.", error=True)
            return

        for item_id in selected_items:
            item = self.tree.item(item_id)
            file_name = item['text']
            full_path = posixpath.join(self.current_directory, file_name)  # Use posixpath for FTP-compatible path

            print(f"Deleting {file_name} with type {item['values'][0]} at path {full_path}")

            if item['values'][0] != "File":  # Ensure the index is correct
                self.update_status(f"Selected item {file_name} is not a file.", error=True)
                continue

            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the file: {file_name}?"):
                try:
                    self.ftp.delete(full_path)
                    self.tree.delete(item_id)
                    self.update_status(f"Deleted file: {file_name}", error=False)
                except Exception as e:
                    self.update_status(f"Failed to delete file: {str(e)}", error=True)
                    print(f"Exception: {str(e)}")
        self.reset_activity_timer()

    def delete_contents(self, path):
        self.ftp.cwd(path)
        items = self.ftp.nlst()
        for item in items:
            if item in ['.', '..']:
                continue  # Skip the current and parent directory entries
            full_path = posixpath.join(path, item)
            if self.is_directory(full_path):
                self.delete_contents(full_path)  # Recursively delete directory contents
                self.ftp.rmd(full_path)  # Remove the now-empty directory
            else:
                self.ftp.delete(full_path)  # Delete the file

    def delete_folder(self):
        selected_items = self.tree.selection()
        if not selected_items:
            self.update_status("No folder selected for deletion.", error=True)
            return

        for item_id in selected_items:
            item = self.tree.item(item_id)
            folder_name = item['text']
            full_path = posixpath.join(self.current_directory, folder_name)  # Ensure full_path uses forward slashes

            # Debug statements to check item values and path
            print(f"Debug - Item ID: {item_id}")
            print(f"Debug - Item text: {folder_name}")
            print(f"Debug - Full path: {full_path}")

            if item['values'][1] != "Directory":
                self.update_status(f"Selected item {folder_name} is not a directory.", error=True)
                continue

            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the folder: {folder_name}?"):
                try:
                    # Recursively delete directory contents before deleting the directory itself
                    self.delete_contents(full_path)
                    
                    # Remove the now-empty directory
                    self.ftp.rmd(full_path)
                    
                    # Remove the item from the tree view
                    self.tree.delete(item_id)
                    self.update_status(f"Deleted folder: {folder_name}", error=False)
                except Exception as e:
                    self.update_status(f"Failed to delete folder: {str(e)}", error=True)
            self.reset_activity_timer()


    def treeview_sort_column(self, tv, col, reverse):
        try:
            if col == "#0":
                l = [(tv.item(k, 'text'), k) for k in tv.get_children('')]  # For the primary column
            else:
                l = [(tv.set(k, col), k) for k in tv.get_children('')]  # For additional columns like "Filetype"

            parent_entry = [item for item in l if tv.item(item[1], 'text') == ".."]
            other_entries = [item for item in l if tv.item(item[1], 'text') != ".."]

            other_entries.sort(key=lambda t: t[0].lower(), reverse=reverse)  # Sort by column value

            # Combine lists with ".." at top
            sorted_items = parent_entry + other_entries

            for index, (_, k) in enumerate(sorted_items):
                tv.move(k, '', index)

            # Set the command for the next sort
            tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

        except Exception as e:
            print(f"Error sorting: {str(e)}")  # Print error if something goes wrong
        self.reset_activity_timer()
    def on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)  # Identify the item row clicked
        if not item_id:
            return

        item = self.tree.item(item_id)
        item_type = item['values'][0]  # This should be either "File" or "Folder"

        if item['text'] == "..":
            # Move up one directory
            self.enter_directory("..")
        elif item_type == "Folder":
            # Enter the selected directory
            self.enter_directory(item['text'])
        elif item_type == "File":
            # Handle file-specific actions, such as downloading
            self.download_files()
        self.reset_activity_timer()




    def enter_directory(self, directory_name):
        try:
            # Handle navigation up or into a directory
            if directory_name == "..":
                new_path = posixpath.dirname(self.current_directory.rstrip('/'))
            else:
                new_path = posixpath.join(self.current_directory, directory_name)

            # Change to the new directory
            self.ftp.cwd(new_path)
            actual_directory = self.ftp.pwd()  # Confirm the directory change

            # Verify the directory change was successful
            if actual_directory.rstrip('/') == new_path.rstrip('/'):
                self.current_directory = actual_directory
                self.list_files()  # Refresh the listing with the new directory's contents
                self.update_status(f"Entered directory: {actual_directory}", error=False)
            else:
                raise Exception(f"Attempted to change to {new_path}, but actual directory is {actual_directory}")

        except Exception as e:
            self.update_status(f"Failed to enter directory {directory_name}: {str(e)}", error=True)
        self.reset_activity_timer()

    def go_up(self):
        if self.current_directory != "/":  # Prevent going up from the root directory
            new_path = posixpath.dirname(self.current_directory.rstrip('/'))
            try:
                self.ftp.cwd(new_path)
                self.current_directory = new_path
                self.list_files()
                self.update_status("Moved up to the parent directory.", error=False)
            except Exception as e:
                self.update_status(f"Failed to move up: {str(e)}", error=True)
        self.reset_activity_timer()

    def select_directory(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Destination Directory")
        tree = ttk.Treeview(dialog, columns=('Type',), show='tree')
        tree.pack(expand=True, fill='both')
        self.reset_activity_timer()

        def populate_tree(directory):
            tree.delete(*tree.get_children())
            self.ftp.cwd(directory)
            items = self.ftp.nlst()
            for item in items:
                item_type = "Directory" if self.is_directory(item) else "File"
                tree.insert('', 'end', iid=item, text=item, values=(item_type,))
            self.reset_activity_timer()
        populate_tree(self.current_directory)

        def on_select(event):
            selected_item = tree.selection()
            if selected_item:
                directory = tree.item(selected_item[0])['text']
                self.new_location = posixpath.join(self.current_directory, directory)
                self.enter_directory(directory)  # Pass the directory name to enter_directory
                dialog.destroy()
            self.reset_activity_timer()
        tree.bind('<Double-1>', on_select)
        return dialog.wait_window()  # This waits until the dialog is closed



    def move_files(self):
        selected_items = self.tree.selection()
        if not selected_items:
            self.update_status("No file selected to move.", error=True)
            return

        self.new_location = None
        self.select_directory()  # User selects the new location through GUI
        if not self.new_location:
            self.update_status("File move cancelled.", error=False)
            return

        for item_id in selected_items:
            file_name = self.tree.item(item_id, 'text')
            item_type = self.tree.item(item_id, 'values')[0]

            if "File" not in item_type:
                self.update_status(f"Item '{file_name}' is not a file and was not moved.", error=True)
                continue

            new_path = posixpath.join(self.new_location, file_name.split('/')[-1])

            try:
                self.ftp.rename(file_name, new_path)
                self.update_status(f"Moved file '{file_name}' to '{new_path}'.", error=False)
            except Exception as e:
                self.update_status(f"Failed to move file '{file_name}': {str(e)}", error=True)

        self.list_files()  # Refresh after moving
        self.reset_activity_timer()


    def move_folders(self):
        selected_items = self.tree.selection()
        if not selected_items:
            self.update_status("No folder selected to move.", error=True)
            return

        # Ask for the new location once for all selected folders
        sample_folder_name = self.tree.item(selected_items[0], 'text')
        new_location = simpledialog.askstring("Move Folders", f"Enter new location for the selected folders:")
        if not new_location:
            self.update_status("Folder move cancelled.", error=False)
            return

        if not new_location.endswith('/'):
            new_location += '/'

        # Process each selected folder
        for item_id in selected_items:
            folder_name = self.tree.item(item_id, 'text')
            item_type = self.tree.item(item_id, 'values')[0]  # Correct index to 0

            if item_type != "Directory":
                self.update_status(f"Item '{folder_name}' is not a folder and was not moved.", error=True)
                continue

            new_path = new_location + folder_name.split('/')[-1]

            try:
                self.ftp.rename(folder_name, new_path)
                self.update_status(f"Moved folder '{folder_name}' to '{new_path}'.", error=False)
            except Exception as e:
                self.update_status(f"Failed to move folder '{folder_name}': {str(e)}", error=True)

        # Refresh the list to show the folders in their new locations
        self.list_files()
        self.reset_activity_timer()

    def start_rename(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.update_status("No file or folder selected to rename.", error=True)
            return

        item_id = selected_item[0]
        item_text = self.tree.item(item_id, 'text')
        item_type = self.tree.item(item_id, 'values')[0]
        self.tree.focus(item_id)
        self.tree.selection_set(item_id)

        # Create an Entry widget
        self.entry = tk.Entry(self.tree)
        self.entry.insert(0, item_text)
        self.entry.select_range(0, 'end')

        # Get the bounding box of the item and place the Entry widget over it
        bbox = self.tree.bbox(item_id, '#0')
        if bbox:
            x, y, width, height = bbox
            icon_width = 20  # Adjust icon width if necessary
            if item_type == "Directory":
                icon = self.folder_icon
            else:
                icon = self.file_icon
            self.icon_label = tk.Label(self.tree, image=icon)
            self.icon_label.place(x=x, y=y, width=icon_width, height=height)
            self.entry.place(x=x + icon_width, y=y, width=width - icon_width, height=height)

        self.entry.bind("<Return>", self.rename_item_confirm)
        self.entry.bind("<FocusOut>", self.rename_item_confirm)
        self.entry.focus()

    def rename_item_confirm(self, event):
        new_name = self.entry.get()
        self.entry.destroy()
        self.icon_label.destroy()

        selected_item = self.tree.selection()
        if not selected_item:
            self.update_status("No file or folder selected to rename.", error=True)
            return

        item_id = selected_item[0]
        current_name = self.tree.item(item_id, 'text')
        item_type = self.tree.item(item_id, 'values')[0]

        if new_name and new_name != current_name:
            try:
                path_parts = current_name.rsplit('/', 1)
                if len(path_parts) > 1:
                    new_name = f"{path_parts[0]}/{new_name}"
                else:
                    new_name = new_name

                self.ftp.rename(current_name, new_name)
                self.update_status(f"Renamed {item_type.lower()} to '{new_name}'.", error=False)
                self.list_files()
            except Exception as e:
                self.update_status(f"Failed to rename {item_type.lower()}: {str(e)}", error=True)
        elif new_name:
            self.update_status("Rename operation cancelled or no change in name.", error=False)
        self.reset_activity_timer()


    def rename_item(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.update_status("No file or folder selected to rename.", error=True)
            return

        # Get the current name and type from the Treeview
        item_id = selected_item[0]
        current_name = self.tree.item(item_id, 'text')
        item_type = self.tree.item(item_id, 'values')[0]  # Correct index to [0] to get the item type

        # Prompt user for the new name
        new_name = simpledialog.askstring("Rename", f"Enter new name for the {item_type.lower()}: '{current_name}'")
        if new_name and new_name != current_name:
            try:
                # Build the path for the new name
                path_parts = current_name.rsplit('/', 1)
                if len(path_parts) > 1:
                    new_name = f"{path_parts[0]}/{new_name}"  # Keep the existing path but change the name
                else:
                    new_name = new_name  # No path to maintain, just a simple rename

                self.ftp.rename(current_name, new_name)
                self.update_status(f"Renamed {item_type.lower()} to '{new_name}'.", error=False)
                self.list_files()  # Refresh the list to show the new name
            except Exception as e:
                self.update_status(f"Failed to rename {item_type.lower()}: {str(e)}", error=True)
        elif new_name:
            self.update_status("Rename operation cancelled or no change in name.", error=False)
        self.reset_activity_timer() 
    def reset_activity_timer(self):
        with self.activity_lock:
            self.last_activity_time = time.time()
            if self.timeout_timer is not None:
                self.timeout_timer.cancel()
            self.start_timeout_timer()

    def start_timeout_timer(self):
        self.timeout_timer = threading.Timer(self.timeout_seconds, self.check_timeout)
        self.timeout_timer.daemon = True  # Set the timer thread as a daemon thread
        self.timeout_timer.start()

    def check_timeout(self):
        with self.activity_lock:
            time_since_last_activity = time.time() - self.last_activity_time
            if time_since_last_activity >= self.timeout_seconds:
                self.perform_logout_due_to_timeout()

    def perform_logout_due_to_timeout(self):
        print("Attempting to logout due to timeout...")
        self.logout()
        print("Logout completed or failed, updating GUI...")
        messagebox.showinfo("Timeout", "You have been logged out due to inactivity.")



    def logout(self):
        try:
            if self.ftp and self.ftp.sock is not None:
                self.ftp.quit()
            self.update_status("Logout successful.", error=False)
        except Exception as e:
            self.update_status(f"Failed to log out gracefully: {str(e)}", error=True)
        finally:
            self.ftp = None
            self.is_logged_in = False
            self.tree.delete(*self.tree.get_children())
            self.disable_interface()
            self.update_status("FTP connection reset.", error=False)
            self.login_button.config(state='normal')
            self.update_buttons_state(False)
            self.reset_tree()

    def reset_tree(self):
        if hasattr(self, 'tree'):
            self.tree.delete(*self.tree.get_children())
            self.tree.unbind('<Double-1>') #Unbind any events



    def stop_timeout_timer(self):
        with self.activity_lock:
            if self.timeout_timer is not None:
                self.timeout_timer.cancel()
                self.timeout_timer = None

    def on_closing(self):
        self.logout()
        self.root.destroy()  # This ensures the entire application is terminated



    def disable_interface(self):
        self.tree.unbind("<Button-1>")
        self.tree.unbind("<B1-Motion>")
        self.tree.unbind("<ButtonRelease-1>")
        self.tree.unbind("<Double-1>")
        self.tree.unbind("<Button-3>")

    def enable_interface(self):
        self.tree.bind("<Button-1>", self.start_drag)
        self.tree.bind("<B1-Motion>", self.on_drag)
        self.tree.bind("<ButtonRelease-1>", self.stop_drag)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)


    def download_files(self):
        selected_items = self.tree.selection()
        if not selected_items:
            self.update_status("No items selected for download.", error=True)
            return

        local_dir = self.check_download_directory()
        if not local_dir:
            self.update_status("Download cancelled.", error=False)
            return

        for item_id in selected_items:
            item = self.tree.item(item_id)
            item_name = item['text']
            item_type = item['values'][0]  # Ensure this index matches where you store the type info

            # Calculate the full remote path to handle nested structures correctly
            remote_path = posixpath.join(self.current_directory, item_name)
            
            if item_type == "Folder":
                folder_path = os.path.join(local_dir, item_name)
                try:
                    self.update_status(f"Starting download of folder: {remote_path}...", error=False)
                    self.download_folder(remote_path, folder_path)  # Pass the full remote path
                except Exception as e:
                    self.update_status(f"Failed to download folder '{item_name}': {str(e)}", error=True)
            elif item_type == "File":
                file_path = os.path.join(local_dir, item_name)
                try:
                    self.update_status(f"Starting download of file: {remote_path}...", error=False)
                    self.perform_file_download(remote_path, file_path)  # Pass the full remote path
                except Exception as e:
                    self.update_status(f"Failed to download file '{item_name}': {str(e)}", error=True)

        self.update_status("Completed downloads.", error=False)

    # Method to check or set the download directory
    def check_download_directory(self):
        # If a download directory hasn't been set or is empty
        if not getattr(self, 'download_directory', None):
            # Prompt the user to select a directory
            directory = filedialog.askdirectory(title="Select Download Directory")
            if directory:  # Make sure the user didn't cancel the dialog
                self.download_directory = directory
            else:
                return None  # Return None if the user cancelled the dialog
        return self.download_directory


    def perform_file_download(self, file_name, local_path):
        try:
            print(f"Attempting to download file: {file_name}")
            with open(local_path, 'wb') as file:
                self.ftp.retrbinary('RETR ' + file_name, file.write)
            print(f"Successfully downloaded {file_name} to {local_path}")
        except Exception as e:
            print(f"Error downloading file {file_name}: {str(e)}")
            raise


    def set_download_directory(self):
        directory = filedialog.askdirectory(title="Select default download directory")
        if directory:
            self.download_directory = directory  # Store the directory in an instance variable
            self.download_option.set("default")
            self.update_status(f"Download directory set to: {directory}", error=False)
        else:
            self.update_status("Download directory setting cancelled.", error=False)
        self.reset_activity_timer()

    def check_download_directory(self):
        if self.download_option.get() == "prompt":
            # Always prompt for the directory
            directory = filedialog.askdirectory(title="Select download directory")
            if not directory:
                self.update_status("Download cancelled.", error=False)
                return None
            return directory
        elif self.download_option.get() == "default" and self.download_directory:
            # Use the set default directory
            return self.download_directory
        
        else:
            # No directory is set, ask for one
            directory = filedialog.askdirectory(title="Select download directory")
            if directory:
                self.download_directory = directory
                self.update_status(f"Download directory set to: {directory}", error=False)
                return directory
            else:
                self.update_status("Download cancelled.", error=False)
                return None


    def download_folder(self, remote_dir, local_dir=None):
        if local_dir is None:
            local_dir = self.check_download_directory()
            if not local_dir:
                self.update_status("Download cancelled.", error=False)
                return

        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        current_dir = self.ftp.pwd()
        try:
            self.ftp.cwd(remote_dir)
            items = self.ftp.nlst()
            print(f"Listing items in {remote_dir}: {items}")

            for item in items:
                if item in ['.', '..']:
                    continue  # Skip current and parent directory entries

                item_path = item  # We use just the name, as we are already in the correct directory
                local_item_path = os.path.join(local_dir, item)
                if self.is_directory(item):
                    self.download_folder(item, local_item_path)
                else:
                    self.perform_file_download(item, local_item_path)

            self.update_status(f"Completed downloading directory: {remote_dir}")
        except Exception as e:
            self.update_status(f"Failed to download folder: {str(e)}", error=True)
            print(f"Exception details: {str(e)}")
        finally:
            self.ftp.cwd(current_dir)  # Return to the original directory



    def download_selected_folder(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.update_status("No folder selected for download.", error=True)
            return

        item_id = selected_item[0]
        item = self.tree.item(item_id)
        folder_name = item['text']
        item_type = item['values'][0]

        if item_type != "Folder":
            self.update_status("Selected item is not a directory.", error=True)
            return

        # Prompt for directory or use the default
        local_dir = self.check_download_directory()
        if not local_dir:
            self.update_status("Download cancelled.", error=False)
            return

        # Append the folder name to the selected or default directory
        full_local_dir = os.path.join(local_dir, folder_name)

        if not os.path.exists(full_local_dir):
            os.makedirs(full_local_dir, exist_ok=True)

        try:
            self.update_status("Starting folder download...", error=False)
            self.download_folder(folder_name, full_local_dir)  # Pass the full path including the folder name
            self.refresh_view()
            self.update_status(f"Folder downloaded successfully to {full_local_dir}", error=False)
            
        except Exception as e:
            self.refresh_view()
            self.update_status(f"Failed to download folder: {str(e)}", error=True)
        self.reset_activity_timer()

    def upload_files(self):
        file_paths = filedialog.askopenfilenames(title="Select Files to Upload", filetypes=[("All files", "*.*")])
        if file_paths:
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                try:
                    with open(file_path, 'rb') as file:
                        self.ftp.storbinary(f'STOR {filename}', file)
                    self.update_status(f"Uploaded {filename}", error=False)
                except Exception as e:
                    self.update_status(f"Failed to upload {filename}: {str(e)}", error=True)
            self.list_files()  # Refresh the file list after uploads
            self.refresh_view()

        # Optionally, re-select the directory to see the new files
        current_directory = self.ftp.pwd()
        self.enter_directory(current_directory)  # A method that refreshes the directory view
        self.reset_activity_timer()

    def on_close(self):
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            self.logout()
            self.root.destroy()  # This ensures the entire application is terminated




def main():
    root = tk.Tk()
    root.update_idletasks()
    app = FTPClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Handle the window close event
    app.setup_treeview
    root.mainloop()
if __name__ == "__main__":
    main()
