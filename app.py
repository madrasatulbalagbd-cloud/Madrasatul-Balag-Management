import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

INSTITUTION_NAME = "মাদরাসাতুল বালাগ"
INSTITUTION_ADDRESS = "পূর্ব জালালপুর, ঘোড়াঘাট, দিনাজপুর"

# ==========================================
#         ১. ডাটাবেজ সেটআপ
# ==========================================
def init_database():
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        balance REAL DEFAULT 0.0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, type TEXT, fund_name TEXT, category TEXT, amount REAL, description TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, jamait TEXT, roll TEXT, father_name TEXT, guardian_phone TEXT, alt_phone TEXT,
        village TEXT, post_office TEXT, thana TEXT, district TEXT, photo_path TEXT,
        admission_fee REAL, monthly_fee REAL, khoraki_fee REAL, abasan_fee REAL, electricity_fee REAL, exam_fee REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER, student_name TEXT, jamait TEXT, roll TEXT, date TEXT, month_year TEXT, fee_category TEXT, amount REAL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, designation TEXT, phone TEXT, basic_salary REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salary_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER, staff_name TEXT, designation TEXT, month_year TEXT, date TEXT,
        basic_salary REAL, prev_due REAL, extra_duty REAL, festival_bonus REAL, medical_allowance REAL,
        housing_allowance REAL, deduction REAL, net_payable REAL, paid_amount REAL, current_due REAL, extra_note TEXT,
        FOREIGN KEY(staff_id) REFERENCES staff(id)
    )
    ''')
    
    default_funds = [
        ("সাধারণ ফান্ড", "সাধারণ"),
        ("বোর্ডিং ফান্ড", "বোর্ডিং"),
        ("নির্মাণ ও উন্নয়ন ফান্ড", "উন্নয়ন"),
        ("মসজিদ ফান্ড", "মসজিদ ফান্ড"),
        ("গোরাবা ফান্ড", "গোরাবা ফান্ড")
    ]
    for fund_name, f_type in default_funds:
        cursor.execute("INSERT OR IGNORE INTO funds (name, type, balance) VALUES (?, ?, 0.0)", (fund_name, f_type))

    # পুরোনো আলাদা শরয়ী ফান্ডগুলোকে নিরাপদে একত্র করে গোরাবা ফান্ডে নেওয়া
    old_goraba_funds = ["যাকাত ফান্ড", "ফিতরা ফান্ড", "চামড়া ফান্ড", "সদকা ফান্ড"]
    for old_fund in old_goraba_funds:
        cursor.execute("SELECT balance FROM funds WHERE name = ?", (old_fund,))
        old_row = cursor.fetchone()
        if old_row is not None:
            old_balance = old_row[0] or 0.0
            if old_balance:
                cursor.execute("UPDATE funds SET balance = balance + ? WHERE name = 'গোরাবা ফান্ড'", (old_balance,))
            cursor.execute("UPDATE transactions SET fund_name = 'গোরাবা ফান্ড' WHERE fund_name = ?", (old_fund,))
            cursor.execute("DELETE FROM funds WHERE name = ?", (old_fund,))

    conn.commit()
    conn.close()

init_database()

# ==========================================
#         ২. মূল ইউজার ইন্টারফেস (UI)
# ==========================================
root = tk.Tk()
root.title(f"{INSTITUTION_NAME} - ডিজিটাল ম্যানেজমেন্ট সিস্টেম")
root.geometry("1350x850")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ------------------------------------------
#   ফাংশনসমূহ আগে ডিক্লেয়ার
# ------------------------------------------
def load_dashboard_data():
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'আয়' AND date LIKE ?", (f"{today_str}%",))
    today_inc = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'ব্যয়' AND date LIKE ?", (f"{today_str}%",))
    today_exp = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'আয়'")
    total_inc = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'ব্যয়'")
    total_exp = cursor.fetchone()[0] or 0.0
    net_cash = total_inc - total_exp

    cursor.execute("SELECT COUNT(*) FROM students")
    total_st = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM staff")
    total_stf = cursor.fetchone()[0] or 0

    lbl_dash_today_inc.config(text=f"আজকের মোট জমা\n{today_inc:.2f} ৳")
    lbl_dash_today_exp.config(text=f"আজকের মোট খরচ\n{today_exp:.2f} ৳")
    lbl_dash_cash.config(text=f"সর্বমোট ক্যাশ ব্যালেন্স\n{net_cash:.2f} ৳")
    lbl_dash_st.config(text=f"মোট শিক্ষার্থী\n{total_st} জন")
    lbl_dash_stf.config(text=f"মোট শিক্ষক/স্টাফ\n{total_stf} জন")

    for row in tree_recent_tx.get_children():
        tree_recent_tx.delete(row)
        
    cursor.execute("SELECT date, type, fund_name, category, amount, description FROM transactions ORDER BY id DESC LIMIT 10")
    for tx in cursor.fetchall():
        tree_recent_tx.insert("", tk.END, values=tx)
        
    conn.close()

def load_accounting_data():
    for row in tree_acc.get_children():
        tree_acc.delete(row)
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, type, fund_name, category, amount, description FROM transactions ORDER BY id DESC")
    for row in cursor.fetchall():
        tree_acc.insert("", tk.END, values=row)
    
    cursor.execute("SELECT name FROM funds")
    funds = [f[0] for f in cursor.fetchall()]
    combo_acc_fund['values'] = [FUND_DISPLAY.get(f, f) for f in funds]
    if funds and not combo_acc_fund.get():
        combo_acc_fund.set(FUND_DISPLAY.get(funds[0], funds[0]))
    conn.close()

def load_funds_data():
    for row in tree_funds.get_children():
        tree_funds.delete(row)
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, type FROM funds")
    funds = cursor.fetchall()

    for f_id, f_name, f_type in funds:
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE fund_name = ? AND type = 'আয়'", (f_name,))
        inc = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE fund_name = ? AND type = 'ব্যয়'", (f_name,))
        exp = cursor.fetchone()[0] or 0.0
        bal = inc - exp
        tree_funds.insert("", tk.END, values=(f_id, f_name, f_type, f"{inc:.2f}", f"{exp:.2f}", f"{bal:.2f}"))
    conn.close()

def load_students_data():
    for row in tree_st.get_children():
        tree_st.delete(row)
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, jamait, roll, father_name, guardian_phone, monthly_fee FROM students")
    for row in cursor.fetchall():
        tree_st.insert("", tk.END, values=row)
    conn.close()

FUND_DISPLAY = {
    "সাধারণ ফান্ড": "সাধারণ ফান্ড",
    "বোর্ডিং ফান্ড": "বোর্ডিং ফান্ড",
    "নির্মাণ ও উন্নয়ন ফান্ড": "নির্মাণ ও উন্নয়ন ফান্ড",
    "মসজিদ ফান্ড": "মসজিদ ফান্ড",
    "গোরাবা ফান্ড": "গোরাবা (যাকাত, ফিতরা, সদকা, মান্নত, চামড়া)"
}
FUND_BY_DISPLAY = {v: k for k, v in FUND_DISPLAY.items()}

def set_categories_for_fund(fund_name, preferred_category=None):
    t_type = combo_acc_type.get()
    if t_type == "আয়":
        fund_categories = {
            "সাধারণ ফান্ড": ["ভর্তি ফি", "মাসিক বেতন", "আবাসন ফি", "পরীক্ষার ফি", "বিদ্যুৎ বিল", "সাধারণ অনুদান", "ফসল/ভাড়া", "বিবিধ"],
            "বোর্ডিং ফান্ড": ["খোরাকি"],
            "নির্মাণ ও উন্নয়ন ফান্ড": ["নির্মাণ ও উন্নয়ন"],
            "মসজিদ ফান্ড": ["মসজিদ ফান্ড"],
            "গোরাবা ফান্ড": ["গোরাবা"]
        }
    else:
        fund_categories = {
            "সাধারণ ফান্ড": expense_categories,
            "বোর্ডিং ফান্ড": ["ছাত্রদের খাবার ও বোর্ডিং খরচ"],
            "নির্মাণ ও উন্নয়ন ফান্ড": ["অফিস ও মাদরাসা মেরামত / রক্ষণাবেক্ষণ"],
            "মসজিদ ফান্ড": ["মসজিদ ফান্ড"],
            "গোরাবা ফান্ড": ["গোরাবা"]
        }
    categories = fund_categories.get(fund_name, income_categories if t_type == "আয়" else expense_categories)
    combo_acc_cat['values'] = categories
    if preferred_category and preferred_category in categories:
        combo_acc_cat.set(preferred_category)
    elif categories:
        combo_acc_cat.set(categories[0])
    check_category_selection(None)

def auto_select_fund(event=None):
    selected_cat = combo_acc_cat.get().strip()
    if selected_cat == "গোরাবা":
        fund_name = "গোরাবা ফান্ড"
    elif selected_cat == "মসজিদ ফান্ড":
        fund_name = "মসজিদ ফান্ড"
    elif selected_cat in ["খোরাকি", "ছাত্রদের খাবার ও বোর্ডিং খরচ"]:
        fund_name = "বোর্ডিং ফান্ড"
    elif selected_cat == "নির্মাণ ও উন্নয়ন":
        fund_name = "নির্মাণ ও উন্নয়ন ফান্ড"
    elif selected_cat == "অফিস ও মাদরাসা মেরামত / রক্ষণাবেক্ষণ":
        fund_name = "নির্মাণ ও উন্নয়ন ফান্ড"
    else:
        fund_name = "সাধারণ ফান্ড"
    combo_acc_fund.set(FUND_DISPLAY.get(fund_name, fund_name))

def fund_selected(event=None):
    display_name = combo_acc_fund.get()
    fund_name = FUND_BY_DISPLAY.get(display_name, display_name)
    set_categories_for_fund(fund_name)

def load_staff_data():
    for row in tree_stf.get_children():
        tree_stf.delete(row)
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, designation, phone, basic_salary FROM staff")
    for row in cursor.fetchall():
        tree_stf.insert("", tk.END, values=row)
    conn.close()

# ------------------------------------------
#   ট্যাব ১: ড্যাশবোর্ড ও অডিট
# ------------------------------------------
tab_dashboard = ttk.Frame(notebook)
notebook.add(tab_dashboard, text=" 📊 ড্যাশবোর্ড ও অডিট ")
frame_dash_cards = tk.Frame(tab_dashboard, pady=10)
frame_dash_cards.pack(fill="x", padx=10)

lbl_dash_today_inc = tk.Label(frame_dash_cards, text="আজকের মোট জমা\n0.00 ৳", font=("Kalpurush", 11, "bold"), bg="#E8F5E9", fg="#2E7D32", width=22, height=3, relief="solid", bd=1)
lbl_dash_today_inc.grid(row=0, column=0, padx=5, pady=5)

lbl_dash_today_exp = tk.Label(frame_dash_cards, text="আজকের মোট খরচ\n0.00 ৳", font=("Kalpurush", 11, "bold"), bg="#FFEBEE", fg="#C62828", width=22, height=3, relief="solid", bd=1)
lbl_dash_today_exp.grid(row=0, column=1, padx=5, pady=5)

lbl_dash_cash = tk.Label(frame_dash_cards, text="সর্বমোট ক্যাশ ব্যালেন্স\n0.00 ৳", font=("Kalpurush", 11, "bold"), bg="#E3F2FD", fg="#1565C0", width=22, height=3, relief="solid", bd=1)
lbl_dash_cash.grid(row=0, column=2, padx=5, pady=5)

lbl_dash_st = tk.Label(frame_dash_cards, text="মোট শিক্ষার্থী\n0 জন", font=("Kalpurush", 11, "bold"), bg="#FFF3E0", fg="#E65100", width=18, height=3, relief="solid", bd=1)
lbl_dash_st.grid(row=0, column=3, padx=5, pady=5)

lbl_dash_stf = tk.Label(frame_dash_cards, text="মোট শিক্ষক/স্টাফ\n0 জন", font=("Kalpurush", 11, "bold"), bg="#F3E5F5", fg="#6A1B9A", width=18, height=3, relief="solid", bd=1)
lbl_dash_stf.grid(row=0, column=4, padx=5, pady=5)

frame_recent = tk.LabelFrame(tab_dashboard, text=" 🕒 সর্বশেষ লেনদেন ও অডিট ট্রেইল ", font=("Kalpurush", 11, "bold"), padx=10, pady=10)
frame_recent.pack(fill="both", expand=True, padx=10, pady=5)

recent_cols = ("date", "type", "fund", "category", "amount", "desc")
tree_recent_tx = ttk.Treeview(frame_recent, columns=recent_cols, show="headings")

tree_recent_tx.heading("date", text="তারিখ ও সময়")
tree_recent_tx.heading("type", text="ধরন")
tree_recent_tx.heading("fund", text="তহবিল/ফান্ড")
tree_recent_tx.heading("category", text="খাত")
tree_recent_tx.heading("amount", text="টাকা (৳)")
tree_recent_tx.heading("desc", text="বিবরণ")

tree_recent_tx.column("date", width=150, anchor="center")
tree_recent_tx.column("type", width=80, anchor="center")
tree_recent_tx.column("fund", width=140, anchor="center")
tree_recent_tx.column("category", width=160, anchor="center")
tree_recent_tx.column("amount", width=100, anchor="center")
tree_recent_tx.column("desc", width=300, anchor="w")

tree_recent_tx.pack(fill="both", expand=True)

# ------------------------------------------
#   ট্যাব ২: আয়-ব্যয়ের হিসাব
# ------------------------------------------
tab_accounting = ttk.Frame(notebook)
notebook.add(tab_accounting, text=" ৳ আয়-ব্যয়ের হিসাব ")

frame_acc_inputs = tk.LabelFrame(tab_accounting, text=" নতুন লেনদেন ইনপুট ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_acc_inputs.pack(fill="x", padx=10, pady=5)

tk.Label(frame_acc_inputs, text="লেনদেনের ধরন:", font=("Kalpurush", 10)).grid(row=0, column=0, sticky="w", pady=5)
combo_acc_type = ttk.Combobox(frame_acc_inputs, values=["আয়", "ব্যয়"], font=("Kalpurush", 10), width=10, state="readonly")
combo_acc_type.set("আয়")
combo_acc_type.grid(row=0, column=1, pady=5, sticky="w")

tk.Label(frame_acc_inputs, text="ফান্ড নির্বাচন:", font=("Kalpurush", 10)).grid(row=0, column=2, sticky="w", pady=5, padx=(15, 0))
combo_acc_fund = ttk.Combobox(frame_acc_inputs, font=("Kalpurush", 10), width=38, state="readonly")
combo_acc_fund['values'] = list(FUND_DISPLAY.values())
combo_acc_fund.grid(row=0, column=3, pady=5, sticky="w")

income_categories = [
    "ভর্তি ফি",
    "মাসিক বেতন",
    "আবাসন ফি",
    "খোরাকি",
    "বিদ্যুৎ বিল",
    "পরীক্ষার ফি",
    "সাধারণ অনুদান",
    "গোরাবা",
    "নির্মাণ ও উন্নয়ন",
    "মসজিদ ফান্ড",
    "ফসল/ভাড়া",
    "বিবিধ"
]

expense_categories = [
    "শিক্ষক ও কর্মচারীদের বেতন",
    "মেহমানদারী",
    "ছাত্রদের খাবার ও বোর্ডিং খরচ",
    "গোরাবা",
    "বিদ্যুৎ, গ্যাস ও ইউটিলিটি বিল",
    "অফিস ও মাদরাসা মেরামত / রক্ষণাবেক্ষণ",
    "বই, খাতা ও শিক্ষা সামগ্রী ক্রয়",
    "প্রিন্টিং ও স্টেশনারি খরচ",
    "প্রচারণা",
    "অনুষ্ঠান ও মাহফিল খরচ",
    "পরিবহন ও যাতায়াত খরচ",
    "ইন্টারনেট ও মোবাইল বিল",
    "পরিষ্কার-পরিচ্ছন্নতা ও চিকিৎসা সামগ্রী",
    "অন্যান্য প্রশাসনিক ব্যয়"
]

tk.Label(frame_acc_inputs, text="খাত নির্বাচন:", font=("Kalpurush", 10)).grid(row=0, column=4, sticky="w", pady=5, padx=(15, 0))
combo_acc_cat = ttk.Combobox(frame_acc_inputs, values=income_categories, font=("Kalpurush", 10), width=30, state="readonly")
combo_acc_cat.set(income_categories[0])
combo_acc_cat.grid(row=0, column=5, pady=5, sticky="w")

frame_bibidh = tk.Frame(frame_acc_inputs)
frame_bibidh.grid(row=0, column=6, padx=5, pady=5, sticky="w")
lbl_bibidh = tk.Label(frame_bibidh, text="বিবিধ বিবরণ:", font=("Kalpurush", 9), fg="#1565C0")
entry_bibidh_detail = tk.Entry(frame_bibidh, font=("Kalpurush", 9), width=15)

def check_category_selection(event):
    selected_cat = combo_acc_cat.get()
    if selected_cat == "বিবিধ":
        lbl_bibidh.pack(side="top", anchor="w")
        entry_bibidh_detail.pack(side="top", pady=2)
    else:
        lbl_bibidh.pack_forget()
        entry_bibidh_detail.pack_forget()
        entry_bibidh_detail.delete(0, tk.END)

def update_category_list(event=None):
    lbl_bibidh.pack_forget()
    entry_bibidh_detail.pack_forget()
    entry_bibidh_detail.delete(0, tk.END)
    combo_acc_fund.set(FUND_DISPLAY["সাধারণ ফান্ড"])
    set_categories_for_fund("সাধারণ ফান্ড")

def fund_selected(event=None):
    display_name = combo_acc_fund.get()
    fund_name = FUND_BY_DISPLAY.get(display_name, display_name)
    set_categories_for_fund(fund_name)

# ইভেন্ট বাইন্ডিং সঠিকভাবে একত্রে যুক্ত করা হলো
combo_acc_type.bind("<<ComboboxSelected>>", update_category_list)
combo_acc_fund.bind("<<ComboboxSelected>>", fund_selected)

def combined_category_handler(event):
    check_category_selection(event)
    auto_select_fund(event)

combo_acc_cat.bind("<<ComboboxSelected>>", combined_category_handler)

tk.Label(frame_acc_inputs, text="পরিমাণ (৳):", font=("Kalpurush", 10)).grid(row=1, column=0, sticky="w", pady=5)
entry_acc_amount = tk.Entry(frame_acc_inputs, font=("Kalpurush", 10), width=12)
entry_acc_amount.grid(row=1, column=1, pady=5, sticky="w")

tk.Label(frame_acc_inputs, text="বিবরণ (ঐচ্ছিক):", font=("Kalpurush", 10)).grid(row=1, column=2, sticky="w", pady=5, padx=(15, 0))
entry_acc_desc = tk.Entry(frame_acc_inputs, font=("Kalpurush", 10), width=35)
entry_acc_desc.grid(row=1, column=3, columnspan=3, pady=5, sticky="w")

def save_transaction():
    t_type = combo_acc_type.get()
    f_name = FUND_BY_DISPLAY.get(combo_acc_fund.get(), combo_acc_fund.get())
    cat = combo_acc_cat.get().strip()
    amount_str = entry_acc_amount.get().strip()
    desc = entry_acc_desc.get().strip()

    if cat == "বিবিধ":
        bibidh_text = entry_bibidh_detail.get().strip()
        if bibidh_text:
            cat = f"বিবিধ ({bibidh_text})"

    if not f_name or not cat or not amount_str:
        messagebox.showwarning("সতর্কতা", "ফান্ড, খাত এবং টাকার পরিমাণ প্রদান করুন!")
        return

    try:
        amount = float(amount_str)
    except ValueError:
        messagebox.showerror("ভুল তথ্য", "টাকার পরিমাণ সঠিকভাবে লিখুন।")
        return

    today_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (date, type, fund_name, category, amount, description) VALUES (?, ?, ?, ?, ?, ?)",
                   (today_str, t_type, f_name, cat, amount, desc))
    
    if t_type == "আয়":
        cursor.execute("UPDATE funds SET balance = balance + ? WHERE name = ?", (amount, f_name))
    else:
        cursor.execute("UPDATE funds SET balance = balance - ? WHERE name = ?", (amount, f_name))

    conn.commit()
    conn.close()

    messagebox.showinfo("সফল", "লেনদেন সফলভাবে সেভ হয়েছে!")
    entry_acc_amount.delete(0, tk.END)
    entry_acc_desc.delete(0, tk.END)
    entry_bibidh_detail.delete(0, tk.END)
    lbl_bibidh.pack_forget()
    entry_bibidh_detail.pack_forget()
    
    load_accounting_data()
    load_dashboard_data()
    load_funds_data()

btn_save_acc = tk.Button(frame_acc_inputs, text="➕ লেনদেন সেভ করুন", command=save_transaction, bg="#2e7d32", fg="white", font=("Kalpurush", 10, "bold"))
btn_save_acc.grid(row=1, column=6, padx=10, pady=5)

frame_acc_list = tk.LabelFrame(tab_accounting, text=" লেনদেন ইতিহাস (ক্যাশ বুক) ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_acc_list.pack(fill="both", expand=True, padx=10, pady=5)

acc_cols = ("id", "date", "type", "fund", "category", "amount", "desc")
tree_acc = ttk.Treeview(frame_acc_list, columns=acc_cols, show="headings")

tree_acc.heading("id", text="ID")
tree_acc.heading("date", text="তারিখ ও সময়")
tree_acc.heading("type", text="ধরন")
tree_acc.heading("fund", text="ফান্ড")
tree_acc.heading("category", text="খাত")
tree_acc.heading("amount", text="টাকা (৳)")
tree_acc.heading("desc", text="বিবরণ")

tree_acc.column("id", width=50, anchor="center")
tree_acc.column("date", width=140, anchor="center")
tree_acc.column("type", width=70, anchor="center")
tree_acc.column("fund", width=130, anchor="center")
tree_acc.column("category", width=190, anchor="w")
tree_acc.column("amount", width=100, anchor="center")
tree_acc.column("desc", width=220, anchor="w")

tree_acc.pack(fill="both", expand=True)

# ------------------------------------------
#   ট্যাব ৩: শরয়ী তহবিল (Fund)
# ------------------------------------------
tab_funds = ttk.Frame(notebook)
notebook.add(tab_funds, text=" 🏦 শরয়ী তহবিল (Fund) ")

frame_fund_add = tk.LabelFrame(tab_funds, text=" নতুন কাস্টম ফান্ড তৈরি ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_fund_add.pack(fill="x", padx=10, pady=5)

tk.Label(frame_fund_add, text="ফান্ডের নাম:", font=("Kalpurush", 10)).grid(row=0, column=0, sticky="w", pady=5)
entry_fund_name = tk.Entry(frame_fund_add, font=("Kalpurush", 10), width=20)
entry_fund_name.grid(row=0, column=1, pady=5, sticky="w")

tk.Label(frame_fund_add, text="ফান্ডের ধরন:", font=("Kalpurush", 10)).grid(row=0, column=2, sticky="w", pady=5, padx=(15, 0))
combo_fund_type = ttk.Combobox(frame_fund_add, values=["শরয়ী", "সাধারণ", "উন্নয়ন", "বিশেষ"], font=("Kalpurush", 10), width=12, state="readonly")
combo_fund_type.set("শরয়ী")
combo_fund_type.grid(row=0, column=3, pady=5, sticky="w")

def add_new_fund():
    f_name = entry_fund_name.get().strip()
    f_type = combo_fund_type.get()
    if not f_name:
        messagebox.showwarning("সতর্কতা", "ফান্ডের নাম লিখুন!")
        return
    
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO funds (name, type, balance) VALUES (?, ?, 0.0)", (f_name, f_type))
        conn.commit()
        messagebox.showinfo("সফল", "নতুন কাস্টম ফান্ড তৈরি হয়েছে!")
        entry_fund_name.delete(0, tk.END)
        load_funds_data()
        load_accounting_data()
    except sqlite3.IntegrityError:
        messagebox.showerror("এরর", "এই নামের ফান্ড ইতোমধ্যে আছে!")
    conn.close()

btn_add_fund = tk.Button(frame_fund_add, text="➕ কাস্টম ফান্ড যোগ করুন", command=add_new_fund, bg="#217346", fg="white", font=("Kalpurush", 10, "bold"))
btn_add_fund.grid(row=0, column=4, padx=15, pady=5)

frame_fund_list = tk.LabelFrame(tab_funds, text=" ফান্ড ভিত্তিক ব্যালেন্স ও স্টেটমেন্ট ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_fund_list.pack(fill="both", expand=True, padx=10, pady=5)

fund_cols = ("id", "name", "type", "inc", "exp", "bal")
tree_funds = ttk.Treeview(frame_fund_list, columns=fund_cols, show="headings")

tree_funds.heading("id", text="ID")
tree_funds.heading("name", text="ফান্ডের নাম")
tree_funds.heading("type", text="ফান্ডের ধরন")
tree_funds.heading("inc", text="মোট জমা (৳)")
tree_funds.heading("exp", text="মোট খরচ (৳)")
tree_funds.heading("bal", text="অবশিষ্ট ব্যালেন্স (৳)")

tree_funds.column("id", width=50, anchor="center")
tree_funds.column("name", width=220, anchor="w")
tree_funds.column("type", width=120, anchor="center")
tree_funds.column("inc", width=120, anchor="center")
tree_funds.column("exp", width=120, anchor="center")
tree_funds.column("bal", width=140, anchor="center")

tree_funds.pack(fill="both", expand=True)

# ------------------------------------------
#   ট্যাব ৪: ছাত্র ভর্তি ও প্রোফাইল
# ------------------------------------------
tab_students = ttk.Frame(notebook)
notebook.add(tab_students, text=" 🎓 ছাত্র ভর্তি ও প্রোফাইল ")

frame_st_inputs = tk.LabelFrame(tab_students, text=" নতুন ছাত্র ভর্তি ফরম ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_st_inputs.pack(fill="x", padx=10, pady=5)

tk.Label(frame_st_inputs, text="ছাত্রের নাম:", font=("Kalpurush", 9)).grid(row=0, column=0, sticky="w", pady=3)
entry_st_add_name = tk.Entry(frame_st_inputs, font=("Kalpurush", 9), width=18)
entry_st_add_name.grid(row=0, column=1, pady=3)

tk.Label(frame_st_inputs, text="পিতার নাম:", font=("Kalpurush", 9)).grid(row=1, column=0, sticky="w", pady=3)
entry_st_father = tk.Entry(frame_st_inputs, font=("Kalpurush", 9), width=18)
entry_st_father.grid(row=1, column=1, pady=3)

tk.Label(frame_st_inputs, text="অভিভাবক মোবাইল:", font=("Kalpurush", 9)).grid(row=2, column=0, sticky="w", pady=3)
entry_st_phone = tk.Entry(frame_st_inputs, font=("Kalpurush", 9), width=18)
entry_st_phone.grid(row=2, column=1, pady=3)

tk.Label(frame_st_inputs, text="জামাত/শ্রেনী:", font=("Kalpurush", 9)).grid(row=0, column=2, sticky="w", pady=3, padx=(15, 0))
entry_st_jamait = tk.Entry(frame_st_inputs, font=("Kalpurush", 9), width=12)
entry_st_jamait.grid(row=0, column=3, pady=3)

tk.Label(frame_st_inputs, text="রোল নম্বর:", font=("Kalpurush", 9)).grid(row=1, column=2, sticky="w", pady=3, padx=(15, 0))
entry_st_roll = tk.Entry(frame_st_inputs, font=("Kalpurush", 9), width=10)
entry_st_roll.grid(row=1, column=3, pady=3)

selected_photo_path = ""
def select_photo():
    global selected_photo_path
    path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
    if path:
        selected_photo_path = path
        lbl_photo_status.config(text="ছবি সিলেক্ট হয়েছে", fg="green")

btn_photo = tk.Button(frame_st_inputs, text="🖼️ ছবি আপলোড", command=select_photo, font=("Kalpurush", 8))
btn_photo.grid(row=3, column=0, pady=3)
lbl_photo_status = tk.Label(frame_st_inputs, text="ছবি সিলেক্ট করা হয়নি", font=("Kalpurush", 8), fg="gray")
lbl_photo_status.grid(row=3, column=1, pady=3, sticky="w")

frame_st_fees = tk.LabelFrame(tab_students, text=" নির্ধারিত ফি সেটআপ (টাকায়) ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_st_fees.pack(fill="x", padx=10, pady=5)

tk.Label(frame_st_fees, text="ভর্তি ফি:", font=("Kalpurush", 9)).grid(row=0, column=0, sticky="w", pady=3)
entry_st_adm_fee = tk.Entry(frame_st_fees, font=("Kalpurush", 9), width=10)
entry_st_adm_fee.insert(0, "0")
entry_st_adm_fee.grid(row=0, column=1, pady=3)

tk.Label(frame_st_fees, text="মাসিক ফি:", font=("Kalpurush", 9)).grid(row=0, column=2, sticky="w", pady=3, padx=(15, 0))
entry_st_mfee = tk.Entry(frame_st_fees, font=("Kalpurush", 9), width=10)
entry_st_mfee.insert(0, "0")
entry_st_mfee.grid(row=0, column=3, pady=3)

tk.Label(frame_st_fees, text="খোরাকি চার্জ:", font=("Kalpurush", 9)).grid(row=0, column=4, sticky="w", pady=3, padx=(15, 0))
entry_st_khoraki = tk.Entry(frame_st_fees, font=("Kalpurush", 9), width=10)
entry_st_khoraki.insert(0, "0")
entry_st_khoraki.grid(row=0, column=5, pady=3)

tk.Label(frame_st_fees, text="আবাসন ফি:", font=("Kalpurush", 9)).grid(row=1, column=0, sticky="w", pady=3)
entry_st_abasan = tk.Entry(frame_st_fees, font=("Kalpurush", 9), width=10)
entry_st_abasan.insert(0, "0")
entry_st_abasan.grid(row=1, column=1, pady=3)

tk.Label(frame_st_fees, text="বিদ্যুৎ বিল:", font=("Kalpurush", 9)).grid(row=1, column=2, sticky="w", pady=3, padx=(15, 0))
entry_st_electricity = tk.Entry(frame_st_fees, font=("Kalpurush", 9), width=10)
entry_st_electricity.insert(0, "0")
entry_st_electricity.grid(row=1, column=3, pady=3)

tk.Label(frame_st_fees, text="পরীক্ষার ফি:", font=("Kalpurush", 9)).grid(row=1, column=4, sticky="w", pady=3, padx=(15, 0))
entry_st_exam = tk.Entry(frame_st_fees, font=("Kalpurush", 9), width=10)
entry_st_exam.insert(0, "0")
entry_st_exam.grid(row=1, column=5, pady=3)

def save_student():
    name = entry_st_add_name.get().strip()
    father = entry_st_father.get().strip()
    jamait = entry_st_jamait.get().strip()
    roll = entry_st_roll.get().strip()
    phone = entry_st_phone.get().strip()
    
    try:
        adm_fee = float(entry_st_adm_fee.get().strip() or 0)
        mfee = float(entry_st_mfee.get().strip() or 0)
        khoraki = float(entry_st_khoraki.get().strip() or 0)
        abasan = float(entry_st_abasan.get().strip() or 0)
        electricity = float(entry_st_electricity.get().strip() or 0)
        exam = float(entry_st_exam.get().strip() or 0)
    except ValueError:
        messagebox.showerror("এরর", "ফি সেটআপে ভুল তথ্য দেওয়া হয়েছে!")
        return

    if not name or not jamait or not roll:
        messagebox.showwarning("সতর্কতা", "ছাত্রের নাম, জামাত এবং রোল প্রদান করা আবশ্যক!")
        return

    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO students (name, jamait, roll, father_name, guardian_phone, photo_path, admission_fee, monthly_fee, khoraki_fee, abasan_fee, electricity_fee, exam_fee)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, jamait, roll, father, phone, selected_photo_path, adm_fee, mfee, khoraki, abasan, electricity, exam))
    conn.commit()
    conn.close()

    messagebox.showinfo("সফল", "শিক্ষার্থী ভর্তি সম্পূর্ণ হয়েছে!")
    load_students_data()
    load_dashboard_data()

btn_save_st = tk.Button(tab_students, text="💾 ছাত্র সেভ করুন", command=save_student, bg="#2e7d32", fg="white", font=("Kalpurush", 10, "bold"), pady=5)
btn_save_st.pack(fill="x", padx=10, pady=5)

frame_st_list = tk.LabelFrame(tab_students, text=" নিবন্ধিত ছাত্রদের তালিকা ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_st_list.pack(fill="both", expand=True, padx=10, pady=5)

st_cols = ("id", "name", "jamait", "roll", "father", "phone", "mfee")
tree_st = ttk.Treeview(frame_st_list, columns=st_cols, show="headings")

tree_st.heading("id", text="ID")
tree_st.heading("name", text="নাম")
tree_st.heading("jamait", text="জামাত")
tree_st.heading("roll", text="রোল")
tree_st.heading("father", text="পিতার নাম")
tree_st.heading("phone", text="মোবাইল")
tree_st.heading("mfee", text="মাসিক ফি (৳)")

tree_st.column("id", width=40, anchor="center")
tree_st.column("name", width=160, anchor="w")
tree_st.column("jamait", width=100, anchor="center")
tree_st.column("roll", width=60, anchor="center")
tree_st.column("father", width=140, anchor="w")
tree_st.column("phone", width=110, anchor="center")
tree_st.column("mfee", width=90, anchor="center")

tree_st.pack(fill="both", expand=True)

# ------------------------------------------
#   ট্যাব ৫: ফি আদায় ও রশিদ প্রিন্ট
# ------------------------------------------
tab_fees = ttk.Frame(notebook)
notebook.add(tab_fees, text=" 📄 ফি আদায় ও রশিদ প্রিন্ট ")

frame_fee_form = tk.LabelFrame(tab_fees, text=" নতুন ফি জমার রসিদ তৈরি ", font=("Kalpurush", 11, "bold"), padx=15, pady=15)
frame_fee_form.pack(fill="x", padx=15, pady=10)

tk.Label(frame_fee_form, text="ছাত্র আইডি (ID) / রোল:", font=("Kalpurush", 10)).grid(row=0, column=0, sticky="w", pady=5)
entry_st_id = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=15)
entry_st_id.grid(row=0, column=1, pady=5, sticky="w")

def fetch_student_info():
    st_id = entry_st_id.get().strip()
    if not st_id:
        return
    
    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, jamait, roll, admission_fee, monthly_fee, khoraki_fee, abasan_fee, electricity_fee, exam_fee FROM students WHERE id = ? OR roll = ?", (st_id, st_id))
    student = cursor.fetchone()
    conn.close()

    if student:
        lbl_fee_st_name.config(text=f"{student[0]} ({student[1]}, রোল: {student[2]})", fg="#0d47a1")
        # সব ফি স্বয়ংক্রিয়ভাবে ফিল্ডে বসবে
        entry_fee_adm.delete(0, tk.END)
        entry_fee_adm.insert(0, str(student[3]))
        
        entry_fee_amount.delete(0, tk.END)
        entry_fee_amount.insert(0, str(student[4]))
        
        entry_fee_khoraki.delete(0, tk.END)
        entry_fee_khoraki.insert(0, str(student[5]))
        
        entry_fee_abasan.delete(0, tk.END)
        entry_fee_abasan.insert(0, str(student[6]))
        
        entry_fee_electricity.delete(0, tk.END)
        entry_fee_electricity.insert(0, str(student[7]))
        
        entry_fee_exam.delete(0, tk.END)
        entry_fee_exam.insert(0, str(student[8]))
    else:
        lbl_fee_st_name.config(text="কোনো ছাত্র সিলেক্ট করা নেই", fg="red")
        messagebox.showwarning("পাওয়া যায়নি", "এই আইডি বা রোলের কোনো শিক্ষার্থী পাওয়া যায়নি!")

btn_search = tk.Button(frame_fee_form, text="খুঁজুন", command=fetch_student_info, bg="#217346", fg="white", font=("Kalpurush", 9))
btn_search.grid(row=0, column=2, padx=5, pady=5)

lbl_fee_st_name = tk.Label(frame_fee_form, text="কোনো ছাত্র সিলেক্ট করা নেই", font=("Kalpurush", 10, "bold"), fg="red")
lbl_fee_st_name.grid(row=0, column=3, columnspan=3, padx=15)

# ভর্তি ফরমের সাথে মিল রেখে সব ফি ফিল্ড যুক্ত করা হলো
tk.Label(frame_fee_form, text="ভর্তি ফি:", font=("Kalpurush", 10)).grid(row=1, column=0, sticky="w", pady=5)
entry_fee_adm = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=10)
entry_fee_adm.insert(0, "0")
entry_fee_adm.grid(row=1, column=1, pady=5, sticky="w")

tk.Label(frame_fee_form, text="মাসিক ফি:", font=("Kalpurush", 10)).grid(row=1, column=2, sticky="w", pady=5, padx=(20, 0))
entry_fee_amount = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=10)
entry_fee_amount.insert(0, "0")
entry_fee_amount.grid(row=1, column=3, pady=5, sticky="w")

tk.Label(frame_fee_form, text="খোরাকি চার্জ:", font=("Kalpurush", 10)).grid(row=1, column=4, sticky="w", pady=5, padx=(20, 0))
entry_fee_khoraki = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=10)
entry_fee_khoraki.insert(0, "0")
entry_fee_khoraki.grid(row=1, column=5, pady=5, sticky="w")

tk.Label(frame_fee_form, text="আবাসন ফি:", font=("Kalpurush", 10)).grid(row=2, column=0, sticky="w", pady=5)
entry_fee_abasan = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=10)
entry_fee_abasan.insert(0, "0")
entry_fee_abasan.grid(row=2, column=1, pady=5, sticky="w")

tk.Label(frame_fee_form, text="বিদ্যুৎ বিল:", font=("Kalpurush", 10)).grid(row=2, column=2, sticky="w", pady=5, padx=(20, 0))
entry_fee_electricity = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=10)
entry_fee_electricity.insert(0, "0")
entry_fee_electricity.grid(row=2, column=3, pady=5, sticky="w")

tk.Label(frame_fee_form, text="পরীক্ষার ফি:", font=("Kalpurush", 10)).grid(row=2, column=4, sticky="w", pady=5, padx=(20, 0))
entry_fee_exam = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=10)
entry_fee_exam.insert(0, "0")
entry_fee_exam.grid(row=2, column=5, pady=5, sticky="w")

tk.Label(frame_fee_form, text="বিবরণ (ঐচ্ছিক):", font=("Kalpurush", 10)).grid(row=3, column=0, sticky="w", pady=5)
entry_fee_desc = tk.Entry(frame_fee_form, font=("Kalpurush", 10), width=30)
entry_fee_desc.grid(row=3, column=1, columnspan=3, pady=5, sticky="w")

def collect_fee_and_print():
    student_id = entry_st_id.get().strip()
    
    try:
        admfee = float(entry_fee_adm.get().strip() or 0)
        mfee = float(entry_fee_amount.get().strip() or 0)
        khoraki = float(entry_fee_khoraki.get().strip() or 0)
        abasan = float(entry_fee_abasan.get().strip() or 0)
        elecfee = float(entry_fee_electricity.get().strip() or 0)
        examfee = float(entry_fee_exam.get().strip() or 0)
    except ValueError:
        messagebox.showerror("ভুল তথ্য", "টাকার পরিমাণ সঠিকভাবে লিখুন।")
        return

    total_amount = admfee + mfee + khoraki + abasan + elecfee + examfee
    custom_desc = entry_fee_desc.get().strip()

    if not student_id or total_amount <= 0:
        messagebox.showwarning("সতর্কতা", "অনুগ্রহ করে শিক্ষার্থী নির্বাচন করুন এবং টাকার পরিমাণ লিখুন!")
        return

    today_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, jamait, roll FROM students WHERE id = ? OR roll = ?", (student_id, student_id))
    st_info = cursor.fetchone()

    cursor.execute('''
    INSERT INTO student_fees (student_id, student_name, jamait, roll, date, month_year, fee_category, amount)
    VALUES (?, ?, ?, ?, ?, 'কাস্টম রসিদ', 'বিভিন্ন ফি', ?)
    ''', (student_id, st_info[0] if st_info else "", st_info[1] if st_info else "", st_info[2] if st_info else "", today_str, total_amount))

    cursor.execute('''
    INSERT INTO transactions (date, type, fund_name, category, amount, description)
    VALUES (?, 'আয়', 'সাধারণ ফান্ড', 'মাসিক বেতন', ?, ?)
    ''', (today_str, total_amount, custom_desc))

    cursor.execute("UPDATE funds SET balance = balance + ? WHERE name = 'সাধারণ ফান্ড'", (total_amount,))

    conn.commit()
    conn.close()

    messagebox.showinfo("সফল", "ফি সফলভাবে জমা নেওয়া হয়েছে!")
    entry_fee_desc.delete(0, tk.END)
    load_dashboard_data()
    load_accounting_data()
    load_funds_data()

btn_save_fee = tk.Button(frame_fee_form, text="💾 ফি জমা নিন ও রশিদ প্রিন্ট করুন", command=collect_fee_and_print, bg="#2e7d32", fg="white", font=("Kalpurush", 11, "bold"), pady=5)
btn_save_fee.grid(row=4, column=0, columnspan=6, pady=15)

lbl_fee_hist = tk.Label(tab_fees, text="অতীতের ফি আদায়ের ইতিহাস", font=("Kalpurush", 10, "bold"))
lbl_fee_hist.pack(pady=(15, 0))

stf_hist_cols = ("id", "id_roll", "name_jamait", "fee_amount", "date")
tree_fee_hist = ttk.Treeview(tab_fees, columns=stf_hist_cols, show="headings", height=8)

tree_fee_hist.heading("id", text="রশিদ নং")
tree_fee_hist.heading("id_roll", text="আইডি/রোল")
tree_fee_hist.heading("name_jamait", text="ছাত্রের নাম ও জামাত")
tree_fee_hist.heading("fee_amount", text="পরিমাণ (৳)")
tree_fee_hist.heading("date", text="তারিখ")

tree_fee_hist.column("id", width=80, anchor="center")
tree_fee_hist.column("id_roll", width=120, anchor="center")
tree_fee_hist.column("name_jamait", width=250, anchor="w")
tree_fee_hist.column("fee_amount", width=120, anchor="center")
tree_fee_hist.column("date", width=150, anchor="center")

tree_fee_hist.pack(fill="x", padx=15, pady=5)

# ------------------------------------------
#   ট্যাব ৬: শিক্ষক ও কর্মচারী বেতন
# ------------------------------------------
tab_staff = ttk.Frame(notebook)
notebook.add(tab_staff, text=" 👨‍🏫 শিক্ষক/কর্মচারী বেতন ")

frame_stf_inputs = tk.LabelFrame(tab_staff, text=" নতুন শিক্ষক/কর্মচারী নিবন্ধন ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_stf_inputs.pack(fill="x", padx=10, pady=5)

tk.Label(frame_stf_inputs, text="নাম:", font=("Kalpurush", 10)).grid(row=0, column=0, sticky="w", pady=5)
entry_stf_name = tk.Entry(frame_stf_inputs, font=("Kalpurush", 10), width=20)
entry_stf_name.grid(row=0, column=1, pady=5)

tk.Label(frame_stf_inputs, text="পদবী:", font=("Kalpurush", 10)).grid(row=0, column=2, sticky="w", pady=5, padx=(15, 0))
entry_stf_desig = tk.Entry(frame_stf_inputs, font=("Kalpurush", 10), width=15)
entry_stf_desig.grid(row=0, column=3, pady=5)

tk.Label(frame_stf_inputs, text="মোবাইল:", font=("Kalpurush", 10)).grid(row=0, column=4, sticky="w", pady=5, padx=(15, 0))
entry_stf_phone = tk.Entry(frame_stf_inputs, font=("Kalpurush", 10), width=15)
entry_stf_phone.grid(row=0, column=5, pady=5)

tk.Label(frame_stf_inputs, text="মূল বেতন (৳):", font=("Kalpurush", 10)).grid(row=0, column=6, sticky="w", pady=5, padx=(15, 0))
entry_stf_salary = tk.Entry(frame_stf_inputs, font=("Kalpurush", 10), width=12)
entry_stf_salary.grid(row=0, column=7, pady=5)

def save_staff():
    name = entry_stf_name.get().strip()
    desig = entry_stf_desig.get().strip()
    phone = entry_stf_phone.get().strip()
    sal = entry_stf_salary.get().strip() or "0"

    if not name or not desig:
        messagebox.showwarning("সতর্কতা", "শিক্ষক/স্টাফের নাম এবং পদবী আবশ্যক!")
        return

    conn = sqlite3.connect("masjid_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO staff (name, designation, phone, basic_salary) VALUES (?, ?, ?, ?)",
                   (name, desig, phone, float(sal)))
    conn.commit()
    conn.close()

    messagebox.showinfo("সফল", "শিক্ষক/কর্মচারী সফলভাবে যুক্ত করা হয়েছে!")
    entry_stf_name.delete(0, tk.END)
    entry_stf_desig.delete(0, tk.END)
    entry_stf_phone.delete(0, tk.END)
    entry_stf_salary.delete(0, tk.END)
    load_staff_data()
    load_dashboard_data()

btn_save_stf = tk.Button(frame_stf_inputs, text="➕ শিক্ষক সেভ করুন", command=save_staff, bg="#2e7d32", fg="white", font=("Kalpurush", 10, "bold"))
btn_save_stf.grid(row=0, column=8, padx=15, pady=5)

frame_stf_list = tk.LabelFrame(tab_staff, text=" নিবন্ধিত শিক্ষক/কর্মচারী তালিকা ", font=("Kalpurush", 10, "bold"), padx=10, pady=10)
frame_stf_list.pack(fill="x", padx=10, pady=5)

stf_cols = ("id", "name", "desig", "phone", "salary")
tree_stf = ttk.Treeview(frame_stf_list, columns=stf_cols, show="headings", height=5)

tree_stf.heading("id", text="ID")
tree_stf.heading("name", text="নাম")
tree_stf.heading("desig", text="পদবী")
tree_stf.heading("phone", text="মোবাইল")
tree_stf.heading("salary", text="মূল বেতন (৳)")

tree_stf.column("id", width=50, anchor="center")
tree_stf.column("name", width=220, anchor="w")
tree_stf.column("desig", width=150, anchor="center")
tree_stf.column("phone", width=140, anchor="center")
tree_stf.column("salary", width=120, anchor="center")

tree_stf.pack(fill="both", expand=True)

# ------------------------------------------
#   বেতন প্রসেস করার পপআপ উইন্ডো
# ------------------------------------------
def open_salary_process_window():
    selected = tree_stf.selection()
    if not selected:
        messagebox.showwarning("নির্বাচন করুন", "অনুগ্রহ করে তালিকা থেকে একজন শিক্ষক সিলেক্ট করুন!")
        return

    item = tree_stf.item(selected[0])
    stf_id, name, desig, phone, basic_sal = item['values']

    sal_win = tk.Toplevel(root)
    sal_win.title(f"পূর্ণাঙ্গ বেতন পরিষদ - {name}")
    sal_win.geometry("520x620")
    sal_win.grab_set()

    f_bottom = tk.Frame(sal_win, bg="#e8f5e9", pady=10, padx=10, bd=2, relief="groove")
    f_bottom.pack(fill="x", side="bottom")

    canvas = tk.Canvas(sal_win)
    scrollbar = ttk.Scrollbar(sal_win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, padx=20, pady=10)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tk.Label(scroll_frame, text=f"{name} ({desig})", font=("Kalpurush", 13, "bold"), fg="#1b5e20").grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

    tk.Label(scroll_frame, text="মাস/বছর:", font=("Kalpurush", 10)).grid(row=1, column=0, sticky="w", pady=4)
    combo_s_month = ttk.Combobox(scroll_frame, values=["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"], font=("Kalpurush", 10), width=18, state="readonly")
    combo_s_month.set("আগস্ট")
    combo_s_month.grid(row=1, column=1, pady=4, sticky="w")

    fields = [
        ("মূল বেতন (৳):", str(basic_sal)),
        ("পূর্বের বকেয়া (৳):", "0"),
        ("অতিরিক্ত দায়িত্ব ভাতা (৳):", "0"),
        ("উৎসব বোনাস (৳):", "0"),
        ("চিকিৎসা ভাতা (৳):", "0"),
        ("আবাসন ভাতা (৳):", "0"),
        ("কর্তন/এডভান্স (Deduction):", "0")
    ]

    entries = {}
    for idx, (label_text, default_val) in enumerate(fields, start=2):
        tk.Label(scroll_frame, text=label_text, font=("Kalpurush", 10)).grid(row=idx, column=0, sticky="w", pady=4)
        e = tk.Entry(scroll_frame, font=("Kalpurush", 10), width=20)
        e.insert(0, default_val)
        e.grid(row=idx, column=1, pady=4, sticky="w")
        entries[label_text] = e

    lbl_net_val = tk.Label(scroll_frame, text=f"{float(basic_sal):.2f} ৳", font=("Kalpurush", 11, "bold"), fg="#0d47a1")
    
    def calculate_net():
        try:
            b = float(entries["মূল বেতন (৳):"].get().strip() or 0)
            p = float(entries["পূর্বের বকেয়া (৳):"].get().strip() or 0)
            ex = float(entries["অতিরিক্ত দায়িত্ব ভাতা (৳):"].get().strip() or 0)
            bo = float(entries["উৎসব বোনাস (৳):"].get().strip() or 0)
            m = float(entries["চিকিৎসা ভাতা (৳):"].get().strip() or 0)
            h = float(entries["আবাসন ভাতা (৳):"].get().strip() or 0)
            d = float(entries["কর্তন/এডভান্স (Deduction):"].get().strip() or 0)
            net = (b + p + ex + bo + m + h) - d
            lbl_net_val.config(text=f"{net:.2f} ৳")
            return net
        except ValueError:
            return 0.0

    btn_calc = tk.Button(scroll_frame, text="🧫 মোট হিসাব আপডেট", command=calculate_net, bg="#0288d1", fg="white", font=("Kalpurush", 9))
    btn_calc.grid(row=9, column=0, pady=8, sticky="w")
    
    tk.Label(scroll_frame, text="মোট প্রদেয় (Net):", font=("Kalpurush", 10, "bold")).grid(row=9, column=1, sticky="w")
    lbl_net_val.grid(row=9, column=1, sticky="e")

    tk.Label(scroll_frame, text="আজকে প্রদান (৳):", font=("Kalpurush", 10, "bold")).grid(row=10, column=0, sticky="w", pady=6)
    e_paid = tk.Entry(scroll_frame, font=("Kalpurush", 10, "bold"), width=20)
    e_paid.insert(0, str(basic_sal))
    e_paid.grid(row=10, column=1, pady=6, sticky="w")

    tk.Label(scroll_frame, text="নোট/বিবরণ:", font=("Kalpurush", 10)).grid(row=11, column=0, sticky="w", pady=4)
    e_note = tk.Entry(scroll_frame, font=("Kalpurush", 10), width=20)
    e_note.grid(row=11, column=1, pady=4, sticky="w")

    def process_payment():
        m_yr = combo_s_month.get()
        try:
            b_sal = float(entries["মূল বেতন (৳):"].get().strip() or 0)
            p_due = float(entries["পূর্বের বকেয়া (৳):"].get().strip() or 0)
            ex_duty = float(entries["অতিরিক্ত দায়িত্ব ভাতা (৳):"].get().strip() or 0)
            f_bonus = float(entries["উৎসব বোনাস (৳):"].get().strip() or 0)
            med = float(entries["চিকিৎসা ভাতা (৳):"].get().strip() or 0)
            house = float(entries["আবাসন ভাতা (৳):"].get().strip() or 0)
            deduct = float(entries["কর্তন/এডভান্স (Deduction):"].get().strip() or 0)
            paid = float(e_paid.get().strip() or 0)
        except ValueError:
            messagebox.showerror("ভুল ইনপুট", "সব ফিল্ডে সঠিকভাবে সংখ্যা ব্যবহার করুন!")
            return

        net_payable = (b_sal + p_due + ex_duty + f_bonus + med + house) - deduct
        curr_due = net_payable - paid
        
        note = e_note.get().strip()
        
        today_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        conn = sqlite3.connect("masjid_data.db")
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO salary_payments (staff_id, staff_name, designation, month_year, date, basic_salary, prev_due, extra_duty, festival_bonus, medical_allowance, housing_allowance, deduction, net_payable, paid_amount, current_due, extra_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (stf_id, name, desig, m_yr, today_str, b_sal, p_due, ex_duty, f_bonus, med, house, deduct, net_payable, paid, curr_due, note))

        cursor.execute("INSERT INTO transactions (date, type, fund_name, category, amount, description) VALUES (?, 'ব্যয়', 'সাধারণ ফান্ড', '১. শিক্ষক ও কর্মচারীদের বেতন', ?, ?)",
                       (today_str, paid, note))
        
        cursor.execute("UPDATE funds SET balance = balance - ? WHERE name = 'সাধারণ ফান্ড'", (paid, ))
        conn.commit()
        conn.close()

        messagebox.showinfo("সফল", f"{name}-এর বেতন সেভ হয়েছে এবং মূল ব্যয় শিটে যোগ করা হয়েছে!")
        sal_win.destroy()
        
        load_dashboard_data()
        load_accounting_data()
        load_funds_data()

    btn_pay_confirm = tk.Button(f_bottom, text="💾 বেতন সেভ করুন ও ব্যয় শিটে যোগ করুন", command=process_payment, bg="#2e7d32", fg="white", font=("Kalpurush", 11, "bold"), pady=6)
    btn_pay_confirm.pack(fill="x")

btn_pay_sal = tk.Button(tab_staff, text="💰 সিলেক্টেড শিক্ষকের বেতন প্রদান", command=open_salary_process_window, bg="#0d47a1", fg="white", font=("Kalpurush", 10, "bold"), pady=4)
btn_pay_sal.pack(fill="x", padx=10, pady=5)

load_dashboard_data()
load_accounting_data()
load_funds_data()
load_students_data()
load_staff_data()

root.mainloop()