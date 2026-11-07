#!/usr/bin/env python3
"""
KGA 2.0 - Çift Yönlü İnteraktif Telegram Asistanı
Kullanıcının Telegram'dan yazdığı soruları anlar, canlı maç skorlarını çeker,
KGA bülten durumunu bildirir ve yapay zeka ile anında yanıt verir.
"""

import os
import sys
import json
import time
import re
import unicodedata
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
from datetime import datetime

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"KGA 2.0 Telegram Bot is LIVE and running 24/7!")

    def log_message(self, format, *args):
        pass

def run_health_server(port):
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        print(f"[!] Health server port {port} error: {e}")

from live_score_service import LiveScoreService
from kga_feedback_engine import KGAFeedbackEngine

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082147299:AAEQubL7YIyr4NPS_MAoT02xixUjQ_RtiD0")
AUTHORIZED_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "664321983"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class KGAInteractiveBot:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        self.score_service = LiveScoreService()
        self.feedback_engine = KGAFeedbackEngine()
        self.last_update_id = 0
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def send_message(self, chat_id, text, parse_mode="HTML"):
        url = f"{self.base_url}/sendMessage"
        chunk_size = 4000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        for chunk in chunks:
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    pass
            except Exception as e:
                print(f"[!] Mesaj gönderme hatası: {e}")

    def get_updates(self):
        url = f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}&timeout=20"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())
                if data.get("ok"):
                    return data.get("result", [])
        except Exception as e:
            time.sleep(2)
        return []

    def get_todays_matches(self):
        """Bugün bültende önerilen güncel maçları çeker."""
        payload_file = os.path.join(self.base_dir, "telegram_payload.txt")
        matches = []
        if os.path.exists(payload_file):
            try:
                with open(payload_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Temel maçları ayıkla
                if "Farul Constanta - Rapid Bükreş" in content:
                    matches.append({"home": "Farul Constanta", "away": "Rapid Bükreş", "tag": "⭐ Günün Altın Maçı", "target": "2.5 Üst"})
                if "Ciudad de Lucena - CD Badajoz" in content:
                    matches.append({"home": "Ciudad de Lucena", "away": "CD Badajoz", "tag": "📈 Kasa Katlama 2. Basamak", "target": "2.5 Üst"})
                if "Cercle Brugge" in content:
                    matches.append({"home": "La Louviere", "away": "Cercle Brugge", "tag": "📈 Kasa Katlama 3. Basamak", "target": "2.5 Üst"})
            except Exception:
                pass
        
        # Eğer özel maç bulunamadıysa örnek fallback
        if not matches:
            matches = [
                {"home": "Farul Constanta", "away": "Rapid Bükreş", "tag": "⭐ Günün Altın Maçı", "target": "2.5 Üst"},
                {"home": "Ciudad de Lucena", "away": "CD Badajoz", "tag": "📈 Kasa Katlama 2. Basamak", "target": "2.5 Üst"}
            ]
        return matches

    def handle_status_inquiry(self):
        """Verilen maçların anlık skor, tamamlanma ve KGA başarı durumunu hazırlar."""
        # Veritabanını taze yükle
        self.feedback_engine = KGAFeedbackEngine()
        db_matches = self.feedback_engine.data.get("matches", [])
        
        matches = self.get_todays_matches()
        live_events = self.score_service.fetch_all_live_events()
        
        now_str = datetime.now().strftime("%H:%M")
        lines = [
            f"📊 <b>KGA 2.0 CANLI MAÇ RADARI ({now_str})</b>",
            "━━━━━━━━━━━━━━━━━━━━"
        ]

        def normalize(t):
            nfkd = unicodedata.normalize('NFKD', str(t).lower())
            ascii_text = ''.join([c for c in nfkd if not unicodedata.combining(c)])
            return re.sub(r'[^a-z0-9]', '', ascii_text)

        for m in matches:
            h_norm = normalize(m["home"])
            a_norm = normalize(m["away"])

            # 1. Önce Sonuçlanmış Maçlar Veritabanında Ara
            db_found = None
            for db_m in db_matches:
                db_h = normalize(db_m.get("home", ""))
                db_a = normalize(db_m.get("away", ""))
                if (h_norm in db_h or db_h in h_norm) and (a_norm in db_a or db_a in a_norm):
                    db_found = db_m
                    break

            lines.append(f"{m['tag']}:")
            lines.append(f"🏟️ <b>{m['home']} - {m['away']}</b>")

            if db_found:
                # Maç tamamlanmış ve skoru arşivde mevcut
                score = db_found.get("score", "-")
                tot = db_found.get("total_goals", 0)
                u_won = db_found.get("ust25_won", False)
                k_won = db_found.get("kgvar_won", False)
                u_odds = db_found.get("ust25_odds", m.get("target", ""))

                lines.append(f"🏁 <b>Bitti (MS):</b> <b>{score}</b> (Toplam {tot} Gol)")
                if u_won:
                    lines.append(f"🎉 <b>✅ 2.5 ÜST KAZANDI!</b> (Oran: {u_odds})")
                else:
                    lines.append(f"❌ <b>2.5 Üst Gelmedi:</b> ({tot} golde kaldı)")
                
                if k_won:
                    lines.append(f"🤝 <b>🔒 KG VAR GELDİ:</b> (1-1 İkiz Kilit Doğrulandı)")
                else:
                    lines.append(f"❌ <b>KG Var Gelmedi</b>")

            else:
                # 2. Canlı Skor Servisinde Ara
                found = self.score_service.search_match_score(m["home"], m["away"], events=live_events)
                if found:
                    h_score = found["home_score"]
                    a_score = found["away_score"]
                    tot = found["total_goals"]
                    detail = found["detail"] or found["clock"] or found["status"]

                    lines.append(f"⚡ <b>Canlı Skor:</b> <b>{h_score} - {a_score}</b> ({detail})")
                    
                    if tot >= 3:
                        lines.append("🎉 <b>✅ 2.5 ÜST KAZANDI!</b> (Hedef Başarıldı)")
                    elif h_score >= 1 and a_score >= 1:
                        lines.append("🔒 <b>⏳ 1-1 İKİZ KİLİDİ AKTİF!</b> (2.5 Üst için son 1 gol bekleniyor)")
                    elif found.get("completed"):
                        lines.append(f"🏁 <b>Maç Sonu:</b> Toplam {tot} gol.")
                    else:
                        lines.append(f"⚽ <b>Maç Devam Ediyor:</b> ({detail})")
                else:
                    # Ne canlıda ne veritabanında bulunamadıysa (henüz oynanmamış veya bülten saati bekleniyor)
                    lines.append("⏳ <i>Maç saati bekleniyor veya canlı skor akışı taranıyor.</i>")
            
            lines.append("────────────────────")

        lines.append("💡 <i>Anlık skorları tazelemek için istediğiniz zaman tekrar 'durum' yazabilirsiniz.</i>")
        return "\n".join(lines)

    def handle_bulletin_inquiry(self):
        payload_file = os.path.join(self.base_dir, "telegram_payload.txt")
        if os.path.exists(payload_file):
            with open(payload_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "Bugüne ait kayıtlı bülten bulunamadı."

    def handle_ai_chat(self, user_text):
        """Genel soruları Gemini AI ile yanıtlar."""
        if not GEMINI_API_KEY:
            return "🤖 Merhaba! Ben KGA 2.0 Asistanınızım.\n\nKullanabileceğiniz komutlar:\n• <b>durum</b>: Bugünün maçlarının canlı skoru\n• <b>bülten</b>: Günün KGA analizi ve kuponları\n• <b>kara liste</b>: Denetim altındaki kısır ligler"
        
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""Sen Kinetik Gol Algoritması 2.0 (KGA) Telegram Asistanısın.
Kullanıcı sana Telegram'dan şu mesajı yazdı:
"{user_text}"

KGA 2.0 Mantığı:
- 2.5 Üst (1.70 - 1.95) ve KG Var (1.40 - 1.62) İkiz Kilit standardı.
- Burnley tipi 1-0'a yatan takımlar ve kışın donan ligler kara listededir.
- Kasa Katlama (Rolling Bet) saatleri kesinlikle çakışmaz.
- Skor kuponunda 2-1, 1-2, 3-1, 2-2 hedeflenir.

Kullanıcıya net, samimi, profesyonel ve kısa bir yanıt ver. Yalnızca Telegram HTML etiketleri (<b>, <i>, <code>) kullan."""
            
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if resp and resp.text:
                return resp.text
        except Exception as e:
            pass
        return "Sorunuzu aldım! Anlık canlı skorlar için <b>durum</b>, bugünün maçları için <b>bülten</b> yazabilirsiniz."

    def process_message(self, text, chat_id):
        clean = text.strip().lower()

        # 1. Canlı Skor / Durum Sorgusu
        if any(w in clean for w in ["durum", "canlı", "skor", "ne durumda", "kaç kaç", "sonuç"]):
            reply = self.handle_status_inquiry()
        # 2. Bülten / Kupon Sorgusu
        elif any(w in clean for w in ["bülten", "kupon", "maçlar", "tahmin", "öneri"]):
            reply = self.handle_bulletin_inquiry()
        # 3. Kara Liste Sorgusu
        elif "kara liste" in clean or "ligler" in clean:
            reply = self.feedback_engine.get_blacklist_and_tier_summary()
        # 4. Başlangıç / Yardım
        elif clean in ["/start", "merhaba", "selam", "yardım", "help"]:
            reply = (
                "👋 <b>Merhaba! KGA 2.0 Canlı Asistanınız Hazır.</b>\n\n"
                "Bana istediğiniz zaman şunları sorabilirsiniz:\n"
                "• <b>Durum</b>: <i>'Verdiğin maçlar ne durumda?'</i> (Anlık canlı skor & dakika)\n"
                "• <b>Bülten</b>: Günün Altın Maçı, Kasa Katlama ve Skor Kuponu\n"
                "• <b>Kara Liste</b>: Güncel denetimdeki kısır ligler\n"
                "• Veya aklınıza takılan herhangi bir takımı/soruyu doğrudan yazabilirsiniz!"
            )
        # 5. Diğer Yapay Zeka Yanıtları
        else:
            reply = self.handle_ai_chat(text)

        self.send_message(chat_id, reply)

    def start_polling(self, once=False):
        print(f"[*] KGA 2.0 İnteraktif Telegram Dinleyicisi Başlatıldı. Hedef Chat ID: {AUTHORIZED_CHAT_ID}")
        
        # Bulut sunucuları (Render/Koyeb vb.) için HTTP Health Check servisi
        port_env = os.getenv("PORT")
        if port_env:
            try:
                p = int(port_env)
                t = threading.Thread(target=run_health_server, args=(p,), daemon=True)
                t.start()
                print(f"[*] Bulut HTTP port {p} üzerinde dinleniyor (Healthcheck aktif).")
            except Exception as e:
                print(f"[!] Port başlatma uyarısı: {e}")
        
        while True:
            updates = self.get_updates()
            for u in updates:
                self.last_update_id = u.get("update_id", self.last_update_id)
                msg = u.get("message", {})
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                text = msg.get("text", "")

                if chat_id == AUTHORIZED_CHAT_ID and text:
                    print(f"[+] Yeni Kullanıcı Mesajı: '{text}' (Chat ID: {chat_id})")
                    self.process_message(text, chat_id)

            if once:
                break
            time.sleep(1)

if __name__ == "__main__":
    bot = KGAInteractiveBot()
    # Tek seferlik veya döngüsel başlatma
    bot.start_polling()
