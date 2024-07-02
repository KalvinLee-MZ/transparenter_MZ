import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
from rembg import remove
import os

# Define global variables
input_path = ""
processed_image = None
undo_stack = []
redo_stack = []
basedir = os.path.dirname(__file__)
manual_erase_active = False
eraser_size = 5
prev_x = None
prev_y = None
status_bar = None
magnifier_active = False
magnifier_radius = 50
magnifier_label = None
popup_window = None
remove_color_mode = None


# Function to select input file
def import_image():
    global input_path, processed_image

    # Ensure that undo and redo stacks are cleared first 
    # whenever a new image is uploaded
    undo_stack.clear()
    redo_stack.clear()

    selected_path = filedialog.askopenfilename(filetypes=[("Image files", "*.*")])

    if not selected_path:  # If the user cancels the file dialog, return early
        return
    
    input_path = selected_path  # Update input_path only if a file is selected

    supported_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]

    if not any(input_path.lower().endswith(ext) for ext in supported_extensions):
        messagebox.showerror("Error", "Please select a supported image file.")
        return

    try:
        processed_image = Image.open(input_path).convert("RGBA")
        max_size = (720, 720)
        processed_image.thumbnail(max_size, Image.LANCZOS)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to convert image to RGBA: {str(e)}")
        return

    display_processed_image(processed_image)
    status_bar.config(text="Image Uploaded")

# Function to remove background
def remove_background():
    global processed_image

    if not input_path:
        messagebox.showerror("Error", "Please upload an input image first.")
        return
    
    status_bar.config(text="Removing image background in progress")
    window.update() 

    try:
        #print("Before background removal:", processed_image)
        undo_stack.append(processed_image.copy())
        processed_image = remove(processed_image)
        #print("After background removal:", processed_image)
        display_processed_image(processed_image)
        status_bar.config(text="Image background removed")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        status_bar.config(text="Ready")

    # Check if processed_image is still None after background removal
    if processed_image is None:
        messagebox.showerror("Error", "Failed to remove background.")
        return

# Function to display processed image
def display_processed_image(image):
    formatted_img = ImageTk.PhotoImage(image)
    label_input_image.config(image=formatted_img)
    label_input_image.image = formatted_img
    window.geometry(f"{processed_image.width + 50}x{processed_image.height + 80}")

# Function to save processed image
def save_processed_image():
    global processed_image

    if processed_image:
        save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                  filetypes=[("PNG files", "*.png"),
                                                             ("All files", "*.*")])
        if save_path:
            processed_image.save(save_path)
            messagebox.showinfo("Success", "Processed image saved successfully.")
            status_bar.config(text="Image saved")
    else:
        messagebox.showerror("Error", "No processed image to save.")
        status_bar.config(text="Ready")

# Function to undo the last step
def undo():
    global processed_image, undo_stack

    if undo_stack:
        redo_stack.append(processed_image)
        processed_image = undo_stack.pop()
        display_processed_image(processed_image)
        status_bar.config(text="Undo action performed")
    else:
        messagebox.showinfo("Info", "Nothing to undo.")
        status_bar.config(text="Ready")

# Function to redo the last undone step
def redo():
    global processed_image, redo_stack

    if redo_stack:
        undo_stack.append(processed_image)
        processed_image = redo_stack.pop()
        display_processed_image(processed_image)
        status_bar.config(text="Redo action performed")
    else:
        messagebox.showinfo("Info", "Nothing to redo.")
        status_bar.config(text="Ready")

# Function to create a status bar
def create_status_bar():
    status_bar = tk.Label(window, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    return status_bar

# Function to activate manual erase mode
def activate_manual_erase():
    global manual_erase_active, eraser_size

    if not input_path:
        messagebox.showerror("Error", "Please upload an input image first.")
        return
    
    manual_erase_active = True
    select_eraser_size()
    if manual_erase_active: # Only show message if manual erase mode is active
        messagebox.showinfo("Manual Erase", "Manual erase mode activated. Click and drag on the image to erase.")
        status_bar.config(text="Eraser on")
        window.config(cursor="circle")  # Change cursor to a circle
    
# Function to deactivate manual erase mode
def deactivate_manual_erase():
    global manual_erase_active

    if not input_path:
        messagebox.showerror("Error", "Please upload an input image first.")
        return
    
    manual_erase_active = False
    messagebox.showinfo("Manual Erase", "Manual erase mode deactivated.")
    status_bar.config(text="Eraser off")
    window.config(cursor="arrow")  # Reset cursor to default arrow

# Function to start manual erasing
def start_erase(event):
    global manual_erase_active, prev_x, prev_y, eraser_size

    if manual_erase_active:
        prev_x, prev_y = event.x, event.y
        undo_stack.append(processed_image.copy())

# Function to select eraser size
def select_eraser_size():
    global eraser_size, manual_erase_active

    if not input_path:  # Check if an input image is selected
        messagebox.showerror("Error", "Please upload an input image first.")
        status_bar.config(text="Error")
        return

    if manual_erase_active:
        size = simpledialog.askinteger("Eraser Size", "Enter eraser size (1-20):", initialvalue=eraser_size)
        if size is not None:
            if 1 <= size <= 20:
                eraser_size = size
                status_bar.config(text=f"Eraser size changed (Size: {eraser_size})")
            else:
                messagebox.showerror("Error", "Please enter an eraser size between 1 to 20.")
                status_bar.config(text="Error: Invalid eraser size")           
        else:
            # If user clicked on "Cancel", deactivate manual erase mode
            manual_erase_active = False
            status_bar.config(text="Eraser off")
            window.config(cursor="arrow")  # Reset cursor to default arrow

# Function to manually erase parts of the image
def erase(event):
    global manual_erase_active, prev_x, prev_y, processed_image

    if manual_erase_active:
        current_x, current_y = event.x, event.y
        draw = ImageDraw.Draw(processed_image)
        draw.line([prev_x, prev_y, current_x, current_y], fill=(255, 255, 255, 0), width=eraser_size)
        prev_x, prev_y = current_x, current_y
        display_processed_image(processed_image)

        # Update the magnifier
        if magnifier_active:
            update_magnifier(event)

# Function to toggle magnifier activation
def toggle_magnifier():
    global magnifier_active

    if not input_path:
        messagebox.showerror("Error", "Please upload an input image first.")
        return
    
    magnifier_active = not magnifier_active
    status_bar.config(text="Magnifier activated" if magnifier_active else "Magnifier deactivated")
    if not magnifier_active:
        hide_magnifier()

# Function to handle mouse motion for updating the magnifier
def update_magnifier(event):
    global magnifier_active, processed_image, magnifier_label

    if magnifier_active and processed_image:
        mouse_x = event.x
        mouse_y = event.y

        # Ensure mouse is within the boundaries of the image
        if 0 <= mouse_x < processed_image.width and 0 <= mouse_y < processed_image.height:
            # Calculate the coordinates for the magnifier window
            magnifier_x = max(0, mouse_x - magnifier_radius)
            magnifier_y = max(0, mouse_y - magnifier_radius)
            magnifier_x_end = min(processed_image.width - 1, mouse_x + magnifier_radius)
            magnifier_y_end = min(processed_image.height - 1, mouse_y + magnifier_radius)

            # Extract the region under the magnifier
            magnified_region = processed_image.crop((magnifier_x, magnifier_y, magnifier_x_end, magnifier_y_end))

            # Resize the extracted region for magnification
            magnified_region = magnified_region.resize((magnifier_radius * 2, magnifier_radius * 2), Image.BICUBIC)

            # Display the magnified region
            display_magnified_image(magnified_region, mouse_x, mouse_y)

# Function to display the magnified region
def display_magnified_image(magnified_image, mouse_x, mouse_y):
    global magnifier_label

    # Resize the magnified region for magnification factor of 1.5
    magnified_image = magnified_image.resize((int(magnifier_radius * 3), int(magnifier_radius * 3)), Image.BICUBIC)

    # Update the magnifier label with the magnified image
    magnified_photo = ImageTk.PhotoImage(magnified_image)
    if magnifier_label:
        magnifier_label.config(image=magnified_photo)
        magnifier_label.image = magnified_photo
    else:
        magnifier_label = tk.Label(window, image=magnified_photo)
        magnifier_label.image = magnified_photo
        magnifier_label.pack()

    # Calculate the coordinates for placing the magnifier label
    label_x = mouse_x + magnifier_radius + 10  # Adjust the x-coordinate for spacing
    label_y = mouse_y + magnifier_radius + 10  # Adjust the y-coordinate for spacing

    # Place the magnifier label at the calculated coordinates
    magnifier_label.place(x=label_x, y=label_y)

# Function to hide the magnifier label when not in use
def hide_magnifier():
    global magnifier_label
    if magnifier_label:
        magnifier_label.place_forget()

# Function to handle right-click event and display popup menu
def popup_menu(event):
    global remove_color_mode

    popup = tk.Menu(window, tearoff=0)
    
    # Add labels from the tools menu to the popup menu
    popup.add_command(label="Remove Background", command=remove_background)

    erase_submenu = tk.Menu(popup, tearoff=0)
    popup.add_cascade(label="Erase", menu=erase_submenu)
    erase_submenu.add_command(label="Activate Manual Erase", command=activate_manual_erase)
    erase_submenu.add_command(label="Deactivate Manual Erase", command=deactivate_manual_erase)
    erase_submenu.add_separator()
    erase_submenu.add_command(label="Eraser Size", command=select_eraser_size)
    popup.add_separator()

    popup.add_command(label="Toggle Magnifier", command=toggle_magnifier)
    popup.add_separator()

    popup.add_command(label="Remove Lighter Colors", command=lambda: set_remove_color_mode("lighter"))
    popup.add_command(label="Remove Darker Colors", command=lambda: set_remove_color_mode("darker"))
    popup.add_separator()

    popup.add_command(label="Undo", command=undo)
    popup.add_command(label="Redo", command=redo)

    try:
        popup.tk_popup(event.x_root, event.y_root, 0)
    finally:
        popup.grab_release()

# Function to set the color removal mode
def set_remove_color_mode(mode):
    global remove_color_mode
    remove_color_mode = mode
    status_bar.config(text=f"Remove {mode.capitalize()} Colors mode activated. Click on an image pixel to select the threshold color.")
    window.config(cursor="tcross")  # Set cursor to cross

# Function to handle mouse click event for color selection
def select_color(event):
    global remove_color_mode

    if remove_color_mode:
        x, y = event.x, event.y
        pixel_color = processed_image.getpixel((x, y))
        status_bar.config(text=f"Selected color: {pixel_color}. Removing {remove_color_mode} colors...")
        window.update()

        if remove_color_mode == "lighter":
            remove_lighter_colors(pixel_color)
        elif remove_color_mode == "darker":
            remove_darker_colors(pixel_color)

        remove_color_mode = None

# Function to remove lighter colors based on a threshold color
def remove_lighter_colors(threshold_color):
    global processed_image

    # Save the current state of the image to the undo stack
    undo_stack.append(processed_image.copy())

    img = processed_image.copy()
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        remove_condition = all(item[i] > threshold_color[i] for i in range(3))
        if remove_condition:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    processed_image = img.copy()
    display_processed_image(processed_image)
    window.config(cursor="arrow")  # Set cursor back to arrow after operation end
    status_bar.config(text="Color removed")

# Function to remove darker colors based on a threshold color
def remove_darker_colors(threshold_color):
    global processed_image

    # Save the current state of the image to the undo stack
    undo_stack.append(processed_image.copy())

    img = processed_image.copy()
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        remove_condition = all(item[i] < threshold_color[i] for i in range(3))
        if remove_condition:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    processed_image = img.copy()
    display_processed_image(processed_image)
    window.config(cursor="arrow")  # Set cursor back to arrow after operation end
    status_bar.config(text="Color removed")

# Main window
window = tk.Tk()
window.title("Transparenter")
window.geometry("800x600")

# Window icon
basedir = os.path.dirname(__file__)
window.iconbitmap(os.path.join(basedir, "icon.ico"))

# Create Canvas for image display
frame_images = tk.Frame(window)
frame_images.pack(pady=10, padx=10, anchor="c")
label_input_image = tk.Label(frame_images)
label_input_image.pack(padx=10, pady=10)

# Create status bar
status_bar = create_status_bar()

# File menu
menu_bar = tk.Menu(window)
window.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Import Image", command=import_image)
file_menu.add_command(label="Save As", command=save_processed_image)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=window.quit)

# Edit menu
edit_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Edit", menu=edit_menu)
edit_menu.add_command(label="Undo", command=undo)
edit_menu.add_command(label="Redo", command=redo)


# Tool menu
tool_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Tool", menu=tool_menu)
tool_menu.add_command(label="Remove Background", command=remove_background)

erase_menu = tk.Menu(tool_menu, tearoff=0)
tool_menu.add_cascade(label="Erase", menu=erase_menu)
erase_menu.add_command(label="Activate Manual Erase", command=activate_manual_erase)
erase_menu.add_command(label="Deactivate Manual Erase", command=deactivate_manual_erase)
erase_menu.add_separator()
erase_menu.add_command(label="Eraser Size", command=select_eraser_size) 

tool_menu.add_command(label="Toggle Magnifier", command=toggle_magnifier)
tool_menu.add_separator()

tool_menu.add_command(label="Remove Lighter Colors", command=lambda: set_remove_color_mode("lighter"))
tool_menu.add_command(label="Remove Darker Colors", command=lambda: set_remove_color_mode("darker"))

# Bind right-click event to display popup menu
label_input_image.bind("<Button-3>", popup_menu)

# Bind mouse click event to start erase function and select color
label_input_image.bind("<Button-1>", lambda event: [start_erase(event),select_color(event)])

# Bind mouse movement event to erase function
label_input_image.bind("<B1-Motion>", erase)

# Bind mouse movement event to update the magnifier
label_input_image.bind("<Motion>", update_magnifier)

# shortcut keys
window.bind("<Control-z>", lambda event: undo())
window.bind("<Control-y>", lambda event: redo())
window.bind("<Control-s>", lambda event: save_processed_image())
window.bind("<Alt-F4>", lambda event: window.quit())

window.mainloop()
