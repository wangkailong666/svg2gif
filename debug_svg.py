import tkinter as tk
from tkinter import filedialog

def select_and_parse_svg():
    print("Opening file dialog...")
    filepath = filedialog.askopenfilename(
        title="Select SVG File for Debugging",
        filetypes=(("SVG files", "*.svg"), ("All files", "*.*"))
    )
    if not filepath:
        print("No file selected. Exiting.")
        return

    print(f"File selected: {filepath}")

    try:
        from lxml import etree
        print("\n--- Testing lxml parsing ---")
        tree = etree.parse(filepath)
        root = tree.getroot()
        width = root.get('width')
        height = root.get('height')
        viewbox = root.get('viewBox')
        print(f"Successfully parsed with lxml.")
        print(f"Found attributes: width='{width}', height='{height}', viewBox='{viewbox}'")
    except Exception as e:
        print(f"!!! lxml parsing failed: {e}")
        return

    try:
        from PIL import Image
        print("\n--- Testing Pillow (PIL) ---")
        # This is just a basic check to see if the library is installed and usable
        print("Pillow library is available.")
    except Exception as e:
        print(f"!!! Pillow (PIL) import failed: {e}")
        return

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        print("\n--- Testing Selenium and WebDriver ---")
        print("Initializing headless Chrome browser...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("WebDriver initialized successfully.")
        driver.quit()
        print("WebDriver quit successfully.")
    except Exception as e:
        print(f"!!! Selenium/WebDriver initialization failed: {e}")
        return

    print("\n--- Debugging script finished ---")
    print("All tested libraries appear to be installed and working correctly.")


def main():
    print("--- SVG Converter Debugging Script ---")
    try:
        print("Initializing Tkinter...")
        root = tk.Tk()
        root.title("Debug Tool")
        label = tk.Label(root, text="Click the button to start the debug process.")
        label.pack(pady=10)
        button = tk.Button(root, text="Select SVG and Run Checks", command=lambda: select_and_parse_svg())
        button.pack(pady=10)
        print("Tkinter initialized successfully.")
        root.mainloop()
    except Exception as e:
        print(f"!!! Tkinter initialization failed: {e}")
        print("\nThis suggests a problem with your Python environment's GUI capabilities.")

if __name__ == "__main__":
    main()
