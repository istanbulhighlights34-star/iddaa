#!/usr/bin/env python3
"""
KGA 2.0 - 100X OTONOM KASA & BİLEŞİK BÜYÜME MOTORU (BANKROLL ENGINE)
Başlangıç: 1.000 TL -> Hedef: 100.000 TL ve Ötesi (Tavansız Bileşik Büyüme)

Bu modül:
1. Güncel kasayı takip eder.
2. Kasayı 3 parçalı güvenlik kalkanına böler ve her kupon için KURUŞU KURUŞUNA yatırılacak TL miktarını hesaplar.
3. Maçlar bittiğinde canlı skorlardan kazanan/kaybeden kuponları tespit edip kasayı otomatik günceller.
4. 100.000 TL ilk büyük kilometre taşıdır; kâr kilitlendikçe tavansız büyümeye devam eder.
"""

import os
import json
from datetime import datetime

class KGABankrollEngine:
    def __init__(self, state_file="kga_bankroll_state.json"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.state_file = os.path.join(self.base_dir, state_file)
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Varsayılan başlangıç durumu
        initial = {
            "initial_balance": 1000.0,
            "current_balance": 1000.0,
            "target_milestone_1": 100000.0,
            "current_step": 1,
            "total_net_profit": 0.0,
            "all_time_peak": 1000.0,
            "active_coupons": [],
            "settled_history": [],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        return initial

    def save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def calculate_daily_stakes(self):
        """
        Mevcut kasaya göre KURUŞU KURUŞUNA yatırılacak 3 parçalı kupon tutarlarını belirler.
        Parçalı Kasa Kuralı:
        - Kupon 1 (Ana Taşıyıcı): %50
        - Kupon 2 (Kademeli Basamak): %30
        - Kupon 3 (Güvenlik / Sigorta Zırhı): %20
        """
        curr = self.state.get("current_balance", 1000.0)
        
        stake_1 = round(curr * 0.50, 0)
        stake_2 = round(curr * 0.30, 0)
        stake_3 = round(curr - (stake_1 + stake_2), 0) # Küsürat yuvarlama koruması

        return {
            "current_balance": curr,
            "step": self.state.get("current_step", 1),
            "stake_1": int(stake_1),
            "stake_2": int(stake_2),
            "stake_3": int(stake_3)
        }

    def register_daily_coupons(self, coupon1_info, coupon2_info, coupon3_info):
        """Günün 3 parçalı kuponunu ve yatırılacak TL miktarlarını aktif kupon listesine kaydeder."""
        stakes = self.calculate_daily_stakes()
        
        c1 = {
            "id": 1,
            "name": "KUPON 1 (⭐ Ana Taşıyıcı - Günün Altın Tercihi)",
            "allocated_stake": stakes["stake_1"],
            "odds": coupon1_info.get("odds", 1.65),
            "matches": coupon1_info.get("matches", []),
            "target_type": coupon1_info.get("target_type", "2.5 Üst / KG Var"),
            "potential_return": round(stakes["stake_1"] * coupon1_info.get("odds", 1.65), 0),
            "status": "BEKLİYOR"
        }

        c2 = {
            "id": 2,
            "name": "KUPON 2 (📈 Kademeli Basamak - Saat Çakışmasız)",
            "allocated_stake": stakes["stake_2"],
            "odds": coupon2_info.get("odds", 1.70),
            "matches": coupon2_info.get("matches", []),
            "target_type": coupon2_info.get("target_type", "2.5 Üst / KG Var"),
            "potential_return": round(stakes["stake_2"] * coupon2_info.get("odds", 1.70), 0),
            "status": "BEKLİYOR"
        }

        c3 = {
            "id": 3,
            "name": "KUPON 3 (🛡️ Güvenlik Kalkanı & Skor Zırhı)",
            "allocated_stake": stakes["stake_3"],
            "odds": coupon3_info.get("odds", 2.20),
            "matches": coupon3_info.get("matches", []),
            "target_type": coupon3_info.get("target_type", "Sistem / Sigorta"),
            "potential_return": round(stakes["stake_3"] * coupon3_info.get("odds", 2.20), 0),
            "status": "BEKLİYOR"
        }

        self.state["active_coupons"] = [c1, c2, c3]
        self.state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.save_state()
        return [c1, c2, c3]

    def settle_coupons_from_results(self, db_matches):
        """Biten maç skorlarına göre aktif kuponları sonuçlandırır ve kasayı günceller."""
        active = self.state.get("active_coupons", [])
        if not active:
            return None

        total_return = 0.0
        settled_count = 0

        for c in active:
            c_status = c.get("status", "BEKLİYOR")
            if c_status != "BEKLİYOR":
                continue

            matches = c.get("matches", [])
            if not matches:
                continue

            all_evaluated = True
            coupon_won = True

            for m in matches:
                # db_matches içinde maçı ara
                found = None
                for db_m in db_matches:
                    if (m["home"].lower() in db_m["home"].lower() or db_m["home"].lower() in m["home"].lower()) and \
                       (m["away"].lower() in db_m["away"].lower() or db_m["away"].lower() in m["away"].lower()):
                        found = db_m
                        break

                if not found:
                    all_evaluated = False
                    break
                else:
                    # Başarı kontrolü
                    req = m.get("req", "ust25")
                    if req == "ust25" and not found.get("ust25_won"):
                        coupon_won = False
                    elif req == "kgvar" and not found.get("kgvar_won"):
                        coupon_won = False

            if all_evaluated:
                settled_count += 1
                if coupon_won:
                    c["status"] = "KAZANDI"
                    total_return += c.get("potential_return", 0)
                else:
                    c["status"] = "KAYBETTİ"

        if settled_count > 0:
            # Yeni kasa hesaplama
            old_bal = self.state["current_balance"]
            # Yatırılan toplam stake
            total_staked = sum(c["allocated_stake"] for c in active)
            # Net Kasa = (Eski Kasa - Toplam Yatırılan) + Gelen Kazanç
            new_bal = (old_bal - total_staked) + total_return
            
            self.state["current_balance"] = round(new_bal, 2)
            self.state["total_net_profit"] = round(new_bal - self.state["initial_balance"], 2)
            
            if new_bal > self.state.get("all_time_peak", 1000.0):
                self.state["all_time_peak"] = round(new_bal, 2)
                self.state["current_step"] += 1

            self.state["settled_history"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "old_balance": old_bal,
                "new_balance": round(new_bal, 2),
                "total_return": total_return,
                "coupons": active
            })
            
            # Tamamı sonuçlandıysa aktif listeyi temizle
            if all(c["status"] in ["KAZANDI", "KAYBETTİ"] for c in active):
                self.state["active_coupons"] = []

            self.save_state()

        return self.get_bankroll_summary()

    def get_bankroll_summary(self):
        """Kasa ve yatırım planının Telegram formatlı anlık raporunu üretir."""
        curr = self.state.get("current_balance", 1000.0)
        init = self.state.get("initial_balance", 1000.0)
        target = self.state.get("target_milestone_1", 100000.0)
        step = self.state.get("current_step", 1)
        net_profit = self.state.get("total_net_profit", 0.0)

        # İlerleme çubuğu
        progress_pct = min(100.0, (curr / target) * 100)
        bar_len = 10
        filled = int(round(bar_len * (curr / target)))
        bar = "▓" * filled + "░" * (bar_len - filled)

        stakes = self.calculate_daily_stakes()

        lines = [
            "💰 <b>KGA 100X OTONOM KASA & BİLEŞİK BÜYÜME RAPORU</b>",
            f"🎯 <b>Mevcut Kasa:</b> <b>{curr:,.2f} TL</b>",
            f"📈 <b>Başlangıç:</b> {init:,.0f} TL | <b>Net Kâr:</b> {net_profit:+,.2f} TL",
            f"🏆 <b>1. Hedef:</b> {target:,.0f} TL+ <i>(Tavansız Büyüme)</i>",
            f"📊 <b>İlerleme:</b> [{bar}] <b>%{progress_pct:.2f}</b> (Basamak: <b>#{step}</b>)",
            "━━━━━━━━━━━━━━━━━━━━",
            "📋 <b>GÜNÜN KURUŞU KURUŞUNA YATIRIM DAĞILIMI:</b>",
            f"🔹 <b>Kupon 1 (Ana Taşıyıcı %50):</b> <b>{stakes['stake_1']} TL</b>",
            f"🔹 <b>Kupon 2 (Kademeli %30):</b> <b>{stakes['stake_2']} TL</b>",
            f"🔹 <b>Kupon 3 (Güvenlik Zırhı %20):</b> <b>{stakes['stake_3']} TL</b>",
            "━━━━━━━━━━━━━━━━━━━━"
        ]

        active = self.state.get("active_coupons", [])
        if active:
            lines.append("⏳ <b>AKTİF OYNANAN KUPONLAR VE DURUM:</b>")
            for c in active:
                icon = "⏳" if c["status"] == "BEKLİYOR" else ("✅" if c["status"] == "KAZANDI" else "❌")
                lines.append(f"• {icon} <b>{c['name']}</b>: {c['allocated_stake']} TL ➔ Hedef: <b>{c['potential_return']} TL</b> ({c['status']})")
        else:
            lines.append("💡 <i>Kuponlar her sabah 09:00 bülteniyle otomatik doldurulur ve maçlar bittiğinde kasa otomatik artar.</i>")

        return "\n".join(lines)

if __name__ == "__main__":
    engine = KGABankrollEngine()
    print(engine.get_bankroll_summary())
