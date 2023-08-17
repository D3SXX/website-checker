# Website checker v0.1 alpha build 3 by D3SXX  

import tkinter as tk
from tkinter import ttk 
import requests
import website_processing

def fill_website_entry():
    website_entry.delete(0, tk.END)
    website_entry.insert(0, "https://hinta.fi/")

def add_website_content():
    global old_website, old_text, entry_xl,items_amount_old,website_content_listbox
    entry_xl_new = []
    website = website_entry.get()
    if len(website) < 1:
        website = old_website
        print("new website link wasn't provided, using the old one")
    print(f"Trying {website}")
    if website:
        old_website = website
        try:
            response = requests.get(website)
            print(f"Got response {response.status_code}")
            if response.status_code == 200:
                print("Checking if the page haven't changed")
                if response.text == old_text:
                    print("The data is the same from the last time, returning..")
                    return
                else:
                    print(f"Page size was changed, proceeding (new {len(response.text)} != past {len(old_text)})")
                    old_text = response.text 
                try:
                    entry, entry_xl_new, items_amount_old = website_processing.process_website_content(website,response.text,items_amount_old,website_content_listbox)
                except:
                    print("Page could not be identified, returning..")
                    return
                if entry_xl == entry_xl_new:
                    print("Got the same data, returning..")
                    return
                else:
                    entry_xl = entry_xl_new
                website_content_listbox.insert(tk.END, entry)
                refresh_xl_window()
                refresh_listbox_focus()
                xl_button.config(state=tk.NORMAL)
            else:
                xl_button.config(state=tk.DISABLED)
                website_content_listbox.insert(tk.END, f"Failed to fetch content from {website}")
        except requests.RequestException:
            website_content_listbox.insert(tk.END, f"Failed to fetch content from {website}")
        website_entry.delete(0, tk.END)

def clear_list():
    website_content_listbox.delete(0, tk.END)

def save_list():
    contents = website_content_listbox.get(0, tk.END)
    with open('website_product_list.txt', 'w', encoding='utf-8') as file:
        for content in contents:
            file.write(content + '\n')

def refresh_xl_window():
    try:
        list_window.destroy()
    except:
        print("The window wasn't openned yet")
    print("Openning list_window")
    on_xl_window()

def on_xl_window():
    global list_window
    list_window = tk.Toplevel(root)
    list_window.title(f"Items listing (currently displaying {items_amount_old} items)")
    window_width = 800
    window_height = 600
    list_window.geometry(f"{window_width}x{window_height}")
    list_window.minsize(width=window_width, height=window_height)

    columns = ("Item","Seller","Price","Currency")
    xl_listbox = tk.ttk.Treeview(list_window, columns=columns, show="headings")
    for col_index, col in enumerate(columns):
        xl_listbox.heading(col, text=col, command=lambda col_index=col_index: sort_column_xl(xl_listbox, col_index))

    for value in entry_xl:
        xl_listbox.insert('', tk.END, values=value)
    xl_listbox.pack(fill="both", expand=True)

def sort_column_xl(xl_listbox, col_index, descending=False):
    if col_index == 2:
        items = [(float(xl_listbox.set(item, col_index)), item) for item in xl_listbox.get_children()]
    else:
        items = [(xl_listbox.set(item, col_index), item) for item in xl_listbox.get_children()]

    items.sort(reverse=descending)

    for index, (_, item) in enumerate(items):
        xl_listbox.move(item, '', index)

    xl_listbox.heading(col_index, command=lambda: sort_column_xl(xl_listbox, col_index, not descending))

def on_checkbox_clicked():
    var = checkbox_var.get()
    print(f"Auto update is set to {bool(var)}")
    if var:
        add_website_content()
        time_delay = 5 * 60 * 1000 # 5 minutes in ms
        root.after(time_delay, on_checkbox_clicked)
        #root.after(3*1000, on_checkbox_clicked)

def refresh_listbox_focus():
    website_content_listbox.yview(tk.END)

entry_xl = []
old_website = ""
old_text = ""
items_amount_old = 0

root = tk.Tk()
root.title("Website Product List")
window_width = 350
window_height = 250
root.geometry(f"{window_width}x{window_height}")
root.minsize(width=window_width, height=window_height)
root.maxsize(width=window_width, height=window_height)

root_width = root.winfo_width()
root_height = root.winfo_height()

def resize(event):
    global root_width, root_height
    root_width = event.width
    root_height = event.height

root.bind("<Configure>", resize)

website_label = tk.Label(root, text="Enter a website:")
website_label.grid(row=0, column=0, columnspan=2, pady=5)

website_entry = tk.Entry(root)
website_entry.grid(row=0, column=2, columnspan=2, pady=5)

fill_button = tk.Button(root, text="hinta", command=fill_website_entry)
fill_button.grid(row=0, column=4, pady=5)

add_button = tk.Button(root, text="Analyze", command=add_website_content)
add_button.grid(row=0, column=5, pady=5)

xl_button = tk.Button(root, text="Open xl window", command=on_xl_window)
xl_button.grid(row=1, column=0,padx=10, pady=5, columnspan=2)
if not entry_xl:
    xl_button.config(state=tk.DISABLED)

checkbox_var = tk.IntVar()

checkbox = tk.Checkbutton(root, text="Auto Update", variable=checkbox_var, command=on_checkbox_clicked)
checkbox.grid(row=1, column=3, pady=5)

# Create a Frame to hold the listbox
listbox_frame = tk.Frame(root)
listbox_frame.grid(row=2, column=0, columnspan=6, padx=10, pady=5, sticky="nsew")
listbox_frame.grid_rowconfigure(0, weight=1)
listbox_frame.grid_columnconfigure(0, weight=1)

website_content_listbox = tk.Listbox(listbox_frame)
website_content_listbox.pack(fill="both", expand=True)

scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=website_content_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
website_content_listbox.config(yscrollcommand=scrollbar.set)

root.mainloop()
