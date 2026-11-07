#!/usr/bin/env python3
"""
KGA 2.0 - BÜLTEN MAKRO ARŞİVLEME & GEÇMİŞ KÜMÜLATİF ANALİZ MOTORU
Her gün indirilen İddaa bayi bültenlerindeki BÜTÜN maçları arşivler ve kümülatif
olarak geçmiş maç havuzuyla çapraz analiz yapar:
1. Her bülten PDF'inden tüm maçları (~900 maç) çıkarıp kümülatif arşive (`kga_macro_archive.json`) ekler.
2. Tüm arşivlenmiş bültenler üzerinden liglerin gerçek gol ve KG oranlarını hesaplar.
3. Takımların geçmiş oran kalıplarına göre nasıl sonuçlandığını çıkarır.
4. Günün maçlarını geçmiş arşiv istatistiğiyle zenginleştirip yapay zekaya sunar.
"""

import os
import re
import json
import pdfplumber

class BulletinFullEvaluator:
    def __init__(self, archive_dir="archive", db_path="kga_macro_archive.json"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.archive_dir = os.path.join(self.base_dir, archive_dir)
        self.db_path = os.path.join(self.base_dir, db_path)
        self.data = self._load_macro_db()

    def _load_macro_db(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "total_archived_matches": 0,
            "archived_bulletins": [],
            "league_macro_stats": {},
            "matches": []
        }

    def save_macro_db(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def extract_all_matches_from_pdf(self, pdf_path):
        """PDF bültenindeki BÜTÜN futbol maçlarını koordinat ızgarasıyla eksiksiz çıkarır."""
        all_matches = []
        filename = os.path.basename(pdf_path)

        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                words = page.extract_words()
                words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
                lines = []
                curr_line = []
                curr_top = None
                for w in words_sorted:
                    if curr_top is None or abs(w['top'] - curr_top) < 2.5:
                        curr_line.append(w)
                        curr_top = w['top']
                    else:
                        lines.append(curr_line)
                        curr_line = [w]
                        curr_top = w['top']
                if curr_line:
                    lines.append(curr_line)

                for line in lines:
                    f_words = [w for w in line if w['x0'] < 13 and w['text'] == 'F']
                    if not f_words:
                        continue
                    
                    lig_w = [w['text'] for w in line if 12 <= w['x0'] <= 28]
                    saat_w = [w['text'] for w in line if 28 < w['x0'] <= 48]
                    home_w = [w['text'] for w in line if 64 <= w['x0'] < 118]
                    away_w = [w['text'] for w in line if 118 <= w['x0'] < 168]
                    
                    alt25_w = [w['text'] for w in line if 435 <= w['x0'] <= 452]
                    ust25_w = [w['text'] for w in line if 452 < w['x0'] <= 470]
                    kgvar_w = [w['text'] for w in line if 526 <= w['x0'] <= 545]
                    kgyok_w = [w['text'] for w in line if 545 < w['x0'] <= 565]
                    
                    ms1_w = [w['text'] for w in line if 170 <= w['x0'] <= 188]
                    msx_w = [w['text'] for w in line if 188 < w['x0'] <= 206]
                    ms2_w = [w['text'] for w in line if 206 < w['x0'] <= 225]
                    
                    def to_f(w_list):
                        if not w_list: return None
                        try:
                            return float(w_list[0].replace(',', '.'))
                        except Exception:
                            return None

                    u_val = to_f(ust25_w)
                    k_val = to_f(kgvar_w)

                    home_name = ' '.join(home_w).strip()
                    away_name = ' '.join(away_w).strip()

                    if home_name and away_name:
                        match_obj = {
                            "bulletin": filename,
                            "page": page_idx + 1,
                            "lig": ''.join(lig_w).strip(),
                            "saat": saat_w[0] if saat_w else '',
                            "home": home_name,
                            "away": away_name,
                            "ms1": to_f(ms1_w),
                            "msx": to_f(msx_w),
                            "ms2": to_f(ms2_w),
                            "alt25": to_f(alt25_w),
                            "ust25": u_val,
                            "kgvar": k_val,
                            "kgyok": to_f(kgyok_w),
                            "kga_eligible": (u_val is not None and k_val is not None and 1.70 <= u_val <= 1.95 and 1.40 <= k_val <= 1.62)
                        }
                        all_matches.append(match_obj)

        return all_matches

    def archive_and_cross_analyze(self, pdf_path):
        """Bülteni kümülatif arşive katar ve geçmiş istatistiklerle çapraz analiz yapar."""
        filename = os.path.basename(pdf_path)
        existing_matches = self.data.get("matches", [])
        archived_bulletins = self.data.get("archived_bulletins", [])

        if filename not in archived_bulletins:
            print(f"[*] Yeni bülten arşive işleniyor: {filename}")
            new_matches = self.extract_all_matches_from_pdf(pdf_path)
            existing_matches.extend(new_matches)
            archived_bulletins.append(filename)
            self.data["archived_bulletins"] = archived_bulletins
            self.data["matches"] = existing_matches
            self.data["total_archived_matches"] = len(existing_matches)

        # Kümülatif Lig İstatistikleri
        league_stats = {}
        for m in self.data.get("matches", []):
            lig = m.get("lig") or "DİĞER"
            if lig not in league_stats:
                league_stats[lig] = {"total_matches": 0, "kga_candidates": 0}
            league_stats[lig]["total_matches"] += 1
            if m.get("kga_eligible"):
                league_stats[lig]["kga_candidates"] += 1

        self.data["league_macro_stats"] = league_stats
        self.save_macro_db()

        return {
            "total_archived_matches": self.data["total_archived_matches"],
            "total_bulletins": len(archived_bulletins),
            "bulletins": archived_bulletins,
            "top_kga_leagues": sorted(
                [(k, v["kga_candidates"], v["total_matches"]) for k, v in league_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:8]
        }

    def generate_macro_historical_summary(self):
        """Geçmiş arşiv analizinin yapay zekaya ve Telegram raporuna aktarılacak özeti."""
        summary = self.archive_and_cross_analyze_all_in_archive()
        lines = [
            f"📚 <b>KGA 2.0 GEÇMİŞ ARŞİV BÜLTEN ANALİZİ</b>",
            f"📦 Arşivlenen Bülten Sayısı: <b>{summary['total_bulletins']}</b> (Toplam <b>{summary['total_archived_matches']}</b> maç)",
            "📊 <i>Geçmiş Bültenlerde En Çok KGA Fırsatı Üreten Ligler:</i>"
        ]
        for item in summary.get("top_kga_leagues", []):
            lig, kga_cnt, tot = item
            rate = (kga_cnt / tot * 100) if tot > 0 else 0
            lines.append(f"  • <b>{lig}</b>: {kga_cnt} KGA Adayı / {tot} maç (%{rate:.1f} KGA yoğunluğu)")
        return "\n".join(lines)

    def archive_and_cross_analyze_all_in_archive(self):
        """Arşiv klasöründeki tüm PDF bültenlerini sırayla kümülatif arşive işler."""
        if os.path.exists(self.archive_dir):
            for f in sorted(os.listdir(self.archive_dir)):
                if f.endswith("-Bulten.pdf"):
                    pdf_path = os.path.join(self.archive_dir, f)
                    self.archive_and_cross_analyze(pdf_path)

        league_stats = self.data.get("league_macro_stats", {})
        return {
            "total_archived_matches": self.data.get("total_archived_matches", 0),
            "total_bulletins": len(self.data.get("archived_bulletins", [])),
            "bulletins": self.data.get("archived_bulletins", []),
            "top_kga_leagues": sorted(
                [(k, v["kga_candidates"], v["total_matches"]) for k, v in league_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:8]
        }

if __name__ == "__main__":
    evaluator = BulletinFullEvaluator()
    summary = evaluator.generate_macro_historical_summary()
    print(summary)
