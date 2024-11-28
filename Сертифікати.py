import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import re
import random
from tkinter import ttk

# Підключення до бази даних
conn = sqlite3.connect('certificates.db')
c = conn.cursor()

# Створення таблиці
c.execute('''CREATE TABLE IF NOT EXISTS certificates
             (protocol_number TEXT, date TEXT, company TEXT, car_number TEXT, note TEXT)''')
conn.commit()

# Функція для додавання сертифікату
def add_certificate():
    global protocol_entry, date_entry, company_entry, car_entry, note_text, msto_var, payment_var

    protocol_number = protocol_entry.get()
    date = date_entry.get()  # Дата повинна вводитися вручну
    company = company_entry.get()
    car_number = car_entry.get()
    msto_selected = msto_var.get()  # Отримання вибору для МСТО
    payment_text = payment_var.get()  # Отримання вибору оплати

    # Перевірка на заповненість усіх полів
    if not protocol_number or not company or not car_number or msto_selected == "Вибрати" or payment_text == "Вибрати":
        messagebox.showerror("Помилка", "Будь ласка, заповніть всі поля.")
        return

    # Форматування тексту МСТО
    msto_text = "МСТО: " + ("ТАК" if msto_selected == "ТАК" else "НІ")

    # Обробка способу оплати
    if payment_text == "Безготівка":
       payment_text = "не оплатив"

    # Створення запису з примітками
    note = f"{msto_text}\n{payment_text}\n" + note_text.get("1.0", tk.END).strip()

    car_number_with_status = car_number + "\nне готові"
    car_number_pattern = r"^[A-ZА-Я]{2}\d{4}[A-ZА-Я]{2}( / [A-ZА-Я]{2}\d{4}[A-ZА-Я]{2})?$"

    try:
        # Перевіряємо, чи дотримано форматів
        if re.match(car_number_pattern, car_number):
            # Вставка запису в базу даних
            c.execute("INSERT INTO certificates (protocol_number, date, company, car_number, note) VALUES (?, ?, ?, ?, ?)",
                      (protocol_number, date, company, car_number_with_status, note))
            conn.commit()
            show_all_records_30_percent()
            messagebox.showinfo("Успіх", "Запис додано до бази даних.")
        else:
            messagebox.showerror("Помилка", "Невірний формат номера машини або причепа. Використовуйте формат AA1234BB або AA1234BB / CC5678DD.")
    except sqlite3.Error as e:
        messagebox.showerror("Помилка бази даних", f"Помилка при вставці даних: {e}")

def format_car_number(event=None):
    text = car_entry.get().strip().upper()  # Отримуємо текст з поля введення

    # Оновлений регулярний вираз для розпізнавання номера машини і причепа
    car_trailer_pattern = r"^([A-ZА-Я]{2}\d{4}[A-ZА-Я]{2})( / ([A-ZА-Я]{2}\d{4}[A-ZА-Я]{2}))?$"
    
    # Підставляємо роздільник, якщо він відсутній і є два номери
    if re.match(car_trailer_pattern, text):
        # Якщо роздільник уже є, нічого не робимо
        car_entry.delete(0, tk.END)
        car_entry.insert(0, text)
    else:
        # Форматування номера з роздільником
        # Якщо вводиться тільки один номер, додаємо його
        if len(text) > 7 and not ' / ' in text:
            formatted_text = f"{text[:8]} / {text[8:]}" if len(text) > 8 else text
            car_entry.delete(0, tk.END)
            car_entry.insert(0, formatted_text)

# Функція для оновлення статусу запису на "готові" і оновлення віджета у вікні
def mark_as_ready(record):
    current_status = record[3].split('\n')[-1]  # Отримуємо поточний статус
    if current_status == "готові":
        messagebox.showwarning("Помилка", "Цей запис вже позначено як готовий.")
        return
    confirm = messagebox.askyesno("Підтвердження", "Ви впевнені, що цей запис готовий?")
    if confirm:
        # Оновлюємо статус запису в базі даних на "готові"
        updated_record = (record[0], record[1], record[2], record[3].replace("не готові", "готові"))
        c.execute("UPDATE certificates SET car_number = ? WHERE protocol_number = ?", (updated_record[3], updated_record[0]))
        conn.commit()
        # Оновлюємо віджет з інформацією про запис у вікні
        for widget in result_frame.winfo_children():
            widget.destroy()
        show_all_records_30_percent()

def mark_as_not_ready(record):
    current_status = record[3].split('\n')[-1]  # Отримуємо поточний статус
    if current_status != "готові":
        messagebox.showwarning("Помилка", "Цей запис вже позначено як не готовий.")
        return
    confirm = messagebox.askyesno("Підтвердження", "Ви впевнені, що цей запис не готовий?")
    if confirm:
        # Оновлюємо статус запису в базі даних на "не готові"
        updated_record = (record[0], record[1], record[2], record[3].replace("готові", "не готові"))
        c.execute("UPDATE certificates SET car_number = ? WHERE protocol_number = ?", (updated_record[3], updated_record[0]))
        conn.commit()
        # Оновлюємо віджет з інформацією про запис у вікні
        for widget in result_frame.winfo_children():
            widget.destroy()
        show_all_records_30_percent()

# Функція для відображення всіх записів з бази даних з врахуванням фільтрації за статусом
def on_enter(button):
    button.config(bg="#d4d4d4")  # Зміна фону при наведенні

def on_leave(button):
    button.config(bg="SystemButtonFace")  # Відновлення фону

def show_all_records_30_percent(status=None):
    # Оновлення вмісту бази даних
    if status:
        # Сортування від я до а
        c.execute("SELECT * FROM certificates WHERE car_number LIKE ? ORDER BY CAST(protocol_number AS INTEGER) DESC", (f'%\n{status}',))
    else:
        # Сортування від я до а
        c.execute("SELECT * FROM certificates ORDER BY CAST(protocol_number AS INTEGER) DESC")

    results = c.fetchall()
    
    # Очищення старих записів
    for widget in all_records_frame.winfo_children():
        widget.destroy()
    for widget in result_frame.winfo_children():
        widget.destroy()

    count_label = tk.Label(all_records_frame, text="", font=("Arial", 12), bg="#afc4e0")
    count_label.pack(side="bottom", fill=tk.X, padx=10, pady=5)

    records_canvas = tk.Canvas(all_records_frame, bd=0, highlightthickness=0)
    records_frame = tk.Frame(records_canvas)
    scrollbar = tk.Scrollbar(all_records_frame, orient="vertical", command=records_canvas.yview)
    records_canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    records_canvas.pack(side="left", fill="both", expand=True)
    records_canvas.create_window((0, 0), window=records_frame, anchor="nw")
    records_frame.bind("<Configure>", lambda e: records_canvas.configure(scrollregion=records_canvas.bbox("all")))
    records_frame.bind("<Enter>", lambda event, canvas=records_canvas: bind_scroll(canvas))
    records_frame.bind("<Leave>", lambda event, canvas=records_canvas: unbind_scroll(canvas))

    count = 0

    for row in results:
        # Визначення кольору рамки на основі статусу
        current_status = row[3].split('\n')[-1]  # Отримуємо статус
        if current_status == "готові":
            border_color = "#1f732d"  # Зелений
        else:
            border_color = "#751313"  # Червоний

        # Створення рамки з заданим кольором
        record_frame = tk.Frame(records_frame, bd=2, relief=tk.GROOVE, highlightbackground=border_color, highlightcolor=border_color, highlightthickness=2)
        record_frame.pack(fill=tk.X, padx=10, pady=5)

        # Виділення номера машини без статусу (видаляємо частину після нового рядка, якщо вона є)
        car_number = row[3].split('\n')[0]

        # Відображаємо Протокол№:, фірму і номер машини
        record_text = f"Протокол №:{row[0]}\n{row[2]}\n{car_number}"
        
        # Збільшення параметра width для кнопок
        record_button = tk.Button(record_frame, text=record_text, command=lambda r=row: edit_record(r), font=("Arial", 12), anchor='center', justify='center', width=50, height=4)

        # Додавання анімації при наведення курсору
        record_button.bind("<Enter>", lambda e, btn=record_button: on_enter(btn))  # Зміна фону при наведенні
        record_button.bind("<Leave>", lambda e, btn=record_button: on_leave(btn))  # Відновлення фону

        record_button.pack(fill=tk.X, expand=True)  # Використання expand=True
        
        count += 1

    count_label.config(text=f"Кількість сертифікатів: {count}")

# Функція для відображення лише записів зі статусом "не готові"
def show_not_ready_records():
    show_all_records_30_percent("не готові")
    # Очищення рядка пошуку
    search_entry.delete(0, tk.END)
# Функція для відображення всіх сертифікатів
def show_all_certificates():
    show_all_records_30_percent()
    # Очищення рядка пошуку
    search_entry.delete(0, tk.END)
# Функція для відображення готових сертифікатів
def show_ready_certificates():
    show_all_records_30_percent("готові")
    # Очищення рядка пошуку
    search_entry.delete(0, tk.END)

# Функція для заборони прокрутки за допомогою коліщатка миші
def unbind_scroll(canvas):
    canvas.unbind_all("<MouseWheel>")

# Функція для дозволу прокрутки за допомогою коліщатка миші
def bind_scroll(canvas):
    canvas.bind_all("<MouseWheel>", lambda event, canvas=canvas: on_mousewheel(event, canvas))

# Функція для обробки події прокрутки коліщатка миші
def on_mousewheel(event, canvas):
    canvas.yview_scroll(-1 * int(event.delta / 120), "units")
    
def delete_record(record):
    confirm = messagebox.askyesno("Підтвердження", "Ви впевнені, що хочете видалити цей запис?")
    if confirm:
        try:
            c.execute("DELETE FROM certificates WHERE protocol_number=?", (record[0],))
            conn.commit()
            # Оновлюємо віджети з усіма записами
            show_all_records_30_percent()
            # Оновлюємо пошук, щоб відобразити актуальні результати
            search()
            messagebox.showinfo("Успіх", "Запис успішно видалено.")
        except sqlite3.Error as e:
            messagebox.showerror("Помилка бази даних", f"Помилка при видаленні даних: {e}")


def edit_record(record):
    global protocol_entry, date_entry, company_entry, car_entry, note_text, msto_var, payment_entry

    # Очищення рядка пошуку
    search_entry.delete(0, tk.END)  # Очищуємо текст у полі пошуку

    # Очищення попереднього вмісту
    for widget in result_frame.winfo_children():
        widget.destroy()

    # Загальний стиль для рамки
    frame_style = {
        'bg': '#f9f9f9',
        'padx': 40,
        'pady': 30,
        'borderwidth': 5,
        'relief': 'flat'
    }

    # Створення рамки для полів введення
    input_frame = tk.Frame(result_frame, **frame_style)
    input_frame.pack(padx=20, pady=20, fill='both', expand=True)

    # Заголовок
    title_label = tk.Label(input_frame, text="Редагувати запис", font=("Helvetica", 24, 'bold'), bg='#f5f6fa', fg='#00030f')
    title_label.grid(row=0, columnspan=2, pady=(0, 20))

    # Функція для плавної анімації заголовка
    def scale_in(label, size=1.0):
        if size < 1.2:  # Збільшити до 1.2
            size += 0.05  # Збільшення розміру
            label.config(font=("Helvetica", int(24 * size), 'bold'))  # Зміна розміру шрифту
            label.after(50, scale_in, label, size)  # Затримка для плавного переходу

    scale_in(title_label)

    # Стиль для міток та полів
    label_font = ("Helvetica", 20)
    entry_font = ("Helvetica", 20)

    # Поле для редагування номера протоколу
    protocol_label = tk.Label(input_frame, text="Протокол №:", font=label_font, bg='#f9f9f9', fg='#555')
    protocol_label.grid(row=1, column=0, sticky='ew', padx=(0, 10), pady=(0, 5))

    # Рамка для поля вводу
    protocol_frame = tk.Frame(input_frame, bg='#f9f9f9')
    protocol_frame.grid(row=2, column=0, pady=(0, 10), padx=(0, 20), sticky='ew')

    # Поле вводу з рамками
    protocol_entry = tk.Entry(protocol_frame, font=entry_font, bd=2, relief='solid', width=15, justify='center')
    protocol_entry.insert(0, record[0])  # Вставка даних з запису
    protocol_entry.config(state='disabled')  # Поле неактивне
    protocol_entry.pack(fill='x', padx=5, pady=5)

    # Лінія під полем вводу (для анімації)
    bottom_line_protocol = tk.Frame(protocol_frame, height=2, bg='#cccccc')  # Початково сіра лінія
    bottom_line_protocol.pack(fill='x', side='bottom')

    # Анімація при натисканні на поле (зміна кольору та зростання лінії)
    def on_protocol_entry_click(event):
        bottom_line_protocol.config(bg='#007aff')  # Змінюємо колір лінії на синій (як у стилі Apple)

    # Анімація при наведенні курсору миші
    def on_protocol_mouse_enter(event):
        protocol_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_protocol_mouse_leave(event):
        protocol_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_protocol_entry_leave(event):
        bottom_line_protocol.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    # Прив'язка подій до поля вводу
    protocol_entry.bind("<FocusIn>", on_protocol_entry_click)  # При натисканні в полі вводу
    protocol_entry.bind("<FocusOut>", on_protocol_entry_leave)  # При втраті фокусу
    protocol_frame.bind("<Enter>", on_protocol_mouse_enter)  # При наведенні миші на поле
    protocol_frame.bind("<Leave>", on_protocol_mouse_leave)  # При виході миші з поля

    # Не забудьте про sticky для вашого grid
    protocol_label.grid(row=1, column=0, sticky='ew', padx=(0, 10), pady=(0, 5))

    # Поле для редагування дати
    date_label = tk.Label(input_frame, text="Дата :", font=label_font, bg='#f9f9f9', fg='#555')
    date_label.grid(row=1, column=1, sticky='ew', padx=(0, 10), pady=(0, 5))

    # Рамка для поля дати
    date_frame = tk.Frame(input_frame, bg='#f9f9f9')
    date_frame.grid(row=2, column=1, pady=(0, 10), padx=(20, 0), sticky='ew')

    # Ініціалізація поля для дати
    date_entry = tk.Entry(date_frame, font=entry_font, bd=2, relief='solid', justify='center', width=15)
    date_entry.insert(0, record[1])  # Вставка дати з запису, замість сьогоднішньої дати
    date_entry.pack(fill='x', padx=5, pady=5)

    # Лінія під полем дати
    bottom_line_date = tk.Frame(date_frame, height=2, bg='#cccccc')
    bottom_line_date.pack(fill='x', side='bottom')

    # Анімація при натисканні на поле дати
    def on_date_click(event):
        bottom_line_date.config(bg='#007aff')

    # Анімація при наведенні курсору миші на поле дати
    def on_mouse_enter(event):
        date_frame.config(bg='#cce0f0')

    def on_mouse_leave(event):
        date_frame.config(bg='#f9f9f9')

    def on_date_leave(event):
        bottom_line_date.config(bg='#cccccc')

    # Прив’язки подій для поля дати
    date_entry.bind("<FocusIn>", on_date_click)
    date_entry.bind("<FocusOut>", on_date_leave)
    date_entry.bind("<Enter>", on_mouse_enter)
    date_entry.bind("<Leave>", on_mouse_leave)

# Блокування вводу тексту
    def block_input(event):
        # Дозволяємо вводити лише цифри (0-9), крапку (.) та клавіші видалення
        if event.char.isdigit() or event.char == '.' or event.keysym in ('BackSpace', 'Delete'):
            return  # Дозволяємо введення
        return "break"  # Блокуємо всі інші натискання клавіш

    date_entry.bind("<KeyPress>", block_input)  # Блокування текстового вводу

    # Поле для редагування фірми
    company_label = tk.Label(input_frame, text="Фірма:", font=label_font, bg='#f9f9f9', fg='#555')
    company_label.grid(row=3, column=0, columnspan=2, sticky='ew', padx=(0, 10), pady=(0, 5))

    company_frame = tk.Frame(input_frame, bg='#f9f9f9')
    company_frame.grid(row=4, column=0, columnspan=2, pady=(5, 10), sticky='ew')

    company_entry = tk.Entry(company_frame, font=entry_font, bd=2, relief='solid', width=35, justify='center')
    company_entry.insert(0, record[2])  # Вставляємо фірму з запису
    company_entry.pack(fill='x', padx=5, pady=5)

    # Лінія під полем "Фірма" (для анімації)
    company_bottom_line = tk.Frame(company_frame, height=2, bg='#cccccc')
    company_bottom_line.pack(fill='x', side='bottom')

    # Додаємо обробник для автоматичного перетворення на верхній регістр
    def on_company_entry_change(event):
        current_text = company_entry.get()
        company_entry.delete(0, tk.END)
        company_entry.insert(0, current_text.upper())

    company_entry.bind("<KeyRelease>", on_company_entry_change)

    # Прив’язки подій для поля "Фірма"
    def on_company_entry_click(event):
        company_bottom_line.config(bg='#007aff')

    def on_company_mouse_enter(event):
        company_frame.config(bg='#cce0f0')

    def on_company_mouse_leave(event):
        company_frame.config(bg='#f9f9f9')

    def on_company_entry_leave(event):
        company_bottom_line.config(bg='#cccccc')

    company_entry.bind("<FocusIn>", on_company_entry_click)
    company_entry.bind("<FocusOut>", on_company_entry_leave)
    company_frame.bind("<Enter>", on_company_mouse_enter)
    company_frame.bind("<Leave>", on_company_mouse_leave)
    company_entry.bind("<KeyRelease>", on_company_entry_change)

    # Поле для редагування номера машини
    car_label = tk.Label(input_frame, text="Номер машини:", font=label_font, bg='#f9f9f9', fg='#555')
    car_label.grid(row=5, column=0, columnspan=2, sticky='ew', padx=(0, 10), pady=(0, 5))

    # Рамка для поля вводу номера машини
    car_frame = tk.Frame(input_frame, bg='#f9f9f9')
    car_frame.grid(row=6, column=0, columnspan=2, pady=(5, 10), sticky='ew')

    # Поле вводу з рамкою для номера машини
    car_entry = tk.Entry(car_frame, font=entry_font, bd=2, relief='solid', width=35, justify='center')
    car_entry.insert(0, record[3].split('\n')[0])  # Вставляємо номер машини з запису
    car_entry.pack(fill='x', padx=5, pady=5)

    # Лінія під полем вводу номера машини (для анімації)
    car_bottom_line = tk.Frame(car_frame, height=2, bg='#cccccc')  # Початково сіра лінія
    car_bottom_line.pack(fill='x', side='bottom')

    # Додаємо обробник для обмеження введення номера машини
    car_entry.bind('<KeyRelease>', format_car_number)

    # Анімація при натисканні на поле номера машини
    def on_car_entry_click(event):
        car_bottom_line.config(bg='#007aff')  # Змінюємо колір лінії на синій

    # Анімація при наведенні курсору миші на поле номера машини
    def on_car_mouse_enter(event):
        car_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_car_mouse_leave(event):
        car_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_car_entry_leave(event):
        car_bottom_line.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    # Прив'язуємо анімацію до поля вводу номера машини
    car_entry.bind("<FocusIn>", on_car_entry_click)  # При натисканні в полі вводу
    car_entry.bind("<FocusOut>", on_car_entry_leave)  # При втраті фокусу

    car_frame.bind("<Enter>", on_car_mouse_enter)  # При наведенні миші на поле
    car_frame.bind("<Leave>", on_car_mouse_leave)  # При виході миші з поля

    # Функція для зняття фокусу з інших полів
    def remove_focus(event=None):
        result_frame.focus_set()  # Встановлюємо фокус на невидимий елемент (рамку або будь-який інший елемент)

   # Меню вибору для "МСТО"
    msto_label = tk.Label(input_frame, text="Потреба МСТО: ", font=label_font, bg='#f9f9f9', fg='#555')
    msto_label.grid(row=7, column=0, sticky='ew', padx=(0, 10), pady=(0, 5))

    msto_frame = tk.Frame(input_frame, bg='#f9f9f9')
    msto_frame.grid(row=8, column=0, pady=(0, 10), padx=(0, 20), sticky='ew')

# Використовуємо StringVar для відображення вибору
    msto_var = tk.StringVar(value="Вибрати")  # Встановлюємо значення за замовчуванням

# Функція для автоматичного перетворення тексту в верхній регістр
    def on_msto_var_change(*args):
    # Отримуємо введене значення
        input_value = msto_var.get()
    # Перетворюємо текст у верхній регістр
        msto_var.set(input_value.upper())

# Прив'язуємо функцію до зміни значення msto_var
    msto_var.trace("w", on_msto_var_change)

# Створюємо текстове поле для відображення вибору
    msto_entry = tk.Entry(msto_frame, textvariable=msto_var, font=entry_font, bd=2, relief='solid', width=15, justify='center')
    msto_entry.pack(fill='x', padx=5, pady=5)

# Лінія під текстовим полем
    bottom_line_msto = tk.Frame(msto_frame, height=2, bg='#cccccc')
    bottom_line_msto.pack(fill='x', side='bottom')

# Анімація при натисканні на текстове поле
    def on_msto_entry_click(event):
        bottom_line_msto.config(bg='#007aff')  # Змінюємо колір лінії на синій

# Анімація при наведенні курсору миші на текстове поле
    def on_msto_mouse_enter(event):
        msto_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_msto_mouse_leave(event):
        msto_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_msto_leave(event):
        bottom_line_msto.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

# Прив'язки подій для текстового поля МСТО
    msto_entry.bind("<FocusIn>", on_msto_entry_click)
    msto_entry.bind("<FocusOut>", on_msto_leave)
    msto_frame.bind("<Enter>", on_msto_mouse_enter)
    msto_frame.bind("<Leave>", on_msto_mouse_leave)

# Вставляємо нотатки з запису (якщо потрібно)
    if "ТАК" in record[4]:  # Якщо вибір "ТАК"
        msto_var.set("ТАК")
    elif "НІ" in record[4]:  # Якщо вибір "НІ"
        msto_var.set("НІ")
    else:
        msto_var.set("Вибрати")  # Якщо нічого не вибрано

    # Створення текстового поля для "Спосіб оплати"
    payment_label = tk.Label(input_frame, text="Спосіб оплати:", font=label_font, bg='#f9f9f9', fg='#555')
    payment_label.grid(row=7, column=1, sticky='ew', padx=(0, 10), pady=(0, 5))

    payment_frame = tk.Frame(input_frame, bg='#f9f9f9')
    payment_frame.grid(row=8, column=1, pady=(0, 10), padx=(20, 0), sticky='ew')

# Використовуємо StringVar для зберігання вибору
    payment_var = tk.StringVar(value="Вибрати")  # Встановлюємо значення за замовчуванням

# Створюємо текстове поле для відображення способу оплати
    payment_entry = tk.Entry(payment_frame, font=entry_font, bd=2, relief='solid', width=15, justify='center')
    payment_entry.pack(fill='x', padx=5, pady=5)

# Лінія під текстовим полем
    bottom_line_payment = tk.Frame(payment_frame, height=2, bg='#cccccc')
    bottom_line_payment.pack(fill='x', side='bottom')

# Анімація при натисканні на текстове поле
    def on_payment_entry_click(event):
        bottom_line_payment.config(bg='#007aff')  # Змінюємо колір лінії на синій

# Анімація при наведенні курсору миші на текстове поле
    def on_payment_mouse_enter(event):
        payment_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_payment_mouse_leave(event):
        payment_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_payment_leave(event):
        bottom_line_payment.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

# Прив’язки подій для текстового поля способу оплати
    payment_entry.bind("<FocusIn>", on_payment_entry_click)
    payment_entry.bind("<FocusOut>", on_payment_leave)
    payment_frame.bind("<Enter>", on_payment_mouse_enter)
    payment_frame.bind("<Leave>", on_payment_mouse_leave)

# Функція для обробки введеного тексту
    def on_payment_entry_change(event):
        input_value = payment_entry.get()  # Отримуємо текст з поля
        payment_var.set(input_value)  # Встановлюємо вибране значення

# Прив'язуємо функцію до зміни тексту в полі
    payment_entry.bind("<KeyRelease>", on_payment_entry_change)

# Якщо спосіб оплати вже є в записі, відображаємо його
    payment_text = record[4].split('\n')[1]  # Витягуємо оплату з нотатки
    payment_entry.insert(0, payment_text)  # Вставляємо витягнуте значення

    # Поле для нотаток
    note_label = tk.Label(input_frame, text="Нотатка: (додаткове поле)", font=label_font, bg='#f9f9f9', fg='#555')
    note_label.grid(row=9, column=0, sticky='ew', padx=(0, 10), pady=(5, 0), columnspan=2)

    # Рамка для текстового поля нотаток
    note_frame = tk.Frame(input_frame, bg='#f9f9f9')
    note_frame.grid(row=10, column=0, columnspan=2, pady=(5, 10), sticky='ew')

    # Текстове поле для нотаток з видимою рамкою
    note_text = tk.Text(note_frame, font=entry_font, height=2, bd=2, relief='solid', width=40)  # Було width=30
    note_text.pack(fill='both', padx=5, pady=5)

    # Лінія під текстовим полем (для анімації)
    note_bottom_line = tk.Frame(note_frame, height=2, bg='#cccccc')  # Початково сіра лінія
    note_bottom_line.pack(fill='x', side='bottom')

    # Анімація для текстового поля
    def on_note_click(event):
        note_bottom_line.config(bg='#007aff')  # Змінюємо колір лінії на синій

    def on_note_leave(event):
        note_bottom_line.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    def on_note_enter(event):
        note_frame.config(bg='#cce0f0')  # Змінюємо фон рамки на світліший при наведенні

    def on_note_exit(event):
        note_frame.config(bg='#f9f9f9')  # Повертаємо фон рамки до початкового при виході миші

    # Прив'язка подій до текстового поля
    note_text.bind("<FocusIn>", on_note_click)  # При натисканні в полі нотаток
    note_text.bind("<FocusOut>", on_note_leave)  # При втраті фокусу
    note_frame.bind("<Enter>", on_note_enter)  # При наведенні миші на поле
    note_frame.bind("<Leave>", on_note_exit)  # При виході миші з поля

    # Вставляємо нотатки з запису
    note_text.insert(tk.END, "\n".join(record[4].split('\n')[2:]))  # Витягуємо нотатки з запису
# Переміщення фокусу на поле "Спосіб оплати"
    payment_entry.focus_set()

    # Функція для зміни кольору кнопки "Зберегти зміни" при наведенні
    def on_enter_save(button):
        button['bg'] = '#3a556b'
        button['fg'] = '#fff'

    # Функція для скидання кольору кнопки "Зберегти зміни" при виході
    def on_leave_save(button):
        button['bg'] = '#e7e7e7'
        button['fg'] = '#333'

    # Функція для зміни кольору кнопки "Готові" при наведенні
    def on_enter_ready(button):
        button['bg'] = '#3a556b'
        button['fg'] = '#fff'

    # Функція для скидання кольору кнопки "Готові" при виході
    def on_leave_ready(button):
        button['bg'] = '#e7e7e7'
        button['fg'] = '#333'

    # Функція для зміни кольору кнопки "Не готові" при наведенні
    def on_enter_not_ready(button):
        button['bg'] = '#3a556b'
        button['fg'] = '#fff'

    # Функція для скидання кольору кнопки "Не готові" при виході
    def on_leave_not_ready(button):
        button['bg'] = '#e7e7e7'
        button['fg'] = '#333'

    # Функція для зміни кольору кнопки "Видалити" при наведенні
    def on_enter_delete(button):
        button['bg'] = '#3a556b'
        button['fg'] = '#fff7f7'

    # Функція для скидання кольору кнопки "Видалити" при виході
    def on_leave_delete(button):
        button['bg'] = '#e7e7e7'
        button['fg'] = '#ff0000'
    
# Кнопка "Зберегти зміни"
    add_button = tk.Button(input_frame, text="Зберегти зміни", font=("Helvetica", 14),
                           command=lambda: save_edited_record(record[0]), 
                           bg='#e7e7e7', bd=0)

    add_button.grid(row=11, column=2, pady=10, sticky='ew')  # Переміщуємо кнопку на стовпець 2

# Анімація при наведенні для кнопки "Зберегти зміни"
    add_button.bind("<Enter>", lambda e: on_enter_save(add_button))
    add_button.bind("<Leave>", lambda e: on_leave_save(add_button))

# Кнопка "Готові"
    confirm_yes_button = tk.Button(input_frame, text="Позначити як (ГОТОВІ)", command=lambda r=record: mark_as_ready(r),
                                    font=("Helvetica", 14), bg='#e7e7e7', bd=0)

    confirm_yes_button.grid(row=11, column=0, padx=5, pady=10, sticky='ew')  # Зліва від кнопки "Зберегти зміни"

# Анімація для кнопки "Готові"
    confirm_yes_button.bind("<Enter>", lambda e: on_enter_ready(confirm_yes_button))
    confirm_yes_button.bind("<Leave>", lambda e: on_leave_ready(confirm_yes_button))

# Кнопка "Не готові"
    confirm_no_button = tk.Button(input_frame, text="Позначити як (НЕ ГОТОВІ)", command=lambda r=record: mark_as_not_ready(r),
                                   font=("Helvetica", 14), bg='#e7e7e7', bd=0)

    confirm_no_button.grid(row=11, column=1, padx=5, pady=10, sticky='ew')  # Поряд з кнопкою "Готові"

# Анімація для кнопки "Не готові"
    confirm_no_button.bind("<Enter>", lambda e: on_enter_not_ready(confirm_no_button))
    confirm_no_button.bind("<Leave>", lambda e: on_leave_not_ready(confirm_no_button))

# Кнопка "Видалити"
    delete_button = tk.Button(input_frame, text="🗑️Видалити", command=lambda: delete_record(record),
                               font=("Arial", 12),  # Зміна шрифту на Arial
                               bg="#e7e7e7",  # Білий фон
                               fg="#ff0000",  # Червоний текст
                               relief=tk.FLAT)  # Приглушений стиль для кращого вигляду
    delete_button.grid(row=11, column=3, padx=5, pady=10, sticky='ew')  # Праворуч від кнопки "Зберегти зміни"

# Анімація для кнопки "Видалити"
    delete_button.bind("<Enter>", lambda e: on_enter_delete(delete_button))
    delete_button.bind("<Leave>", lambda e: on_leave_delete(delete_button))

# Налаштування вирівнювання стовпців
    input_frame.grid_columnconfigure(0, weight=1)  # Готові
    input_frame.grid_columnconfigure(1, weight=1)  # Не готові
    input_frame.grid_columnconfigure(2, weight=1)  # Зберегти зміни
    input_frame.grid_columnconfigure(3, weight=1)  # Видалити

def format_car_number(event):
    input_text = car_entry.get()

    # Перетворюємо текст у верхній регістр
    formatted_text = input_text.upper()
    
    # Вилучаємо всі зайві символи (крім букв і цифр)
    formatted_text = re.sub(r'[^A-ZА-Я0-9]', '', formatted_text)

    # Якщо введено більше 8 символів, додаємо роздільник між тягачем і причепом
    if len(formatted_text) > 8:
        formatted_text = f"{formatted_text[:8]} / {formatted_text[8:]}"

    # Оновлюємо поле введення з відформатованим текстом
    car_entry.delete(0, tk.END)
    car_entry.insert(0, formatted_text)
    
def save_edited_record(protocol_number):
    global protocol_entry, date_entry, company_entry, car_entry, note_text, msto_var, payment_entry

    date = date_entry.get()
    company = company_entry.get()
    car_number = car_entry.get()
    note = note_text.get("1.0", tk.END).strip()

    # Перевірка типу оплати
    payment_text = payment_entry.get()
    
    # Форматування статусу МСТО
    msto_text = "МСТО: " + ("ТАК" if msto_var.get() == "ТАК" else "НІ")  # Переконайтеся, що тут все правильно
    full_note = f"{msto_text}\n{payment_text}\n{note}"

    # Встановлення шаблонів для перевірки дати та номера автомобіля
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    car_number_pattern = r"^[A-ZА-Я]{2}\d{4}[A-ZА-Я]{2}( / [A-ZА-Я]{2}\d{4}[A-ZА-Я]{2})?$"

    # Перевірка обов'язкових полів
    if not date.strip() or not company.strip() or not car_number.strip() or not payment_text.strip():
        messagebox.showerror("Помилка", "Будь ласка, заповніть всі поля.")
        return

    # Перевірка правильності формату дати та номера автомобіля
    if re.match(date_pattern, date) and re.match(car_number_pattern, car_number):
        # Отримання поточного статусу автомобіля з бази даних
        current_status = c.execute("SELECT car_number FROM certificates WHERE protocol_number=?", (protocol_number,)).fetchone()[0].split('\n')[-1]
        car_number_with_status = car_number + '\nне готові'
        if current_status == 'готові':
            car_number_with_status = car_number + '\nготові'
        
        # Оновлення запису в базі даних
        c.execute("UPDATE certificates SET date=?, company=?, car_number=?, note=? WHERE protocol_number=?",
                  (date, company, car_number_with_status, full_note, protocol_number))
        conn.commit()
        
        # Очищення рядка пошуку та оновлення відображення записів
        search_entry.delete(0, tk.END)
        show_all_records_30_percent()
        messagebox.showinfo("Успіх", "Запис успішно відредаговано.")
    else:
        # Виведення повідомлення про помилку у разі неправильного формату дати або номера автомобіля
        if not re.match(date_pattern, date):
            messagebox.showerror("Помилка", "Невірний формат дати. Використовуйте формат ДД.ММ.РРРР.")
        else:
            messagebox.showerror("Помилка", "Невірний формат номера машини. Використовуйте формат AA1234BB або AA1234BB / CC5678DD.")

def on_enter_button(event):
    event.widget['background'] = '#f0f0f0'  # Світлий колір фону при наведенні

def on_leave_button(event):
    event.widget['background'] = '#ffffff'  # Початковий колір фону

def search(event=None):
    search_term = search_entry.get().strip()  # Видаляємо пробіли з початку та кінця рядка

    # Очищення попередніх результатів
    for widget in result_frame.winfo_children():
        widget.destroy()

    if search_term:
        if filter_by_protocol.get():
            # Пошук тільки по номеру протоколу, сортуємо за спаданням
            c.execute("SELECT * FROM certificates WHERE protocol_number LIKE ? ORDER BY CAST(protocol_number AS INTEGER) DESC",
                      ('%' + search_term + '%',))
        else:
            # Пошук по номеру машини та фірмі, сортуємо за спаданням
            search_term_lower = search_term.lower()
            search_term_upper = search_term.upper()
            c.execute("SELECT * FROM certificates WHERE LOWER(car_number) LIKE ? OR UPPER(car_number) LIKE ? OR LOWER(company) LIKE ? OR UPPER(company) LIKE ? ORDER BY CAST(protocol_number AS INTEGER) DESC",
                      ('%' + search_term_lower + '%', '%' + search_term_upper + '%', '%' + search_term_lower + '%', '%' + search_term_upper + '%'))

        results = c.fetchall()

        # Створення Canvas і Scrollbar для прокрутки
        records_canvas = tk.Canvas(result_frame, bd=0, highlightthickness=0)
        records_frame = tk.Frame(records_canvas)
        scrollbar = tk.Scrollbar(result_frame, orient="vertical", command=records_canvas.yview)
        records_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        records_canvas.pack(side="left", fill="both", expand=True)
        records_canvas.create_window((0, 0), window=records_frame, anchor="nw")
        records_frame.bind("<Configure>", lambda e: records_canvas.configure(scrollregion=records_canvas.bbox("all")))
        records_frame.bind("<Enter>", lambda event, canvas=records_canvas: bind_scroll(canvas))
        records_frame.bind("<Leave>", lambda event, canvas=records_canvas: unbind_scroll(canvas))

        if results:
            for index, row in enumerate(results, start=1):
                # Отримуємо статус з номера машини
                current_status = row[3].split('\n')[-1]

                # Визначення кольору рамки
                if current_status.lower() == "готові":
                    border_color = "#ffffff"  # Білий для готових
                    status_icon = "✅"  # Іконка готовності
                elif current_status.lower() == "не готові":
                    border_color = "#ffffff"  # Білий для неготів
                    status_icon = "❌"  # Іконка неготовності
                else:
                    border_color = "#ffffff"
                    status_icon = "ℹ️"  # Нейтральна іконка

                # Створення фрейму для запису
                entry_frame = tk.Frame(records_frame)
                entry_frame.pack(fill=tk.X, padx=10, pady=5)

                # Створення рамки з фоновим кольором для запису
                record_frame = tk.Frame(entry_frame, bd=2, relief=tk.GROOVE, bg=border_color)
                record_frame.pack(side="left", fill=tk.X, expand=True)

                # Відображення номера протоколу зверху по центру
                protocol_number_label = tk.Label(record_frame, text=f"Протокол №: {row[0]}", font=("Arial", 18, "bold"),
                                                 bg=border_color, anchor="center")
                protocol_number_label.pack(fill=tk.X)

                # Розбиття нотатки на частини для відображення МСТО та оплати
                note_parts = row[4].split('\n')
                msto = note_parts[0] if len(note_parts) > 0 else "немає"
                oplata = note_parts[1] if len(note_parts) > 1 else "немає"
                note_text = "\n".join(note_parts[2:]) if len(note_parts) > 2 else ""

                # Перевірка, чи текст "Спосіб оплати" містить "не оплатив" і додавання цього тексту до нотаток, якщо він присутній
                if "не оплатив" in oplata.lower():
                    note_text += "\nне оплатив"

                # Оновлений текст з форматуванням
                record_text = (f"{row[2]}\n"
                               f"{row[3].replace(current_status, '').strip()}\n"
                               f"{msto}\n"
                               f"Спосіб оплати: {oplata}")

                # Створення кнопки з текстом по центру
                record_button = tk.Button(record_frame, text=record_text, command=lambda r=row: edit_record(r),
                                          font=("Arial", 14), anchor='center', justify='center', width=70, height=4, wraplength=400)
                record_button.pack(fill=tk.X, padx=5, pady=5)
                
                # Додавання подій для анімації наведення
                record_button.bind("<Enter>", on_enter_button)
                record_button.bind("<Leave>", on_leave_button)

                # Створення нотатки з червоним текстом
                note_label = tk.Label(record_frame, text=f"{note_text}", font=("Arial", 14), fg="red", bg=border_color, anchor="center")
                note_label.pack(fill=tk.X)

                # Створення фрейму для дати та статусу
                status_date_frame = tk.Frame(record_frame, bg=border_color)
                status_date_frame.pack(side="bottom", fill=tk.X)

                # Відображення дати зліва
                date_label = tk.Label(status_date_frame, text=row[1], bg=border_color, font=("Arial", 12))
                date_label.pack(side="left", padx=5, pady=5)

                # Відображення статусу справа з іконкою
                status_label = tk.Label(status_date_frame, text=f"{status_icon} {current_status}", bg=border_color, font=("Arial", 12))
                status_label.pack(side="right", padx=5)

                # Додати кнопку "Видалити" праворуч від запису
                delete_button = tk.Button(
                    entry_frame,
                    text="🗑️Видалити",
                    command=lambda r=row: delete_record(r),
                    font=("Arial", 12),
                    bg="#ffffff",
                    fg="#4a0101",
                    relief=tk.FLAT,
                )
                delete_button.pack(side="right", padx=5, pady=5)
                
                # Додавання подій для анімації наведення
                delete_button.bind("<Enter>", on_enter_button)
                delete_button.bind("<Leave>", on_leave_button)

                # Додавання горизонтального роздільника
                separator = tk.Frame(records_frame, height=2, bg="#e0e0e0")
                separator.pack(fill=tk.X, padx=10, pady=5)

        else:
            result_label = tk.Label(records_frame, text="Сертифікат не знайдено", font=("Arial", 30), fg="#330000", anchor="center")
            result_label.pack(pady=20)
    else:
        # Якщо пошуковий рядок порожній, очищаємо вікно результатів пошуку
        for widget in result_frame.winfo_children():
            widget.destroy()
# Функціонал закриття вікна
def close_app(event=None):
    root.destroy()

def add_certificate_directly():
    global protocol_entry, date_entry, company_entry, car_entry, note_text, msto_var, payment_var

    # Очищення попереднього вмісту
    for widget in result_frame.winfo_children():
        widget.destroy()

    # Загальний стиль для рамки
    frame_style = {
        'bg': '#f9f9f9',
        'padx': 40,
        'pady': 30,
        'borderwidth': 5,
        'relief': 'flat'
    }

    # Створення рамки для полів введення
    input_frame = tk.Frame(result_frame, **frame_style)
    input_frame.pack(padx=20, pady=20, fill='both', expand=True)

    # Заголовок
    title_label = tk.Label(input_frame, text="Додати запис", font=("Helvetica", 24, 'bold'), bg='#f5f6fa', fg='#00030f')
    title_label.grid(row=0, columnspan=2, pady=(0, 20))

    # Функція для плавної анімації заголовка
    def scale_in(label, size=1.0):
        if size < 1.2:  # Збільшити до 1.2
            size += 0.05  # Збільшення розміру
            label.config(font=("Helvetica", int(24 * size), 'bold'))  # Зміна розміру шрифту
            label.after(50, scale_in, label, size)  # Затримка для плавного переходу

    scale_in(title_label)

    # Стиль для міток та полів
    label_font = ("Helvetica", 20)
    entry_font = ("Helvetica", 20)

    # Поле для введення номера протоколу
    protocol_label = tk.Label(input_frame, text="Протокол №:", font=label_font, bg='#f9f9f9', fg='#555')
    protocol_label.grid(row=1, column=0, sticky='ew', padx=(0, 10), pady=(0, 5))

    # Рамка для поля вводу
    protocol_frame = tk.Frame(input_frame, bg='#f9f9f9')
    protocol_frame.grid(row=2, column=0, pady=(0, 10), padx=(0, 20), sticky='ew')

    # Поле вводу з рамками
    protocol_entry = tk.Entry(protocol_frame, font=entry_font, bd=2, relief='solid', width=15, justify='center')  # Було width=10
    protocol_entry.pack(fill='x', padx=5, pady=5)

    # Лінія під полем вводу (для анімації)
    bottom_line_protocol = tk.Frame(protocol_frame, height=2, bg='#cccccc')  # Початково сіра лінія
    bottom_line_protocol.pack(fill='x', side='bottom')

    # Додаємо обробник для обмеження введення
    def validate_protocol_input(event):
        char = event.char
        allowed_characters = "0123456789-+*/ "
        if char not in allowed_characters and char not in ('\x08', '\x7f'):
            return "break"

    protocol_entry.bind("<KeyPress>", validate_protocol_input)

    # Анімація при натисканні на поле (зміна кольору та зростання лінії)
    def on_protocol_entry_click(event):
        bottom_line_protocol.config(bg='#007aff')  # Змінюємо колір лінії на синій (як у стилі Apple)

    # Анімація при наведенні курсору миші
    def on_protocol_mouse_enter(event):
        protocol_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_protocol_mouse_leave(event):
        protocol_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_protocol_entry_leave(event):
        bottom_line_protocol.config(bg='#cccccc')  # Повертаємо лінію до сірої при втраті фокусу

    # Упевніться, що елементи не зміщуються, використовуючи fill та expand
    input_frame.pack(fill='both', expand=True)

    # Не забудьте про sticky для вашого grid
    protocol_label.grid(row=1, column=0, sticky='ew', padx=(0, 10), pady=(0, 5))

    protocol_entry.bind("<FocusIn>", on_protocol_entry_click)  # При натисканні в полі вводу
    protocol_entry.bind("<FocusOut>", on_protocol_entry_leave)  # При втраті фокусу

    protocol_frame.bind("<Enter>", on_protocol_mouse_enter)  # При наведенні миші на поле
    protocol_frame.bind("<Leave>", on_protocol_mouse_leave)  # При виході миші з поля

    # Автоматичне встановлення фокусу на поле вводу протоколу
    protocol_entry.focus_set()  # Додаємо цю строку
    
    # Поле для введення дати
    date_label = tk.Label(input_frame, text="Дата:", font=("Helvetica", 20), bg='#f9f9f9', fg='#555')
    date_label.grid(row=1, column=1, sticky='ew', padx=(0, 10), pady=(0, 5))

    # Поле вводу дати
    date_frame = tk.Frame(input_frame, bg='#f9f9f9')
    date_frame.grid(row=2, column=1, pady=(0, 10), padx=(20, 0), sticky='ew')

    date_entry = tk.Entry(date_frame, font=("Helvetica", 20), bd=2, relief='solid', width=15, justify='center')
    date_entry.pack(fill='x', padx=5, pady=5)

    # Встановлення сьогоднішньої дати
    today_date = datetime.today().strftime('%d.%m.%Y')
    date_entry.insert(0, today_date)  # Вставляємо сьогоднішню дату

    # Лінія під полем дати
    bottom_line_date = tk.Frame(date_frame, height=2, bg='#cccccc')
    bottom_line_date.pack(fill='x', side='bottom')

    # Валідація вводу дати
    def validate_date_input(event):
        char = event.char
        allowed_characters = "0123456789."
        if char not in allowed_characters and char not in ('\x08', '\x7f', '\x09', '\x13'):
            return "break"

    date_entry.bind("<KeyPress>", validate_date_input)

    # Анімація при натисканні на поле
    def on_date_click(event):
        bottom_line_date.config(bg='#007aff')

    # Анімація при наведенні курсору миші
    def on_mouse_enter(event):
        date_frame.config(bg='#cce0f0')

    def on_mouse_leave(event):
        date_frame.config(bg='#f9f9f9')

    def on_date_leave(event):
        bottom_line_date.config(bg='#cccccc')

    date_entry.bind("<FocusIn>", on_date_click)
    date_entry.bind("<FocusOut>", on_date_leave)
    date_entry.bind("<Enter>", on_mouse_enter)
    date_entry.bind("<Leave>", on_mouse_leave)

    # Поле для введення фірми
    company_label = tk.Label(input_frame, text="Фірма:", font=label_font, bg='#f9f9f9', fg='#555')
    company_label.grid(row=3, column=0, columnspan=2, sticky='ew', padx=(0, 10), pady=(0, 5))  # Додаємо columnspan для центрування

    # Рамка для поля вводу "Фірма"
    company_frame = tk.Frame(input_frame, bg='#f9f9f9')
    company_frame.grid(row=4, column=0, columnspan=2, pady=(5, 10), sticky='ew')

    # Поле вводу з рамками для фірми
    company_entry = tk.Entry(company_frame, font=entry_font, bd=2, relief='solid', width=35, justify='center')  # Було width=30
    company_entry.pack(fill='x', padx=5, pady=5)

    # Лінія під полем вводу "Фірма" (для анімації)
    company_bottom_line = tk.Frame(company_frame, height=2, bg='#cccccc')  # Початково сіра лінія
    company_bottom_line.pack(fill='x', side='bottom')

    # Додаємо обробник для автоматичного перетворення на верхній регістр
    def on_company_entry_change(event):
        current_text = company_entry.get()  # Отримуємо текст з поля вводу
        company_entry.delete(0, tk.END)  # Очищаємо поле вводу
        company_entry.insert(0, current_text.upper())  # Вставляємо текст у верхньому регістрі

    company_entry.bind("<KeyRelease>", on_company_entry_change)  # Зв'язуємо обробник з подією

    # Анімація при натисканні на поле "Фірма"
    def on_company_entry_click(event):
        company_bottom_line.config(bg='#007aff')  # Змінюємо колір лінії на синій

    # Анімація при наведенні курсору миші на поле "Фірма"
    def on_company_mouse_enter(event):
        company_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_company_mouse_leave(event):
        company_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_company_entry_leave(event):
        company_bottom_line.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    # Прив'язуємо анімацію до поля вводу "Фірма"
    company_entry.bind("<FocusIn>", on_company_entry_click)  # При натисканні в полі вводу
    company_entry.bind("<FocusOut>", on_company_entry_leave)  # При втраті фокусу

    company_frame.bind("<Enter>", on_company_mouse_enter)  # При наведенні миші на поле
    company_frame.bind("<Leave>", on_company_mouse_leave)  # При виході миші з поля

    company_entry.bind("<KeyRelease>", on_company_entry_change)  # Зв'язуємо обробник з подією
    
    # Поле для номера машини
    car_label = tk.Label(input_frame, text="Номер машини:", font=label_font, bg='#f9f9f9', fg='#555')
    car_label.grid(row=5, column=0, columnspan=2, sticky='ew', padx=(0, 10), pady=(0, 5))

    # Рамка для поля вводу номера машини
    car_frame = tk.Frame(input_frame, bg='#f9f9f9')
    car_frame.grid(row=6, column=0, columnspan=2, pady=(5, 10), sticky='ew')

    # Поле вводу з рамкою для номера машини
    car_entry = tk.Entry(car_frame, font=entry_font, bd=2, relief='solid', width=35, justify='center')  # Було width=30
    car_entry.pack(fill='x', padx=5, pady=5)

    # Лінія під полем вводу номера машини (для анімації)
    car_bottom_line = tk.Frame(car_frame, height=2, bg='#cccccc')  # Початково сіра лінія
    car_bottom_line.pack(fill='x', side='bottom')

    # Додаємо обробник для обмеження введення номера машини
    car_entry.bind('<KeyRelease>', format_car_number)

    # Анімація при натисканні на поле номера машини
    def on_car_entry_click(event):
        car_bottom_line.config(bg='#007aff')  # Змінюємо колір лінії на синій
    # Анімація при наведенні курсору миші на поле номера машини
    def on_car_mouse_enter(event):
        car_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_car_mouse_leave(event):
        car_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_car_entry_leave(event):
        car_bottom_line.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    # Прив'язуємо анімацію до поля вводу номера машини
    car_entry.bind("<FocusIn>", on_car_entry_click)  # При натисканні в полі вводу
    car_entry.bind("<FocusOut>", on_car_entry_leave)  # При втраті фокусу

    car_frame.bind("<Enter>", on_car_mouse_enter)  # При наведенні миші на поле
    car_frame.bind("<Leave>", on_car_mouse_leave)  # При виході миші з поля
# Функція для зняття фокусу з інших полів
    def remove_focus(event):
        result_frame.focus_set()  # Встановлюємо фокус на невидимий елемент (рамку або будь-який інший елемент)

    # Функція для зняття фокусу з інших полів
    def remove_focus(event=None):
        result_frame.focus_set()  # Встановлюємо фокус на невидимий елемент (рамку або будь-який інший елемент)

    # Меню вибору для "МСТО"
    msto_label = tk.Label(input_frame, text="Потреба МСТО: ", font=label_font, bg='#f9f9f9', fg='#555')
    msto_label.grid(row=7, column=0, sticky='ew', padx=(0, 10), pady=(0, 5))

    msto_frame = tk.Frame(input_frame, bg='#f9f9f9')
    msto_frame.grid(row=8, column=0, pady=(0, 10), padx=(0, 20), sticky='ew')

    msto_var = tk.StringVar(value="Вибрати")  # Встановлюємо значення за замовчуванням

    msto_options = ["ТАК", "НІ"]
    msto_menu = tk.OptionMenu(msto_frame, msto_var, *msto_options)
    msto_menu.config(font=entry_font, width=15)  # Було width=10
    msto_menu['menu'].config(bg='#f9f9f9', activebackground='#007aff', font=entry_font)  # Налаштування стилю меню
    msto_menu.pack(fill='x', padx=5, pady=5)

    # Прив'язуємо функцію зняття фокусу до натискання на меню "МСТО"
    msto_menu.bind("<Button-1>", remove_focus)  # Знімаємо фокус при натисканні на меню

    # Лінія під меню вибору МСТО
    bottom_line_msto = tk.Frame(msto_frame, height=2, bg='#cccccc')
    bottom_line_msto.pack(fill='x', side='bottom')

    # Анімація при натисканні на меню МСТО
    def on_msto_click(event):
        bottom_line_msto.config(bg='#007aff')  # Змінюємо колір лінії на синій

    # Анімація при наведенні курсору миші на меню МСТО
    def on_msto_mouse_enter(event):
        msto_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_msto_mouse_leave(event):
        msto_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_msto_leave(event):
        bottom_line_msto.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    # Прив’язки подій для меню МСТО
    msto_menu.bind("<FocusIn>", on_msto_click)
    msto_menu.bind("<FocusOut>", on_msto_leave)
    msto_frame.bind("<Enter>", on_msto_mouse_enter)
    msto_frame.bind("<Leave>", on_msto_mouse_leave)

    # Створення меню вибору для "Спосіб оплати"
    payment_label = tk.Label(input_frame, text="Спосіб оплати:", font=label_font, bg='#f9f9f9', fg='#555')
    payment_label.grid(row=7, column=1, sticky='ew', padx=(0, 10), pady=(0, 5))

    payment_frame = tk.Frame(input_frame, bg='#f9f9f9')
    payment_frame.grid(row=8, column=1, pady=(0, 10), padx=(20, 0), sticky='ew')

    payment_var = tk.StringVar(value="Вибрати")  # Встановлюємо значення за замовчуванням

    payment_options = ["Готівка", "Безготівка"]
    payment_menu = tk.OptionMenu(payment_frame, payment_var, *payment_options)
    payment_menu.config(font=entry_font, width=15)  # Було width=10
    payment_menu['menu'].config(bg='#f9f9f9', activebackground='#007aff', font=entry_font)  # Налаштування стилю меню
    payment_menu.pack(fill='x', padx=5, pady=5)

    # Лінія під меню вибору оплати
    bottom_line_payment = tk.Frame(payment_frame, height=2, bg='#cccccc')
    bottom_line_payment.pack(fill='x', side='bottom')

    # Анімація при натисканні на меню оплати
    def on_payment_click(event):
        bottom_line_payment.config(bg='#007aff')  # Змінюємо колір лінії на синій

    # Анімація при наведенні курсору миші на меню оплати
    def on_payment_mouse_enter(event):
        payment_frame.config(bg='#cce0f0')  # Змінюємо фон на світліший при наведенні

    def on_payment_mouse_leave(event):
        payment_frame.config(bg='#f9f9f9')  # Повертаємо фон до початкового при виході миші

    def on_payment_leave(event):
        bottom_line_payment.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    # Прив'язуємо функцію зняття фокусу до натискання на меню "Спосіб оплати"
    payment_menu.bind("<Button-1>", remove_focus)  # Знімаємо фокус при натисканні на меню

    # Прив’язки подій для меню оплати
    payment_menu.bind("<FocusIn>", on_payment_click)
    payment_menu.bind("<FocusOut>", on_payment_leave)
    payment_frame.bind("<Enter>", on_payment_mouse_enter)
    payment_frame.bind("<Leave>", on_payment_mouse_leave)

    # Поле для нотаток
    note_label = tk.Label(input_frame, text="Нотатка:(додаткове поле)", font=label_font, bg='#f9f9f9', fg='#555')
    note_label.grid(row=9, column=0, sticky='ew', padx=(0, 10), pady=(5, 0), columnspan=2)

# Рамка для текстового поля нотаток
    note_frame = tk.Frame(input_frame, bg='#f9f9f9')
    note_frame.grid(row=10, column=0, columnspan=2, pady=(5, 10), sticky='ew')

# Текстове поле для нотаток з видимою рамкою
    note_text = tk.Text(note_frame, font=entry_font, height=2, bd=2, relief='solid', width=40)  # Було width=30
    note_text.pack(fill='both', padx=5, pady=5)

# Лінія під текстовим полем (для анімації)
    note_bottom_line = tk.Frame(note_frame, height=2, bg='#cccccc')  # Початково сіра лінія
    note_bottom_line.pack(fill='x', side='bottom')

# Анімація для текстового поля
    def on_note_click(event):
        note_bottom_line.config(bg='#007aff')  # Змінюємо колір лінії на синій

    def on_note_leave(event):
        note_bottom_line.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

    def on_note_enter(event):
        note_frame.config(bg='#cce0f0')  # Змінюємо фон рамки на світліший при наведенні

    def on_note_exit(event):
        note_frame.config(bg='#f9f9f9')  # Повертаємо фон рамки до початкового при виході миші

# Прив'язка подій до текстового поля
    note_text.bind("<FocusIn>", on_note_click)  # При натисканні в полі нотаток
    note_text.bind("<FocusOut>", on_note_leave)  # При втраті фокусу
    note_frame.bind("<Enter>", on_note_enter)  # При наведенні миші на поле
    note_frame.bind("<Leave>", on_note_exit)  # При виході миші з поля

    # Кнопка для додавання запису з анімацією при наведенні
    def on_enter(e):
        add_button['bg'] = '#3a556b'
        add_button['fg'] = '#fff'
    
    def on_leave(e):
        add_button['bg'] = '#e7e7e7'
        add_button['fg'] = '#333'

    add_button = tk.Button(input_frame, text="Додати запис", font=("Helvetica", 14), command=add_certificate, bg='#e7e7e7', bd=0)
    add_button.grid(row=11, columnspan=2, pady=10)
    add_button.bind("<Enter>", on_enter)
    add_button.bind("<Leave>", on_leave)

    # Очищення рядка пошуку
    search_entry.delete(0, tk.END)
    
    # Розміщення фрейму результатів пошуку
    result_frame.place(x=20, y=130, width=root.winfo_screenwidth() * 0.7 - 40, height=root.winfo_screenheight() - 200)
    
# Змінні для кроків зміни кольорів
r_step, g_step, b_step = 0.3, 0.3, -0.3  # Невеликі кроки для зміни кольорів
min_value, max_value = 50, 100  # Діапазон для RGB (менш яскраві кольори)

# Встановлюємо початковий колір
start_r, start_g, start_b = 59, 81, 115  # RGB для #3b5173

def change_bg_color(r, g, b):
    global r_step, g_step, b_step  # Вказуємо, що використовуємо глобальні змінні
    
    # Формуємо новий колір у форматі HEX
    color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
    root.config(bg=color)
    
    # Оновлюємо кольори
    r += r_step
    g += g_step
    b += b_step
    
    # Перевіряємо межі для компонентів RGB, щоб залишитися близько до основного кольору
    if r > start_r + 10 or r < start_r - 10:
        r_step *= -1
        r = max(min_value, min(max_value, r))
    if g > start_g + 10 or g < start_g - 10:
        g_step *= -1
        g = max(min_value, min(max_value, g))
    if b > start_b + 10 or b < start_b - 10:
        b_step *= -1
        b = max(min_value, min(max_value, b))
    
    # Задаємо новий таймер для наступного оновлення кольору
    root.after(50, change_bg_color, r, g, b)  # Збільшено інтервал зміни кольору

def start_color_change():
    # Затримка на 2 секунди (2000 мілісекунд) перед початком зміни кольору
    root.after(2000, change_bg_color, start_r, start_g, start_b)

def on_protocol_checkbox_toggle():
    # Очищення рядка пошуку
    search_entry.delete(0, tk.END)
    # Додатковий код для зміни пошукового фільтра, якщо потрібно
    search()  # Якщо потрібно оновити результати пошуку

def on_key_press(event):
    # Вивести символ, незалежно від розкладки
    if event.keysym in ['и', 'i']:  # українська "и" і англійська "i"
        print("Натиснуто 'и' або 'i'")
    # Можна додати інші умови для інших клавіш
    else:
        print(f"Натиснуто іншу клавішу: {event.keysym}")

# GUI
root = tk.Tk()
root.title("Менеджер сертифікатів")

# Зробити вікно максимально можливим
root.state('zoomed')  # Максимізуємо вікно

# Додати опцію закриття
def close_app(event=None):
    root.destroy()
def clean_car_entry(event=None):
    # Отримуємо текст з поля вводу
    car_number = car_entry.get()

    # Видаляємо зайві переноси рядків і пробіли
    car_number = car_number.replace("\n", "").replace("\r", "").strip()

    # Оновлюємо поле з виправленим значенням
    car_entry.delete(0, tk.END)
    car_entry.insert(0, car_number)

# Встановлюємо фоновий колір на стартовий
root.config(bg="#3b5173")

# Запускаємо анімацію зміни кольору через 2 секунди
start_color_change()

# Функції для зміни кольору кнопки пошуку при наведенні миші
def on_enter_search(e):
    search_button['bg'] = '#3a556b'
    search_button['fg'] = '#fff'

def on_leave_search(e):
    search_button['bg'] = '#e7e7e7'
    search_button['fg'] = '#333'

# Кнопка пошуку
search_button = tk.Button(root, text="Пошук", command=search, font=("Arial", 24), bg='#e7e7e7')
search_button.place(x=280, y=10, width=150)
search_button.bind("<Enter>", on_enter_search)
search_button.bind("<Leave>", on_leave_search)

# Очищення рядка пошуку
def clear_search_entry():
    search_entry.delete(0, tk.END)  # Очищуємо текст у полі пошуку

# Функції для зміни кольору тексту чекбоксу при наведенні миші
def on_enter_protocol_checkbox(e):
    if not filter_by_protocol.get():  # Якщо чекбокс не активовано
        protocol_checkbox['fg'] = '#114dad'  # Змінити колір тексту на темно-синій

def on_leave_protocol_checkbox(e):
    if not filter_by_protocol.get():  # Якщо чекбокс не активовано
        protocol_checkbox['fg'] = '#000000'  # Змінити колір тексту на чорний

def on_protocol_checkbox_toggle():
    # Перевірка стану чекбокса і зміна кольору тексту
    if filter_by_protocol.get():
        protocol_checkbox['fg'] = '#002fff'  # Залишити темно-синій при активованому стані
    else:
        protocol_checkbox['fg'] = '#000000'  # Повернути до чорного при деактивованому стані
    
    clear_search_entry()  # Очищення рядка пошуку при зміні стану чекбокса

# Створення змінної для чекбоксу
filter_by_protocol = tk.BooleanVar()

# Додавання чекбоксу з текстом
protocol_checkbox = tk.Checkbutton(
    root,
    text="Пошук тільки по номеру протоколу",
    variable=filter_by_protocol,
    font=("Arial", 12),  # Збільшений шрифт
    command=on_protocol_checkbox_toggle
)
protocol_checkbox.place(x=700, y=80)  # Задайте координати для чекбоксу

# Додавання обробників подій для анімації
protocol_checkbox.bind("<Enter>", on_enter_protocol_checkbox)
protocol_checkbox.bind("<Leave>", on_leave_protocol_checkbox)

# Вікно пошукового рядка
search_frame = tk.Frame(root)  # Створюємо фрейм для поля пошуку та лінії
search_frame.place(x=50, y=80, width=600)

search_entry = tk.Entry(search_frame, font=("Arial", 24), bd=0)  # Без обводки
search_entry.pack(fill='x')  # Заповнюємо фрейм

# Лінія під текстовим полем (для анімації)
search_bottom_line = tk.Frame(search_frame, height=2, bg='#cccccc')  # Початково сіра лінія
search_bottom_line.pack(fill='x', side='bottom')

# Анімація для текстового поля
def on_search_click(event):
    search_bottom_line.config(bg='#007aff')  # Змінюємо колір лінії на синій

def on_search_leave(event):
    search_bottom_line.config(bg='#cccccc')  # Повертаємо лінію до сірого при втраті фокусу

def on_search_enter(event):
    search_frame.config(bg='#cce0f0')  # Змінюємо фон рамки на світліший при наведенні

def on_search_exit(event):
    search_frame.config(bg='#f9f9f9')  # Повертаємо фон рамки до початкового при виході миші

# Прив'язка подій до текстового поля
search_entry.bind("<FocusIn>", on_search_click)  # При натисканні в полі пошуку
search_entry.bind("<FocusOut>", on_search_leave)  # При втраті фокусу
search_frame.bind("<Enter>", on_search_enter)  # При наведенні миші на поле
search_frame.bind("<Leave>", on_search_exit)  # При виході миші з поля

search_entry.focus()  # Активуємо пошуковий рядок при відкритті програми

# Фрейм для відображення результатів пошуку
result_frame = tk.Frame(root)
result_frame.place(x=20, y=130, width=root.winfo_screenwidth() * 0.7 - 40, height=root.winfo_screenheight() - 200)

# Функції для зміни кольору кнопки "Додати сертифікат" при наведенні миші
def on_enter_add_certificate(e):
    add_button['bg'] = '#3a556b'
    add_button['fg'] = '#fff'

def on_leave_add_certificate(e):
    add_button['bg'] = '#e7e7e7'
    add_button['fg'] = '#333'

# Кнопка "Додати сертифікат"
add_button = tk.Button(root, text="Додати сертифікат", command=add_certificate_directly, font=("Arial", 24), bg='#e7e7e7')
add_button.place(x=root.winfo_screenwidth() - 500, y=10, width=365)
add_button.bind("<Enter>", on_enter_add_certificate)
add_button.bind("<Leave>", on_leave_add_certificate)

# Змінна для збереження активної кнопки
active_button = None

# Функція для оновлення кольору активної кнопки
def update_button_colors():
    if active_button == "all_certificates":
        all_certificates_button['bg'] = '#3a556b'
        all_certificates_button['fg'] = '#fff'
    else:
        all_certificates_button['bg'] = '#e7e7e7'
        all_certificates_button['fg'] = '#333'
    
    if active_button == "ready":
        confirm_yes_button['bg'] = '#3a556b'
        confirm_yes_button['fg'] = '#fff'
    else:
        confirm_yes_button['bg'] = '#e7e7e7'
        confirm_yes_button['fg'] = '#333'
    
    if active_button == "not_ready":
        confirm_no_button['bg'] = '#3a556b'
        confirm_no_button['fg'] = '#fff'
    else:
        confirm_no_button['bg'] = '#e7e7e7'
        confirm_no_button['fg'] = '#333'

# Функції для кожної кнопки, які змінюють активну кнопку і оновлюють кольори
def on_all_certificates_click():
    global active_button
    active_button = "all_certificates"
    update_button_colors()
    show_all_certificates()

def on_ready_click():
    global active_button
    active_button = "ready"
    update_button_colors()
    show_ready_certificates()

def on_not_ready_click():
    global active_button
    active_button = "not_ready"
    update_button_colors()
    show_not_ready_records()

# Функції для зміни кольору кнопок при наведенні миші
def on_enter_all_certificates(e):
    if active_button != "all_certificates":
        all_certificates_button['bg'] = '#3a556b'
        all_certificates_button['fg'] = '#fff'

def on_leave_all_certificates(e):
    if active_button != "all_certificates":
        all_certificates_button['bg'] = '#e7e7e7'
        all_certificates_button['fg'] = '#333'

def on_enter_ready(e):
    if active_button != "ready":
        confirm_yes_button['bg'] = '#3a556b'
        confirm_yes_button['fg'] = '#fff'

def on_leave_ready(e):
    if active_button != "ready":
        confirm_yes_button['bg'] = '#e7e7e7'
        confirm_yes_button['fg'] = '#333'

def on_enter_not_ready(e):
    if active_button != "not_ready":
        confirm_no_button['bg'] = '#3a556b'
        confirm_no_button['fg'] = '#fff'

def on_leave_not_ready(e):
    if active_button != "not_ready":
        confirm_no_button['bg'] = '#e7e7e7'
        confirm_no_button['fg'] = '#333'

# Кнопка "ВСІ СЕРТИФІКАТИ"
all_certificates_button = tk.Button(root, text="ВСІ СЕРТИФІКАТИ", command=on_all_certificates_click, font=("Arial", 12), bg='#e7e7e7')
all_certificates_button.place(x=root.winfo_screenwidth() - 500, y=90, width=160)
all_certificates_button.bind("<Enter>", on_enter_all_certificates)
all_certificates_button.bind("<Leave>", on_leave_all_certificates)

# Кнопка "ГОТОВІ"
confirm_yes_button = tk.Button(root, text="ГОТОВІ", command=on_ready_click, font=("Arial", 12), bg='#e7e7e7')
confirm_yes_button.place(x=root.winfo_screenwidth() - 215, y=90, width=80)
confirm_yes_button.bind("<Enter>", on_enter_ready)
confirm_yes_button.bind("<Leave>", on_leave_ready)

# Кнопка "НЕ ГОТОВІ"
confirm_no_button = tk.Button(root, text="НЕ ГОТОВІ", command=on_not_ready_click, font=("Arial", 12), bg='#e7e7e7')
confirm_no_button.place(x=root.winfo_screenwidth() - 335, y=90, width=110)
confirm_no_button.bind("<Enter>", on_enter_not_ready)
confirm_no_button.bind("<Leave>", on_leave_not_ready)

# Фрейм для відображення всіх записів
all_records_frame = tk.Frame(root)
all_records_frame.place(x=root.winfo_screenwidth() * 0.7, y=130, width=root.winfo_screenwidth() * 0.3 - 20, height=root.winfo_screenheight() - 200)

# Функціонал закриття вікна
root.protocol("WM_DELETE_WINDOW", close_app)
root.bind("<Escape>", close_app)

# Зв'язування події натискання клавіші "Enter" з функцією пошуку
search_entry.bind("<KeyRelease>", search)

# При відкритті програми показуємо всі записи на 30%
show_all_certificates()

root.mainloop()