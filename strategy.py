import time

class Position:
    def __init__(self, symbol: str, entry_price: float, amount_usd: float):
        self.symbol = symbol
        self.entry_price = entry_price
        self.highest_price = entry_price
        self.amount_usd = amount_usd
        self.entry_time = time.time()

class TradingStrategyManager:
    def __init__(self, config):
        self.base_trailing_pct = config["trailing_stop_pct"]
        self.activation_pct = config["take_profit_activation_pct"]
        self.hard_stop_pct = config["hard_stop_loss_pct"]
        self.timeout_sec = config["trade_timeout_minutes"] * 60
        self.cooldown_sec = config["cooldown_minutes"] * 60
        
        self.active_positions = {}
        self.cooldown_list = {} # { 'BTC/USDT': timestamp }

    def is_in_cooldown(self, symbol):
        if symbol in self.cooldown_list:
            if time.time() - self.cooldown_list[symbol] < self.cooldown_sec:
                return True
            else:
                del self.cooldown_list[symbol]
        return False

    def add_position(self, symbol, current_price, amount_usd):
        if symbol not in self.active_positions:
            self.active_positions[symbol] = Position(symbol, current_price, amount_usd)

    def check_position(self, symbol, current_price):
        if symbol not in self.active_positions:
            return None

        pos = self.active_positions[symbol]
        
        if current_price > pos.highest_price:
            pos.highest_price = current_price

        gain_from_entry_pct = ((pos.highest_price - pos.entry_price) / pos.entry_price) * 100
        drop_from_high_pct = ((pos.highest_price - current_price) / pos.highest_price) * 100
        current_pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100

        # Kademeli İzüren Stop (Pro Risk Yönetimi)
        current_trailing_pct = self.base_trailing_pct
        if gain_from_entry_pct >= 3.0:
            current_trailing_pct = self.base_trailing_pct * 0.4 
        elif gain_from_entry_pct >= 1.5:
            current_trailing_pct = self.base_trailing_pct * 0.6 

        # Çıkış Kuralları
        reason = ""
        if gain_from_entry_pct >= self.activation_pct and drop_from_high_pct >= current_trailing_pct:
            reason = f"Dinamik Stop (Zirveden %{drop_from_high_pct:.2f} düşüş)"
        elif current_pnl_pct <= -self.hard_stop_pct:
            reason = "Hard Stop-Loss (Kol Kesildi)"
        elif (time.time() - pos.entry_time) >= self.timeout_sec:
            reason = "Zaman Aşımı (İşlem Yattı)"

        if reason:
            del self.active_positions[symbol]
            self.cooldown_list[symbol] = time.time() # Satış yapıldı, coini cezaya at
            return ("SELL", reason, current_pnl_pct)

        return None