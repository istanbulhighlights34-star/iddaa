#!/usr/bin/env python3
"""
Kinetik Gol Algoritması 2.0 (KGA) - 7/24 Tam Otomatik & Kendini Geliştiren Bulut Motoru
1. İddaa bültenini çeker ve KGA 2.0 İkiz Kilidini çalıştırır.
2. Dünün maç sonuçlarını ve skorlarını analiz eder.
3. Algoritmanın başarı oranını (2.5 Üst, KG Var, Skor) ölçer.
4. Kural iyileştirme ve kalibrasyon önerileri üretir.
5. Raporu ve önerileri Telegram botunuza (@ElgAnaliz_2026_bot) iletir.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
import pdfplumber

from kga_feedback_engine import KGAFeedbackEngine

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082147299:AAEQubL7YIyr4NPS_MAoT02xixUjQ_RtiD0")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "664321983")

def get_turkey_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=3)

def get_active_bulletin_info(current_dt):
    weekday = current_dt.weekday()
    if weekday in [1, 2, 3]: # Salı, Çarşamba, Perşembe
        days_back = weekday - 1
    elif weekday in [4, 5, 6]: # Cuma, Cumartesi, Pazar
        days_back = weekday - 4
    else: # Pazartesi (0)
        days_back = 3 # Cuma bülteni

    bulletin_date = current_dt - timedelta(days=days_back)
    filename = bulletin_date.strftime("%d-%m-%Y-Bulten.pdf")
    url = f"https://www.iddaa.com/dosyalar/bayimalzemeleri/{filename}"
    return filename, url, bulletin_date

def ensure_bulletin_pdf(filename, url, archive_dir):
    os.makedirs(archive_dir, exist_ok=True)
    local_path = os.path.join(archive_dir, filename)
    
    if os.path.exists(local_path) and os.path.getsize(local_path) > 10000:
        return local_path
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp, open(local_path, "wb") as f:
            f.write(resp.read())
        return local_path
    except Exception as e:
        existing = [f for f in os.listdir(archive_dir) if f.endswith("-Bulten.pdf")]
        if existing:
            latest = sorted(existing)[-1]
            return os.path.join(archive_dir, latest)
        return None

def parse_kga_matches(pdf_path):
    all_matches = []
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
                
                if ust25_w and kgvar_w:
                    try:
                        u = float(ust25_w[0].replace(',', '.'))
                        k = float(kgvar_w[0].replace(',', '.'))
                        if 1.70 <= u <= 1.95 and 1.40 <= k <= 1.62:
                            all_matches.append({
                                'page': page_idx + 1,
                                'lig': ''.join(lig_w),
                                'saat': saat_w[0] if saat_w else '',
                                'home': ' '.join(home_w),
                                'away': ' '.join(away_w),
                                'ms1': ms1_w[0] if ms1_w else '',
                                'msx': msx_w[0] if msx_w else '',
                                'ms2': ms2_w[0] if ms2_w else '',
                                'alt25': alt25_w[0] if alt25_w else '',
                                'ust25': u,
                                'kgvar': k,
                                'kgyok': kgyok_w[0] if kgyok_w else ''
                            })
                    except Exception:
                        pass
    return all_matches

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    chunk_size = 4000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                pass
            print("[✓] Telegram gönderimi başarılı.")
        except Exception as e:
            print(f"[!] Telegram gönderim hatası: {e}")

def main():
    tr_time = get_turkey_time()
    tarih_str = tr_time.strftime("%d.%m.%Y")
    gun_str = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][tr_time.weekday()]
    
    print(f"[*] KGA 2.0 Analiz & Geri Besleme Motoru Başlatıldı: {tarih_str} {gun_str}")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    archive_dir = os.path.join(base_dir, "archive")
    
    # 1. Geri Besleme ve Öğrenme Motorunu Çalıştır
    feedback_engine = KGAFeedbackEngine()
    learning_report = feedback_engine.generate_daily_learning_report()
    
    # 2. Bülten Analizini Yükle
    payload_file = os.path.join(base_dir, "telegram_payload.txt")
    bulten_msg = ""
    if os.path.exists(payload_file):
        with open(payload_file, "r", encoding="utf-8") as f:
            bulten_msg = f.read().strip()
            
    # 3. İki Raporu Birleştir ve Gönder
    final_message = f"{bulten_msg}\n\n━━━━━━━━━━━━━━━━━━━━\n{learning_report}"
    send_telegram(final_message)

if __name__ == "__main__":
    main()
