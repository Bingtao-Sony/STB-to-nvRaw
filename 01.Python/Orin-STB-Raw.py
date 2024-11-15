import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import os

def get_dimensions_from_header(head):
    """
    Extract width and height from the header of the STB file.
    The values are in little-endian format.
    """
    width = head[8] + (head[9] << 8)  # head[8] + (head[9] * 256)
    height = head[12] + (head[13] << 8)  # head[12] + (head[13] * 256)
    
    return width, height  # Return the width and height


def Open_STB(stb_file_Path):
    """
    Open and read the STB file, extract the header and content, and reshape the data into a 2D frame.
    """
    with open(stb_file_Path, 'rb') as f:
        data = f.read()

    content = data[16:]  # Data excluding the first 16 bytes (header)
    head = data[0:16]  # First 16 bytes (header)

    print(f"File read, content length: {len(content)}")
    
    width, height = get_dimensions_from_header(head)  # Extract width and height

    # Reshape the raw content into a 2D numpy array
    Frame_SONY = np.frombuffer(content, dtype=np.uint16).reshape(height, width)

    print(f"Reshaped to {Frame_SONY.shape[1]} x {Frame_SONY.shape[0]} ")
    print(f"Data type = {Frame_SONY.dtype}")

    return Frame_SONY, width, height


def Save_Frame(Frame, Stb_file_Path, Method, width, height):
    """
    Save the processed frame to a raw file, with a name indicating the method used.
    """
    Process = ["STB_to_Raw", "STB_to_NV(0 Padding)", "STB_to_NV(Standard)"]
    Raw_file_Path = Stb_file_Path[:-4] + "_" + str(width) + "x" + str(height) + "_" + Process[Method] + ".raw"
    Frame.tofile(Raw_file_Path)
    
    # Print a separator and a success message in ASCII art
    print("---------------------------------------------------------")
    print("███████╗██╗   ██╗ ██████╗ ██████╗███████╗███████╗███████╗")
    print("██╔════╝██║   ██║██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝")
    print("███████╗██║   ██║██║     ██║     █████╗  ███████╗███████╗")
    print("╚════██║██║   ██║██║     ██║     ██╔══╝  ╚════██║╚════██║")
    print("███████║╚██████╔╝╚██████╗╚██████╗███████╗███████║███████║")
    print("---------------------------------------------------------")


def STB_to_RAW(Frame_SONY, stb_file_Path, width, height):
    """
    Process the STB file to extract raw frame data and save it as a raw file.
    Excludes the first 16 bytes (header).
    """
    print(f"Excluding first 16 bytes from {stb_file_Path}")
    Save_Frame(Frame_SONY, stb_file_Path, 0, width, height)


def STB_to_NV_RAW_0(Frame_SONY, stb_file_Path, width, height):
    """
    Convert the STB frame to NV format (0 padding), then save it.
    Shifts each pixel's value by 4 bits.
    """
    Frame_NV = Frame_SONY << 4
    print("Frame_NV shape:", Frame_NV.shape)
    print(f"Swapped high and low nibbles from {stb_file_Path}")
    Save_Frame(Frame_NV, stb_file_Path, 1, width, height)


def STB_to_NV_RAW(Frame_SONY, stb_file_Path, width, height):
    """
    Convert the STB frame to NV format (standard), then save it.
    This includes separating and shifting specific parts of the image.
    """
    FEBD_SONY = Frame_SONY[0:1, :]
    PIC_SONY = Frame_SONY[1:height-20, :]
    REBD_SONY = Frame_SONY[-20:, :]

    # Apply 4-bit shift to different parts of the frame
    FEBD_NV = FEBD_SONY << 4
    PIC_NV = (PIC_SONY << 4 & 0xFFFF) + ((PIC_SONY & 0x0F00) >> 8)
    REBD_NV = REBD_SONY << 4

    print("FEBD_NV shape:", FEBD_NV.shape)
    print("PIC_NV shape:", PIC_NV.shape)
    print("REBD_NV shape:", REBD_NV.shape)

    # Stack the processed frame parts
    Frame_NV = np.vstack((FEBD_NV, PIC_NV, REBD_NV))

    print(f"Swapped high and low nibbles from {stb_file_Path}")
    Save_Frame(Frame_NV, stb_file_Path, 2, width, height)


class STBProcessorApp:
    def __init__(self, root):
        """
        Initialize the main application window with UI components.
        """
        self.root = root
        self.root.title("STB File Processor  --- Bingtao.Liu@sony.com")

        # Initialize paths and selected scripts
        self.folder_path = ""
        self.file_path = ""
        self.selected_scripts = []

        # Radio button variable for file/folder selection
        self.selection_var = tk.StringVar(value="file")  # Default selection is 'file'

        # Folder selection UI components
        self.folder_radio = tk.Radiobutton(root, text="Select Folder", variable=self.selection_var, value="folder", command=self.update_selection)
        self.folder_radio.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.folder_button = tk.Button(root, text="Select Folder", command=self.select_folder)
        self.folder_button.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Entry to show folder path (readonly)
        self.folder_path_entry = tk.Entry(root, width=70)
        self.folder_path_entry.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.folder_path_entry.config(state="readonly")

        # File selection UI components
        self.file_radio = tk.Radiobutton(root, text="Select File", variable=self.selection_var, value="file", command=self.update_selection)
        self.file_radio.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.file_button = tk.Button(root, text="Select File", command=self.select_file)
        self.file_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Entry to show file path (readonly)
        self.file_path_entry = tk.Entry(root, width=70)
        self.file_path_entry.grid(row=2, column=2, padx=10, pady=10, sticky="w")
        self.file_path_entry.config(state="readonly")

        # Script selection UI components
        self.script_label = tk.Label(root, text="Select Scripts to Run")
        self.script_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # Define script options with checkboxes
        self.script_vars = {
            "STB_to_Raw": tk.BooleanVar(),
            "STB_to_NV(0 Padding)": tk.BooleanVar(),
            "STB_to_NV(Standard)": tk.BooleanVar(),
        }

        # Create and arrange checkbuttons for scripts
        self.script_checkbuttons = []
        row = 5
        for col, (script, var) in enumerate(self.script_vars.items()):
            cb = tk.Checkbutton(root, text=script, variable=var)
            cb.grid(row=row, column=col, padx=10, pady=10, sticky="w")
            self.script_checkbuttons.append(cb)

        # Configure column weights to make columns equal width
        for col in range(3):
            root.grid_columnconfigure(col, weight=1, uniform="equal")

        # Run button to start processing
        self.run_button = tk.Button(root, text="Run", command=self.run_scripts)
        self.run_button.grid(row=row + 1, column=0, columnspan=3, padx=10, pady=10)

        # Initialize file/folder selection
        self.update_selection()

        # Limit window size
        self.root.geometry('600x250')

    def update_selection(self):
        """
        Update UI components based on the selected file/folder option.
        Enable or disable buttons accordingly.
        """
        if self.selection_var.get() == "folder":
            self.folder_button.config(state="normal")
            self.file_button.config(state="disabled")
        elif self.selection_var.get() == "file":
            self.folder_button.config(state="disabled")
            self.file_button.config(state="normal")

    def select_folder(self):
        """
        Open folder dialog to select a folder, and display the folder path in the Entry widget.
        """
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.folder_path = folder
            self.folder_path_entry.config(state="normal")
            self.folder_path_entry.delete(0, tk.END)
            self.folder_path_entry.insert(0, folder)
            self.folder_path_entry.config(state="readonly")
        else:
            messagebox.showwarning("Warning", "No folder selected")

    def select_file(self):
        """
        Open file dialog to select an STB file, and display the file path in the Entry widget.
        """
        file = filedialog.askopenfilename(title="Select STB File", filetypes=[("STB Files", "*.stb")])
        if file:
            self.file_path = file
            self.file_path_entry.config(state="normal")
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file)
            self.file_path_entry.config(state="readonly")
        else:
            messagebox.showwarning("Warning", "No file selected")

    def run_scripts(self):
        """
        Run the selected scripts on the chosen file or folder.
        Iterate through the files in the folder (if selected) or process the single file.
        """
        if self.selection_var.get() == "folder" and not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder")
            return

        if self.selection_var.get() == "file" and not self.file_path:
            messagebox.showwarning("Warning", "Please select a file")
            return

        # Get selected scripts
        selected_scripts = [script for script, var in self.script_vars.items() if var.get()]
        if not selected_scripts:
            messagebox.showwarning("Warning", "Please select at least one script to run")
            return

        # Process files in the selected folder
        if self.selection_var.get() == "folder":
            for root_dir, dirs, files in os.walk(self.folder_path):
                for file_name in files:
                    if file_name.lower().endswith('.stb'):
                        file_path = os.path.join(root_dir, file_name)
                        Frame_SONY, width, height = Open_STB(file_path)
                        for script in selected_scripts:
                            if script == "STB_to_Raw":
                                STB_to_RAW(Frame_SONY, file_path, width, height)
                            elif script == "STB_to_NV(0 Padding)":
                                STB_to_NV_RAW_0(Frame_SONY, file_path, width, height)
                            elif script == "STB_to_NV(Standard)":
                                STB_to_NV_RAW(Frame_SONY, file_path, width, height)

        messagebox.showinfo("Success", "Scripts executed successfully")


if __name__ == "__main__":
    root = tk.Tk()
    app = STBProcessorApp(root)
    root.mainloop()
