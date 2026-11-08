#!/usr/bin/env python3
"""
KGA 3.0 - Gün Sonu Kapanış ve Kasa Denetim Raporu
Her gece maçlar bittiğinde (23:55 TSİ) oynanan tüm maçları aşağıdan yukarıya
sonuçları (✅ Kazandı / ❌ Kaybetti / ⏸️ Ertelendi) ile Telegram'a iletir
ve kalıcı olarak GUNLUK_MAC_VE_KASA_DEFTERI.md dosyasına işler.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082147299:AAEQubL7YIyr4NPS_MAoT02xixUjQ_RtiD0")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "664321983")

def get_turkey_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=3)

def generate_eod_report(target_date=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    history_file = os.path.join(base_dir, "kga_betting_history.json")
    
    if not os.path.exists(history_file):
        return "Henüz kayıtlı maç geçmişi bulunamadı."
        
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    # İstenen tarih veya tüm geçmiş (aşağıdan yukarıya sıralama)
    # Kullanıcı talebi: oynadığımız maçları aşağıdan yukarıya şeklinde kaydet
    # Kronolojik olarak en eskiden en yeniye doğru aşağıdan yukarıya listelenir
    
    lines = [
        "📋 <b>KGA 3.0 GÜN SONU KEPENK KAPANIŞ & KASA RAPORU</b>",
        f"📅 <b>Rapor Zamanı:</b> {get_turkey_time().strftime('%d.%m.%Y %H:%M')}",
        "━━━━━━━━━━━━━━━━━━━━",
        "⚽ <b>TÜM OYNANAN MAÇLAR & SONUÇLAR (AŞAĞIDAN YUKARIYA):</b>",
        ""
    ]

    total_stake = 0
    total_return = 0
    won_count = 0
    lost_count = 0
    postponed_count = 0

    # Ters sıra (En yeni en üstte veya aşağıdan yukarıya akış)
    # En eski maç altta, en yeni maç en üstte olacak şekilde (veya kronolojik):
    # Kullanıcı 'aşağıdan yukarıya şeklinde kaydetmeni' dediği için:
    # 1. Maç en altta, son maç en üstte yer alır
    reversed_history = list(reversed(history))

    for idx, m in enumerate(reversed_history, 1):
        status = m.get("status", "").lower()
        if status == "won":
            icon = "✅"
            res_text = "KAZANDI"
            won_count += 1
        elif status == "lost":
            icon = "❌"
            res_text = "KAYBETTİ"
            lost_count += 1
        else:
            icon = "⏸️"
            res_text = "ERTELENDİ / İADE"
            postponed_count += 1

        stake = m.get("stake", 0)
        ret = m.get("return", 0)
        total_stake += stake
        total_return += ret

        date_str = m.get("date", "")
        day_str = m.get("day", "")
        home = m.get("home", "")
        away = m.get("away", "")
        league = m.get("league", "")
        bet = m.get("bet", "")
        score = m.get("score", "-")

        lines.append(f"{icon} <b>[{res_text}]</b> {home} {score} {away}")
        lines.append(f"   • <b>Tarih/Lig:</b> {date_str} {day_str} ({league})")
        lines.append(f"   • <b>Oynanan Tercih:</b> <code>{bet}</code>")
        lines.append(f"   • <b>Yatırım/Dönüş:</b> {stake} TL ➔ <b>{ret:.2f} TL</b>")
        lines.append("────────────────────")

    net_pl = total_return - total_stake
    pl_sign = "+" if net_pl >= 0 else ""

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💰 <b>GENEL KASA VE PERFORMANS TABLOSU:</b>")
    lines.append(f"• <b>Toplam İncelenen Maç:</b> {len(history)}")
    lines.append(f"• <b>Başarılı (✅):</b> {won_count} | <b>Başarısız (❌):</b> {lost_count} | <b>Ertelenen (⏸️):</b> {postponed_count}")
    lines.append(f"• <b>Toplam Yatırılan:</b> {total_stake:.2f} TL")
    lines.append(f"• <b>Toplam Geri Dönen:</b> {total_return:.2f} TL")
    lines.append(f"• <b>Kümülatif Net Kâr/Zarar:</b> <b>{pl_sign}{net_pl:.2f} TL</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 <i>KGA 3.0 ile 3.5 Alt Ana Kale disiplini devreye alınmış ve sermaye koruma zırhı güçlendirilmiştir.</i>")

    full_report = chr(10).join(lines)
    return full_report

def save_to_markdown_ledger(report_text):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ledger_path = os.path.join(base_dir, "GUNLUK_MAC_VE_KASA_DEFTERI.md")
    
    clean_md = report_text.replace("<b>", "**").replace("</b>", "**").replace("<i>", "*").replace("</i>", "*").replace("<code>", "")
    header = chr(10) + chr(10) + "## [KAPANIS RAPORU] " + get_turkey_time().strftime("%d.%m.%Y %H:%M") + " TSİ" + chr(10) + chr(10)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(header + clean_md)
    print("[*] GUNLUK_MAC_VE_KASA_DEFTERI.md güncellendi.")

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
            print("[✓] Gün sonu raporu Telegram'a başarıyla iletildi.")
        except Exception as e:
            print(f"[!] Telegram gönderim hatası: {e}")

def main():
    report = generate_eod_report()
    save_to_markdown_ledger(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
