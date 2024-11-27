import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import time
import google.generativeai as genai
import os
import re

# Configure Gemini API
genai.configure(api_key="API key here")

def parse_gemini_response(response_text):
    """Parse the Gemini response into structured data."""
    data = {
        'person1': '',
        'person2': '',
        'tone': '',
        'title': '',
        'summary': ''
    }
    
    # Extract information using regular expressions
    person_match = re.search(r'Person(?:\s+)?1?:?\s*([^\n]+)', response_text)
    person2_match = re.search(r'Person\s*2:?\s*([^\n]+)', response_text)
    tone_match = re.search(r'Tone:?\s*([^\n]+)', response_text)
    title_match = re.search(r'Title:?\s*([^\n]+)', response_text)
    summary_match = re.search(r'Summary:?\s*(.+)', response_text, re.DOTALL)
    
    if person_match:
        data['person1'] = person_match.group(1).strip()
    if person2_match:
        data['person2'] = person2_match.group(1).strip()
    if data['person2']=='':
        # If Person 2 isn't found, look for a single Person entry
        single_person = re.search(r'Person:?\s*([^\n]+)', response_text)
        if single_person:
            data['person1'] = single_person.group(1).strip()
            data['person2'] = "Other participant"
        data['person2'] = "You (sender)"
    
    if tone_match:
        data['tone'] = tone_match.group(1).strip()
    if title_match:
        data['title'] = title_match.group(1).strip()
    if summary_match:
        data['summary'] = summary_match.group(1).strip()
    
    return data

def create_structured_output(frame):
    """Create the structured output layout with fixed headings."""
    # Create a container frame for the structured output
    output_frame = tk.Frame(frame, bg="black", padx=20, pady=10)
    output_frame.pack(fill="both", expand=True)
    
    # Define headings and create labels
    headings = {
        'person1': "Person 1:",
        'person2': "Person 2:",
        'tone': "Tone:",
        'title': "Title:",
        'summary': "Summary:"
    }
    
    labels = {}
    content_labels = {}
    
    for key, heading in headings.items():
        # Create a frame for each row
        row_frame = tk.Frame(output_frame, bg="black")
        row_frame.pack(fill="x", pady=5, anchor="w")
        
        # Heading label (left side)
        labels[key] = tk.Label(
            row_frame,
            text=heading,
            font=("Courier", 12, "bold"),
            fg="#FF00FF",
            bg="black",
            width=10,
            anchor="w"
        )
        labels[key].pack(side="left", padx=(0, 10))
        
        # Content label (right side)
        content_labels[key] = tk.Label(
            row_frame,
            text="",
            font=("Arial", 12),
            fg="white",
            bg="black",
            wraplength=300,
            justify="left",
            anchor="w"
        )
        content_labels[key].pack(side="left", fill="x", expand=True)
    
    return content_labels

def display_gemini_response(response_text, status_frame):
    """Displays the Gemini API response in the structured format."""
    # Clear previous content except upload button and status frame
    for widget in right_frame.winfo_children():
        if widget not in [upload_button, status_frame]:
            widget.destroy()
    
    # Create saved message label
    saved_message_label = tk.Label(
        status_frame,
        text="",
        font=("Courier", 10, "bold"),
        fg="#00FF00",
        bg="black",
        anchor="e"
    )
    saved_message_label.pack(side="top", anchor="e", padx=10, pady=(2, 5))
    
    # Create and get content labels
    content_labels = create_structured_output(right_frame)
    
    # Parse the response
    parsed_data = parse_gemini_response(response_text)
    
    def type_text(field_name, text, index=0):
        if index < len(text):
            current_text = content_labels[field_name].cget("text")
            content_labels[field_name].config(text=current_text + text[index])
            right_frame.after(23, type_text, field_name, text, index + 1)
        elif field_name == 'summary':  # After all text is typed
            saved_message_label.config(text="The result has been saved ✓")
    
    # Start typing animation for each field
    delay = 0
    for field, content in parsed_data.items():
        right_frame.after(delay, type_text, field, content)
        delay += len(content) * 17  # Adjust delay based on content length

def upload_screenshot():
    """Opens a file dialog to choose a screenshot, displays it with animation, and sends it to Gemini API."""
    # Clear previous image and response, but keep the upload button
    for widget in left_frame.winfo_children():
        if widget.winfo_class() != "Button":  # Keep the upload button
            widget.destroy()
    for widget in right_frame.winfo_children():
        if widget not in [upload_button]:  # Keep the upload button
            widget.destroy()

    # Create a status frame at the top of the right frame
    status_frame = tk.Frame(right_frame, bg="black")
    status_frame.pack(side="top", fill="x", pady=(10, 0))

    file_path = filedialog.askopenfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )
    if not file_path:
        return  # No file selected

    try:
        # Load the image and set up initial dimensions for zoom effect
        img = Image.open(file_path)
        img.thumbnail((700, 700))  # Full size limit

        # Calculate center position based on the final size
        img_width, img_height = img.size
        center_x = (left_frame.winfo_width() - img_width) // 2
        center_y = (left_frame.winfo_height() - img_height) // 2

        # Create a label to hold the image
        image_label = tk.Label(left_frame)
        image_label.pack()

        # Animation loop to grow from center outwards
        for scale in range(10, 101, 5):  # Start from 10% to 100%
            # Calculate current size
            current_width = img_width * scale // 100
            current_height = img_height * scale // 100

            # Resize image
            img_resized = img.resize((current_width, current_height))

            # Apply blur based on scale (strong blur at the beginning, clear at end)
            blur_level = 5 - (scale / 20)  # Reduced blur gradually
            img_effect = img_resized.filter(ImageFilter.GaussianBlur(blur_level))

            # Apply sharpen effect gradually
            enhancer = ImageEnhance.Sharpness(img_effect)
            img_effect = enhancer.enhance(scale / 100)

            # Convert to PhotoImage and set to label
            photo = ImageTk.PhotoImage(img_effect)
            image_label.config(image=photo)
            image_label.image = photo  # Keep reference to avoid garbage collection

            # Place image at centered position with resizing offset
            offset_x = center_x + (img_width - current_width) // 2
            offset_y = center_y + (img_height - current_height) // 2
            image_label.place(x=offset_x, y=offset_y)

            # Update window and delay for smooth animation
            window.update()
            time.sleep(0.03)

        # Set the final, clear image
        final_photo = ImageTk.PhotoImage(img)
        image_label.config(image=final_photo)
        image_label.image = final_photo
        image_label.place(x=center_x, y=center_y)

        # Create result folder
        result_folder = "Result"
        os.makedirs(result_folder, exist_ok=True)
        unique_folder = os.path.join(result_folder, f"result_{int(time.time())}")
        os.makedirs(unique_folder, exist_ok=True)

        # Save the image to the folder
        img.save(os.path.join(unique_folder, "uploaded_image.png"))

        # Status messages in matrix green with tick marks
        display_status_message("The image has been processed ✓", status_frame, 2000)
        display_status_message("Sent to AI processing ✓", status_frame, 3500)

        # Send the image to Gemini and display the result
        right_frame.after(3500, lambda: send_to_gemini(file_path, unique_folder, status_frame))

    except Exception as e:
        print(f"Error loading image: {e}")
        messagebox.showerror("Error", "Could not load the image.")




def display_status_message(message, status_frame, delay=0):
    """Displays status messages with delays in matrix green in the status frame."""
    status_label = tk.Label(
        status_frame,
        text=message,
        font=("Courier", 10, "bold"),
        fg="#00FF00",
        bg="black",
        anchor="e"
    )
    right_frame.after(delay, status_label.pack, {"side": "top", "anchor": "e", "padx": 10, "pady": 2})

def send_to_gemini(file_path, unique_folder, status_frame):
    """Sends the uploaded image to the Gemini API and displays the output in the right frame."""
    try:
        with open(file_path, "rb") as img_file:
            organ = Image.open(img_file)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(["give name of person, tone, good funny sarcastic title for conversation and summary of the chat", organ])

            with open(os.path.join(unique_folder, "output.txt"), "w") as output_file:
                output_file.write(response.text)

            # Display response with typing effect, passing the status frame
            display_gemini_response(response.text, status_frame)

    except genai.errors.APIError as e:
        print(f"API Error: {e}")
        messagebox.showerror("API Error", "Failed to process image with Gemini API.")
    except Exception as e:
        print(f"Unexpected Error: {e}")
        messagebox.showerror("Error", "An unexpected error occurred.")

def on_enter(event):
    upload_button.config(
        bg="#ff00ff",
        fg="#000000",
        relief="groove",
        highlightbackground="#00ffff",
        font=("Orbitron", 12, "bold")
    )

def on_leave(event):
    upload_button.config(
        bg="#0d0d0d",
        fg="#00ffff",
        relief="flat",
        highlightbackground="#ff00ff"
    )

# Create the main window
window = tk.Tk()
window.title("chatPersona")
window.geometry("900x750")
window.configure(bg="#1a1a1a")

# Create frames for layout
left_frame = tk.Frame(window, width=400, height=700, bg="white")
left_frame.pack(side="left", fill="y")

right_frame = tk.Frame(window, width=450, height=700, bg="black")
right_frame.pack(side="right", fill="both", expand=True)

# Create upload button
upload_button = tk.Button(
    right_frame,
    text="Upload Screenshot",
    command=upload_screenshot,
    font=("Orbitron", 12, "bold"),
    bg="#0d0d0d",
    fg="#00ffff",
    activebackground="#ff00ff",
    activeforeground="#000000",
    relief="flat",
    bd=2,
    width=20,
    height=2,
    cursor="hand2",
    highlightthickness=2,
    highlightbackground="#ff00ff",
    highlightcolor="#ff00ff"
)

# Apply hover effects
upload_button.bind("<Enter>", on_enter)
upload_button.bind("<Leave>", on_leave)

# Center the button and add padding
upload_button.pack(pady=50)
upload_button.config(padx=10, pady=5)

window.mainloop()