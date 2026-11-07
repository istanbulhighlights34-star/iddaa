#!/usr/bin/env python3
"""
KGA 2.0 - Canlı Maç Skoru & Durum Servisi
ESPN ve genel futbol API'leri üzerinden canlı maç skorunu, dakikasını ve durumunu çeker.
"""

import json
import urllib.request
import re

class LiveScoreService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_all_live_events(self):
        """Dünya genelindeki tüm canlı ve güncel maçları çeker."""
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/scorepanel"
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
                all_events = []
                for score_group in data.get("scores", []):
                    for ev in score_group.get("events", []):
                        all_events.append(self._parse_espn_event(ev))
                return all_events
        except Exception as e:
            print(f"[!] Canlı skor çekme hatası: {e}")
            return []

    def _parse_espn_event(self, ev):
        status_info = ev.get("status", {})
        status_type = status_info.get("type", {})
        description = status_type.get("description", "")
        detail = status_type.get("detail", "")
        clock = status_info.get("displayClock", "")
        completed = status_type.get("completed", False)

        comps = ev.get("competitions", [])
        home_team = "Ev Sahibi"
        away_team = "Deplasman"
        home_score = 0
        away_score = 0

        if comps:
            for c in comps[0].get("competitors", []):
                t_name = c.get("team", {}).get("displayName", c.get("team", {}).get("name", ""))
                score = c.get("score", "0")
                try:
                    score_int = int(score) if score is not None else 0
                except ValueError:
                    score_int = 0

                if c.get("homeAway") == "home":
                    home_team = t_name
                    home_score = score_int
                else:
                    away_team = t_name
                    away_score = score_int

        return {
            "name": ev.get("name", f"{home_team} vs {away_team}"),
            "home": home_team,
            "away": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "total_goals": home_score + away_score,
            "status": description,
            "detail": detail,
            "clock": clock,
            "completed": completed
        }

    def search_match_score(self, home_query, away_query, events=None):
        """Belirli iki takım arasındaki maçın skorunu ve dakikasını arar."""
        if events is None:
            events = self.fetch_all_live_events()

        def normalize(text):
            return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

        h_clean = normalize(home_query)
        a_clean = normalize(away_query)

        # 1. Tam veya yakın eşleşme
        for ev in events:
            ev_h = normalize(ev["home"])
            ev_a = normalize(ev["away"])

            if (h_clean in ev_h or ev_h in h_clean) and (a_clean in ev_a or ev_a in a_clean):
                return ev

        # 2. Tekil takım eşleşmesi (Deplasman veya Ev)
        for ev in events:
            ev_h = normalize(ev["home"])
            ev_a = normalize(ev["away"])
            if (h_clean in ev_h or a_clean in ev_a) and len(h_clean) >= 4:
                return ev

        return None

if __name__ == "__main__":
    service = LiveScoreService()
    events = service.fetch_all_live_events()
    print(f"Toplam canlı/tamamlanan maç sayısı: {len(events)}")
    if events:
        for ev in events[:5]:
            print(f"🏟️ {ev['home']} {ev['home_score']} - {ev['away_score']} {ev['away']} [{ev['detail']} | {ev['status']}]")
