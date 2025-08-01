import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
from lxml import etree
import subprocess
import os
import tempfile
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class SvgToGifConverter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SVG to GIF Converter")
        self.geometry("600x600")
        self.init_ui()

    def init_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        file_frame = ttk.LabelFrame(main_frame, text="SVG File")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.filepath_label = ttk.Label(file_frame, text="No file selected.")
        self.filepath_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.size_label = ttk.Label(file_frame, text="")
        self.size_label.grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)

        self.select_button = ttk.Button(file_frame, text="Select SVG", command=self.select_svg_file)
        self.select_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E)

        self.svg_filepath = None

        preview_frame = ttk.LabelFrame(main_frame, text="Preview")
        preview_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.preview_canvas = tk.Canvas(preview_frame, bg="white", width=400, height=240)
        self.preview_canvas.grid(row=0, column=0, padx=5, pady=5)
        self.preview_canvas.create_text(200, 120, text="SVG Preview Area", fill="grey")

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

        size_frame = ttk.LabelFrame(main_frame, text="Output Size")
        size_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.use_custom_size_var = tk.BooleanVar(value=False)
        self.custom_size_check = ttk.Checkbutton(
            size_frame, text="Use Custom Size", variable=self.use_custom_size_var,
            command=self.toggle_custom_size_fields
        )
        self.custom_size_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        ttk.Label(size_frame, text="Width:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.custom_width_var = tk.IntVar()
        self.width_spinbox = ttk.Spinbox(size_frame, from_=1, to=4096, textvariable=self.custom_width_var, state="disabled")
        self.width_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(size_frame, text="Height:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.custom_height_var = tk.IntVar()
        self.height_spinbox = ttk.Spinbox(size_frame, from_=1, to=4096, textvariable=self.custom_height_var, state="disabled")
        self.height_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        convert_frame = ttk.Frame(main_frame)
        convert_frame.grid(row=2, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.S), padx=5, pady=5)

        self.convert_button = ttk.Button(convert_frame, text="Convert to GIF", command=self.start_conversion)
        self.convert_button.pack(pady=10, fill=tk.X)

        self.status_label = ttk.Label(convert_frame, text="Ready.")
        self.status_label.pack(pady=5, fill=tk.X)

    def toggle_custom_size_fields(self):
        if self.use_custom_size_var.get():
            self.width_spinbox.config(state="normal")
            self.height_spinbox.config(state="normal")
        else:
            self.width_spinbox.config(state="disabled")
            self.height_spinbox.config(state="disabled")

    def select_svg_file(self):
        filepath = filedialog.askopenfilename(
            title="Select SVG File",
            filetypes=(("SVG files", "*.svg"), ("All files", "*.*"))
        )
        if filepath:
            self.svg_filepath = filepath
            self.filepath_label.config(text=os.path.basename(filepath))

            width, height = self.get_svg_size(filepath)
            if width and height:
                self.size_label.config(text=f"Detected Size: {width} x {height}")
                self.status_label.config(text="File selected. Ready to convert.")
                self.custom_width_var.set(width)
                self.custom_height_var.set(height)
            else:
                self.size_label.config(text="Could not detect size.")
                messagebox.showerror("SVG Error", "Could not determine the dimensions of the selected SVG file.")

    def start_conversion(self):
        if not self.svg_filepath:
            messagebox.showerror("Error", "Please select an SVG file first.")
            return

        if not self.is_animated(self.svg_filepath):
            if not messagebox.askyesno("No Animation", "No animation detected. Create a static GIF?"):
                return

        output_filepath = filedialog.asksaveasfilename(
            title="Save GIF as...",
            defaultextension=".gif",
            filetypes=(("GIF files", "*.gif"), ("All files", "*.*"))
        )
        if not output_filepath:
            self.status_label.config(text="Save cancelled.")
            return

        self.convert_button.config(state="disabled")
        self.status_label.config(text="Converting...")

        thread = threading.Thread(target=self._conversion_thread, args=(output_filepath,))
        thread.daemon = True
        thread.start()

    def _conversion_thread(self, output_filepath):
        try:
            detected_width, detected_height = self.get_svg_size(self.svg_filepath)
            if not detected_width or not detected_height:
                self.update_status("Error: Could not determine SVG dimensions.")
                return

            if self.use_custom_size_var.get():
                output_width = self.custom_width_var.get()
                output_height = self.custom_height_var.get()
            else:
                output_width = detected_width
                output_height = detected_height

            render_width, render_height = detected_width, detected_height

            loop = self.loop_var.get()
            duration = self.duration_var.get()
            fps = self.fps_var.get()

            temp_dir = tempfile.mkdtemp(prefix="svg2gif_")

            render_success = self.render_frames(self.svg_filepath, temp_dir, render_width, render_height, duration, fps)
            if not render_success:
                self.update_status("Frame rendering failed.")
                return

            gif_success = self.create_gif(temp_dir, output_filepath, loop, duration, fps, output_width, output_height)
            if gif_success:
                self.update_status("Conversion complete!")
                self.after(0, lambda: messagebox.showinfo("Success", f"GIF saved to:\n{output_filepath}"))
            else:
                self.update_status("GIF creation failed.")

        except Exception as e:
            self.update_status(f"An error occurred: {e}")
        finally:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)
            self.after(0, lambda: self.convert_button.config(state="normal"))
            self.after(0, lambda: self.status_label.config(text="Ready."))

    def update_status(self, message):
        self.after(0, lambda: self.status_label.config(text=message))

    def is_animated(self, svg_path):
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '@keyframes' in content: return True
            tree = etree.fromstring(content.encode('utf-8'))
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            for tag in ['animate', 'animateMotion', 'animateTransform', 'animateColor', 'set']:
                if tree.find(f'.//svg:{tag}', namespaces=ns) is not None:
                    return True
            return False
        except:
            return False

    def get_svg_size(self, svg_path):
        try:
            tree = etree.parse(svg_path)
            root = tree.getroot()
            width, height = root.get('width'), root.get('height')
            if width and height:
                return int(float(''.join(filter(str.isdigit, width)))), int(float(''.join(filter(str.isdigit, height))))
            viewbox = root.get('viewBox')
            if viewbox:
                parts = viewbox.split()
                if len(parts) == 4:
                    return int(float(parts[2])), int(float(parts[3]))
            return None, None
        except:
            return None, None

    def render_frames(self, svg_path, output_dir, width, height, duration, fps):
        self.update_status("Rendering frames...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Suppress non-critical browser logging
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--log-level=3')
        # Add some vertical padding to prevent browser chrome from cutting off the bottom
        options.add_argument(f'--window-size={width},{height + 50}')
        try:
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            html_content = f"""
            <html>
            <body style='margin:0; padding:0; background:transparent; overflow: hidden;'>
                <img src='file://{os.path.abspath(svg_path)}'>
            </body>
            </html>
            """
            html_path = os.path.join(tempfile.gettempdir(), 'svg_wrapper.html')
            with open(html_path, 'w') as f:
                f.write(html_content)

            driver.get(f"file://{html_path}")
            time.sleep(1)

            num_frames = int(duration * fps)
            time_per_frame = 1.0 / fps
            for i in range(num_frames):
                self.update_status(f"Rendering frame {i+1}/{num_frames}")
                driver.save_screenshot(os.path.join(output_dir, f"frame_{i:04d}.png"))
                time.sleep(time_per_frame)
            driver.quit()
            return True
        except Exception as e:
            self.update_status(f"Frame rendering failed: {e}")
            return False

    def resize_and_paste_frame(self, frame_path, output_width, output_height):
        try:
            frame = Image.open(frame_path).convert("RGBA")

            # Scale the original frame down to 90%
            scale_factor = 0.90
            new_size = (int(frame.width * scale_factor), int(frame.height * scale_factor))
            frame = frame.resize(new_size, Image.Resampling.LANCZOS)

            new_frame = Image.new("RGBA", (output_width, output_height), "WHITE")
            paste_x = (output_width - frame.width) // 2
            paste_y = 0 # Align to top
            new_frame.paste(frame, (paste_x, paste_y), mask=frame)
            new_frame.save(frame_path)
            return True
        except Exception as e:
            self.update_status(f"Error resizing frame: {e}")
            return False

    def create_gif(self, frames_dir, output_path, loop, duration, fps, output_width, output_height):
        self.update_status("Assembling GIF...")
        try:
            files = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith('.png')])
            if not files: return False

            raw_frames = []
            for f in files:
                if not self.resize_and_paste_frame(f, output_width, output_height):
                    return False
                raw_frames.append(Image.open(f))

            if not raw_frames: return False

            frames = [frame.convert("RGB").quantize(colors=255) for frame in raw_frames]

            loop_count = 0 if loop == "Forever" else int(loop)
            frames[0].save(
                output_path, save_all=True, append_images=frames[1:],
                duration=int(1000 / fps), loop=loop_count, disposal=2
            )
            return True
        except Exception as e:
            self.update_status(f"GIF creation failed: {e}")
            return False

if __name__ == "__main__":
    app = SvgToGifConverter()
    app.mainloop()
