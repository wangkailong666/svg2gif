import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from lxml import etree
import subprocess
import os
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class SvgToGifConverter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SVG to GIF Converter")
        self.geometry("600x550")
        self.init_ui()

    def init_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- File Selection ---
        file_frame = ttk.LabelFrame(main_frame, text="SVG File")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.filepath_label = ttk.Label(file_frame, text="No file selected.")
        self.filepath_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.select_button = ttk.Button(file_frame, text="Select SVG", command=self.select_svg_file)
        self.select_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E)

        self.svg_filepath = None

        # --- Preview ---
        preview_frame = ttk.LabelFrame(main_frame, text="Preview")
        preview_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.preview_canvas = tk.Canvas(preview_frame, bg="white", width=400, height=300)
        self.preview_canvas.grid(row=0, column=0, padx=5, pady=5)
        self.preview_canvas.create_text(200, 150, text="SVG Preview Area", fill="grey")

        # --- GIF Parameters ---
        params_frame = ttk.LabelFrame(main_frame, text="GIF Parameters")
        params_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        ttk.Label(params_frame, text="Loop:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.loop_var = tk.StringVar(value="Forever")
        loop_options = ["Forever"] + list(range(1, 31))
        self.loop_menu = ttk.Combobox(params_frame, textvariable=self.loop_var, values=loop_options, state="readonly")
        self.loop_menu.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(params_frame, text="Duration (s):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.duration_var = tk.DoubleVar(value=5.0)
        self.duration_spinbox = ttk.Spinbox(params_frame, from_=1.0, to=60.0, increment=0.5, textvariable=self.duration_var)
        self.duration_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(params_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.fps_var = tk.IntVar(value=10)
        self.fps_spinbox = ttk.Spinbox(params_frame, from_=2, to=30, increment=1, textvariable=self.fps_var)
        self.fps_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        # --- Conversion ---
        convert_frame = ttk.Frame(main_frame)
        convert_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.S), padx=5, pady=5)

        self.convert_button = ttk.Button(convert_frame, text="Convert to GIF", command=self.start_conversion)
        self.convert_button.pack(pady=10, fill=tk.X)

        self.status_label = ttk.Label(convert_frame, text="Ready.")
        self.status_label.pack(pady=5, fill=tk.X)

    def select_svg_file(self):
        filepath = filedialog.askopenfilename(
            title="Select SVG File",
            filetypes=(("SVG files", "*.svg"), ("All files", "*.*"))
        )
        if filepath:
            self.svg_filepath = filepath
            self.filepath_label.config(text=os.path.basename(filepath))
            self.status_label.config(text="File selected. Ready to convert.")
            # self.preview_svg() # We will implement this later

    def start_conversion(self):
        if not self.svg_filepath:
            messagebox.showerror("Error", "Please select an SVG file first.")
            return

        self.status_label.config(text="Analyzing SVG...")
        self.update_idletasks()

        # Check for animation
        if not self.is_animated(self.svg_filepath):
            proceed = messagebox.askyesno(
                "No Animation Detected",
                "This SVG does not appear to be animated. "
                "Do you want to continue and create a static GIF?"
            )
            if not proceed:
                self.status_label.config(text="Conversion cancelled.")
                return

        # Get SVG dimensions
        width, height = self.get_svg_size(self.svg_filepath)
        if not width or not height:
            messagebox.showerror("Error", "Could not determine SVG dimensions.")
            self.status_label.config(text="Error: Invalid SVG size.")
            return

        # Get parameters from UI
        loop = self.loop_var.get()
        duration = self.duration_var.get()
        fps = self.fps_var.get()

        # Ask for output file path
        output_filepath = filedialog.asksaveasfilename(
            title="Save GIF as...",
            defaultextension=".gif",
            filetypes=(("GIF files", "*.gif"), ("All files", "*.*"))
        )
        if not output_filepath:
            self.status_label.config(text="Save cancelled.")
            return

        # Create a temporary directory for frames
        temp_dir = tempfile.mkdtemp(prefix="svg2gif_")

        try:
            # 1. Render frames
            self.status_label.config(text="Rendering frames...")
            render_success = self.render_frames(self.svg_filepath, temp_dir, width, height, duration, fps)

            if not render_success:
                self.status_label.config(text="Frame rendering failed.")
                return

            # 2. Create GIF
            self.status_label.config(text="Assembling GIF...")
            gif_success = self.create_gif(temp_dir, output_filepath, loop, duration, fps)

            if gif_success:
                messagebox.showinfo("Success", f"GIF saved successfully to:\n{output_filepath}")
                self.status_label.config(text="Conversion complete!")
            else:
                self.status_label.config(text="GIF creation failed.")

        finally:
            # 3. Cleanup
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)

    def is_animated(self, svg_path):
        """Check if the SVG has animation tags."""
        try:
            tree = etree.parse(svg_path)
            root = tree.getroot()
            # The namespace is often present in SVG files, so we need to handle it.
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            animation_tags = [
                'animate', 'animateMotion', 'animateTransform',
                'animateColor', 'set'
            ]
            for tag in animation_tags:
                if root.find(f'.//svg:{tag}', namespaces=ns) is not None:
                    return True
            return False
        except Exception as e:
            print(f"Error checking for animation: {e}")
            return False

    def get_svg_size(self, svg_path):
        """Get the width and height from the SVG file."""
        try:
            tree = etree.parse(svg_path)
            root = tree.getroot()
            width_str = root.get('width')
            height_str = root.get('height')

            # Simple parsing, removing 'px'
            width = int(float(width_str.replace('px', '')))
            height = int(float(height_str.replace('px', '')))

            return width, height
        except Exception as e:
            print(f"Error getting SVG size: {e}")
            return None, None

    def render_frames(self, svg_path, output_dir, width, height, duration, fps):
        """Render SVG frames to PNG images using a headless browser."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--window-size={width},{height}')

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            # Load the SVG file
            abs_svg_path = os.path.abspath(svg_path)
            driver.get(f"file://{abs_svg_path}")
            time.sleep(1) # Allow SVG to load

            svg_element = driver.find_element(By.TAG_NAME, "svg")

            num_frames = int(duration * fps)
            time_step = 1.0 / fps

            for i in range(num_frames):
                current_time = i * time_step
                # Use JS to set the animation time
                driver.execute_script(f"document.documentElement.setCurrentTime({current_time});")

                frame_path = os.path.join(output_dir, f"frame_{i:04d}.png")
                svg_element.screenshot(frame_path)

                self.status_label.config(text=f"Rendering frame {i+1}/{num_frames}")
                self.update_idletasks()

            return True
        except Exception as e:
            messagebox.showerror("Rendering Error", f"Failed to render frames: {e}")
            return False
        finally:
            driver.quit()

    def crop_image(self, image_path):
        """Crop the transparent border of an image."""
        try:
            image = Image.open(image_path)
            bbox = image.getbbox()
            if bbox:
                cropped_image = image.crop(bbox)
                cropped_image.save(image_path)
            return True
        except Exception as e:
            print(f"Could not crop {image_path}: {e}")
            return False

    def create_gif(self, frames_dir, output_path, loop, duration, fps):
        """Create a GIF from a directory of frames."""
        self.status_label.config(text="Creating GIF...")
        self.update_idletasks()

        try:
            frames = []
            frame_files = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith('.png')])

            for frame_file in frame_files:
                self.crop_image(frame_file)
                frames.append(Image.open(frame_file))

            if not frames:
                messagebox.showerror("Error", "No frames were generated.")
                return False

            frame_duration_ms = int(1000 / fps)

            # The loop parameter in Pillow is 0 for infinite, or a number for repetitions.
            loop_count = 0 if loop == "Forever" else int(loop)

            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration_ms,
                loop=loop_count,
                disposal=2  # Dispose of the previous frame
            )
            return True
        except Exception as e:
            messagebox.showerror("GIF Creation Error", f"Failed to create GIF: {e}")
            return False


if __name__ == "__main__":
    app = SvgToGifConverter()
    app.mainloop()
