import customtkinter as ctk
import threading
import time
from scanner import MarketScannerEngine

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kripto Algoritmik Terminal (Pro Edition v5.0)")
        self.geometry("980x850")
        self.resizable(False, False)

        self.engine = MarketScannerEngine()
        self.engine.log_callback = self.add_log
        self.bot_thread = None
        
        self.radar_ui_elements = {} 
        self.trade_card_elements = {}

        self.setup_ui()

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab_dashboard = self.tabview.add("Ana Terminal")
        self.tab_settings = self.tabview.add("Risk Yönetimi")
        self.tab_logs = self.tabview.add("Sistem Logları")

        self.build_dashboard_tab()
        self.build_settings_tab()
        self.build_logs_tab()

    def build_dashboard_tab(self):
        # 4'lü Metrik Paneli
        self.info_frame = ctk.CTkFrame(self.tab_dashboard, corner_radius=10)
        self.info_frame.pack(fill="x", pady=(0, 10))

        self.lbl_balance = ctk.CTkLabel(self.info_frame, text=f"Kasa: {self.engine.balance:.2f} $", font=("Arial", 16, "bold"), text_color="#4CAF50")
        self.lbl_balance.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.lbl_win_rate = ctk.CTkLabel(self.info_frame, text="Kazanma Oranı: % 0 (0 İşlem)", font=("Arial", 14))
        self.lbl_win_rate.grid(row=0, column=1, padx=15, pady=12)

        self.lbl_fees = ctk.CTkLabel(self.info_frame, text="Komisyon: 0.00 $", font=("Arial", 14), text_color="#FF9800")
        self.lbl_fees.grid(row=0, column=2, padx=15, pady=12)

        self.lbl_active_trades = ctk.CTkLabel(self.info_frame, text="Açık Pozisyon: 0", font=("Arial", 14))
        self.lbl_active_trades.grid(row=0, column=3, padx=15, pady=12, sticky="e")

        # Radar
        ctk.CTkLabel(self.tab_dashboard, text="Piyasa Radarı (Likidite ve Momentum İzleniyor)", font=("Arial", 14, "bold")).pack(anchor="w", pady=(5, 5))
        self.radar_frame = ctk.CTkScrollableFrame(self.tab_dashboard, corner_radius=10, height=200)
        self.radar_frame.pack(fill="x", pady=(0, 15))
        
        col, row = 0, 0
        for sym in self.engine.symbols:
            card = ctk.CTkFrame(self.radar_frame, fg_color="#2A2D34", corner_radius=8)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            
            lbl_sym = ctk.CTkLabel(card, text=sym, font=("Arial", 13, "bold"))
            lbl_sym.pack(pady=(4, 0), padx=15)
            
            lbl_price = ctk.CTkLabel(card, text="-- $", font=("Arial", 12))
            lbl_price.pack()
            
            lbl_change = ctk.CTkLabel(card, text="% 0.00", font=("Arial", 12, "bold"))
            lbl_change.pack(pady=(0, 4))
            
            self.radar_ui_elements[sym] = {"price": lbl_price, "change": lbl_change}
            col += 1
            if col > 3:
                col, row = 0, row + 1

        # Açık Pozisyonlar
        ctk.CTkLabel(self.tab_dashboard, text="Açık Emirler ve Pozisyonlar", font=("Arial", 14, "bold")).pack(anchor="w", pady=(5, 5))
        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_dashboard, corner_radius=10, height=160)
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.btn_start = ctk.CTkButton(self.tab_dashboard, text="Algoritmayı Başlat", command=self.toggle_bot, fg_color="#00695C", hover_color="#004D40", height=40)
        self.btn_start.pack(fill="x")

    def build_settings_tab(self):
        settings_frame = ctk.CTkFrame(self.tab_settings, corner_radius=10)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(settings_frame, text="İzüren Stop Baz Oranı (%):").grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self.entry_trailing = ctk.CTkEntry(settings_frame)
        self.entry_trailing.insert(0, str(self.engine.config["trailing_stop_pct"]))
        self.entry_trailing.grid(row=0, column=1, padx=15, pady=15)

        btn_save = ctk.CTkButton(settings_frame, text="Risk Parametrelerini Güncelle", command=self.update_settings)
        btn_save.grid(row=1, column=0, columnspan=2, pady=30)

    def build_logs_tab(self):
        self.log_box = ctk.CTkTextbox(self.tab_logs, corner_radius=10, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.add_log("Algoritma Başlatıldı. CSV Kayıt Sistemi Aktif.")

    def add_log(self, text):
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_box.see("end")

    def update_settings(self):
        try:
            new_trailing = float(self.entry_trailing.get())
            self.engine.strategy_manager.base_trailing_pct = new_trailing
            self.add_log(f"Ayarlar güncellendi: İzüren Stop %{new_trailing}")
        except ValueError:
            self.add_log("⚠️ Hata: Lütfen geçerli sayılar girin.")

    def update_trade_cards(self):
        active_symbols = list(self.engine.strategy_manager.active_positions.keys())
        
        for sym in list(self.trade_card_elements.keys()):
            if sym not in active_symbols:
                self.trade_card_elements[sym]["frame"].destroy()
                del self.trade_card_elements[sym]

        for sym in active_symbols:
            pos = self.engine.strategy_manager.active_positions[sym]
            current_price = self.engine.market_state[sym]["price"]
            elapsed_mins = int((time.time() - pos.entry_time) / 60)
            pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100
            pnl_color = "#4CAF50" if pnl_pct > 0 else "#F44336"
            
            details_text = f"Giriş: {pos.entry_price:.5f}$ | Zirve: {pos.highest_price:.5f}$ | Anlık: %{pnl_pct:+.2f} | Süre: {elapsed_mins} dk"

            if sym not in self.trade_card_elements:
                card = ctk.CTkFrame(self.scroll_frame, fg_color="#1E1E1E", corner_radius=8, border_width=1, border_color="#333333")
                card.pack(fill="x", pady=5, padx=5)
                lbl_sym = ctk.CTkLabel(card, text=sym, font=("Arial", 15, "bold"), text_color="#FFA000")
                lbl_sym.pack(side="left", padx=10, pady=10)
                lbl_details = ctk.CTkLabel(card, text=details_text, font=("Arial", 12), text_color=pnl_color)
                lbl_details.pack(side="right", padx=10, pady=10)
                
                self.trade_card_elements[sym] = {"frame": card, "lbl_details": lbl_details}
            else:
                self.trade_card_elements[sym]["lbl_details"].configure(text=details_text, text_color=pnl_color)

    def refresh_ui_elements(self):
        # Radar
        for sym, state in self.engine.market_state.items():
            if sym in self.radar_ui_elements:
                change = state["change"]
                color = "#4CAF50" if change > 0.05 else ("#F44336" if change < -0.05 else "#FFFFFF")
                sign = "+" if change > 0.05 else ""
                self.radar_ui_elements[sym]["price"].configure(text=f"{state['price']:.5f} $")
                self.radar_ui_elements[sym]["change"].configure(text=f"% {sign}{change:.2f}", text_color=color)

        # İstatistikler
        self.lbl_balance.configure(text=f"Kasa: {self.engine.balance:.2f} $")
        self.lbl_fees.configure(text=f"Komisyon: {self.engine.total_fees_paid:.2f} $")
        
        total_trades = self.engine.total_closed_trades
        win_rate = (self.engine.winning_trades / total_trades * 100) if total_trades > 0 else 0
        self.lbl_win_rate.configure(text=f"Kazanma Oranı: %{win_rate:.1f} ({total_trades} İşlem)")

        active_count = len(self.engine.strategy_manager.active_positions)
        self.lbl_active_trades.configure(text=f"Açık Pozisyon: {active_count} / {self.engine.config['max_open_trades']}")
        
        self.update_trade_cards()

    def toggle_bot(self):
        if not self.engine.running:
            self.engine.running = True
            self.btn_start.configure(text="Algoritmayı Durdur", fg_color="#C62828", hover_color="#8E0000")
            self.bot_thread = threading.Thread(target=self.run_loop, daemon=True)
            self.bot_thread.start()
        else:
            self.engine.running = False
            self.btn_start.configure(text="Algoritmayı Başlat", fg_color="#00695C", hover_color="#004D40")

    def run_loop(self):
        self.engine.initialize_references()
        while self.engine.running:
            success = self.engine.scan_cycle()
            if success:
                self.after(0, self.refresh_ui_elements)
            time.sleep(self.engine.config["poll_interval_sec"])

if __name__ == "__main__":
    app = App()
    app.mainloop()