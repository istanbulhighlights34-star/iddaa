#!/usr/bin/env python3
"""
Kinetik Gol Algoritması 2.0 (KGA) - 7/24 Tam Otomatik, Yapay Zeka Destekli & Kendini Geliştiren Bulut Motoru
1. İddaa bültenini otomatik çeker (Salı/Cuma döngüsü).
2. 1. Aşama Matematiksel Süzgeç: İkiz Oran Kilidi (2.5 Üst 1.70-1.95 & KG Var 1.40-1.62) adaylarını çıkarır.
3. 2. Aşama Yapay Zeka Süzgeci (Gemini AI Brain):
   - Burnley tipi 1-0'a yatan takımları ve kısır ligleri eler.
   - En yüksek xG ve hücum geçişi olan maçı "Günün Altın Tek Maçı (Tier 1)" seçer.
   - Saatleri kesinlikle çakışmayan Kademeli Kasa Katlama (Rolling Bet) zincirini kurar.
   - Sistem 2-3 Skor kombinasyonlarını üretir.
4. 3. Aşama Geri Besleme (Feedback Engine): Dünün maç sonuçlarını ve algoritma optimizasyon önerilerini ekler.
5. Telegram botunuza (@ElgAnaliz_2026_bot) eksiksiz teslim eder.
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
from bulletin_full_evaluator import BulletinFullEvaluator
from kga_bankroll_engine import KGABankrollEngine

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082147299:AAEQubL7YIyr4NPS_MAoT02xixUjQ_RtiD0")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "664321983")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

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
                        # KGA İkiz Kilidi: 2.5 Üst 1.70-1.95 & KG Var 1.40-1.62
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

def ai_filter_and_generate_report(candidate_matches, blacklisted_candidates, blacklist_summary, date_str, gun_str, learning_report):
    """
    Yapay Zeka Süzgeci (Gemini AI Brain):
    Matematiksel ikiz kilidi geçen maçları alır; taktiksel xG analizi, dinamik kara liste,
    kış şartları kontrolleri, çakışmasız kasa katlama ve günün altın tek maçını belirler.
    """
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""Sen Kinetik Gol Algoritması 2.0 (KGA) Yapay Zeka Uzmanısın.
Bugünün resmi İddaa bülteninden matematiksel İkiz Oran Kilidini (2.5 Üst 1.70-1.95 & KG Var 1.40-1.62) geçen aday maçları taktiksel xG, dinamik kara liste ve tempo süzgecinden geçirerek nihai analiz raporunu hazırla.

TARİH: {date_str} {gun_str}

KGA 2.0 KURALLARI VE YÖNERGELER (KGA_MANIFESTO.md):
1. ⭐ GÜNÜN ALTIN TEK MAÇI (TIER 1):
   - Adaylar arasından hücum geçişi en tempolu, lig dinamizmi en yüksek, 1-1 kesinliği en net olan SADECE 1 MAÇ seçilecek (Hedef Oran: 1.75 - 2.10 bandı).
   - 🛡️ KALİBRASYON KURALI: Romanya veya İspanya alt ligleri gibi 1-1'den sonra maçı soğutan ligler Altın Maçta DÜZ 2.5 ÜST olarak seçilmez. Düz 2.5 Üst YALNIZCA 1-1'den sonra durmayan saf hücum liglerinden (Almanya 1-2, Hollanda 1-2, İsviçre vb.) seçilebilir. Diğer liglerde tercih KG Var veya KG Var & 2.5 Üst hibriti olarak kilitlenir.
   - Canlı kadro, xG ve taktiksel teşhisini maddelerle açıkla.
2. 📈 KADEMELİ KASA KATLAMA (ROLLING BET - ÇAKIŞMASIZ ZİNCİR):
   - Gün içinde saatleri KESİNLİKLE ÇAKIŞMAYAN 2 ila 3 basamaklı seri oluştur.
   - 🛡️ KASA KORUMASI: 1. basamakta kasanın riske girmemesi için KG Var (1.40 - 1.62) veya Tier 1 süper tempo 2.5 Üst seç. Skor koruyan liglerde çıplak 2.5 Üst riskine girme.
   - Temiz maç yoksa zorlama basamak açma, 2 basamakta bırak.
3. 🎲 SİSTEM 2-3 SKOR KUPONU:
   - KGA 1-1 barajını aşarak 2-1, 1-2, 3-1 veya 2-2 skoruna evrilecek 3 maç ve hedef skorlarını yaz.
4. ⛔ DİNAMİK KARA LİSTE ELEMELERİ (CANLI KONTROLLERLE ELENENLER):
   - Aşağıda verilen elenmiş maçları ve dinamik kontrolleri kullanarak; mevsimsel kış karartmasına uğrayan ligleri (Polonya Ekstraklasa vb.), düşük oranlı/kısır Serie B ekolünü ve Burnley tipi aşırı pragmatik kapanan takımları gerekçeleriyle listele.
5. 💎 ÖZEL FIRSAT VE PATLAMA RADARI (EKSTRA DEĞER & VALUE BET MODÜLÜ):
   - Ana omurgamız 2.5 Üst ve KG Var olmakla birlikte; bültende geçmiş oran kalıplarına ve istatistiklere dayanarak çok belirgin bir "Net Maç Sonucu (MS 1/2)", "4+ Gol / 3.5 Üst Patlaması" veya "İddaa Oran Sapması" fark ettiğin istisnai maçlar varsa bunları bu özel başlık altında gerekçesiyle paylaş.
   - Temiz bir fırsat yoksa zorlama yapma.

GÜNCEL CANLI LİG & KARA LİSTE DENETİM TABLOSU:
{blacklist_summary}

SİSTEM TARAFINDAN ÖN-DENETİMLE KARA LİSTEYE ALINIP ELENEN MAÇLAR:
{json.dumps(blacklisted_candidates, ensure_ascii=False, indent=2)}

BUGÜNÜN MATEMATİKSEL İKİZ KİLİDİ GEÇEN GÜVENLİ ADAY MAÇLARI:
{json.dumps(candidate_matches, ensure_ascii=False, indent=2)}

FORMAT KURALLARI:
- Yalnızca Telegram HTML etiketleri kullan (<b>, <i>, <code>, <u>). Asla Markdown (#, **, *) veya <div>/<p> kullanma.
- Çıktı doğrudan Telegram mesajı olarak gönderilecektir, profesyonel emojili ve net formatla üret.
"""
        model_name = "gemini-3.8-flash"
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
        except Exception as m_err:
            print(f"[!] {model_name} hatası, alternatif model deneniyor: {m_err}")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

        if response and response.text:
            print("[✓] Yapay zeka (Gemini AI) süzme ve raporlama sürecini başarıyla tamamladı.")
            return response.text
    except Exception as e:
        print(f"[!] Yapay zeka süzgeci çağrılırken hata: {e}")
    return None

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
    
    print(f"[*] KGA 2.0 Yapay Zeka Motoru Başlatıldı: {tarih_str} {gun_str} (Saat: {tr_time.strftime('%H:%M')})")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    archive_dir = os.path.join(base_dir, "archive")
    
    # 1. Geri Besleme ve Öğrenme Motorunu Çalıştır
    feedback_engine = KGAFeedbackEngine()
    learning_report = feedback_engine.generate_daily_learning_report()
    
    # 2. Bülten PDF'ini Al ve Matematiksel Süzgeci Çalıştır
    filename, url, bulletin_date = get_active_bulletin_info(tr_time)
    pdf_path = ensure_bulletin_pdf(filename, url, archive_dir)
    
    if not pdf_path or not os.path.exists(pdf_path):
        print("[!] Bülten PDF'ine ulaşılamadı.")
        return

    # Kümülatif Bülten Arşivleme ve Geçmiş Karşılaştırmalı Analiz Motoru
    evaluator = BulletinFullEvaluator(archive_dir=archive_dir)
    macro_info = evaluator.archive_and_cross_analyze(pdf_path)
    historical_macro_report = evaluator.generate_macro_historical_summary()
    print(f"[*] Kümülatif Arşiv Güncellendi: {macro_info['total_bulletins']} bülten, {macro_info['total_archived_matches']} toplam maç.")
        
    candidate_matches = parse_kga_matches(pdf_path)
    print(f"[*] Matematiksel İkiz Kilidi geçen aday maç sayısı: {len(candidate_matches)}")
    
    # Güvenlik ve Dinamik Kara Liste Ayrıştırması
    safe_candidates = []
    blacklisted_candidates = []
    for m in candidate_matches:
        is_safe, status, reason = feedback_engine.check_match_safety(m, current_date=tr_time)
        m["safety_status"] = status
        m["safety_reason"] = reason
        if is_safe:
            safe_candidates.append(m)
        else:
            blacklisted_candidates.append(m)

    print(f"[*] Dinamik Denetim: {len(safe_candidates)} güvenli aday, {len(blacklisted_candidates)} kara listeye alınan maç.")
    blacklist_summary = feedback_engine.get_blacklist_and_tier_summary()
    
    # 3. Yapay Zeka (Gemini AI Brain) Süzgecinden Geçir
    ai_report = ai_filter_and_generate_report(
        safe_candidates, 
        blacklisted_candidates, 
        blacklist_summary, 
        tarih_str, 
        gun_str, 
        learning_report
    )
    
    # 4. Kasa Yönetimi ve Parçalı Yatırım Planını Ekle
    bankroll_engine = KGABankrollEngine()
    bankroll_summary = bankroll_engine.get_bankroll_summary()
    
    if ai_report and len(ai_report.strip()) > 100:
        final_message = f"{ai_report}\n\n━━━━━━━━━━━━━━━━━━━━\n{bankroll_summary}\n\n━━━━━━━━━━━━━━━━━━━━\n{learning_report}"
    else:
        # Yedek mekanizma (Fallback)
        payload_file = os.path.join(base_dir, "telegram_payload.txt")
        bulten_msg = ""
        if os.path.exists(payload_file):
            with open(payload_file, "r", encoding="utf-8") as f:
                bulten_msg = f.read().strip()
        final_message = f"{bulten_msg}\n\n━━━━━━━━━━━━━━━━━━━━\n{bankroll_summary}\n\n━━━━━━━━━━━━━━━━━━━━\n{learning_report}"

    send_telegram(final_message)

if __name__ == "__main__":
    main()
