#!/usr/bin/env python3
"""
Kinetik Gol Algoritması (KGA) - Kapalı Devre Öğrenme & Geri Besleme Motoru (Feedback Engine)
Bu modül:
1. Oynanan KGA maçlarının resmi skorlarını kaydeder.
2. Tahmin ile gerçekleşen skorları karşılaştırır (2.5 Üst, KG Var, Skor Kuponu).
3. Lig, oran bandı ve takım bazlı ROI / Başarı oranını hesaplar.
4. KGA algoritmasını kusursuzlaştırmak için otomatik kalibrasyon önerileri üretir.
"""

import os
import json
from datetime import datetime

class KGAFeedbackEngine:
    def __init__(self, db_path="kga_learning_db.json"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, db_path)
        self.data = self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"matches": [], "lig_stats": {}, "odds_bracket_stats": {}, "recommendations": []}

    def save_db(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def record_match_result(self, bulletin, date_str, lig, home, away, ust25_odds, kgvar_odds, home_score, away_score):
        """Maç sonucunu ve tahmin başarısını kaydeder."""
        total_goals = home_score + away_score
        is_ust25_won = total_goals >= 3
        is_kgvar_won = home_score > 0 and away_score > 0
        exact_score = f"{home_score}-{away_score}"

        record = {
            "bulletin": bulletin,
            "date": date_str,
            "lig": lig,
            "home": home,
            "away": away,
            "ust25_odds": ust25_odds,
            "kgvar_odds": kgvar_odds,
            "score": exact_score,
            "total_goals": total_goals,
            "ust25_won": is_ust25_won,
            "kgvar_won": is_kgvar_won,
            "both_won": is_ust25_won and is_kgvar_won
        }

        # Mevcut kaydı güncelle veya yenisini ekle
        existing_idx = None
        for i, m in enumerate(self.data["matches"]):
            if m.get("date") == date_str and m.get("home") == home and m.get("away") == away:
                existing_idx = i
                break

        if existing_idx is not None:
            self.data["matches"][existing_idx] = record
        else:
            self.data["matches"].append(record)

        self._recalculate_analytics()
        self.save_db()
        return record

    def _recalculate_analytics(self):
        """Lig ve oran bandı bazında istatistikleri ve önerileri günceller."""
        matches = self.data["matches"]
        if not matches:
            return

        lig_stats = {}
        bracket_stats = {
            "1.70-1.75": {"total": 0, "won": 0},
            "1.76-1.85": {"total": 0, "won": 0},
            "1.86-1.95": {"total": 0, "won": 0}
        }

        for m in matches:
            lig = m.get("lig", "DİĞER")
            if lig not in lig_stats:
                lig_stats[lig] = {"total": 0, "ust_won": 0, "kg_won": 0, "both_won": 0}
            
            lig_stats[lig]["total"] += 1
            if m["ust25_won"]:
                lig_stats[lig]["ust_won"] += 1
            if m["kgvar_won"]:
                lig_stats[lig]["kg_won"] += 1
            if m["both_won"]:
                lig_stats[lig]["both_won"] += 1

            # Oran bandı
            u_odds = m.get("ust25_odds", 0)
            if 1.70 <= u_odds <= 1.75:
                b = "1.70-1.75"
            elif 1.76 <= u_odds <= 1.85:
                b = "1.76-1.85"
            elif 1.86 <= u_odds <= 1.95:
                b = "1.86-1.95"
            else:
                b = None

            if b:
                bracket_stats[b]["total"] += 1
                if m["ust25_won"]:
                    bracket_stats[b]["won"] += 1

        self.data["lig_stats"] = lig_stats
        self.data["odds_bracket_stats"] = bracket_stats
        self.data["recommendations"] = self._generate_recommendations(lig_stats, bracket_stats, matches)

    def _generate_recommendations(self, lig_stats, bracket_stats, matches):
        """KGA 2.0 kural motorunu kusursuzlaştırmak için makine öğrenmesi/istatistiki tavsiyeler üretir."""
        recs = []
        total_matches = len(matches)
        if total_matches < 3:
            return ["Veri tabanı henüz başlangıç aşamasında. Daha fazla maç sonucu işlendikçe otomatik kurallar kalibre edilecek."]

        # 1. Lig bazlı öneriler
        for lig, s in lig_stats.items():
            if s["total"] >= 3:
                win_rate = (s["ust_won"] / s["total"]) * 100
                if win_rate >= 80:
                    recs.append(f"🟢 <b>[TİER 1 TERFİ]</b> {lig} ligi son {s['total']} maçta %{win_rate:.1f} 2.5 Üst başarısına ulaştı. Günün Altın Maçı seçimlerinde öncelik verilmeli.")
                elif win_rate <= 40:
                    recs.append(f"🔴 <b>[KARA LİSTE UYARISI]</b> {lig} ligi son {s['total']} maçta sadece %{win_rate:.1f} 2.5 Üst üretti. Burnley/kısır filtreye eklenmeli ve elenmeli.")

        # 2. Oran bandı tatlı nokta önerisi
        best_bracket = None
        best_rate = -1
        for b, s in bracket_stats.items():
            if s["total"] >= 3:
                rate = (s["won"] / s["total"]) * 100
                if rate > best_rate:
                    best_rate = rate
                    best_bracket = b
        
        if best_bracket and best_rate > 70:
            recs.append(f"🎯 <b>[TATLI NOKTA OPTİMİZASYONU]</b> En yüksek getiri sağlayan oran bandı: <b>{best_bracket}</b> (Başarı: %{best_rate:.1f}). Kasa Katlama zincirinde bu aralık ağırlıklandırılmalı.")

        return recs

    def generate_daily_learning_report(self):
        """Telegram'a ve kullanıcıya sunulacak günlük performans ve öğrenme raporu."""
        matches = self.data.get("matches", [])
        if not matches:
            return "Henüz sonuçlanmış maç kaydı bulunmamaktadır."

        total = len(matches)
        ust_won = sum(1 for m in matches if m.get("ust25_won"))
        kg_won = sum(1 for m in matches if m.get("kgvar_won"))
        both_won = sum(1 for m in matches if m.get("both_won"))

        ust_rate = (ust_won / total) * 100 if total > 0 else 0
        kg_rate = (kg_won / total) * 100 if total > 0 else 0
        both_rate = (both_won / total) * 100 if total > 0 else 0

        report = [
            "📊 <b>KGA 2.0 KENDİNİ GELİŞTİREN ALGORİTMA PERFORMANS RAPORU</b>",
            f"📈 Toplam İncelenen KGA Maçı: <b>{total}</b>",
            f"✅ 2.5 Üst İsabeti: <b>%{ust_rate:.1f}</b> ({ust_won}/{total})",
            f"🤝 KG Var İsabeti: <b>%{kg_rate:.1f}</b> ({kg_won}/{total})",
            f"🔥 İkiz Kilit (Hem 2.5Ü hem KG): <b>%{both_rate:.1f}</b> ({both_won}/{total})",
            "━━━━━━━━━━━━━━━━━━━━",
            "🧠 <b>ALGORİTMA OTOMATİK KALİBRASYON ÖNERİLERİ:</b>"
        ]

        for r in self.data.get("recommendations", []):
            report.append(f"• {r}")

        return "\n".join(report)

if __name__ == "__main__":
    engine = KGAFeedbackEngine()
    # Örnek test verisi işleme (6 Kasım Cuma sonuçları simülasyonu)
    engine.record_match_result(
        bulletin="06-11-2026-Bulten.pdf",
        date_str="06.11.2026",
        lig="SÜPL",
        home="GAZİANTEP FK",
        away="KASIMPAŞA",
        ust25_odds=1.72,
        kgvar_odds=1.57,
        home_score=2,
        away_score=2
    )
    engine.record_match_result(
        bulletin="06-11-2026-Bulten.pdf",
        date_str="06.11.2026",
        lig="HRV2L",
        home="DİNAMO ZAGREB II",
        away="NK JADRAN LP",
        ust25_odds=1.72,
        kgvar_odds=1.56,
        home_score=3,
        away_score=1
    )
    engine.record_match_result(
        bulletin="06-11-2026-Bulten.pdf",
        date_str="06.11.2026",
        lig="POR2",
        home="AVS FUTEBOL SAD",
        away="FC VİZELA",
        ust25_odds=1.75,
        kgvar_odds=1.58,
        home_score=1,
        away_score=2
    )
    print(engine.generate_daily_learning_report())
