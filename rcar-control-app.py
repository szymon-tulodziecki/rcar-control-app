import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time

class RobotController:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Controller") 
        self.root.geometry("900x700")
        self.root.minsize(900, 700)      
        
        self.serial_port = None
        self.is_connected = False
        
        self.setup_ui()
        
    def setup_ui(self):
        self.left_frame = ttk.Frame(self.root, padding="10")
        self.left_frame.pack(side="left", fill="both", expand=True)
        
        self.right_frame = ttk.Frame(self.root, padding="10")
        self.right_frame.pack(side="right", fill="both", expand=True)
        
        self.setup_left_ui()
        
        self.setup_right_ui()
        
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.focus_set()

    def setup_left_ui(self):
        connection_frame = ttk.LabelFrame(self.left_frame, text="Połączenie", padding="10")
        connection_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=0, sticky="w")
        self.port_var = tk.StringVar(value="COM3")
        port_entry = ttk.Entry(connection_frame, textvariable=self.port_var, width=15)
        port_entry.grid(row=0, column=1, padx=5)
        
        self.connect_btn = ttk.Button(connection_frame, text="Połącz", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=2, padx=5)
        
        self.status_label = ttk.Label(connection_frame, text="Rozłączony", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        control_frame = ttk.LabelFrame(self.left_frame, text="Sterowanie", padding="10")
        control_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ttk.Button(control_frame, text="↑ PRZÓD", command=lambda: self.send_command('F')).grid(row=0, column=1, padx=5, pady=5, ipadx=20)
        ttk.Button(control_frame, text="← LEWO", command=lambda: self.send_command('L')).grid(row=1, column=0, padx=5, pady=5, ipadx=20)
        ttk.Button(control_frame, text="STOP", command=lambda: self.send_command('S')).grid(row=1, column=1, padx=5, pady=5, ipadx=20)
        ttk.Button(control_frame, text="PRAWO →", command=lambda: self.send_command('R')).grid(row=1, column=2, padx=5, pady=5, ipadx=20)
        ttk.Button(control_frame, text="↓ TYŁ", command=lambda: self.send_command('B')).grid(row=2, column=1, padx=5, pady=5, ipadx=20)
        
        speed_frame = ttk.LabelFrame(self.left_frame, text="Prędkość", padding="10")
        speed_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(speed_frame, text="Wolno (1)", command=lambda: self.send_command('1')).pack(side="left", padx=5)
        ttk.Button(speed_frame, text="Średnio (3)", command=lambda: self.send_command('3')).pack(side="left", padx=5)
        ttk.Button(speed_frame, text="Szybko (q)", command=lambda: self.send_command('q')).pack(side="left", padx=5)
        
        keyboard_frame = ttk.LabelFrame(self.left_frame, text="Sterowanie klawiaturą", padding="10")
        keyboard_frame.pack(fill="x", padx=10, pady=5)
        
        instructions = [
            "W - Przód",
            "S - Tył", 
            "A - Lewo",
            "D - Prawo",
            "Spacja - Stop",
            "1,2,3 - Prędkość"
        ]
        
        for i, instruction in enumerate(instructions):
            ttk.Label(keyboard_frame, text=instruction, font=("Arial", 8)).grid(
                row=i//2, column=i%2, sticky="w", padx=5, pady=2
            )

    def setup_right_ui(self):
        terminal_frame = ttk.LabelFrame(self.right_frame, text="Terminal", padding="10")
        terminal_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.terminal_text = tk.Text(terminal_frame, height=25, state='disabled', 
                                   bg='black', fg='white', font=('Courier', 10))
        
        scrollbar = ttk.Scrollbar(terminal_frame, orient="vertical", command=self.terminal_text.yview)
        self.terminal_text.configure(yscrollcommand=scrollbar.set)
        
        self.terminal_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        clear_btn = ttk.Button(self.right_frame, text="Wyczyść terminal", command=self.clear_terminal)
        clear_btn.pack(pady=5)
        
        entry_frame = ttk.Frame(self.right_frame)
        entry_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(entry_frame, text="Niestandardowy sygnał:").pack(anchor="w")
        
        signal_input_frame = ttk.Frame(entry_frame)
        signal_input_frame.pack(fill="x", pady=5)
        
        self.custom_signal_var = tk.StringVar()
        self.custom_signal_entry = ttk.Entry(signal_input_frame, textvariable=self.custom_signal_var)
        self.custom_signal_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        send_button = ttk.Button(signal_input_frame, text="Wyślij sygnał", command=self.send_custom_signal)
        send_button.pack(side="right")
        
        self.custom_signal_entry.bind('<Return>', lambda e: self.send_custom_signal())

    def clear_terminal(self):
        """Czyści zawartość terminala"""
        self.terminal_text.config(state='normal')
        self.terminal_text.delete('1.0', tk.END)
        self.terminal_text.config(state='disabled')
        self.append_terminal("Terminal wyczyszczony")

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        try:
            self.serial_port = serial.Serial(
                port=self.port_var.get(),
                baudrate=9600,
                timeout=1
            )
            self.is_connected = True
            self.status_label.config(text="Połączony", foreground="green")
            self.connect_btn.config(text="Rozłącz")
            self.append_terminal(f"Połączono z portem {self.port_var.get()}")
            self.start_reading_thread()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można połączyć z portem: {e}")
            self.append_terminal(f"Błąd połączenia: {e}")
            
    def disconnect_serial(self):
        if self.serial_port:
            self.serial_port.close()
        self.is_connected = False
        self.status_label.config(text="Rozłączony", foreground="red")
        self.connect_btn.config(text="Połącz")
        self.append_terminal("Rozłączono")
        
    def send_command(self, command):
        if self.is_connected and self.serial_port:
            try:
                self.serial_port.write(command.encode())
                self.append_terminal(f">> Wysłano: {command}")
            except Exception as e:
                self.append_terminal(f"!! Błąd wysyłania: {e}")
        else:
            self.append_terminal(f"!! Nie połączono - próba wysłania: {command}")
            
    def send_custom_signal(self):
        signal = self.custom_signal_var.get().strip()
        if signal:
            self.send_command(signal)
            self.custom_signal_var.set("")
            self.custom_signal_entry.focus()

    def on_key_press(self, event):
        """Obsługa naciśnięcia klawisza"""
        if isinstance(self.root.focus_get(), tk.Entry):
            return
            
        key_commands = {
            'w': 'F',  # przód
            's': 'B',  # tył
            'a': 'L',  # lewo
            'd': 'R',  # prawo
            ' ': 'S',  # stop (spacja)
            '1': '1',  # wolno
            '2': '3',  # średnio
            '3': 'q'   # szybko
        }
        
        if event.char.lower() in key_commands:
            command = key_commands[event.char.lower()]
            self.send_command(command)
            self.append_terminal(f"[KLAWIATURA] {event.char.upper()} -> {command}")
            
    def on_key_release(self, event):
        """Obsługa puszczenia klawisza"""
        if isinstance(self.root.focus_get(), tk.Entry):
            return
            
        if event.char.lower() in ['w', 's', 'a', 'd']:
            self.send_command('S')
            self.append_terminal(f"[KLAWIATURA] Puszczono {event.char.upper()} -> STOP")

    def append_terminal(self, message):
        """Dodaje wiadomość do terminala z timestampem"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.terminal_text.config(state='normal')
        self.terminal_text.insert(tk.END, formatted_message + "\n")
        self.terminal_text.see(tk.END)
        self.terminal_text.config(state='disabled')
        
    def start_reading_thread(self):
        """Uruchamia wątek do odczytu danych z portu szeregowego"""
        self.reading_thread = threading.Thread(target=self.read_serial_data, daemon=True)
        self.reading_thread.start()
        
    def read_serial_data(self):
        """Odczytuje dane z portu szeregowego w osobnym wątku"""
        while True:
            if self.is_connected and self.serial_port:
                try:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.readline().decode().strip()
                        if data:
                            self.root.after(0, lambda d=data: self.append_terminal(f"<< Odebrano: {d}"))
                except Exception as e:
                    self.root.after(0, lambda e=e: self.append_terminal(f"!! Błąd odczytu: {e}"))
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotController(root)
    root.mainloop()
