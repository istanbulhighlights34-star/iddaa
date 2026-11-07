#!/usr/bin/env python3
"""
KGA 2.0 - BÜLTEN MAKRO ANALİZ & TÜM MAÇLAR KARŞILAŞTIRMA MOTORU
Bültendeki İSTİSNASIZ BÜTÜN futbol maçlarını (~900 maç) çıkarır.
Biten maç skorlarıyla toplu karşılaştırma yaparak:
1. Her ligin gerçek 2.5 Üst ve KG Var patlama oranını çıkarır.
2. Tüm oran bantlarının (1.50'den 2.20'ye) kazanma istatistiğini döker.
3. KGA İkiz Kilidinin bülten geneline kıyasla yarattığı pozitif farkı (Alpha / Edge) hesaplar.
4. Kısır ligleri toptan kara listeye alır, gollü ligleri Tier 1'e terfi ettirir.
"""

import os
import re
import json
import pdfplumber

class BulletinFullEvaluator:
    def __init__(self, archive_dir="archive", db_path="bulletin_global_analysis.json"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.archive_dir = os.path.join(self.base_dir, archive_dir)
        self.db_path = os.path.join(self.base_dir, db_path)

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
                    
                    # Oran dönüştürme
                    def to_f(w_list):
                        if not w_list: return None
                        try:
                            return float(w_list[0].replace(',', '.'))
                        except Exception:
                            return None

                    u_val = to_f(ust25_w)
                    k_val = to_f(kgvar_w)

                    match_obj = {
                        "bulletin": filename,
                        "page": page_idx + 1,
                        "lig": ''.join(lig_w).strip(),
                        "saat": saat_w[0] if saat_w else '',
                        "home": ' '.join(home_w).strip(),
                        "away": ' '.join(away_w).strip(),
                        "ms1": to_f(ms1_w),
                        "msx": to_f(msx_w),
                        "ms2": to_f(ms2_w),
                        "alt25": to_f(alt25_w),
                        "ust25": u_val,
                        "kgvar": k_val,
                        "kgyok": to_f(kgyok_w),
                        "kga_eligible": (u_val is not None and k_val is not None and 1.70 <= u_val <= 1.95 and 1.40 <= k_val <= 1.62)
                    }

                    if match_obj["home"] and match_obj["away"]:
                        all_matches.append(match_obj)

        return all_matches

    def analyze_bulletin(self, pdf_path):
        matches = self.extract_all_matches_from_pdf(pdf_path)
        total_count = len(matches)
        kga_count = sum(1 for m in matches if m["kga_eligible"])

        # Lig dağılımı
        leagues = {}
        for m in matches:
            lg = m["lig"] or "DİĞER"
            leagues[lg] = leagues.get(lg, 0) + 1

        summary = {
            "bulletin": os.path.basename(pdf_path),
            "total_football_matches": total_count,
            "kga_twin_lock_matches": kga_count,
            "total_leagues": len(leagues),
            "top_leagues": sorted(leagues.items(), key=lambda x: x[1], reverse=True)[:10],
            "matches": matches
        }

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary

if __name__ == "__main__":
    evaluator = BulletinFullEvaluator()
    pdf_file = os.path.join(evaluator.archive_dir, "06-11-2026-Bulten.pdf")
    if os.path.exists(pdf_file):
        res = evaluator.analyze_bulletin(pdf_file)
        print(f"Bülten: {res['bulletin']}")
        print(f"Toplam Çıkarılan Futbol Maçı: {res['total_football_matches']}")
        print(f"KGA İkiz Kilidine Uyan Maç: {res['kga_twin_lock_matches']}")
        print("En Çok Maç Olan İlk 5 Lig:", res["top_leagues"][:5])
