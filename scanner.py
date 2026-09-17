import ccxt
import json
import time
import os
import csv
from datetime import datetime
from strategy import TradingStrategyManager

class MarketScannerEngine:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.exchange = ccxt.binance({"enableRateLimit": True})
        self.symbols = self.config["symbols_to_scan"]
        if "BTC/USDT" not in self.symbols:
            self.symbols.append("BTC/USDT")
            
        self.balance = self.config["initial_balance"]
        self.trade_amount = self.config["trade_amount_usd"]
        self.fee_rate = self.config["commission_rate"]
        
        self.strategy_manager = TradingStrategyManager(self.config)
        self.running = False
        self.log_callback = None

        self.reference_prices = {}
        self.market_state = {} 
        
        # İstatistik Takibi
        self.total_closed_trades = 0
        self.winning_trades = 0
        self.total_fees_paid = 0.0
        self.csv_file = "trades_history.csv"
        self.init_csv()

    def init_csv(self):
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Tarih/Saat", "Sembol", "Giriş Fiyatı", "Çıkış Fiyatı", "Net K/Z ($)", "K/Z (%)", "Sebep", "Kasa ($)"])

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def initialize_references(self):
        self.log("Kurumsal filtreler ve referans fiyatlar yükleniyor...")
        for sym in self.symbols:
            try:
                candles = self.exchange.fetch_ohlcv(sym, timeframe=self.config["timeframe"], limit=2)
                ref_price = candles[-2][4]
                self.reference_prices[sym] = ref_price
                self.market_state[sym] = {"price": ref_price, "change": 0.0}
            except Exception:
                pass
        self.log("Sistem hazır. Likidite ve Momentum aranıyor...")

    def execute_buy(self, symbol, price, rvol):
        cost = self.trade_amount
        fee = cost * self.fee_rate
        self.balance -= fee
        self.total_fees_paid += fee
        self.strategy_manager.add_position(symbol, price, cost)
        self.log(f"🟢 [İŞLEME GİRİLDİ] {symbol} | Fiyat: {price:.5f} $ | RVOL: {rvol:.1f}x")

    def execute_sell(self, symbol, price, pnl_pct, reason):
        pos = self.strategy_manager.active_positions[symbol]
        entry_price = pos.entry_price
        
        gross_return = self.trade_amount * (1 + (pnl_pct / 100))
        sell_fee = gross_return * self.fee_rate
        net_profit = (gross_return - self.trade_amount) - sell_fee
        
        self.balance += net_profit
        self.total_fees_paid += sell_fee
        self.total_closed_trades += 1
        
        if net_profit > 0:
            self.winning_trades += 1

        # CSV Dosyasına Satır Olarak Ekle
        try:
            with open(self.csv_file, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    symbol,
                    f"{entry_price:.5f}",
                    f"{price:.5f}",
                    f"{net_profit:+.2f}",
                    f"{pnl_pct:+.2f}%",
                    reason,
                    f"{self.balance:.2f}"
                ])
        except Exception as e:
            self.log(f"CSV Yazma Hatası: {e}")

        color = "🔴" if net_profit < 0 else "🟢"
        self.log(f"{color} [POZİSYON KAPANDI] {symbol} | Çıkış: {price:.5f} $ | {reason} | Net: {net_profit:+.2f} $")

    def check_institutional_filters(self, symbol, current_price):
        try:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe=self.config["timeframe"], limit=15)
            volumes = [c[5] for c in candles[:-1]]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = candles[-1][5]
            rvol = current_volume / avg_volume if avg_volume > 0 else 0
            
            closes = [c[4] for c in candles[:-1]]
            sma_10 = sum(closes[-10:]) / 10
            is_uptrend = current_price > sma_10

            return (rvol >= self.config["rvol_multiplier"] and is_uptrend), rvol
        except Exception:
            return False, 0

    def scan_cycle(self):
        try:
            tickers = self.exchange.fetch_tickers(self.symbols)

            btc_is_safe = True
            if "BTC/USDT" in self.reference_prices and "BTC/USDT" in tickers:
                btc_ref = self.reference_prices["BTC/USDT"]
                btc_curr = tickers["BTC/USDT"]["last"]
                btc_change = ((btc_curr - btc_ref) / btc_ref) * 100
                if btc_change < self.config["btc_safe_drop_limit_pct"]:
                    btc_is_safe = False

            for sym in self.symbols:
                if sym not in tickers or sym not in self.reference_prices: 
                    continue

                current_price = tickers[sym]["last"]
                ref_price = self.reference_prices[sym]
                price_change_pct = ((current_price - ref_price) / ref_price) * 100

                self.market_state[sym] = {"price": current_price, "change": price_change_pct}

                # 1. Çıkış Kontrolü
                if sym in self.strategy_manager.active_positions:
                    signal = self.strategy_manager.check_position(sym, current_price)
                    if signal:
                        action, reason, pnl_pct = signal
                        self.execute_sell(sym, current_price, pnl_pct, reason)
                        # Pozisyonu stratejiden sil
                        del self.strategy_manager.active_positions[sym]
                        self.strategy_manager.cooldown_list[sym] = time.time()
                    continue

                # 2. Giriş Öncesi Güvenlik
                if len(self.strategy_manager.active_positions) >= self.config["max_open_trades"]: 
                    continue 
                if self.strategy_manager.is_in_cooldown(sym): 
                    continue
                if not btc_is_safe and sym != "BTC/USDT": 
                    continue

                # 3. Tetikleyici ve Filtreler
                if price_change_pct >= self.config["buy_trigger_pct_up"]:
                    passed_filters, rvol = self.check_institutional_filters(sym, current_price)
                    
                    if passed_filters:
                        self.execute_buy(sym, current_price, rvol)
                    
                    self.reference_prices[sym] = current_price

            return True
        except Exception as e:
            self.log(f"⚠️ Tarama Hatası: {str(e)}")
            return False