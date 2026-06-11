import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# Database setup
conn = sqlite3.connect("pos.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        total REAL NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        subtotal REAL NOT NULL
    )
""")

conn.commit()

# ---- MAIN WINDOW ----

root = tk.Tk()
root.title("Point of Sale")
root.geometry("800x600")
root.iconbitmap("cashregister.ico")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

products_frame = ttk.Frame(notebook)
sales_frame = ttk.Frame(notebook)

notebook.add(products_frame, text="Products")
notebook.add(sales_frame, text="New Sale")
# ---- ALL FUNCTIONS ----

cart = []

def load_products():
    for row in product_tree.get_children():
        product_tree.delete(row)
    cursor.execute("SELECT id, name, price, quantity FROM products ORDER BY name")
    for row in cursor.fetchall():
        product_tree.insert("", "end", values=(row[0], row[1], f"{row[2]:.2f}", row[3]))

def load_products_for_sale():
    for row in sale_product_tree.get_children():
        sale_product_tree.delete(row)
    cursor.execute("SELECT id, name, price, quantity FROM products WHERE quantity > 0 ORDER BY name")
    for row in cursor.fetchall():
        sale_product_tree.insert("", "end", values=(row[0], row[1], f"{row[2]:.2f}", row[3]))

def add_product():
    name = entry_name.get().strip()
    price = entry_price.get().strip()
    quantity = entry_quantity.get().strip()
    if not name or not price or not quantity:
        messagebox.showwarning("Missing Info", "Please fill in all fields.")
        return
    try:
        price = float(price)
        quantity = int(quantity)
    except ValueError:
        messagebox.showerror("Invalid Input", "Price must be a number, quantity must be a whole number.")
        return
    cursor.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)", (name, price, quantity))
    conn.commit()
    entry_name.delete(0, tk.END)
    entry_price.delete(0, tk.END)
    entry_quantity.delete(0, tk.END)
    load_products()
    load_products_for_sale()

def adjust_stock():
    selected = product_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a product to adjust stock.")
        return
    item = product_tree.item(selected[0])
    product_id = item["values"][0]
    product_name = item["values"][1]
    current_qty = item["values"][3]

    popup = tk.Toplevel(root)
    popup.title(f"Adjust Stock - {product_name}")
    popup.geometry("300x150")
    popup.grab_set()

    ttk.Label(popup, text=f"Current stock: {current_qty}").pack(pady=10)
    ttk.Label(popup, text="Add quantity:").pack()
    entry_adjust = ttk.Entry(popup, width=10)
    entry_adjust.pack(pady=5)

    def confirm_adjust():
        try:
            amount = int(entry_adjust.get().strip())
            if amount <= 0:
                messagebox.showerror("Invalid", "Please enter a positive number.", parent=popup)
                return
            cursor.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (amount, product_id))
            conn.commit()
            load_products()
            load_products_for_sale()
            popup.destroy()
            messagebox.showinfo("Stock Updated", f"Added {amount} units to '{product_name}'.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a whole number.", parent=popup)

    ttk.Button(popup, text="Confirm", command=confirm_adjust).pack(pady=5)

def delete_product():
    selected = product_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a product to delete.")
        return
    item = product_tree.item(selected[0])
    product_id = item["values"][0]
    product_name = item["values"][1]

    cursor.execute("SELECT COUNT(*) FROM sale_items WHERE product_name = ?", (product_name,))
    count = cursor.fetchone()[0]
    if count > 0:
        messagebox.showerror("Cannot Delete", f"'{product_name}' has {count} sales record(s).\nProducts with sales history cannot be deleted.")
        return

    confirm = messagebox.askyesno("Confirm Delete", f"Delete '{product_name}'?\nThis product has no sales history.")
    if confirm:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        load_products()
        load_products_for_sale()

def modify_product():
    selected = product_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a product to modify.")
        return
    item = product_tree.item(selected[0])
    product_id = item["values"][0]
    product_name = item["values"][1]
    product_price = item["values"][2]

    popup = tk.Toplevel(root)
    popup.title(f"Modify Product - {product_name}")
    popup.geometry("300x180")
    popup.grab_set()

    ttk.Label(popup, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    entry_mod_name = ttk.Entry(popup, width=20)
    entry_mod_name.insert(0, product_name)
    entry_mod_name.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(popup, text="Price:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    entry_mod_price = ttk.Entry(popup, width=20)
    entry_mod_price.insert(0, product_price)
    entry_mod_price.grid(row=1, column=1, padx=10, pady=5)

    def confirm_modify():
        new_name = entry_mod_name.get().strip()
        new_price = entry_mod_price.get().strip()
        if not new_name or not new_price:
            messagebox.showwarning("Missing Info", "Please fill in all fields.", parent=popup)
            return
        try:
            new_price = float(new_price)
        except ValueError:
            messagebox.showerror("Invalid Input", "Price must be a number.", parent=popup)
            return
        cursor.execute("UPDATE products SET name = ?, price = ? WHERE id = ?", (new_name, new_price, product_id))
        conn.commit()
        load_products()
        load_products_for_sale()
        popup.destroy()
        messagebox.showinfo("Updated", f"'{product_name}' has been updated.")

    ttk.Button(popup, text="Save Changes", command=confirm_modify).grid(row=2, column=0, columnspan=2, pady=15)

def add_to_cart():
    selected = sale_product_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a product to add to the sale.")
        return
    item = sale_product_tree.item(selected[0])
    product_id = item["values"][0]
    product_name = item["values"][1]
    product_price = float(item["values"][2])
    stock = item["values"][3]

    try:
        qty = int(entry_qty.get().strip())
        if qty <= 0:
            messagebox.showerror("Invalid", "Quantity must be at least 1.")
            return
        if qty > stock:
            messagebox.showerror("Not Enough Stock", f"Only {stock} units available for '{product_name}'.")
            return
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a whole number for quantity.")
        return

    subtotal = qty * product_price
    cart.append({
        "id": product_id,
        "name": product_name,
        "price": product_price,
        "qty": qty,
        "subtotal": subtotal
    })
    update_cart_display()
    entry_qty.delete(0, tk.END)

def update_cart_display():
    for row in cart_tree.get_children():
        cart_tree.delete(row)
    total = 0
    for item in cart:
        cart_tree.insert("", "end", values=(item["name"], item["qty"], f"{item['price']:.2f}", f"{item['subtotal']:.2f}"))
        total += item["subtotal"]
    lbl_total.config(text=f"Total: R {total:.2f}")

def remove_from_cart():
    selected = cart_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select an item to remove.")
        return
    index = cart_tree.index(selected[0])
    cart.pop(index)
    update_cart_display()

def complete_sale():
    if not cart:
        messagebox.showwarning("Empty Cart", "Please add products to the sale first.")
        return

    total = sum(item["subtotal"] for item in cart)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("INSERT INTO sales (date, total) VALUES (?, ?)", (date, total))
    sale_id = cursor.lastrowid

    receipt_lines = []
    receipt_lines.append("=" * 40)
    receipt_lines.append("         POINT OF SALE RECEIPT")
    receipt_lines.append("=" * 40)
    receipt_lines.append(f"Date: {date}")
    receipt_lines.append("-" * 40)

    for item in cart:
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_name, quantity, price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, (sale_id, item["name"], item["qty"], item["price"], item["subtotal"]))
        cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (item["qty"], item["id"]))
        receipt_lines.append(f"{item['name']}")
        receipt_lines.append(f"  {item['qty']} x R{item['price']:.2f} = R{item['subtotal']:.2f}")

    conn.commit()
    receipt_lines.append("-" * 40)
    receipt_lines.append(f"TOTAL:  R {total:.2f}")
    receipt_lines.append("=" * 40)
    receipt_lines.append("      Thank you for your purchase!")
    receipt_lines.append("=" * 40)

    cart.clear()
    update_cart_display()
    load_products_for_sale()
    load_products()

    receipt_popup = tk.Toplevel(root)
    receipt_popup.title("Receipt")
    receipt_popup.geometry("350x450")
    receipt_popup.grab_set()

    receipt_text = tk.Text(receipt_popup, font=("Courier", 10), padx=10, pady=10)
    receipt_text.pack(fill="both", expand=True)
    receipt_text.insert("end", "\n".join(receipt_lines))
    receipt_text.config(state="disabled")

    ttk.Button(receipt_popup, text="Close", command=receipt_popup.destroy).pack(pady=10)
    # ---- PRODUCTS TAB LAYOUT ----

form_frame = ttk.LabelFrame(products_frame, text="Add New Product")
form_frame.pack(fill="x", padx=10, pady=10)

ttk.Label(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_name = ttk.Entry(form_frame, width=25)
entry_name.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form_frame, text="Price:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
entry_price = ttk.Entry(form_frame, width=10)
entry_price.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form_frame, text="Quantity:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
entry_quantity = ttk.Entry(form_frame, width=10)
entry_quantity.grid(row=0, column=5, padx=5, pady=5)

ttk.Button(form_frame, text="Add Product", command=add_product).grid(row=0, column=6, padx=10, pady=5)

list_frame = ttk.LabelFrame(products_frame, text="Product List")
list_frame.pack(fill="both", expand=True, padx=10, pady=5)

product_tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Price", "Quantity"), show="headings")
product_tree.heading("ID", text="ID")
product_tree.heading("Name", text="Name")
product_tree.heading("Price", text="Price")
product_tree.heading("Quantity", text="Qty in Stock")
product_tree.column("ID", width=50)
product_tree.column("Name", width=250)
product_tree.column("Price", width=100)
product_tree.column("Quantity", width=100)
product_tree.pack(fill="both", expand=True, padx=5, pady=5)

btn_frame = ttk.Frame(list_frame)
btn_frame.pack(pady=5)

ttk.Button(btn_frame, text="Modify Product", command=modify_product).grid(row=0, column=0, padx=5)
ttk.Button(btn_frame, text="Adjust Stock", command=adjust_stock).grid(row=0, column=1, padx=5)
ttk.Button(btn_frame, text="Delete Product", command=delete_product).grid(row=0, column=2, padx=5)

# ---- SALES TAB LAYOUT ----

left_frame = ttk.LabelFrame(sales_frame, text="Products Available")
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

sale_product_tree = ttk.Treeview(left_frame, columns=("ID", "Name", "Price", "Stock"), show="headings")
sale_product_tree.heading("ID", text="ID")
sale_product_tree.heading("Name", text="Name")
sale_product_tree.heading("Price", text="Price")
sale_product_tree.heading("Stock", text="In Stock")
sale_product_tree.column("ID", width=40)
sale_product_tree.column("Name", width=150)
sale_product_tree.column("Price", width=70)
sale_product_tree.column("Stock", width=70)
sale_product_tree.pack(fill="both", expand=True, padx=5, pady=5)

qty_frame = ttk.Frame(left_frame)
qty_frame.pack(pady=5)

ttk.Label(qty_frame, text="Quantity:").grid(row=0, column=0, padx=5)
entry_qty = ttk.Entry(qty_frame, width=8)
entry_qty.grid(row=0, column=1, padx=5)
ttk.Button(qty_frame, text="Add to Sale", command=add_to_cart).grid(row=0, column=2, padx=5)

right_frame = ttk.LabelFrame(sales_frame, text="Current Sale")
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

cart_tree = ttk.Treeview(right_frame, columns=("Name", "Qty", "Price", "Subtotal"), show="headings")
cart_tree.heading("Name", text="Product")
cart_tree.heading("Qty", text="Qty")
cart_tree.heading("Price", text="Price")
cart_tree.heading("Subtotal", text="Subtotal")
cart_tree.column("Name", width=150)
cart_tree.column("Qty", width=50)
cart_tree.column("Price", width=70)
cart_tree.column("Subtotal", width=80)
cart_tree.pack(fill="both", expand=True, padx=5, pady=5)

lbl_total = ttk.Label(right_frame, text="Total: R 0.00", font=("Helvetica", 14, "bold"))
lbl_total.pack(pady=5)

sale_btn_frame = ttk.Frame(right_frame)
sale_btn_frame.pack(pady=5)

ttk.Button(sale_btn_frame, text="Remove Item", command=remove_from_cart).grid(row=0, column=0, padx=5)
ttk.Button(sale_btn_frame, text="Complete Sale", command=complete_sale).grid(row=0, column=1, padx=5)

# ---- START ----
load_products()
load_products_for_sale()
root.mainloop()