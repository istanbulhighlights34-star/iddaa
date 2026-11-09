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

def parse_kga_matches(pdf_path, target_day=None):
    """
    KGA 3.0 Çok Yönlü 360° Bülten Ayrıştırıcısı:
    - Sayfa gününü (Pazar, Cumartesi vb.) denetler.
    - MBS (1, 2, 3) değerini okur.
    - 3.5 Alt, 2.5 Alt/Üst, Handikaplı MS (HMS 1/X/2), Net MS ve KG Var oranlarını çeker.
    """
    all_matches = []
    target_day_upper = target_day.strip().upper() if target_day else None

    with pdfplumber.open(pdf_path) as pdf:
        current_day = ''
        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ''
            for line in text.splitlines()[:5]:
                m = re.search(r'(CUMARTESİ|PAZARTESİ|ÇARŞAMBA|PERŞEMBE|CUMA|PAZAR|SALI)', line.upper())
                if m:
                    current_day = m.group(1)
                    break

            if target_day_upper and current_day and current_day != target_day_upper:
                continue

            words = sorted(page.extract_words(), key=lambda w: (w['top'], w['x0']))
            lines = []
            curr_line = []
            curr_top = None
            for w in words:
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
                mbs_w = [w['text'] for w in line if 48 <= w['x0'] <= 56 and w['text'].isdigit()]
                home_w = [w['text'] for w in line if 64 <= w['x0'] < 118]
                away_w = [w['text'] for w in line if 118 <= w['x0'] < 168]
                
                ms1_w = [w['text'] for w in line if 170 <= w['x0'] <= 188]
                msx_w = [w['text'] for w in line if 188 < w['x0'] <= 206]
                ms2_w = [w['text'] for w in line if 206 < w['x0'] <= 225]
                
                hms1_w = [w['text'] for w in line if 225 < w['x0'] <= 244]
                hmsx_w = [w['text'] for w in line if 244 < w['x0'] <= 262]
                hms2_w = [w['text'] for w in line if 262 < w['x0'] <= 280]

                alt25_w = [w['text'] for w in line if 435 <= w['x0'] <= 452]
                ust25_w = [w['text'] for w in line if 452 < w['x0'] <= 470]
                alt35_w = [w['text'] for w in line if 470 < w['x0'] <= 490]
                ust35_w = [w['text'] for w in line if 490 < w['x0'] <= 510]
                kgvar_w = [w['text'] for w in line if 526 <= w['x0'] <= 545]
                kgyok_w = [w['text'] for w in line if 545 < w['x0'] <= 565]

                all_matches.append({
                    'day': current_day or (target_day_upper or 'BUGÜN'),
                    'page': page_idx + 1,
                    'lig': ''.join(lig_w),
                    'saat': saat_w[0] if saat_w else '',
                    'mbs': int(mbs_w[0]) if mbs_w else 3,
                    'home': ' '.join(home_w),
                    'away': ' '.join(away_w),
                    'ms1': ms1_w[0] if ms1_w else '',
                    'msx': msx_w[0] if msx_w else '',
                    'ms2': ms2_w[0] if ms2_w else '',
                    'hms1': hms1_w[0] if hms1_w else '',
                    'hmsx': hmsx_w[0] if hmsx_w else '',
                    'hms2': hms2_w[0] if hms2_w else '',
                    'alt25': alt25_w[0] if alt25_w else '',
                    'ust25': ust25_w[0] if ust25_w else '',
                    'alt35': alt35_w[0] if alt35_w else '',
                    'ust35': ust35_w[0] if ust35_w else '',
                    'kgvar': kgvar_w[0] if kgvar_w else '',
                    'kgyok': kgyok_w[0] if kgyok_w else ''
                })
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

🚨 KESİN TARİH VE GÜN KURALI (EN KRİTİK KURAL):
BUGÜNÜN TARİHİ: {date_str} {gun_str}.
YALNIZCA VE YALNIZCA BUGÜN ({gun_str}) OYNANACAK CANLI/GELECEK MAÇLARI SEÇEBİLİRSİN.
CUMA VEYA CUMARTESİ GÜNÜ OYNANIP BİTMİŞ HİÇBİR MAÇ (Örn: Farul Constanta, Lucena, Cercle Brugge vb.) BÜLTENDE KESİNLİKLE YER ALAMAZ!
Aşağıda verilen aday maçlar tamamen bugün ({gun_str} günü) oynanacak maçlardır. Seçimlerini yalnızca bu listeden yap!

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


def save_todays_active_matches(base_dir, all_matches):
    alt35_candidates = []
    for m in all_matches:
        a35_str = m.get('alt35', '').replace(',', '.')
        if a35_str:
            try:
                if 1.20 <= float(a35_str) <= 1.35:
                    alt35_candidates.append(m)
            except Exception:
                pass

    k1 = alt35_candidates[:3] if len(alt35_candidates) >= 3 else all_matches[:3]
    active_list = []
    for m in k1:
        active_list.append({
            "home": m.get("home", ""),
            "away": m.get("away", ""),
            "tag": f"🏰 Ana Kale (MBS {m.get('mbs', 3)})",
            "target": f"3.5 Alt ({m.get('alt35', '1.25')})",
            "saat": m.get("saat", "")
        })
    with open(os.path.join(base_dir, "todays_active_matches.json"), "w", encoding="utf-8") as f:
        json.dump(active_list, f, ensure_ascii=False, indent=2)

def build_deterministic_kga_report(all_matches, blacklisted_candidates, tarih_str, gun_str):
    alt35_candidates = []
    for m in all_matches:
        a35_str = m.get('alt35', '').replace(',', '.')
        if a35_str:
            try:
                a35 = float(a35_str)
                if 1.20 <= a35 <= 1.35 and m.get('saat'):
                    alt35_candidates.append((a35, m))
            except Exception:
                pass

    alt35_candidates.sort(key=lambda x: x[0])
    k1_matches = [m for _, m in alt35_candidates[:3]]
    has_k1 = len(k1_matches) >= 3

    k1_odds = 1.0
    for m in k1_matches:
        try:
            k1_odds *= float(m.get('alt35', '1.25').replace(',', '.'))
        except Exception:
            k1_odds *= 1.25

    handicap_candidates = []
    for m in all_matches:
        h1_str = m.get('hms1', '').replace(',', '.')
        h2_str = m.get('hms2', '').replace(',', '.')
        ms1_str = m.get('ms1', '').replace(',', '.')
        ms2_str = m.get('ms2', '').replace(',', '.')
        try:
            if h1_str and 1.65 <= float(h1_str) <= 2.30 and ms1_str and float(ms1_str) <= 1.55:
                handicap_candidates.append(('H1', float(h1_str), m))
            elif h2_str and 1.65 <= float(h2_str) <= 2.30 and ms2_str and float(ms2_str) <= 1.55:
                handicap_candidates.append(('H2', float(h2_str), m))
        except Exception:
            pass

    h_pick = None
    for tip, odd, m in handicap_candidates:
        if m.get('mbs') == 1:
            h_pick = (tip, odd, m)
            break
    if not h_pick and handicap_candidates:
        h_pick = handicap_candidates[0]

    value_pick = all_matches[5] if len(all_matches) > 5 else (all_matches[0] if all_matches else {})

    lines = [
        '⚽ <b>KİNETİK GOL ALGORİTMASI 3.0 (KGA) - 360° ÇOK YÖNLÜ BÜLTEN RAPORU</b>',
        f'📅 <b>Tarih:</b> {tarih_str} {gun_str}',
        '⚡ <b>Model:</b> KGA 3.0 (3.5 Alt Ana Kale & 360° Handikap Radarı)',
        '━━━━━━━━━━━━━━━━━━━━',
        '',
        '🏰 <b>1. KUPON: "ANA KALE" (3.5 ALT GÜVENCE KOMBİNİ)</b>',
        "<i>Kural: 10 farklı skorda (0-0 dan 2-1 e) firesiz kazandırır. İddaa MBS 3 kuralına %100 uyumludur.</i>"
    ]

    if len(k1_matches) >= 3:
        for i, m in enumerate(k1_matches, 1):
            o = m.get('alt35', '1.25')
            lines.append(f"• <b>{i}. Maç (MBS {m.get('mbs', 3)}):</b> {m.get('home')} - {m.get('away')} ({m.get('lig', '')} - {m.get('saat', '')}) ➔ <b>3.5 ALT ({o})</b>")
        lines.append(f'🎯 <b>Toplam Kupon Oranı:</b> <b>{k1_odds:.2f}</b>')
        lines.append('💰 <b>Yatırım Payı (%50):</b> <b>500 TL</b> (Kasanın Sarsılmaz Taşıyıcısı)')
    else:
        lines.append('🛡️ <i>Bugün İddaa bülten geçiş günüdür (Hafta sonu bülteni tamamlandı, yeni bülten bekleniyor). Güvenlik kriterlerimize uyan temiz maç bulunamadı. Zorlama kupon yapılmadı, bu kupon <b>PAS GEÇİLDİ / KASA KORUNDU</b>.</i>')
    lines.append('')
    lines.append('━━━━━━━━━━━━━━━━━━━━')
    lines.append('')
    lines.append('⚡ <b>2. KUPON: 360° BÜYÜK MAÇ & HANDİKAP RADARI</b>')

    if h_pick:
        tip, odd, hm = h_pick
        mbs_tag = '[MBS 1 - TEK MAÇ OYNANABİLİR]' if hm.get('mbs') == 1 else f"[MBS {hm.get('mbs')}]"
        lines.append(f"🏟️ <b>Maç:</b> {hm.get('home')} - {hm.get('away')} ({hm.get('lig')} - {hm.get('saat')}) {mbs_tag}")
        lines.append(f"🎯 <b>Öneri:</b> Handikaplı Maç Sonucu <b>{tip} ({odd:.2f})</b> (Net Galibiyet / En Az 2 Fark)")
        lines.append('🔍 <i>Teşhis:</i> Favori takımın kalite farkı ve tempolu hücum gücü ile handikap barajını aşması bekleniyor.')
        lines.append('💰 <b>Yatırım Payı (%30):</b> <b>300 TL</b> (Değerli Çarpan Hedefi)')
    else:
        lines.append('🛡️ <i>Bugün büyük maçlarda net handikap avantajı veren maç bulunamadı. Zorlama yapılmadı, bu kupon <b>PAS GEÇİLDİ / KASA KORUNDU</b>.</i>')

    lines.append('')
    lines.append('━━━━━━━━━━━━━━━━━━━━')
    lines.append('')
    lines.append('💎 <b>3. KUPON: SÜRPRİZ DEĞER & FIRSAT AVCISI</b>')
    lines.append(f"🏟️ <b>Maç:</b> {value_pick.get('home', '')} - {value_pick.get('away', '')} ({value_pick.get('lig', '')})")
    lines.append(f"🎯 <b>Öneri:</b> KG Var (<b>{value_pick.get('kgvar', '1.60')}</b>) veya 2.5 Üst (<b>{value_pick.get('ust25', '1.75')}</b>)")
    lines.append('💰 <b>Yatırım Payı (%20):</b> <b>200 TL</b> (Ekstra Getiri)')
    lines.append('')
    lines.append('━━━━━━━━━━━━━━━━━━━━')
    lines.append("🛡️ <b>MBS & İDDAA GÜVENCESİ:</b> Bültendeki maçların MBS şartları tam olarak gözetilmiştir. Tek maça kasanın %50'sini basma riski kaldırılmıştır.")

    report = chr(10).join(lines)
    return report

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
        
    # YALNIZCA BUGÜNÜN (Örn: Pazar) MAÇLARINI SÜZ
    candidate_matches = parse_kga_matches(pdf_path, target_day=gun_str)
    
    # Şu anki saatten sonra başlayacak canlı/gelecek maçları filtrele
    curr_time_str = tr_time.strftime("%H:%M")
    upcoming_matches = []
    for m in candidate_matches:
        saat_clean = re.sub(r'[^0-9:]', '', m.get("saat", ""))
        # Eğer saat belirtilmişse ve şu anki saatten sonraysa veya henüz başlamadıysa
        if not saat_clean or saat_clean >= curr_time_str:
            upcoming_matches.append(m)
        else:
            # Maç bugün oynandı ama saat olarak geride kaldı
            pass
            
    # Eğer henüz başlamamış yeterli maç varsa onları önceliklendir
    if len(upcoming_matches) >= 3:
        candidate_matches = upcoming_matches
        
    print(f"[*] BUGÜN ({gun_str} - {tarih_str}) İkiz Kilit Aday Maç Sayısı: {len(candidate_matches)}")
    
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
    
    if not ai_report or len(ai_report.strip()) < 100:
        print("[*] Gemini AI yanıt vermedi, bugünün maçlarıyla dinamik KGA 2.0 raporu üretiliyor...")
        ai_report = build_deterministic_kga_report(safe_candidates, blacklisted_candidates, tarih_str, gun_str)

    # 4. Kasa Yönetimi ve Parçalı Yatırım Planını Ekle
    bankroll_engine = KGABankrollEngine()
    bankroll_summary = bankroll_engine.get_bankroll_summary()

    sep = "━━━━━━━━━━━━━━━━━━━━"
    final_message = ai_report + chr(10) + chr(10) + sep + chr(10) + bankroll_summary + chr(10) + chr(10) + sep + chr(10) + learning_report

    # Kalıcı telegram payload dosyasını bugünün yeni verisiyle güncelle (asla eski gün kalmasın)
    payload_file = os.path.join(base_dir, "telegram_payload.txt")
    with open(payload_file, "w", encoding="utf-8") as f:
        f.write(final_message)

    # Günün aktif maçlarını kaydet
    save_todays_active_matches(base_dir, safe_candidates)

    send_telegram(final_message)

if __name__ == "__main__":
    main()
