import shutil
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox


class FileOrganizer:
    """
    - task 1: scan a folder and list its files
    - task 2: classify files into categories based on their extension
    - task 3: create destination folders and move files with shutil.move()
    - task 4: log every moved file (source, destination, time)
    - task 6: keep a history of moves so the last organization can be undone
    - task 8: handle errors (name conflicts, permission issues)
    """

    LOG_FILENAME = "file_organizer.log"

    # Rules dictionary: each category maps to a list of extensions.
    CATEGORIES = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".odt"],
        "Spreadsheets": [".xls", ".xlsx", ".csv"],
        "Audio": [".mp3", ".wav", ".flac"],
        "Video": [".mp4", ".avi", ".mkv", ".mov"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    }

    def __init__(self, folder_path):
        # Path automatically handles the separators (/ or \) depending on the OS.
        self.folder_path = Path(folder_path)
        self.log_file = self.folder_path / self.LOG_FILENAME
        self.history = []

# task 4
    def setup_logging(self):
        """Configure logging so each move is written to the log file.

        The "%(asctime)s" placeholder automatically inserts the date and
        time of each entry, which covers the "time" requirement.
        """
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

# task 2
    def scan_files(self):
        """Return the list of files in the folder (without the subfolders)."""
        
        # First, check that the folder actually exists.
        if not self.folder_path.exists():
            raise FileNotFoundError(f"The folder does not exist: {self.folder_path}")

        # Check that it is really a folder and not a file.
        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"This is not a folder: {self.folder_path}")

        # iterdir() goes through everything the folder contains.
        files = [		
    	element		
        for element in self.folder_path.iterdir()		
    	if element.is_file() and element.name != self.LOG_FILENAME		
        ]
        return files


    def get_category(self, file_path):
        """Return the category of a file based on its extension."""
        
        # .suffix gives the extension; .lower() avoids the .PDF / .pdf trap
        extension = file_path.suffix.lower()

        # Look for which category this extension belongs to.
        for category, extensions in self.CATEGORIES.items():
            if extension in extensions:
                return category
        return "Other"


    def classify_files(self):
        result = {}

        for file_path in self.scan_files():
            category = self.get_category(file_path)

            if category not in result:
                result[category] = []
            result[category].append(file_path)
        return result

    def organize(self):
        classification = self.classify_files()
        self.setup_logging()

        for category, files in classification.items():
            destination_folder = self.folder_path / category
            destination_folder.mkdir(parents=True, exist_ok=True)
            for file_path in files:
                destination = destination_folder / file_path.name
                destination = self.get_unique_destination(destination)
                try:
                    shutil.move(str(file_path), str(destination))
                except PermissionError as error:
                    logging.error(f"PERMISSION DENIED | {file_path} | {error}")
                    print(f"Skipped (permission denied): {file_path.name}")
                    continue
                except OSError as error:
                    logging.error(f"FAILED | {file_path} | {error}")
                    print(f"Skipped (error): {file_path.name}")
                    continue

                self.history.append({"source": file_path, "destination": destination})
                logging.info(f"MOVED | source={file_path} | destination={destination}")

                print(f"Moved: {file_path.name} -> {category}/")


    def get_unique_destination(self, destination):
        """Return a destination path that does not overwrite an existing file.

        If 'destination' is free, return it as is. Otherwise append a number:
        photo.jpg -> photo_1.jpg -> photo_2.jpg ... until a free name is found.
        """
        # If nothing is there yet, the original destination is fine.
        if not destination.exists():
            return destination

        stem = destination.stem        # file name without extension, e.g. "photo"
        suffix = destination.suffix    # extension, e.g. ".jpg"
        folder = destination.parent    # the destination folder

        counter = 1
        while True:
            candidate = folder / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def undo(self):
        if not self.history:
            print("Nothing to undo.")
            return

        # reversed() walks the list from the last move to the first.
        for move in reversed(self.history):
            source = move["source"]
            destination = move["destination"]

            # Move the file back: from destination to its original source.
            shutil.move(str(destination), str(source))

            logging.info(f"UNDO | moved back {destination} -> {source}")
            print(f"Restored: {source.name}")

        self.history.clear()
        print("Undo complete.")



class Menu:
    """
    - task 5: menu to let the user choose which folder to organize
    - task 6: undo option that restores the last organized folder

    """
    def __init__(self):
        self.last_organizer = None

    def show_options(self):
        """Display the list of available options."""
        print("\n===== Smart File Organizer =====")
        print("1. Organize a folder")
        print("2. Undo last organization")
        print("3. Quit")


    def organize_folder(self):
        """Ask the user for a folder and organize it."""
        # .strip() removes spaces and the newline around the answer.
        folder = input("Enter the path of the folder to organize: ").strip()
        organizer = FileOrganizer(folder)

        # Minimal safety net so a wrong path does not crash the menu.
        try:
            print()
            organizer.organize()
            print("\nDone.")
            self.last_organizer = organizer 
        except (FileNotFoundError, NotADirectoryError) as error:
            print("Error:", error)


    def undo_last(self):
        """Undo the last organization, if there is one."""
        if self.last_organizer is None:
            print("Nothing to undo yet.")
            return
        self.last_organizer.undo()


    def run(self):
        """Main loop: show the menu and react to the user's choice."""
        while True:
            self.show_options()
            choice = input("Your choice: ").strip()

            if choice == "1":
                self.organize_folder()
            elif choice == "2":
                self.undo_last()
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid choice, please try again.")

class OrganizerGUI:
    """Graphical interface (tkinter) for the file organizer.

    - task 7: GUI with a folder selection dialog and Start/Stop buttons.

    Like Menu, this class only handles user interaction. The real work
    is still done by FileOrganizer.
    """

    def __init__(self):
        # The folder chosen by the user (None until they pick one).
        self.selected_folder = None

        # The main window of the application.
        self.window = tk.Tk()
        self.window.title("Smart File Organizer")
        self.window.geometry("440x240")

        # A label that shows which folder is currently selected.
        self.folder_label = tk.Label(
            self.window, text="No folder selected", wraplength=400
        )
        self.folder_label.pack(pady=15)

        # "Select folder" button -> opens the folder dialog.
        # command=... links the button to the method to call on click.
        tk.Button(
            self.window, text="Select folder", width=20, command=self.select_folder
        ).pack(pady=5)

        # "Start" button -> organizes the selected folder.
        tk.Button(
            self.window, text="Start", width=20, command=self.start
        ).pack(pady=5)

        # "Stop" button -> closes the application.
        tk.Button(
            self.window, text="Stop", width=20, command=self.stop
        ).pack(pady=5)

    def select_folder(self):
        """Open a dialog so the user can pick the folder to organize."""
        # askdirectory() returns the chosen path, or "" if the user cancels.
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=f"Selected:\n{folder}")

    def start(self):
        """Organize the selected folder and report the result in a popup."""
        # If no folder was picked yet, warn the user and stop here.
        if not self.selected_folder:
            messagebox.showwarning("No folder", "Please select a folder first.")
            return

        organizer = FileOrganizer(self.selected_folder)
        try:
            organizer.organize()
            # history holds one entry per moved file (see task 6).
            count = len(organizer.history)
            messagebox.showinfo("Done", f"Organized {count} file(s).")
        except (FileNotFoundError, NotADirectoryError) as error:
            messagebox.showerror("Error", str(error))

    def stop(self):
        """Close the window and end the program."""
        self.window.destroy()

    def run(self):
        """Start the tkinter event loop (keeps the window open)."""
        self.window.mainloop()



# This block only runs if this file is executed directly.
if __name__ == "__main__":
    gui = OrganizerGUI()
    gui.run()