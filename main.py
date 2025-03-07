import tkinter as tk
from tkinter import messagebox, simpledialog
import pyautogui
import json
import os
import time
import numpy as np
from PIL import ImageGrab, ImageTk, Image

class BoxDrawingSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("MyLabMath Box Drawing Selector")
        
        # Get screen dimensions
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Set window size
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Variables
        self.current_quiz_region = None
        self.review_quiz_region = None
        self.next_button_pos = None
        self.next_button_region = None
        
        # For drawing
        self.overlay = None
        self.start_x = None
        self.start_y = None
        self.current_rectangle = None
        self.drawing_mode = None
        
        # Main frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="MyLabMath Quiz Comparison Tool", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = tk.Label(main_frame, text="Follow the steps below to set up the comparison:", font=("Arial", 12))
        instructions.pack(anchor=tk.W, pady=(0, 10))
        
        # Step 1: Current Quiz Region
        step1_frame = tk.LabelFrame(main_frame, text="Step 1: Set Current Quiz Region", padx=10, pady=10)
        step1_frame.pack(fill=tk.X, pady=5)
        
        self.current_quiz_button = tk.Button(step1_frame, text="Draw Current Quiz Region", 
                                           command=lambda: self.start_drawing("current"), bg="#e0f0ff", padx=10)
        self.current_quiz_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.current_quiz_status = tk.Label(step1_frame, text="Not Set", fg="red")
        self.current_quiz_status.pack(side=tk.LEFT, padx=10)
        
        # Step 2: Review Quiz Region
        step2_frame = tk.LabelFrame(main_frame, text="Step 2: Set Review Quiz Region", padx=10, pady=10)
        step2_frame.pack(fill=tk.X, pady=5)
        
        self.review_quiz_button = tk.Button(step2_frame, text="Draw Review Quiz Region", 
                                          command=lambda: self.start_drawing("review"), bg="#e0f0ff", padx=10)
        self.review_quiz_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.review_quiz_status = tk.Label(step2_frame, text="Not Set", fg="red")
        self.review_quiz_status.pack(side=tk.LEFT, padx=10)
        
        # Step 3: Next Button
        step3_frame = tk.LabelFrame(main_frame, text="Step 3: Set Next Button Position", padx=10, pady=10)
        step3_frame.pack(fill=tk.X, pady=5)
        
        self.next_button_button = tk.Button(step3_frame, text="Draw Next Button Region", 
                                          command=self.set_next_button, bg="#ffe0e0", padx=10)
        self.next_button_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.next_button_status = tk.Label(step3_frame, text="Not Set", fg="red")
        self.next_button_status.pack(side=tk.LEFT, padx=10)
        
        # Step 4: Tesseract Path (if needed)
        step4_frame = tk.LabelFrame(main_frame, text="Step 4: Set Tesseract Path (for OCR)", padx=10, pady=10)
        step4_frame.pack(fill=tk.X, pady=5)
        
        self.tesseract_path_var = tk.StringVar(value=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        self.tesseract_entry = tk.Entry(step4_frame, textvariable=self.tesseract_path_var, width=40)
        self.tesseract_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.tesseract_button = tk.Button(step4_frame, text="Browse", 
                                         command=self.browse_tesseract_path, padx=10)
        self.tesseract_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Step 5: Run Comparison
        step5_frame = tk.LabelFrame(main_frame, text="Step 5: Run Comparison", padx=10, pady=10)
        step5_frame.pack(fill=tk.X, pady=5)
        
        self.run_button = tk.Button(step5_frame, text="RUN COMPARISON", 
                                   command=self.run_comparison, 
                                   bg="#e0ffe0", padx=20, pady=10, 
                                   font=("Arial", 12, "bold"),
                                   state=tk.DISABLED)
        self.run_button.pack(padx=5, pady=5)
        
        # Save/Load Config
        config_frame = tk.Frame(main_frame)
        config_frame.pack(fill=tk.X, pady=10)
        
        self.save_button = tk.Button(config_frame, text="Save Configuration", 
                                    command=self.save_config, padx=10)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.load_button = tk.Button(config_frame, text="Load Configuration", 
                                    command=self.load_config, padx=10)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        self.test_ocr_button = tk.Button(config_frame, text="Test OCR", 
                                       command=self.test_ocr, padx=10)
        self.test_ocr_button.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Start by setting the regions and next button position.")
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Config file name
        self.config_file = "mylabmath_box_config.json"
        
        # Check if config exists and load it
        self.load_config()
        
        # Update button states
        self.check_run_button_state()
    
    def browse_tesseract_path(self):
        """Browse for Tesseract executable"""
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Tesseract Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.tesseract_path_var.set(path)
    
    def check_run_button_state(self):
        """Enable the run button only if all regions are set"""
        if self.current_quiz_region and self.review_quiz_region and self.next_button_pos:
            self.run_button.config(state=tk.NORMAL)
        else:
            self.run_button.config(state=tk.DISABLED)
    
    def start_drawing(self, mode):
        """Start the drawing mode to select a region"""
        self.drawing_mode = mode
        
        # Hide main window
        self.root.withdraw()
        
        # Take a screenshot for overlay
        screen = ImageGrab.grab()
        
        # Create transparent overlay window
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-alpha', 0.3)
        self.overlay.attributes('-topmost', True)
        
        # Convert PIL Image to ImageTk
        screen_tk = ImageTk.PhotoImage(screen)
        
        # Create canvas with screenshot as background
        self.canvas = tk.Canvas(self.overlay, cursor="cross", 
                                width=self.screen_width, height=self.screen_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Display the screenshot
        self.canvas.create_image(0, 0, image=screen_tk, anchor=tk.NW)
        self.canvas.image = screen_tk  # Keep a reference
        
        # Instructions label at the top
        region_type = "Current Quiz" if mode == "current" else "Review Quiz"
        instruction_text = f"Draw a box around the {region_type} region by clicking and dragging.\nPress ESC to cancel."
        instructions = tk.Label(
            self.overlay, text=instruction_text, 
            bg="white", font=("Arial", 12), padx=10, pady=5
        )
        instructions.place(relx=0.5, y=30, anchor=tk.CENTER)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        # Bind escape to cancel
        self.overlay.bind("<Escape>", self.cancel_drawing)
    
    def on_button_press(self, event):
        """Handle mouse button press"""
        # Save starting position
        self.start_x = event.x
        self.start_y = event.y
        
        # Create a rectangle if it doesn't exist
        if self.current_rectangle:
            self.canvas.delete(self.current_rectangle)
        self.current_rectangle = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline="red", width=2
        )
    
    def on_mouse_drag(self, event):
        """Handle mouse drag"""
        # Update rectangle as mouse moves
        if self.current_rectangle:
            self.canvas.coords(self.current_rectangle, self.start_x, self.start_y, event.x, event.y)
    
    def on_button_release(self, event):
        """Handle mouse button release"""
        if not self.current_rectangle:
            return
            
        # Get final coordinates
        end_x, end_y = event.x, event.y
        
        # Ensure we have a minimum size (avoid accidental clicks)
        if abs(self.start_x - end_x) < 10 or abs(self.start_y - end_y) < 10:
            messagebox.showinfo("Info", "Selection too small. Please draw a larger box.")
            return
            
        # Swap coordinates if needed
        if self.start_x > end_x:
            self.start_x, end_x = end_x, self.start_x
        if self.start_y > end_y:
            self.start_y, end_y = end_y, self.start_y
        
        # Format as (left, top, width, height)
        region = (self.start_x, self.start_y, end_x - self.start_x, end_y - self.start_y)
        
        # Save the region based on mode
        if self.drawing_mode == "current":
            self.current_quiz_region = region
            self.current_quiz_status.config(text=f"Set: {region}", fg="green")
        else:  # review
            self.review_quiz_region = region
            self.review_quiz_status.config(text=f"Set: {region}", fg="green")
        
        # Close overlay and show main window
        self.overlay.destroy()
        self.overlay = None
        self.root.deiconify()
        
        # Update status
        self.status_var.set(f"{self.drawing_mode.title()} quiz region set to {region}")
        
        # Update run button state
        self.check_run_button_state()
    
    def set_next_button(self):
        """Start the drawing mode to select the next button region"""
        self.drawing_mode = "next_button"
        
        # Hide main window
        self.root.withdraw()
        
        # Take a screenshot for overlay
        screen = ImageGrab.grab()
        
        # Create transparent overlay window
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-alpha', 0.3)
        self.overlay.attributes('-topmost', True)
        
        # Convert PIL Image to ImageTk
        screen_tk = ImageTk.PhotoImage(screen)
        
        # Create canvas with screenshot as background
        self.canvas = tk.Canvas(self.overlay, cursor="cross", 
                                width=self.screen_width, height=self.screen_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Display the screenshot
        self.canvas.create_image(0, 0, image=screen_tk, anchor=tk.NW)
        self.canvas.image = screen_tk  # Keep a reference
        
        # Instructions label at the top
        instruction_text = "Draw a box around the NEXT button in the review quiz.\nPress ESC to cancel."
        instructions = tk.Label(
            self.overlay, text=instruction_text, 
            bg="white", font=("Arial", 12), padx=10, pady=5
        )
        instructions.place(relx=0.5, y=30, anchor=tk.CENTER)
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_next_button_release)
        
        # Bind escape to cancel
        self.overlay.bind("<Escape>", self.cancel_drawing)
    
    def on_next_button_release(self, event):
        """Handle mouse button release for next button selection"""
        if not self.current_rectangle:
            return
            
        # Get final coordinates
        end_x, end_y = event.x, event.y
        
        # Ensure we have a minimum size (avoid accidental clicks)
        if abs(self.start_x - end_x) < 10 or abs(self.start_y - end_y) < 10:
            messagebox.showinfo("Info", "Selection too small. Please draw a larger box.")
            return
            
        # Swap coordinates if needed
        if self.start_x > end_x:
            self.start_x, end_x = end_x, self.start_x
        if self.start_y > end_y:
            self.start_y, end_y = end_y, self.start_y
        
        # Format as (left, top, width, height)
        region = (self.start_x, self.start_y, end_x - self.start_x, end_y - self.start_y)
        
        # Calculate center point of the region for clicking
        center_x = self.start_x + (end_x - self.start_x) // 2
        center_y = self.start_y + (end_y - self.start_y) // 2
        self.next_button_pos = (center_x, center_y)
        
        # Save the region for display purposes
        self.next_button_region = region
        self.next_button_status.config(text=f"Set: {region} (click at {self.next_button_pos})", fg="green")
        
        # Close overlay and show main window
        self.overlay.destroy()
        self.overlay = None
        self.root.deiconify()
        
        # Update status
        self.status_var.set(f"Next button region set to {region} (click at center: {self.next_button_pos})")
        
        # Update run button state
        self.check_run_button_state()
    
    def cancel_drawing(self, event=None):
        """Cancel the drawing process"""
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        self.root.deiconify()
        self.status_var.set("Drawing canceled")
    
    def save_config(self):
        """Save the current configuration to file"""
        config = {
            "current_quiz_region": self.current_quiz_region,
            "review_quiz_region": self.review_quiz_region,
            "next_button_pos": self.next_button_pos,
            "next_button_region": self.next_button_region,
            "tesseract_path": self.tesseract_path_var.get()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            self.status_var.set(f"Configuration saved to {self.config_file}")
            messagebox.showinfo("Success", f"Configuration saved successfully to {self.config_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config(self):
        """Load configuration from file if it exists"""
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Load regions and button position
            if "current_quiz_region" in config and config["current_quiz_region"]:
                self.current_quiz_region = tuple(config["current_quiz_region"])
                self.current_quiz_status.config(text=f"Set: {self.current_quiz_region}", fg="green")
                
            if "review_quiz_region" in config and config["review_quiz_region"]:
                self.review_quiz_region = tuple(config["review_quiz_region"])
                self.review_quiz_status.config(text=f"Set: {self.review_quiz_region}", fg="green")
                
            if "next_button_pos" in config and config["next_button_pos"]:
                self.next_button_pos = tuple(config["next_button_pos"])
                
            if "next_button_region" in config and config["next_button_region"]:
                self.next_button_region = tuple(config["next_button_region"])
                self.next_button_status.config(
                    text=f"Set: {self.next_button_region} (click at {self.next_button_pos})", 
                    fg="green"
                )
                
            if "tesseract_path" in config and config["tesseract_path"]:
                self.tesseract_path_var.set(config["tesseract_path"])
            
            self.status_var.set(f"Configuration loaded from {self.config_file}")
            self.check_run_button_state()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def test_ocr(self):
        """Test OCR on both regions to verify it's working correctly"""
        # Check if all required regions are set
        if not self.current_quiz_region or not self.review_quiz_region:
            messagebox.showerror("Error", "Please set both quiz regions first")
            return
            
        # Try to import the OCR libraries
        try:
            import pytesseract
            import cv2
            
            # Set tesseract path
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path_var.get()
            
            # Capture screenshots of both regions
            current_img = self.capture_region(self.current_quiz_region)
            review_img = self.capture_region(self.review_quiz_region)
            
            # Extract text
            current_text = self.extract_text(current_img)
            review_text = self.extract_text(review_img)
            
            # Calculate similarity
            similarity = self.calculate_similarity(current_text, review_text)
            
            # Create result window
            result_window = tk.Toplevel(self.root)
            result_window.title("OCR Test Results")
            result_window.geometry("800x600")
            
            # Create frames
            current_frame = tk.LabelFrame(result_window, text="Current Quiz Text")
            current_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            current_text_widget = tk.Text(current_frame, wrap=tk.WORD, height=10)
            current_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            current_text_widget.insert(tk.END, current_text)
            
            review_frame = tk.LabelFrame(result_window, text="Review Quiz Text")
            review_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            review_text_widget = tk.Text(review_frame, wrap=tk.WORD, height=10)
            review_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            review_text_widget.insert(tk.END, review_text)
            
            # Similarity score
            similarity_label = tk.Label(
                result_window, 
                text=f"Similarity Score: {similarity:.2f}",
                font=("Arial", 14, "bold")
            )
            similarity_label.pack(pady=10)
            
            # Highlight common words
            words1 = set(current_text.lower().split())
            words2 = set(review_text.lower().split())
            common_words = words1.intersection(words2)
            
            common_frame = tk.LabelFrame(result_window, text="Common Words")
            common_frame.pack(fill=tk.X, padx=10, pady=5)
            
            common_text = tk.Text(common_frame, wrap=tk.WORD, height=3)
            common_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            common_text.insert(tk.END, ", ".join(common_words))
            
            # Close button
            close_button = tk.Button(
                result_window, 
                text="Close", 
                command=result_window.destroy,
                padx=20
            )
            close_button.pack(pady=10)
            
        except ImportError:
            messagebox.showerror("Error", "OCR libraries not found. Please install pytesseract and opencv-python.")
        except Exception as e:
            messagebox.showerror("Error", f"OCR test failed: {str(e)}")
    
    def capture_region(self, region):
        """Capture a specific region of the screen"""
        screenshot = pyautogui.screenshot(region=region)
        return np.array(screenshot)
    
    def extract_text(self, image):
        """Extract text from the image using OCR"""
        try:
            import pytesseract
            import cv2
            
            # Set tesseract path
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path_var.get()
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply threshold to get black and white image
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # OCR
            text = pytesseract.image_to_string(thresh)
            return text.strip()
        except Exception as e:
            return f"OCR Error: {str(e)}"
    
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two text strings"""
        # Simple method: count common words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        return len(common_words) / max(len(words1), len(words2))
    
            # Add a separate "Advanced Settings" button
        self.settings_button = tk.Button(step5_frame, text="Advanced Settings", 
                                       command=self.show_settings, padx=10, pady=5)
        self.settings_button.pack(pady=5)
        
    def show_settings(self):
        """Show the advanced settings dialog"""
        self.run_comparison(show_dialog=True)
        
    def run_comparison(self, show_dialog=False):
        """Run the comparison using pyautogui to click through questions"""
        if not self.current_quiz_region or not self.review_quiz_region or not self.next_button_pos:
            messagebox.showerror("Error", "Please set all regions and the next button position first")
            return
        
        # Try to import OCR libraries
        try:
            import pytesseract
            import cv2
            ocr_available = True
            
            # Set tesseract path
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path_var.get()
            
        except ImportError:
            ocr_available = False
            messagebox.showinfo("OCR Unavailable", 
                              "OCR libraries not found. Running in manual click mode only.")
        
        # If show_dialog is True, show the settings dialog
        if show_dialog:
            # Create the comparison settings dialog
            settings_window = tk.Toplevel(self.root)
            settings_window.title("Advanced Comparison Settings")
            settings_window.geometry("500x400")
            settings_window.resizable(False, False)
            
            settings_frame = tk.Frame(settings_window, padx=20, pady=20)
            settings_frame.pack(fill=tk.BOTH, expand=True)
            
            # Mode selection
            mode_label = tk.Label(settings_frame, text="Select Comparison Mode:", font=("Arial", 12, "bold"))
            mode_label.pack(anchor=tk.W, pady=(0, 10))
            
            mode_var = tk.StringVar(value="manual" if not ocr_available else "auto")
            
            manual_radio = tk.Radiobutton(
                settings_frame, text="Manual Clicking (Just click Next button at regular intervals)", 
                variable=mode_var, value="manual"
            )
            manual_radio.pack(anchor=tk.W, pady=5)
            
            if ocr_available:
                auto_radio = tk.Radiobutton(
                    settings_frame, text="Auto Compare with OCR (Stop when questions match)", 
                    variable=mode_var, value="auto"
                )
                auto_radio.pack(anchor=tk.W, pady=5)
            
            # Click delay
            delay_frame = tk.Frame(settings_frame)
            delay_frame.pack(fill=tk.X, pady=10)
            
            delay_label = tk.Label(delay_frame, text="Click Delay (seconds):")
            delay_label.pack(side=tk.LEFT, padx=5)
            
            delay_var = tk.DoubleVar(value=1.0)
            delay_spinbox = tk.Spinbox(
                delay_frame, from_=0.5, to=5.0, increment=0.1, 
                textvariable=delay_var, width=5
            )
            delay_spinbox.pack(side=tk.LEFT, padx=5)
            
            # Wait after click
            wait_frame = tk.Frame(settings_frame)
            wait_frame.pack(fill=tk.X, pady=10)
            
            wait_label = tk.Label(wait_frame, text="Wait After Click (seconds):")
            wait_label.pack(side=tk.LEFT, padx=5)
            
            wait_var = tk.DoubleVar(value=0.5)
            wait_spinbox = tk.Spinbox(
                wait_frame, from_=0.1, to=3.0, increment=0.1, 
                textvariable=wait_var, width=5
            )
            wait_spinbox.pack(side=tk.LEFT, padx=5)
            
            # OCR settings (only if OCR is available)
            if ocr_available:
                ocr_frame = tk.LabelFrame(settings_frame, text="OCR Settings", padx=10, pady=10)
                ocr_frame.pack(fill=tk.X, pady=10)
                
                # Similarity threshold
                threshold_frame = tk.Frame(ocr_frame)
                threshold_frame.pack(fill=tk.X, pady=5)
                
                threshold_label = tk.Label(threshold_frame, text="Similarity Threshold (0-1):")
                threshold_label.pack(side=tk.LEFT, padx=5)
                
                threshold_var = tk.DoubleVar(value=0.7)
                threshold_spinbox = tk.Spinbox(
                    threshold_frame, from_=0.1, to=1.0, increment=0.05, 
                    textvariable=threshold_var, width=5
                )
                threshold_spinbox.pack(side=tk.LEFT, padx=5)
                
                # Max attempts
                attempts_frame = tk.Frame(ocr_frame)
                attempts_frame.pack(fill=tk.X, pady=5)
                
                attempts_label = tk.Label(attempts_frame, text="Maximum Attempts:")
                attempts_label.pack(side=tk.LEFT, padx=5)
                
                attempts_var = tk.IntVar(value=100)
                attempts_spinbox = tk.Spinbox(
                    attempts_frame, from_=1, to=1000, increment=10, 
                    textvariable=attempts_var, width=5
                )
                attempts_spinbox.pack(side=tk.LEFT, padx=5)
                
                # Max retry on OCR failure
                retry_frame = tk.Frame(ocr_frame)
                retry_frame.pack(fill=tk.X, pady=5)
                
                retry_label = tk.Label(retry_frame, text="Max OCR Retries:")
                retry_label.pack(side=tk.LEFT, padx=5)
                
                retry_var = tk.IntVar(value=3)
                retry_spinbox = tk.Spinbox(
                    retry_frame, from_=1, to=10, increment=1, 
                    textvariable=retry_var, width=5
                )
                retry_spinbox.pack(side=tk.LEFT, padx=5)
            
            # Start button
            button_frame = tk.Frame(settings_frame)
            button_frame.pack(pady=20)
            
            start_button = tk.Button(
                button_frame, text="Apply Settings & Start", 
                command=lambda: self.start_comparison(
                    settings_window,
                    mode_var.get(),
                    delay_var.get(),
                    wait_var.get(),
                    threshold_var.get() if ocr_available else 0.7,
                    attempts_var.get() if ocr_available else 100,
                    retry_var.get() if ocr_available else 3
                ),
                padx=20, pady=10, bg="#e0ffe0", font=("Arial", 11, "bold")
            )
            start_button.pack(side=tk.LEFT, padx=10)
            
            cancel_button = tk.Button(
                button_frame, text="Cancel", 
                command=settings_window.destroy,
                padx=20, pady=10
            )
            cancel_button.pack(side=tk.LEFT, padx=10)
        else:
            # Start directly with default settings
            mode = "auto" if ocr_available else "manual"
            click_delay = 1.0
            wait_delay = 0.5
            similarity_threshold = 0.7
            max_attempts = 100
            max_retries = 3
            
            # Start the comparison directly
            self.start_comparison(None, mode, click_delay, wait_delay, 
                                similarity_threshold, max_attempts, max_retries)
    
    def start_comparison(self, settings_window, mode, click_delay, wait_delay, 
                        similarity_threshold=0.7, max_attempts=100, max_retries=3):
        """Start the comparison process"""
        # Close settings window if it exists
        if settings_window:
            settings_window.destroy()
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Comparison Progress")
        progress_window.geometry("600x500")
        progress_window.attributes('-topmost', True)
        
        # Progress frame
        progress_frame = tk.Frame(progress_window, padx=20, pady=20)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mode display
        mode_label = tk.Label(
            progress_frame, 
            text=f"Mode: {'Auto Compare with OCR' if mode == 'auto' else 'Manual Clicking'}",
            font=("Arial", 12, "bold")
        )
        mode_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Settings display
        settings_text = f"Click Delay: {click_delay}s, Wait After Click: {wait_delay}s"
        if mode == "auto":
            settings_text += f", Similarity Threshold: {similarity_threshold}"
        
        settings_label = tk.Label(progress_frame, text=settings_text)
        settings_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Progress display
        progress_var = tk.StringVar(value="Ready to start...")
        progress_label = tk.Label(
            progress_frame, 
            textvariable=progress_var,
            font=("Arial", 12),
            wraplength=560
        )
        progress_label.pack(pady=10)
        
        # Create text frame for current and review text
        text_frame = tk.Frame(progress_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Current quiz text
        current_frame = tk.LabelFrame(text_frame, text="Current Quiz Text")
        current_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        current_text_var = tk.StringVar(value="")
        current_text_label = tk.Label(
            current_frame, 
            textvariable=current_text_var,
            wraplength=250,
            justify=tk.LEFT,
            anchor=tk.NW,
            bg="white",
            relief=tk.SUNKEN,
            padx=5, pady=5
        )
        current_text_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Review quiz text
        review_frame = tk.LabelFrame(text_frame, text="Review Quiz Text")
        review_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        review_text_var = tk.StringVar(value="")
        review_text_label = tk.Label(
            review_frame, 
            textvariable=review_text_var,
            wraplength=250,
            justify=tk.LEFT,
            anchor=tk.NW,
            bg="white",
            relief=tk.SUNKEN,
            padx=5, pady=5
        )
        review_text_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Similarity display
        similarity_frame = tk.Frame(progress_frame)
        similarity_frame.pack(fill=tk.X, pady=10)
        
        similarity_label = tk.Label(similarity_frame, text="Similarity:")
        similarity_label.pack(side=tk.LEFT, padx=5)
        
        similarity_var = tk.StringVar(value="N/A")
        similarity_value = tk.Label(
            similarity_frame, 
            textvariable=similarity_var,
            font=("Arial", 12, "bold")
        )
        similarity_value.pack(side=tk.LEFT, padx=5)
        
        # Attempt counter
        attempt_frame = tk.Frame(progress_frame)
        attempt_frame.pack(fill=tk.X, pady=5)
        
        attempt_label = tk.Label(attempt_frame, text="Attempts:")
        attempt_label.pack(side=tk.LEFT, padx=5)
        
        attempt_var = tk.StringVar(value="0")
        attempt_value = tk.Label(
            attempt_frame, 
            textvariable=attempt_var,
            font=("Arial", 12, "bold")
        )
        attempt_value.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        button_frame = tk.Frame(progress_frame)
        button_frame.pack(pady=10)
        
        # Running state variable
        running = tk.BooleanVar(value=False)
        
        # Toggle function
        def toggle_running():
            if running.get():
                running.set(False)
                toggle_button.config(text="Start")
                progress_var.set("Paused. Click Start to resume.")
            else:
                running.set(True)
                toggle_button.config(text="Pause")
                progress_var.set("Running...")
                
                # Start the appropriate process
                if mode == "auto":
                    start_auto_comparison()
                else:
                    start_manual_clicking()
        
        # Manual clicking function
        def start_manual_clicking():
            if not running.get():
                return
                
            # Click the next button
            pyautogui.click(self.next_button_pos)
            
            # Update attempts
            attempts = int(attempt_var.get()) + 1
            attempt_var.set(str(attempts))
            
            # Schedule next click
            progress_window.after(int(click_delay * 1000), start_manual_clicking)
        
        # Auto comparison function
        def start_auto_comparison():
            if not running.get():
                return
                
            # Import OCR libraries
            import pytesseract
            import cv2
            
            # Set tesseract path
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path_var.get()
            
            # Get current attempt count
            attempts = int(attempt_var.get())
            
            # Stop if max attempts reached
            if attempts >= max_attempts:
                running.set(False)
                toggle_button.config(text="Start")
                progress_var.set(f"Maximum attempts ({max_attempts}) reached.")
                return
            
            # Update progress
            progress_var.set(f"Clicking Next button (attempt {attempts+1})...")
            progress_window.update()
            
            # Click the next button
            pyautogui.click(self.next_button_pos)
            
            # Wait after click
            progress_var.set(f"Waiting {wait_delay}s for page to load...")
            progress_window.update()
            time.sleep(wait_delay)
            
            # Capture review quiz region
            progress_var.set("Capturing review quiz region...")
            progress_window.update()
            
            # Initialize variables
            review_text = ""
            retry_count = 0
            ocr_success = False
            
            # Try OCR with retries
            while not ocr_success and retry_count < max_retries:
                try:
                    # Capture review region
                    review_img = self.capture_region(self.review_quiz_region)
                    
                    # Convert to grayscale
                    gray = cv2.cvtColor(review_img, cv2.COLOR_RGB2GRAY)
                    
                    # Apply threshold
                    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                    
                    # OCR
                    review_text = pytesseract.image_to_string(thresh).strip()
                    
                    # Check if OCR returned text
                    if review_text:
                        ocr_success = True
                    else:
                        retry_count += 1
                        progress_var.set(f"OCR returned empty text, retrying ({retry_count}/{max_retries})...")
                        progress_window.update()
                        time.sleep(0.2)
                except Exception as e:
                    retry_count += 1
                    progress_var.set(f"OCR error: {str(e)}, retrying ({retry_count}/{max_retries})...")
                    progress_window.update()
                    time.sleep(0.2)
            
            # If OCR failed after retries, skip this attempt
            if not ocr_success:
                progress_var.set("OCR failed after multiple retries. Skipping to next.")
                attempts += 1
                attempt_var.set(str(attempts))
                progress_window.after(500, start_auto_comparison)
                return
            
            # Get current quiz text (only once)
            if current_text_var.get() == "":
                try:
                    current_img = self.capture_region(self.current_quiz_region)
                    gray = cv2.cvtColor(current_img, cv2.COLOR_RGB2GRAY)
                    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                    current_text = pytesseract.image_to_string(thresh).strip()
                    current_text_var.set(current_text)
                except Exception as e:
                    progress_var.set(f"Error capturing current quiz text: {str(e)}")
                    running.set(False)
                    toggle_button.config(text="Start")
                    return
            
            # Get current text
            current_text = current_text_var.get()
            
            # Update review text display
            review_text_var.set(review_text)
            
            # Calculate similarity
            similarity = self.calculate_similarity(current_text, review_text)
            similarity_var.set(f"{similarity:.2f}")
            
            # Update attempts
            attempts += 1
            attempt_var.set(str(attempts))
            
            # Check if match found
            if similarity >= similarity_threshold:
                progress_var.set(f"MATCH FOUND! Similarity: {similarity:.2f}")
                running.set(False)
                toggle_button.config(text="Start")
                
                # Flash the window
                for _ in range(5):
                    progress_window.configure(background='green')
                    progress_window.update()
                    time.sleep(0.1)
                    progress_window.configure(background='SystemButtonFace')
                    progress_window.update()
                    time.sleep(0.1)
            else:
                # Continue to next
                progress_var.set(f"No match. Similarity: {similarity:.2f}")
                progress_window.after(100, start_auto_comparison)
        
        # Create buttons
        toggle_button = tk.Button(
            button_frame, text="Start", 
            command=toggle_running,
            padx=20, pady=5, bg="#e0ffe0", font=("Arial", 11)
        )
        toggle_button.pack(side=tk.LEFT, padx=10)
        
        close_button = tk.Button(
            button_frame, text="Close", 
            command=progress_window.destroy,
            padx=20, pady=5
        )
        close_button.pack(side=tk.LEFT, padx=10)

def main():
    root = tk.Tk()
    app = BoxDrawingSelector(root)
    root.mainloop()

if __name__ == "__main__":
    main()