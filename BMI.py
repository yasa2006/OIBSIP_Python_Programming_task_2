import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime
import random 

# --- Matplotlib Imports for Data Visualization ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np 
from PIL import Image, ImageTk

# --- Constants (Updated Colors) ---
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 650
CANVAS_BG = '#fff0f5' # Light Pink (Lavender Blush) for the animation canvas
MAIN_FRAME_BG = '#f0f4f8' # Light, clean background for the inner frame
HEADER_BG = '#5d00a0' # Deep Violet for the header
HEADER_FG = 'white'
BUTTON_COLOR = '#87cefa' # Light Sky Blue for the main button
HISTORY_FILE = 'bmi_history.json'
ANIMATION_SPEED = 50 # ms for animation refresh
ENTRY_BG = 'white'
ENTRY_FOCUS_COLOR = '#e9f7ff' # Light blue on focus

# Define Dark Pink for Underweight status
DARK_PINK = '#e60073' 

# --- Core Logic ---
def calculate_bmi(weight_kg, height_cm):
    """
    Calculates BMI (Body Mass Index).
    BMI = weight (kg) / (height (m) * height (m))
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Weight and height must be positive values.")
    
    # Convert height from cm to meters
    height_m = height_cm / 100
    
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)

def calculate_bmr(weight_kg, height_cm, age_years, gender):
    """
    Calculates Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.
    """
    # W = weight in kg, H = height in cm, A = age in years
    
    base_bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years)
    
    if gender == 'Male':
        bmr = base_bmr + 5
    elif gender == 'Female':
        bmr = base_bmr - 161
    else:
        # Fallback for undefined gender
        bmr = base_bmr
        
    return round(bmr)

def calculate_ideal_weight_range(height_cm):
    """
    Calculates the ideal weight range based on BMI range 18.5 to 24.9.
    """
    height_m = height_cm / 100
    
    # Target BMI 18.5 (low end of normal)
    low_weight = 18.5 * (height_m ** 2)
    
    # Target BMI 24.9 (high end of normal)
    high_weight = 24.9 * (height_m ** 2)
    
    return round(low_weight, 1), round(high_weight, 1)

def get_bmi_classification(bmi):
    """
    Classifies the BMI and provides associated advice.
    The Underweight color has been updated to DARK_PINK.
    """
    if bmi < 18.5:
        category = "Underweight"
        color = DARK_PINK # Changed from Yellow to Dark Pink
        advice = "Focus on a nutrient-rich diet to gain weight safely."
    elif 18.5 <= bmi <= 24.9:
        category = "Normal Weight"
        color = "#28a745" # Green
        advice = "Maintain your current healthy habits. Excellent!"
    elif 25.0 <= bmi <= 29.9:
        category = "Overweight"
        color = "#fd7e14" # Orange
        advice = "Consider consulting a doctor or dietitian to manage weight."
    else: # bmi >= 30.0
        category = "Obese"
        color = "#dc3545" # Red
        advice = "It is highly recommended to seek professional health guidance immediately."
        
    return category, color, advice

def generate_diet_plan(category, bmr, age):
    """
    Generates a basic diet plan and caloric goal based on BMI category and BMR.
    """
    daily_goal_kcal = bmr
    plan_title = ""
    diet_focus = ""
    macro_split = "Protein: 25%, Carbs: 45%, Fats: 30%"
    meal_suggestions = []

    if category in ["Overweight", "Obese"]:
        daily_goal_kcal = max(1200, bmr - 500) 
        plan_title = f"Weight Management Plan ({category})"
        diet_focus = f"Your primary goal is to safely achieve a sustainable calorie deficit to promote weight loss. We estimate your daily goal to be **{daily_goal_kcal} kcal**."
        meal_suggestions = [
            "Prioritize lean proteins (chicken breast, fish, tofu) and high-fiber foods.",
            "Choose complex carbohydrates (oats, brown rice, whole wheat) over simple sugars.",
            "Focus on large portions of non-starchy vegetables at every meal.",
            "Drink plenty of water (2-3 liters) and limit sugary drinks."
        ]
    elif category == "Underweight":
        daily_goal_kcal = bmr + 300 
        plan_title = f"Healthy Weight Gain Plan ({category})"
        diet_focus = f"Your goal is to increase caloric intake safely and nutrient-densely to reach a healthy weight. We estimate your daily goal to be **{daily_goal_kcal} kcal**."
        meal_suggestions = [
            "Eat 5-6 smaller, frequent meals throughout the day.",
            "Incorporate healthy fats (nuts, seeds, avocado, olive oil) and starches (potatoes, sweet potatoes).",
            "Focus on protein and complex carbs post-workout to support muscle and mass gain.",
            "Use full-fat dairy or dairy alternatives for extra calories."
        ]
    else: # Normal Weight
        daily_goal_kcal = bmr + 200
        plan_title = f"Maintenance & Wellness Plan ({category})"
        diet_focus = f"Continue your balanced eating habits to maintain your healthy weight. We estimate your daily goal to be around **{daily_goal_kcal} kcal**."
        meal_suggestions = [
            "Maintain diversity: eat a wide range of colorful fruits and vegetables.",
            "Balance protein, fats, and carbs in every meal.",
            "Limit processed snacks and excessive alcohol.",
            "Stay consistent with portion sizes based on your activity level."
        ]
    
    if age >= 50:
        macro_split = "Protein: 30%, Carbs: 40%, Fats: 30% (Higher protein supports muscle mass retention)"

    return {
        'title': plan_title,
        'goal_kcal': daily_goal_kcal,
        'focus': diet_focus,
        'macros': macro_split,
        'suggestions': meal_suggestions
    }


# --- GUI Application Class ---
class BMICalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BMI Calculator")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.config(bg=CANVAS_BG) 

        # Tkinter Variables
        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.gender_var = tk.StringVar(value='Male')
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()
        
        self.last_metrics = None 

        # Animation Variables
        self.animation_y = 0

        self.history = self._load_history() 
        self.workout_image = None # To hold the reference to the workout image
        self._setup_ui()
        self._animate_background() 

    # --- Data Loading/Saving Methods ---
    def _load_history(self):
        """Loads BMI history from a JSON file."""
        if os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 0:
            try:
                with open(HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_history(self, entry):
        """Saves a new BMI entry to the history list and JSON file."""
        self.history.append(entry)
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=4)
        except IOError:
            messagebox.showerror("File Error", "Could not save BMI history to file.")
            
    def clear_history(self, history_window):
        """
        Clears all BMI history records and the history file after user confirmation.
        """
        if messagebox.askyesno(
            "Confirm Clear History", 
            "Are you sure you want to permanently delete ALL recorded history? This action cannot be undone."
        ):
            self.history = []
            try:
                with open(HISTORY_FILE, 'w') as f:
                    json.dump([], f)
                
                messagebox.showinfo("History Cleared", "All BMI history records have been successfully deleted.")
                history_window.destroy()

            except IOError:
                messagebox.showerror("File Error", "Could not clear BMI history file.")


    # --- Input Validation and Focus Handlers ---
    def _on_focus_in(self, event):
        """Changes entry background color when widget gains focus."""
        event.widget.config(bg=ENTRY_FOCUS_COLOR)

    def _on_focus_out(self, event):
        """Changes entry background color when widget loses focus."""
        event.widget.config(bg=ENTRY_BG)
    
    def _validate_input(self, new_value):
        """Allows only digits and a single decimal point."""
        if new_value == "":
            return True
        
        try:
            float(new_value)
            if new_value.count('.') > 1:
                return False
            return True
        except ValueError:
            return False

    def _validate_int(self, new_value):
        """Allows only digits for age."""
        if new_value == "":
            return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False

    # --- Animation (Light Red/Pink Theme) ---
    def _animate_background(self):
        """Creates a subtle, floating bubble animation in the background canvas."""
        # 1. Clear previous drawings
        self.bg_canvas.delete("animation_elements")

        # Define light red/pink colors for animation
        bubble_fill = '#ffc0cb' # Pink
        bubble_outline = '#ff9999' # Light Coral

        # 2. Draw 5 floating bubbles
        for i in range(5):
            x = (i * WINDOW_WIDTH / 5) + (random.randint(10, 50) if i % 2 == 0 else -random.randint(10, 50))
            y = (self.animation_y + i * 100 + WINDOW_HEIGHT) % (WINDOW_HEIGHT + 200) - 100
            radius = 20 + (i % 3) * 5 

            self.bg_canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                outline=bubble_outline, fill=bubble_fill, tags="animation_elements", 
                width=2, stipple="gray50" 
            )
        
        # 3. Increment Y position for movement (simulating upward flow)
        self.animation_y = (self.animation_y + 1) % 200 
        
        # 4. Schedule the next animation frame
        self.root.after(ANIMATION_SPEED, self._animate_background)

    # --- UI Setup (Light Blue/Violet Buttons) ---
    def _setup_ui(self):
        # --- Header Canvas ---
        self.header_canvas = tk.Canvas(self.root, height=50, bg=HEADER_BG, highlightthickness=0)
        self.header_canvas.pack(fill='x')
        self.header_canvas.create_text(
            WINDOW_WIDTH / 2, 25, 
            text="📏 BODY & HEALTH CALCULATOR", 
            fill=HEADER_FG, 
            font=("Arial", 14, "bold")
        )

        # --- Animated Background Canvas ---
        self.bg_canvas = tk.Canvas(self.root, bg=CANVAS_BG, highlightthickness=0)
        self.bg_canvas.pack(fill='both', expand=True)

        # --- Main Content Frame ---
        main_content_frame = tk.Frame(self.bg_canvas, padx=20, pady=10, bg=MAIN_FRAME_BG, bd=5, relief=tk.RAISED)
        main_content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.9, relheight=0.95)

        # --- Inputs organized by Grid ---
        input_frame = tk.Frame(main_content_frame, bg=MAIN_FRAME_BG)
        input_frame.pack(pady=10)
        
        vcmd_float = self.root.register(self._validate_input)
        vcmd_int = self.root.register(self._validate_int)

        inputs = [
            ("Name:", self.name_var, None),
            ("Age (years):", self.age_var, vcmd_int),
            ("Weight (kg):", self.weight_var, vcmd_float),
            ("Height (cm):", self.height_var, vcmd_float),
        ]
        
        for i, (label_text, var, vcmd) in enumerate(inputs):
            tk.Label(input_frame, text=label_text, font=("Arial", 12), bg=MAIN_FRAME_BG, fg="#333").grid(row=i, column=0, sticky='w', padx=5, pady=5)
            
            entry = tk.Entry(input_frame, textvariable=var, width=15, font=("Arial", 12), justify='center', bg=ENTRY_BG)
            if vcmd:
                entry.config(validate='key', validatecommand=(vcmd, '%P'))
            
            entry.grid(row=i, column=1, sticky='e', padx=5, pady=5)
            entry.bind("<FocusIn>", self._on_focus_in)
            entry.bind("<FocusOut>", self._on_focus_out)
            if label_text == "Name:":
                entry.focus_set()

        # Gender Input (OptionMenu)
        tk.Label(input_frame, text="Gender:", font=("Arial", 12), bg=MAIN_FRAME_BG, fg="#333").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        gender_options = ["Male", "Female"]
        self.gender_menu = tk.OptionMenu(input_frame, self.gender_var, *gender_options)
        self.gender_menu.config(width=12, font=("Arial", 10), bg=ENTRY_BG, bd=1, relief=tk.FLAT)
        self.gender_menu.grid(row=4, column=1, sticky='e', padx=5, pady=5)
        
        # 3. Calculate Button (Light Blue)
        tk.Button(main_content_frame, text="Calculate All Metrics", command=self.calculate_bmi_gui,
                  bg=BUTTON_COLOR, fg='white', font=("Arial", 12, "bold"), 
                  activebackground="#6495ed", activeforeground="white", # Deeper Blue on click
                  relief='raised', bd=3).pack(pady=(15, 10))
        
        # 4. Diet Plan Button (Violet)
        self.diet_plan_button = tk.Button(main_content_frame, text="Generate Diet & Calorie Goal", 
                                          command=self.open_diet_plan_window,
                                          bg='#9370db', fg='white', font=("Arial", 10), # Medium Purple/Violet
                                          activebackground="#4b0082", activeforeground="white", # Indigo on click
                                          state=tk.DISABLED)
        self.diet_plan_button.pack(pady=(0, 10))


        # 5. History Button (Lighter Blue)
        tk.Button(main_content_frame, text="View History, Stats, & Trends", command=self.view_history,
                  bg='#add8e6', fg='#333', font=("Arial", 10), # Light Blue
                  activebackground="#4682b4", activeforeground="white", # Steel Blue on click
                  ).pack(pady=(0, 20))

        # --- Results Display ---
        
        # BMR and Ideal Weight Results
        self.bmr_label = tk.Label(main_content_frame, text="BMR: N/A kcal/day", font=("Arial", 11, "bold"), bg=MAIN_FRAME_BG, fg="#0056b3")
        self.bmr_label.pack(pady=(0, 5))
        
        self.ideal_weight_label = tk.Label(main_content_frame, text="Ideal Weight Range: N/A kg", font=("Arial", 11, "bold"), bg=MAIN_FRAME_BG, fg="#0056b3")
        self.ideal_weight_label.pack(pady=(0, 10))

        # BMI Results
        self.bmi_label = tk.Label(main_content_frame, text="Your BMI: N/A", font=("Arial", 16, "bold"), bg=MAIN_FRAME_BG, fg="#333")
        self.bmi_label.pack()
        
        self.category_label = tk.Label(main_content_frame, text="Category: ", font=("Arial", 14), bg=MAIN_FRAME_BG)
        self.category_label.pack(pady=(5, 5))
        
        self.advice_label = tk.Label(main_content_frame, text="", font=("Arial", 10, "italic"), bg=MAIN_FRAME_BG, wraplength=350, justify='center')
        self.advice_label.pack()


    # --- Diet Plan Window ---
    def open_diet_plan_window(self):
        if not self.last_metrics:
            messagebox.showwarning("Metrics Missing", "Please run a calculation first to generate a diet plan.")
            return

        plan_data = generate_diet_plan(
            self.last_metrics['category'],
            self.last_metrics['bmr'],
            self.last_metrics['age_years']
        )

        diet_window = tk.Toplevel(self.root)
        diet_window.title(plan_data['title'])
        diet_window.geometry("450x450")
        diet_window.config(bg=MAIN_FRAME_BG)
        diet_window.resizable(False, False)
        
        # --- Load and display workout image ---
        try:
            # Load the image using Pillow
            img = Image.open("workout.png")
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            
            # Keep a reference to avoid garbage collection
            self.workout_image = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(diet_window, image=self.workout_image, bg=MAIN_FRAME_BG)
            img_label.place(relx=0.98, rely=0.98, anchor='se')

        except FileNotFoundError:
            # If image is not found, just print a message to console and continue
            print("workout.png not found. Skipping image display.")

        # Center the new window over the main window
        x = self.root.winfo_x() + (self.root.winfo_width() - 450) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 450) // 2
        diet_window.geometry(f'+{x}+{y}')

        # Title
        tk.Label(diet_window, text=plan_data['title'], 
                 font=("Arial", 14, "bold"), bg=HEADER_BG, fg=HEADER_FG).pack(fill='x', pady=(0, 10))

        content_frame = tk.Frame(diet_window, bg=MAIN_FRAME_BG, padx=15, pady=10)
        content_frame.pack(fill='both', expand=True)

        # Calorie Goal
        tk.Label(content_frame, text="🔥 Daily Calorie Goal (TDEE Estimate)", 
                 font=("Arial", 11, "bold"), bg=MAIN_FRAME_BG, fg='#0056b3').pack(anchor='w', pady=(5, 0))
        tk.Label(content_frame, text=f"{plan_data['goal_kcal']:.0f} kcal", 
                 font=("Arial", 24, "bold"), bg=MAIN_FRAME_BG, fg='#dc3545').pack(pady=(0, 10))
        
        # Focus
        tk.Label(content_frame, text="🎯 Plan Focus:", font=("Arial", 11, "bold"), 
                 bg=MAIN_FRAME_BG, fg='#28a745').pack(anchor='w', pady=(5, 0))
        tk.Label(content_frame, text=plan_data['focus'], font=("Arial", 10), 
                 bg=MAIN_FRAME_BG, wraplength=400, justify='left').pack(anchor='w')

        # Macros
        tk.Label(content_frame, text="📊 Suggested Macro Split:", font=("Arial", 11, "bold"), 
                 bg=MAIN_FRAME_BG, fg='#0056b3').pack(anchor='w', pady=(10, 0))
        tk.Label(content_frame, text=plan_data['macros'], font=("Arial", 10, 'italic'), 
                 bg=MAIN_FRAME_BG).pack(anchor='w')

        # Suggestions
        tk.Label(content_frame, text="🥦 Meal Strategy:", font=("Arial", 11, "bold"), 
                 bg=MAIN_FRAME_BG, fg='#28a745').pack(anchor='w', pady=(10, 0))
        
        # Display suggestions as list
        for i, suggestion in enumerate(plan_data['suggestions']):
             tk.Label(content_frame, text=f"• {suggestion}", font=("Arial", 9), 
                      bg=MAIN_FRAME_BG, wraplength=400, justify='left').pack(anchor='w')
        
        tk.Label(diet_window, text="*Consult a healthcare professional before starting any new diet.", 
                 font=("Arial", 8, "italic"), bg=MAIN_FRAME_BG, fg='gray').pack(pady=10)


    # --- Calculation Handlers ---
    def calculate_bmi_gui(self):
        try:
            # Get and validate input values
            name_str = self.name_var.get().strip()
            age_str = self.age_var.get()
            gender_str = self.gender_var.get()
            weight_str = self.weight_var.get()
            height_str = self.height_var.get()

            # Input validation
            if not name_str:
                messagebox.showwarning("Input Error", "Please enter your name.")
                return
            if not age_str or int(age_str) <= 0:
                messagebox.showwarning("Input Error", "Please enter a valid age (> 0).")
                return
            if not weight_str or not height_str:
                messagebox.showwarning("Input Error", "Please enter values for both weight and height.")
                return

            age_years = int(age_str)
            weight_kg = float(weight_str)
            height_cm = float(height_str)
            
            if weight_kg <= 0 or height_cm <= 0:
                 messagebox.showwarning("Input Error", "Please enter positive values for weight and height.")
                 return

            # --- 1. Perform Calculation ---
            bmi_value = calculate_bmi(weight_kg, height_cm)
            category, color, advice = get_bmi_classification(bmi_value)
            
            # --- 2. Calculate BMR and Ideal Weight (New Metrics) ---
            bmr_value = calculate_bmr(weight_kg, height_cm, age_years, gender_str)
            low_ideal, high_ideal = calculate_ideal_weight_range(height_cm)

            # --- 3. Record and save the new history entry ---
            new_entry = {
                'name': name_str,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'weight_kg': weight_kg,
                'height_cm': height_cm,
                'bmi': bmi_value,
                'category': category,
            }
            self._save_history(new_entry)

            # --- 4. Store metrics for Diet Plan ---
            self.last_metrics = {
                'category': category,
                'bmr': bmr_value,
                'age_years': age_years
            }

            # --- 5. Update GUI labels and enable Diet Plan Button ---
            
            # BMR and Ideal Weight Updates
            self.bmr_label.config(text=f"BMR: {bmr_value} kcal/day", fg="#0056b3")
            self.ideal_weight_label.config(text=f"Ideal Weight Range: {low_ideal} - {high_ideal} kg", fg="#0056b3")

            # BMI Updates
            self.bmi_label.config(text=f"Your BMI: {bmi_value}", fg=color)
            self.category_label.config(text=f"Category: {category}", fg=color)
            self.advice_label.config(text=advice, fg="#555")
            
            # Enable the diet plan button
            self.diet_plan_button.config(state=tk.NORMAL)


        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all fields contain valid numerical data (Age, Weight, Height).")
        except Exception as e:
            messagebox.showerror("An Error Occurred", f"An unexpected error happened: {e}")

    # --- Dashboard Helper Methods ---
    def _calculate_statistics(self):
        """Calculates key statistics from the BMI history."""
        if not self.history:
            return {
                'count': 0,
                'avg_bmi': 'N/A',
                'min_bmi': 'N/A',
                'max_bmi': 'N/A',
            }
        
        bmis = [entry['bmi'] for entry in self.history]
        
        return {
            'count': len(bmis),
            'avg_bmi': f"{sum(bmis) / len(bmis):.2f}",
            'min_bmi': f"{min(bmis):.2f}",
            'max_bmi': f"{max(bmis):.2f}",
        }

    def _display_statistics(self, frame):
        """Creates the statistics summary section."""
        stats = self._calculate_statistics()
        
        tk.Label(frame, text="Summary Statistics", font=("Arial", 12, "bold"), 
                 bg='#e0e0e0', anchor='w').pack(fill='x', pady=(0, 5))

        stats_frame = tk.Frame(frame, bg='#e0e0e0', padx=10, pady=5)
        stats_frame.pack(fill='x')
        
        data = [
            ("Total Records:", stats['count']),
            ("Average BMI:", stats['avg_bmi']),
            ("Lowest BMI:", stats['min_bmi']),
            ("Highest BMI:", stats['max_bmi']),
        ]

        for i, (label, value) in enumerate(data):
            tk.Label(stats_frame, text=label, bg='#e0e0e0', font=("Arial", 10)).grid(row=i, column=0, sticky='w')
            tk.Label(stats_frame, text=value, bg='#e0e0e0', font=("Arial", 10, 'bold')).grid(row=i, column=1, sticky='e', padx=(50, 0))
            stats_frame.grid_columnconfigure(1, weight=1) 

    def _generate_bmi_plot(self, frame):
        """Generates a matplotlib line graph of BMI trend over time."""
        
        # Check for history entries
        if len(self.history) < 2:
            tk.Label(frame, text="Need at least 2 records to show a trend graph.", font=("Arial", 10, "italic"), bg=MAIN_FRAME_BG).pack(expand=True, fill='both', pady=20)
            return

        # Prepare data
        dates = [datetime.strptime(entry['date'].split(" ")[0], "%Y-%m-%d") for entry in self.history]
        bmis = [entry['bmi'] for entry in self.history]

        # 1. Create the Matplotlib Figure
        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=MAIN_FRAME_BG)
        ax = fig.add_subplot(111)
        
        # 2. Plot the data
        ax.plot(dates, bmis, marker='o', linestyle='-', color='#0056b3', linewidth=2)
        
        # 3. Add BMI Classification Zones (Shading)
        # Assuming BMI data is generally under 40 for a clean plot
        max_y = max(max(bmis) + 5, 35) # Ensure the top is visible even if max BMI is low
        
        ax.axhspan(0, 18.5, facecolor=DARK_PINK, alpha=0.15, label='Underweight')
        ax.axhspan(18.5, 24.9, facecolor='#28a745', alpha=0.15, label='Normal')
        ax.axhspan(25.0, 29.9, facecolor='#fd7e14', alpha=0.15, label='Overweight')
        ax.axhspan(30.0, max_y, facecolor='#dc3545', alpha=0.15, label='Obese')
        
        # 4. Formatting
        ax.set_title('BMI Trend Over Time', fontsize=12, color='#333')
        ax.set_xlabel('Date', fontsize=10, color='#555')
        ax.set_ylabel('BMI Value', fontsize=10, color='#555')
        
        # Format the date ticks
        fig.autofmt_xdate(rotation=45, ha='right')
        
        # Set y-axis limits dynamically
        min_bmi = min(bmis)
        ax.set_ylim(max(0, min_bmi - 2), max_y) 

        ax.grid(True, linestyle='--', alpha=0.6)
        
        # 5. Embed the plot into the Tkinter frame
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True)
        canvas.draw()


    def view_history(self):
        """Opens a new window to display the recorded BMI history, stats, and trend chart."""
        self.history = self._load_history() 
        
        history_window = tk.Toplevel(self.root)
        history_window.title("BMI History & Trends")
        history_window.geometry("750x600") 
        history_window.config(bg=MAIN_FRAME_BG)
        history_window.resizable(True, True)

        tk.Label(history_window, 
                 text="📊 BMI TRACKING DASHBOARD", 
                 font=("Arial", 16, "bold"), 
                 bg=HEADER_BG, fg=HEADER_FG).pack(fill='x', pady=5)
        
        if not self.history:
            tk.Label(history_window, text="No history recorded yet. Calculate your first BMI!", bg=MAIN_FRAME_BG, fg="#555").pack(pady=20)
            
            
            tk.Button(history_window, text="🚨 Clear All History Records 🚨", 
                      command=lambda: self.clear_history(history_window),
                      bg='#dc3545', fg='white', font=("Arial", 10, "bold")).pack(pady=10)
            return

        
        top_frame = tk.Frame(history_window, bg=MAIN_FRAME_BG)
        top_frame.pack(fill='x', padx=10, pady=5)
        
        
        stats_frame = tk.Frame(top_frame, bg='#e0e0e0', bd=2, relief=tk.SUNKEN, width=300, height=250)
        stats_frame.pack(side='left', fill='y', padx=(0, 10))
        stats_frame.pack_propagate(False)
        self._display_statistics(stats_frame)

        
        plot_frame = tk.Frame(top_frame, bg=MAIN_FRAME_BG, bd=2, relief=tk.SUNKEN)
        plot_frame.pack(side='left', fill='both', expand=True) 
        self._generate_bmi_plot(plot_frame)
        
        
        tk.Label(history_window, text="Full Measurement History", font=("Arial", 12, "bold"), 
                 bg='#e0e0e0', anchor='w').pack(fill='x', padx=10, pady=(10, 5))

        
        canvas_history = tk.Canvas(history_window, bg=MAIN_FRAME_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(history_window, orient="vertical", command=canvas_history.yview)
        scrollable_frame = tk.Frame(canvas_history, bg=MAIN_FRAME_BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_history.configure(
                scrollregion=canvas_history.bbox("all")
            )
        )

        canvas_history.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_history.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas_history.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # --- Create Table Headers ---
        headers = ["Date", "Name", "Weight (kg)", "Height (cm)", "BMI", "Category"]
        for col, header in enumerate(headers):
            tk.Label(scrollable_frame, text=header, 
                     font=("Arial", 10, "bold"), 
                     bg="#b3d4ff", width=12, relief='raised', borderwidth=1).grid(row=0, column=col, sticky="nsew")

        # --- Populate Table Rows ---
        for row_index, entry in enumerate(self.history):
            _, color, _ = get_bmi_classification(entry['bmi'])
            
            data = [
                entry['date'].split(" ")[0],
                entry.get('name', 'N/A'),
                f"{entry['weight_kg']:.1f}",
                f"{entry['height_cm']:.0f}",
                f"{entry['bmi']:.2f}",
                entry['category']
            ]
            
            for col, item in enumerate(data):
                tk.Label(scrollable_frame, text=item, 
                         font=("Arial", 9), 
                         bg=MAIN_FRAME_BG, fg=color, 
                         width=12, relief='flat', borderwidth=0).grid(row=row_index + 1, column=col, sticky="nsew", pady=2)
                
        # --- Clear History Button (Alert/Destructive Action color kept red) ---
        tk.Button(history_window, text="🚨 Clear All History Records 🚨", 
                  command=lambda: self.clear_history(history_window),
                  bg='#dc3545', fg='white', font=("Arial", 10, "bold"), 
                  activebackground="#c82333", activeforeground="white").pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed') # Make the window full screen
    app = BMICalculatorApp(root)
    root.mainloop()