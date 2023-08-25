# Website checker v0.1 alpha build 8 by D3SXX  

import tkinter as tk
from tkinter import ttk 
import requests
import website_processing

def fill_website_entry():
    website_entry.delete(0, tk.END)
    website_entry.insert(0, "https://hinta.fi/")

def on_back_page(newwebsite = None):
    global back_page_index,back_page
    if newwebsite == None:
        print(f"Removing {back_page[back_page_index-1]} from the back_page[{back_page_index-1}]")
        back_page_index -= 1
        back_page.pop(back_page_index)
        add_website_content(True,back_page[back_page_index-1])
    elif newwebsite == "clear":
        back_page_index = 0
        back_page.clear()
    else:
        print(f"Adding {newwebsite} to the back_page[{back_page_index}]")
        back_page_index += 1
        back_page.append(newwebsite)
    print(back_page)

def update_progress(value, maxvalue):
    try:
        progress_bar["value"] = value
        progress_bar["maximum"] = maxvalue
        list_window.update_idletasks()
    except:
        print("Could not update progress_bar")

def add_website_content(redirect = False, redirect_link = ""):
    global old_website, old_text, entry_xl,items_amount_old,website_content_listbox, columns
    entry_xl_new = []
    stop_flag = stop_checkbox_var.get()
    if stop_flag:
        stop_flag = stop_at
        
    if redirect == False:
        website = website_entry.get()
        if len(website) < 1:
            website = old_website
            print("Warning - A new website link wasn't provided, using the old_website")
    else:
        website = redirect_link
    print(f"Trying {website}")
    if website:
        old_website = website
        try:
            response = requests.get(website,timeout=5)
            print(f"Got response {response.status_code}")
            if response.status_code == 200:
                print("Checking if the page haven't changed")
                if response.text == old_text:
                    print("Warning - The data is the same from the last time, returning..")
                    return
                else:
                    print(f"Page size was changed, proceeding (new {len(response.text)} != past {len(old_text)})")
                    old_text = response.text 
                try:
                    entry, entry_xl_new, items_amount_old, columns = website_processing.process_website_content(website,response.text,items_amount_old,website_content_listbox,update_progress,on_back_page,stop_flag,redirect)
                except Exception as e:
                    print("Warning - Page could not be identified (or an error occurred), returning..")
                    print("",type(e).__name__, "–", e)
                    #print(e)
                    return
                if entry_xl == entry_xl_new:
                    print(f"Warning - Got the same data (new {len(entry_xl_new)} == past {len(entry_xl)}), returning..")
                    return
                else:
                    entry_xl = entry_xl_new
                print("Data check successful, trying to open list_window")
                website_content_listbox.insert(tk.END, entry)
                refresh_xl_window()
                refresh_listbox_focus()
                xl_button.config(state=tk.NORMAL)
            else:
                print("Error - Failed to fetch content")
                xl_button.config(state=tk.DISABLED)
                website_content_listbox.insert(tk.END, f"Failed to fetch content from {website}")
        except requests.RequestException:
            print("Error - Failed to fetch content after 5 seconds of trying")
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
    global xl_listbox,xl_scrollbar
    print("Trying to refresh list_window")
    try:
        print("Destroying xl_listbox",end="-->")
        xl_listbox.destroy()
        print("Creating xl_listbox",end="-->")
        xl_listbox = tk.ttk.Treeview(frame_centre, columns=columns, show="headings")
        print("Filling xl_window",end="-->")
        for col_index, col in enumerate(columns):
            xl_listbox.heading(col, text=col, command=lambda col_index=col_index: sort_column_xl(xl_listbox, col_index))
        for value in entry_xl:
            xl_listbox.insert('', tk.END, values=value)
        xl_listbox.pack(fill="both", expand=True,side="left")
        xl_listbox.bind("<ButtonRelease-1>", handle_selection)  # Mouse left-click
        xl_listbox.bind("<Return>", handle_selection)           # Enter key
        print("Refreshing xl_scrollbar",end="-->")
        xl_scrollbar.destroy()
        xl_scrollbar = tk.Scrollbar(frame_centre, orient="vertical", command=xl_listbox.yview)
        xl_listbox.configure(yscrollcommand=xl_scrollbar.set)
        xl_scrollbar.pack(fill="y", side="right")
        print("Refreshing website_entry",end="-->")
        website_entry.configure(state="normal")
        website_entry.delete(0, tk.END)
        website_entry.insert(0, f"{old_website}")
        website_entry.configure(state="readonly")
        print("Refreshing window title")
        list_window.title(f"Items listing (currently displaying {items_amount_old} items)")

        list_window.update_idletasks()
        list_window.update()
        return

    except Exception as e:
        print("The window wasn't openned yet or an error occured, destroying list_window")
        print(e)
    try:
        list_window.destroy()
    except:
        print("The window wasn't openned yet")
    on_xl_window()

def on_xl_window():
    global list_window, columns, progress_bar,list_window,xl_listbox,website_entry,frame_centre, xl_scrollbar,handle_selection

    list_window = tk.Toplevel(root)
    list_window.title(f"Items listing (currently displaying {items_amount_old} items)")
    window_width = 800
    window_height = 600
    list_window.geometry(f"{window_width}x{window_height}")
    list_window.minsize(width=window_width, height=window_height)

    list_window.grid_rowconfigure(1, weight=1)
    list_window.grid_columnconfigure(0, weight=1)

    frame_top = tk.Frame(master=list_window)
    frame_centre = tk.Frame(master=list_window)
    frame_bottom = tk.Frame(master=list_window)

    frame_top.grid(row=0, column=0, sticky="nsew")
    frame_centre.grid(row=1, column=0, sticky="nsew")
    frame_bottom.grid(row=2, column=0, sticky="nsew")

    if len(columns) < 1:
        columns = ("Item", "Seller", "Price", "Currency")  # Fallback option

    website_entry = tk.Entry(frame_top)
    website_entry.grid(row=0, column=0)
    website_entry.insert(0, old_website)
    website_entry.configure(state="readonly")

    back_button = tk.Button(frame_top, text="Return", command=on_back_page)
    back_button.grid(row=0, column=1)

    # Create and configure xl_listbox within frame_centre
    xl_listbox = tk.ttk.Treeview(frame_centre, columns=columns, show="headings")

    for col_index, col in enumerate(columns):
        xl_listbox.heading(col, text=col, command=lambda col_index=col_index: sort_column_xl(xl_listbox, col_index))

    for value in entry_xl:
        xl_listbox.insert("", tk.END, values=value)

    xl_scrollbar = tk.Scrollbar(frame_centre, orient="vertical", command=xl_listbox.yview)
    xl_listbox.configure(yscrollcommand=xl_scrollbar.set)

    xl_listbox.pack(fill="both", expand=True,side="left")
    xl_scrollbar.pack(fill="y", side="right")

    progress_bar = ttk.Progressbar(frame_bottom, mode="determinate")
    progress_bar.pack(fill="x")

    # Define a function to handle the selection
    def handle_selection(event):
        selected_item = xl_listbox.selection()  # Get the selected item's ID
        if selected_item:
            item_values = xl_listbox.item(selected_item, 'values')
            try:
                link_place = columns.index("Link")
            except:
                return
            global old_website
            try:
                old_website = item_values[link_place]
            except:
                return
            print(f"Trying to redirect to {old_website}")
            # Call the function you want to execute with the selected item's values
            add_website_content(True, old_website)
            on_back_page(old_website)

    # Bind the function to mouse left-click and Enter key press events
    xl_listbox.bind("<ButtonRelease-1>", handle_selection)  # Mouse left-click
    xl_listbox.bind("<Return>", handle_selection)           # Enter key


def sort_column_xl(xl_listbox, col_index, descending=False):
    global columns
    if columns[col_index] == "Price":
        items = [(float(xl_listbox.set(item, col_index)), item) for item in xl_listbox.get_children()]
    else:
        items = [(xl_listbox.set(item, col_index), item) for item in xl_listbox.get_children()]

    items.sort(reverse=descending)

    for index, (_, item) in enumerate(items):
        xl_listbox.move(item, '', index)

    xl_listbox.heading(col_index, command=lambda: sort_column_xl(xl_listbox, col_index, not descending))

def on_checkbox_clicked():
    var = update_checkbox_var.get()
    print(f"Auto update is set to {bool(var)}")
    if var:
        add_website_content()
        time_delay = 5 * 60 * 1000 # 5 minutes in ms
        root.after(time_delay, on_checkbox_clicked)
        #root.after(3*1000, on_checkbox_clicked)

def on_checkbox_stop_skip():
    var = stop_checkbox_var.get()
    print(f"Stop page is set to {bool(var)}")
    if var:
        stop_entry.config(state="normal")
    else:
        stop_entry.config(state="disabled")

def refresh_listbox_focus():
    website_content_listbox.yview(tk.END)

def update_stop_at(*args):
    try:
        new_stop_at = int(stop_entry_var.get())
        global stop_at
        stop_at = new_stop_at
        print(f"Updated stop_at value ({stop_at})")
    except:
        pass  # Ignore non-integer values

entry_xl = []
old_website = ""
old_text = ""
items_amount_old = 0
columns = ""
stop_at = 10

back_page = []
back_page_index = 0

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

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

root_frame_top = tk.Frame(master=root)
root_frame_centre = tk.Frame(master=root)
root_frame_bottom = tk.Frame(master=root)

root_frame_top.grid(row=0, column=0, sticky="nsew")
root_frame_centre.grid(row=1, column=0, sticky="nsew")
root_frame_bottom.grid(row=2, column=0, sticky="nsew")


website_label = tk.Label(root_frame_top, text="Enter a website:")
website_label.pack(side="left",padx=5,pady=5)

website_entry = tk.Entry(root_frame_top)
website_entry.pack(side="left")

fill_button = tk.Button(root_frame_top, text="hinta", command=fill_website_entry)
fill_button.pack(side="left",padx=5)

add_button = tk.Button(root_frame_top, text="Analyze", command=add_website_content)
add_button.pack(side="left")

xl_button = tk.Button(root_frame_centre, text="Open xl window", command=on_xl_window)
xl_button.pack(side="left",padx=5)
if not entry_xl:
    xl_button.config(state=tk.DISABLED)

update_checkbox_var = tk.IntVar()

checkbox = tk.Checkbutton(root_frame_centre, text="Auto Update", variable=update_checkbox_var, command=on_checkbox_clicked)
checkbox.pack(side="left")

stop_checkbox_var = tk.IntVar()

checkbox = tk.Checkbutton(root_frame_centre, text="Stop scan after", variable=stop_checkbox_var, command=on_checkbox_stop_skip)

checkbox.pack(side="left")

stop_entry_var = tk.IntVar()
stop_entry_var.set(stop_at)

stop_entry_var.trace("w", update_stop_at)


stop_entry = tk.Entry(root_frame_centre,textvariable=stop_entry_var)
stop_entry.pack(side="left")

stop_entry.config(state="disabled")

# Create a Frame to hold the listbox
listbox_frame = tk.Frame(root_frame_bottom)
listbox_frame.pack(fill="both",padx=5)

website_content_listbox = tk.Listbox(listbox_frame)
website_content_listbox.pack(fill="both", expand=True,side="left")

scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=website_content_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
website_content_listbox.config(yscrollcommand=scrollbar.set)

root.mainloop()
