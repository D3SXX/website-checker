# Website checker v0.1 alpha build 16 by D3SXX  

import tkinter as tk
from tkinter import ttk 
import requests
import website_processing
import argparse
import datetime
import threading

parser = argparse.ArgumentParser(description="Website Checker by D3SXX")

parser.add_argument('--Debug',action='store_true',help='Enable debug output')
parser.add_argument('--Warning',action='store_true',help='Enable output of warnings and errors')

args = parser.parse_args()

args.Debug = True

class DataHolder:
    list_count = 0
    link_count = 0
    
    def __init__(self):
        self.data_lists = {}
        self.link_lists = []
    
    def add_data(self, item):
        list_name = f"list_{DataHolder.list_count}"
        DataHolder.list_count += 1
        self.data_lists[list_name] = item
    
    def get_data(self):
        try:
            self.data_lists.pop(f"list_{DataHolder.list_count-1}")
            self.data_lists.pop(f"list_{DataHolder.list_count-2}")
            DataHolder.list_count -= 2
            return self.data_lists[f"list_{DataHolder.list_count-2}"],self.data_lists[f"list_{DataHolder.list_count-1}"]
        except:
            return None
    def add_link(self, item):
        self.link_lists.append(item)
        DataHolder.link_count += 1
    def get_link(self):
        DataHolder.link_count -= 1
        try:
            if self.link_count < 0:
                self.link_count = 0
            elif self.link_count == 0:
                self.link_count = 1
                return False 
            link = self.link_lists[DataHolder.link_count-1]
            self.link_lists.pop(DataHolder.link_count)
            return link
        except:
            return None
    def reset_data(self):
        self.data_lists.clear()
        self.link_lists.clear()
        DataHolder.list_count = 0
        DataHolder.link_count = 0

class DebugPrint:

    def __init__(self):
        pass
    
    def d_print(self,item,ending="\n", timestamp = None):
         if args.Debug:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            if ending == "\n":
                if timestamp == None or timestamp == True:
                    print(f"{current_time} - {str(item)}")
                else:
                    print(f"{str(item)}")
            else:
                if timestamp:
                    print(f"{current_time} - ",end="")
                print(f"{str(item)}",end=ending)
    def warning_print(self,item,type = "W",timestamp = True):
        if args.Debug or args.Warning:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            if type == "W":
                if timestamp or args.Warning:
                    print("\033[93m{}\033[00m".format(f"{current_time} - (Warning) {str(item)}"))
                else:
                    print("\033[93m{}\033[00m".format(f"(Warning) {str(item)}"))
            else:
                if timestamp or args.Warning:
                    print("\033[91m{}\033[00m".format(f"{current_time} - (Error) {str(item)}"))
                else:
                    print("\033[91m{}\033[00m".format(f"(Error) {str(item)}"))

def fill_website_entry():
    root.after(0, lambda: website_entry_var.set("https://hinta.fi/"))

def on_back_page(newwebsite = None):
    global back_button, entry_xl, data_holder, columns, old_website, debug
    if newwebsite == None:
        debug.d_print("Trying to get the link from DataHolder-->","",True)
        try:
            link = data_holder.get_link()
            if link == False:
                back_button.config(state="disabled")
                debug.d_print("Reached the first page, returning","\n",False)
                return
            old_website = link
            debug.d_print(link,"\n",False)
            if link == None:
                raise Exception
        except:
            debug.warning_print("Error hapenned while trying to get link, doing reset_data()","E")
            data_holder.reset_data()
            back_button.config(state="disabled")
            return
        debug.d_print(f"Trying to access data from the Dataholder-->","",True)
        update_progress(0,1)
        try:
            columns,entry_xl = data_holder.get_data()
            global items_amount_old
            items_amount_old = len(entry_xl)
        except:
            debug.warning_print("Could not access data from Dataholder","E",False)
            add_website_content(True,link, False)
            return
        if columns != None:
            debug.d_print("Got correct data","\n",False)
            update_progress(1,1)
            init_browser_window()
        else:
            debug.warning_print("Could not retrieve data, redirecting to add_website_content","E",False)
            add_website_content(True,link, False)
    else:
        try:
            back_button.config(state="normal")
        except:
            pass
        debug.d_print(f"Adding {newwebsite} to DataHolder")
        data_holder.add_link(newwebsite)

def update_progress(value, maxvalue):
    try:
        progress_bar["value"] = value
        progress_bar["maximum"] = maxvalue
        percentage = (value / maxvalue) * 100
        list_window.title(f"Items listing - {value}/{maxvalue}({percentage:.2f}%) (press escape to stop)")
        list_window.update_idletasks()
    except:
        debug.warning_print("Could not update progress_bar","W")

def escape_pressed(event):
    debug.d_print("escape_pressed() triggered, returning..")
    global esc_pressed 
    esc_pressed = True

def stop_scan():
    global esc_pressed,stop_scan_button
    list_window.bind("<Escape>", escape_pressed)
    try:
        if not stop_scan_button.winfo_ismapped():
            stop_scan_button = tk.Button(frame_top, text="Stop scan", command=lambda: escape_pressed(""))
            stop_scan_button.pack(side="left")
    except:
        stop_scan_button = tk.Button(frame_top, text="Stop scan", command=lambda: escape_pressed(""))
        stop_scan_button.pack(side="left")
    list_window.update_idletasks()
    list_window.update()
    if esc_pressed:
        stop_scan_button.destroy()
        return True
    else:
        return False
    

def add_website_content(redirect = False, redirect_link = "",hold_data = True):
    global old_website, old_text, entry_xl,items_amount_old,website_content_listbox, columns,website,stop_scan_button, esc_pressed
    entry_xl_new = []
    esc_pressed = False
    stop_flag = stop_checkbox_var.get()
    if stop_flag:
        stop_flag = stop_at

    if redirect == False:
        if website == "":
            debug.warning_print("Got an empty link, returning..","E")
            return
        else:
            if not website:
                debug.d_print("Didn't get any links, using old_website","W")
                website = old_website
    else:
        website = redirect_link
    debug.d_print(f"Trying {website}")
    if website:
        old_website = website
        try:
            response = requests.get(website,timeout=5)
            debug.d_print(f"Got response {response.status_code}")
            if response.status_code == 200:
                debug.d_print("Checking if the page haven't changed")
                if response.text == old_text:
                    debug.warning_print("The data is the same from the last time, returning..", "W")
                    return
                else:
                    debug.d_print(f"Page size was changed, proceeding (new {len(response.text)} != past {len(old_text)})")
                    old_text = response.text 
                try:
                    entry, entry_xl_new, items_amount_old, columns = website_processing.process_website_content(website,response.text,items_amount_old,website_content_listbox,update_progress,on_back_page,stop_scan,debug,stop_flag,redirect)
                except Exception as e:
                    debug.warning_print("Page could not be identified (or an error occurred), returning..","W")
                    debug.warning_print(f"{e}","E")
                    return
                if entry_xl == entry_xl_new:
                    debug.warning_print(f"Got the same data (new {len(entry_xl_new)} == past {len(entry_xl)}), returning..","W")
                    return
                else:
                    entry_xl = entry_xl_new
                    xl_button.config(state=tk.NORMAL)
                    if hold_data:
                        debug.d_print(f"Recorded data to the Dataholder")
                        data_holder.add_data(columns)
                        data_holder.add_data(entry_xl)
                debug.d_print("Data check successful, trying to init_browser_window()")
                website_content_listbox.insert(tk.END, entry)
                init_browser_window()
                refresh_listbox_focus()
            else:
                debug.warning_print("Failed to fetch content","E")
                xl_button.config(state=tk.DISABLED)
                website_content_listbox.insert(tk.END, f"Failed to fetch content from {website}")
        except requests.RequestException:
            debug.warning_print("Failed to fetch content after 5 seconds of trying","E")
            website_content_listbox.insert(tk.END, f"Failed to fetch content from {website}")

def clear_list():
    website_content_listbox.delete(0, tk.END)

def save_list():
    contents = website_content_listbox.get(0, tk.END)
    with open('website_product_list.txt', 'w', encoding='utf-8') as file:
        for content in contents:
            file.write(content + '\n')

def on_list_window():
    global list_window,columns, progress_bar,xl_listbox,website_entry,frame_top,frame_centre,back_button, xl_scrollbar,handle_selection

    list_window.title(f"Items listing (currently displaying {items_amount_old} items)")
    window_width = 800
    window_height = 600
    list_window.geometry(f"{window_width}x{window_height}")
    list_window.minsize(width=window_width, height=window_height)

    list_window.grid_rowconfigure(0, weight=0)
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

    website_entry = tk.Entry(frame_top, width=100)
    website_entry.pack(side="left", fill="both")

    website_entry.insert(0, old_website)
    website_entry.configure(state="readonly")

    back_button = tk.Button(frame_top, text="Return↵", command=on_back_page)
    back_button.pack(side="left",expand=True)

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
            debug.d_print(f"Trying to redirect to {old_website}")
            thread = threading.Thread(target=add_website_content, args=(True,old_website))
            thread.start()
            #add_website_content(True, old_website)
            on_back_page(old_website)

    # Bind the function to mouse left-click and Enter key press events
    xl_listbox.bind("<ButtonRelease-1>", handle_selection)  # Mouse left-click
    xl_listbox.bind("<Return>", handle_selection)           # Enter key

def init_browser_window():
    debug.d_print("init_browser_window","-->",True)
    global list_window
    try:
        if list_window is None or not list_window.winfo_exists():
            list_window = tk.Toplevel(root)
            on_list_window()
            debug.d_print("list_window was created", "-->")
    except:
        list_window = tk.Toplevel(root)
        on_list_window()
        debug.d_print("list_window was created","-->")
    debug.d_print("Going to on_list_window","\n",False)
    on_list_window()

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
    debug.d_print(f"Auto update is set to {bool(var)}")
    if var:
        add_website_content()
        time_delay = 5 * 60 * 1000 # 5 minutes in ms
        root.after(time_delay, on_checkbox_clicked)
        #root.after(3*1000, on_checkbox_clicked)

def on_checkbox_stop_skip():
    var = stop_checkbox_var.get()
    debug.d_print(f"Stop page is set to {bool(var)}")
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
        debug.d_print(f"Updated stop_at value ({stop_at})")
    except:
        pass  # Ignore non-integer values
def update_website_label(*args):
    try:
        new_website = str(website_entry_var.get())
        global website
        website = new_website
        debug.d_print(f"Updated website value ({website})")
    except:
        pass

website = ""
entry_xl = []
old_website = ""
old_text = ""
items_amount_old = 0
columns = ""
stop_at = 10
data_holder = DataHolder()
debug = DebugPrint()

root = tk.Tk()
root.title("Website Product List")
window_width = 350
window_height = 250
root.geometry(f"{window_width}x{window_height}")
root.minsize(width=window_width, height=window_height)
#root.maxsize(width=window_width, height=window_height)

root_width = root.winfo_width()
root_height = root.winfo_height()

def resize(event):
    global root_width, root_height
    root_width = event.width
    root_height = event.height

root.bind("<Configure>", resize)

root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=0)
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)

root_frame_top = tk.Frame(master=root)
root_frame_centre = tk.Frame(master=root)
root_frame_bottom = tk.Frame(master=root)

root_frame_top.grid(row=0, column=0, sticky="nsew")
root_frame_centre.grid(row=1, column=0, sticky="nsew")
root_frame_bottom.grid(row=2, column=0, sticky="nsew")

website_label = tk.Label(root_frame_top, text="Enter a website:")
website_label.pack(side="left",padx=5,pady=5)

website_entry_var = tk.StringVar()

website_entry = tk.Entry(root_frame_top,textvariable=website_entry_var)
website_entry.pack(side="left", expand=True, fill="both",padx=5,pady=5)

website_entry_var.trace("w", update_website_label)

fill_button = tk.Button(root_frame_top, text="hinta", command=fill_website_entry)
fill_button.pack(side="left",padx=5,pady=2, expand=True, fill="both")

add_button = tk.Button(root_frame_top, text="Analyze", command=add_website_content)
add_button.pack(side="left",padx=5,pady=2, expand=True, fill="both")

xl_button = tk.Button(root_frame_centre, text="Open xl window", command=init_browser_window)
xl_button.pack(side="left", padx=5,pady=2, expand=True, fill="both")
if not entry_xl:
    xl_button.config(state=tk.DISABLED)

update_checkbox_var = tk.IntVar()

checkbox = tk.Checkbutton(root_frame_centre, text="Auto Update", variable=update_checkbox_var, command=on_checkbox_clicked)
checkbox.pack(side="left", expand=True, fill="both")

stop_checkbox_var = tk.IntVar()

checkbox = tk.Checkbutton(root_frame_centre, text="Stop scan after", variable=stop_checkbox_var, command=on_checkbox_stop_skip)
checkbox.pack(side="left", expand=True, fill="both")

stop_entry_var = tk.IntVar()
stop_entry_var.set(stop_at)

stop_entry_var.trace("w", update_stop_at)

stop_entry = tk.Entry(root_frame_centre, textvariable=stop_entry_var, width=4)
stop_entry.pack(side="left", expand=True, fill="both",padx=5,pady=2)

stop_entry.config(state="disabled")

website_content_listbox = tk.Listbox(root_frame_bottom)
website_content_listbox.pack(fill="both", expand=True,side="left")

scrollbar = tk.Scrollbar(root_frame_bottom, orient=tk.VERTICAL, command=website_content_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
website_content_listbox.config(yscrollcommand=scrollbar.set)

root.mainloop()
