#!/usr/bin/env python3
"""
Kinetik Gol Algoritması (KGA) - Kapalı Devre Öğrenme, Dinamik Kara Liste & Geri Besleme Motoru
Bu modül:
1. Oynanan KGA maçlarının resmi skorlarını kaydeder.
2. Tahmin ile gerçekleşen skorları karşılaştırır (2.5 Üst, KG Var, Skor Kuponu).
3. Lig, oran bandı ve takım bazlı ROI / Başarı oranını hesaplar.
4. Kısırlaşan ligleri ve takımları dinamik kontrollerle KARA LİSTEYE alır veya şartlar düzelince listeden çıkarır.
5. Mevsimsel / Kış şartlarını (Kasım-Şubat) otomatik algılayıp zemin riski olan ligleri kısıtlar.
6. KGA algoritmasını kusursuzlaştırmak için otomatik kalibrasyon raporu üretir.
"""

import os
import json
from datetime import datetime

# Temel Referans Lig Grupları
DEFAULT_TIER1_LEAGUES = {
    "ALM1": "Almanya Bundesliga 1",
    "ALM2": "Almanya Bundesliga 2",
    "HOL1": "Hollanda Eredivisie",
    "HOL2": "Hollanda Eerste Divisie",
    "BEL1": "Belçika Pro League",
    "İSVİÇ": "İsviçre Süper Ligi",
    "İNG1": "İngiltere Championship",
    "İNG2": "İngiltere League One",
    "İSKOP": "İskoçya Premiership",
    "FRA1": "Fransa Ligue 1"
}

DEFAULT_BLACKLISTED_LEAGUES = {
    "İTB": "İtalya Serie B (Taktiksel Kısır / 1-0 Ekolü)",
    "İSP2": "İspanya Segunda División (Düşük xG / Katı Blok)",
    "YUN1": "Yunanistan Süper Lig Alt Sıralar (Sert Savunma / Düşük Tempo)",
    "ASŞMP": "Asya Şampiyonlar Ligi Doğu Grubu (Dengesiz Geçiş / Ritim Eksikliği)"
}

SEASONAL_WINTER_LEAGUES = {
    "POL1": "Polonya Ekstraklasa (Kasım-Şubat Ağır Kış Şartları / Donmuş Zemin Kısırlığı)",
    "RUS1": "Rusya Premier Ligi (Dondurucu Soğuk & Düşük Hücum Üretimi)",
    "ROM1": "Romanya Liga 1 Alt Sıralar (Ağır Çim ve Zemin Bozulması)"
}

DEFENSIVE_TEAMS_PRAGMATIC = [
    "BURNLEY", "SHEFFIELD UNITED", "GETAFE", "LEGANES", "RAYO VALLECANO",
    "MALLORCA", "EMPOLI", "MONZA", "GENOA", "JUVENTUS", "ATLETICO MADRID"
]

class KGAFeedbackEngine:
    def __init__(self, db_path="kga_learning_db.json"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, db_path)
        self.data = self._load_db()
        self._ensure_dynamic_structures()

    def _ensure_dynamic_structures(self):
        """Veritabanında dinamik kara liste ve tier listesi yapılarının varlığını garanti eder."""
        changed = False
        if "matches" not in self.data:
            self.data["matches"] = []
            changed = True
        if "lig_stats" not in self.data:
            self.data["lig_stats"] = {}
            changed = True
        if "odds_bracket_stats" not in self.data:
            self.data["odds_bracket_stats"] = {}
            changed = True
        if "recommendations" not in self.data:
            self.data["recommendations"] = []
            changed = True
        if "dynamic_blacklist" not in self.data:
            self.data["dynamic_blacklist"] = {}
            changed = True
        if "dynamic_tier1" not in self.data:
            self.data["dynamic_tier1"] = {}
            changed = True
        if "league_tactical_overrides" not in self.data:
            self.data["league_tactical_overrides"] = {}
            changed = True
        if "last_control_audit" not in self.data:
            self.data["last_control_audit"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            changed = True
        
        if changed:
            self.save_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "matches": [],
            "lig_stats": {},
            "odds_bracket_stats": {},
            "recommendations": [],
            "dynamic_blacklist": {},
            "dynamic_tier1": {},
            "last_control_audit": None
        }

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

    def check_match_safety(self, match, current_date=None):
        """
        Bir maçın dinamik kara listede olup olmadığını veya Tier 1 olup olmadığını denetler.
        Dönen değer: (is_safe: bool, status: str, reason: str)
        """
        lig = match.get("lig", "").strip().upper()
        home = match.get("home", "").strip().upper()
        away = match.get("away", "").strip().upper()

        if current_date is None:
            current_date = datetime.now()

        # 1. Mevsimsel Kış Kontrolü (Kasım, Aralık, Ocak, Şubat)
        month = current_date.month
        is_winter = month in [11, 12, 1, 2]
        if is_winter and lig in SEASONAL_WINTER_LEAGUES:
            return False, "KARA_LİSTE_KIŞ", f"Mevsimsel Kış Şartları & Zemin Kısırlığı ({SEASONAL_WINTER_LEAGUES[lig]})"

        # 2. Statik Temel Kara Liste
        if lig in DEFAULT_BLACKLISTED_LEAGUES:
            return False, "KARA_LİSTE_STATİK", f"Yapısal Savunma / Kısır Lig ({DEFAULT_BLACKLISTED_LEAGUES[lig]})"

        # 3. Dinamik Performans Kara Listesi (Sonuçlara dayalı kontrol)
        dyn_bl = self.data.get("dynamic_blacklist", {})
        if lig in dyn_bl:
            info = dyn_bl[lig]
            return False, "KARA_LİSTE_DİNAMİK", f"Son denetimlerde düşük 2.5 Üst oranı (%{info.get('win_rate', 0):.1f} - {info.get('reason', '')})"

        # 4. Taktiksel Katı Takım Kontrolü (Burnley / Kapanan takım filtresi)
        for d_team in DEFENSIVE_TEAMS_PRAGMATIC:
            if d_team in home or d_team in away:
                return False, "KARA_LİSTE_TAKIM", f"Pragmatik 1-0 Kurgusu / Aşırı Katı Blok ({d_team})"

        # 5. Tier 1 Kontrolü
        dyn_tier1 = self.data.get("dynamic_tier1", {})
        if lig in dyn_tier1 or lig in DEFAULT_TIER1_LEAGUES:
            desc = dyn_tier1.get(lig, {}).get("name") if lig in dyn_tier1 else DEFAULT_TIER1_LEAGUES.get(lig)
            return True, "TIER_1_ALTIN", f"Yüksek Tempolu Hücum Ligi ({desc})"

        return True, "STANDART", "Standart KGA Adayı"

    def _recalculate_analytics(self):
        """Lig ve oran bandı bazında istatistikleri ve dinamik kara listeleri günceller."""
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
            if m.get("ust25_won"):
                lig_stats[lig]["ust_won"] += 1
            if m.get("kgvar_won"):
                lig_stats[lig]["kg_won"] += 1
            if m.get("both_won"):
                lig_stats[lig]["both_won"] += 1

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
                if m.get("ust25_won"):
                    bracket_stats[b]["won"] += 1

        self.data["lig_stats"] = lig_stats
        self.data["odds_bracket_stats"] = bracket_stats

        # Dinamik Kara Liste ve Tier 1 Otomatik Kalibrasyonu
        dynamic_blacklist = self.data.get("dynamic_blacklist", {})
        dynamic_tier1 = self.data.get("dynamic_tier1", {})
        tactical_overrides = self.data.get("league_tactical_overrides", {})

        for lig, s in lig_stats.items():
            # 1-1 Tuzağı Denetimi: KG Var yüksek ama 2.5 Üst düşükse otomatik KG_VAR_ONLY yap
            if s["total"] >= 1 and s["kg_won"] >= 1 and s["ust_won"] == 0:
                tactical_overrides[lig] = {
                    "rule": "KG_VAR_ONLY",
                    "reason": f"{lig} liginde maçlar 1-1 barajına ulaşıyor ancak 3. golü bulamıyor. Düz 2.5 Üst yasaklandı, sadece KG Var oynanacak.",
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }

            if s["total"] >= 3:
                win_rate = (s["ust_won"] / s["total"]) * 100
                if win_rate <= 45.0:
                    # Kara listeye al
                    dynamic_blacklist[lig] = {
                        "name": lig,
                        "win_rate": round(win_rate, 1),
                        "total_matches": s["total"],
                        "reason": f"Son {s['total']} maçta %{win_rate:.1f} başarı (Kısır lig barajı)",
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    if lig in dynamic_tier1:
                        del dynamic_tier1[lig]
                elif win_rate >= 75.0:
                    # Tier 1'e terfi ettir
                    dynamic_tier1[lig] = {
                        "name": lig,
                        "win_rate": round(win_rate, 1),
                        "total_matches": s["total"],
                        "reason": f"Son {s['total']} maçta %{win_rate:.1f} yüksek gol isabeti",
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    if lig in dynamic_blacklist:
                        del dynamic_blacklist[lig]
                else:
                    # %45 ile %75 arası: Eğer önceden kara listedeyse ve toparlandıysa şartlı çıkar
                    if lig in dynamic_blacklist and win_rate >= 60.0:
                        del dynamic_blacklist[lig]

        self.data["dynamic_blacklist"] = dynamic_blacklist
        self.data["dynamic_tier1"] = dynamic_tier1
        self.data["league_tactical_overrides"] = tactical_overrides
        self.data["last_control_audit"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.data["recommendations"] = self._generate_recommendations(lig_stats, bracket_stats, matches)

    def _generate_recommendations(self, lig_stats, bracket_stats, matches):
        recs = []
        total_matches = len(matches)
        if total_matches < 3:
            return ["Veri tabanı kalibrasyon aşamasında. Maç sonuçları biriktikçe kara liste ve Tier 1 otomatik güncellenecek."]

        # 1. Dinamik Kara Liste Bildirimleri
        dyn_bl = self.data.get("dynamic_blacklist", {})
        for lig, info in dyn_bl.items():
            recs.append(f"⛔ <b>[DİNAMİK KARA LİSTE]</b> {lig} ligi {info['reason']}. Otomatik elemeye alındı.")

        # 2. Tier 1 Bildirimleri
        dyn_tier1 = self.data.get("dynamic_tier1", {})
        for lig, info in dyn_tier1.items():
            recs.append(f"⭐ <b>[DİNAMİK TİER 1]</b> {lig} ligi {info['reason']}. Öncelikli bülten odağında.")

        # 3. Oran bandı tatlı nokta önerisi
        best_bracket = None
        best_rate = -1
        for b, s in bracket_stats.items():
            if s["total"] >= 3:
                rate = (s["won"] / s["total"]) * 100
                if rate > best_rate:
                    best_rate = rate
                    best_bracket = b
        
        if best_bracket and best_rate > 70:
            recs.append(f"🎯 <b>[ORAN TATLI NOKTASI]</b> En yüksek isabet: <b>{best_bracket}</b> (Başarı: %{best_rate:.1f}).")

        return recs

    def get_blacklist_and_tier_summary(self):
        """Aktif kara liste ve Tier 1 denetim tablosunu metin olarak üretir."""
        now = datetime.now()
        is_winter = now.month in [11, 12, 1, 2]

        lines = [
            "🛡️ <b>KGA 2.0 CANLI LİG & KARA LİSTE DENETİM DURUMU</b>",
            f"🕒 <i>Son Kontrol Tarihi:</i> {self.data.get('last_control_audit', 'Aktif')}",
            "━━━━━━━━━━━━━━━━━━━━",
            "⛔ <b>GÜNCEL AKTİF KARA LİSTE (OTOMATİK ELENENLER):</b>"
        ]

        # Kış Şartları
        if is_winter:
            lines.append("❄️ <i>Mevsimsel Kış Karartması (Kasım-Şubat):</i>")
            for k, v in SEASONAL_WINTER_LEAGUES.items():
                lines.append(f"  • <b>{k}</b>: {v}")

        # Taktiksel / Statik Kara Liste
        lines.append("🧱 <i>Yapısal Savunma / Kısır Ligler:</i>")
        for k, v in DEFAULT_BLACKLISTED_LEAGUES.items():
            lines.append(f"  • <b>{k}</b>: {v}")

        # Dinamik Kara Liste (Sonuçlara göre düşenler)
        dyn_bl = self.data.get("dynamic_blacklist", {})
        if dyn_bl:
            lines.append("📉 <i>Sonuç Kontrolleriyle Kara Listeye Alınanlar:</i>")
            for k, v in dyn_bl.items():
                lines.append(f"  • <b>{k}</b>: Başarı %{v.get('win_rate', 0)} ({v.get('reason', '')})")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("⭐ <b>GÜNCEL TİER 1 ONAYLI TEMPO LİGLERİ:</b>")
        for k, v in DEFAULT_TIER1_LEAGUES.items():
            lines.append(f"  • <b>{k}</b>: {v}")
        dyn_t1 = self.data.get("dynamic_tier1", {})
        for k, v in dyn_t1.items():
            if k not in DEFAULT_TIER1_LEAGUES:
                lines.append(f"  • <b>{k}</b> [TERFİ ETTİ]: Başarı %{v.get('win_rate', 0)}")

        # Taktiksel Kısıtlamalar (1-1 Tuzağı Korumaları)
        overrides = self.data.get("league_tactical_overrides", {})
        if overrides:
            lines.append("━━━━━━━━━━━━━━━━━━━━")
            lines.append("🔒 <b>OTOMATİK TAKTİKSEL KORUMA (SADECE KG VAR LİGLERİ):</b>")
            for k, v in overrides.items():
                lines.append(f"  • <b>{k}</b>: {v.get('rule')} ({v.get('reason', '')})")

        return "\n".join(lines)

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
            "🧠 <b>CANLI KONTROLLER & KALİBRASYON:</b>"
        ]

        for r in self.data.get("recommendations", []):
            report.append(f"• {r}")

        return "\n".join(report)

if __name__ == "__main__":
    engine = KGAFeedbackEngine()
    print(engine.get_blacklist_and_tier_summary())
    print("\n" + "="*40 + "\n")
    print(engine.generate_daily_learning_report())

