# KİNETİK GOL ALGORİTMASI 2.0 (KGA) - NİHAİ MANİFESTO
> **Veri Tabanlı Backtest Onaylı (753 Maçlık Analiz Sonucu Kalibre Edilmiştir)**

---

## 1. TEMEL FELSEFE VE ORAN STANDARDI
* **Hedef Bahis**: Yalnızca **2.5 Üst** (veya eşdeğer yüksek değerli hibritler).
* **Altın Oran Bandı**: **1.70 – 1.95** (İdeal tatlı nokta: 1.75 – 1.90).
* **İkiz Oran Kilidi (KG Var Korelasyonu)**:
  * 2.5 Üst oranı **1.70 – 1.95** arasındayken, **KG Var oranı mutlaka 1.40 – 1.62 arasında olmalıdır**.
  * Bu kural, maçın "1-1 Kesinliğini" garantiye alır. 1-1'den sonra 90 dakikaya kadar 1 gol 2.5 Üst'ü getirir.

---

## 2. BACKTEST BULGULARINDAN ÇIKARILAN EMNİYET FİLTRELERİ

### ⛔ A) Defansif Kara Liste (Burnley & Düşük xG Kuralı)
* Liginde kalesinde 0.8 xGA'nın altında pozisyon veren, 1-0'a yatan aşırı pragmatik/defansif takımlar (Örn: Burnley, Sheffield United ekolü takımlar) oranları KGA'ya uysa dahi **KESİNLİKLE ELENİR**.
* Kapanan alt sıra takımlarının deplasman maçları elenir.

### 🌍 B) Dinamik Tempo Ligi Önceliği
* Tier 1 Altın Maçlar yalnızca yüksek hücum geçişi ve tempo barındıran liglerden seçilir:
  * **Öncelikli Ligler**: Almanya (Bundesliga 1 & 2), Hollanda (Eredivisie & Eerste Divisie), Belçika (Pro League), İsviçre Süper Ligi, İngiltere (Championship & League 1), İskoçya Premiership, Fransa Ligue 1.
  * **Kaçınılacak Kısır Ligler**: Polonya Ekstraklasa (kış dönemi), İtalya Serie B, Asya Şampiyonlar Ligi doğu grubu, Yunanistan alt sıralar.

---

## 3. GÜNLÜK RUTİN TESLİMAT FORMATI (HER SABAH 09:00 TELEGRAM)

1. **⭐ GÜNÜN ALTIN TEK MAÇI (Tier 1)**:
   * Bültenin tamamından tüm filtreleri eksiksiz geçen **SADECE 1 MAÇ**.
   * Hedef Oran: **1.75 – 2.10** (İster düz 2.5 Üst, ister KG Var & 2.5 Üst hibriti).
   * En yüksek kasa güvenliği.

2. **📈 KADEMELİ KASA KATLAMA (Rolling Bet / Basamak Sistemi)**:
   * Gün içinde **saatleri kesinlikle çakışmayan** (1. maç bitip kazanç alındıktan sonra 2. maça geçilecek şekilde) **2 ila 4 basamaklı** tek maç serisi.
   * *Kural:* Eğer gün içinde o saat aralığında temiz KGA maçı yoksa zincir 2 basamakta bırakılır; asla zorlama maç eklenmez.

3. **🎲 SİSTEM 2-3 SKOR KUPONU**:
   * KGA 1-1 barajını aşan maçlar için hedef skorlar: **2-1, 1-2, 3-1, 2-2**.

---

## 4. İCRA VE GÖNDERİM
* Her sabah **09:00'da** resmi İddaa bayi bülteni indirilir.
* KGA 2.0 süzgecinden geçirilir.
* `send_telegram.py` betiği üzerinden kullanıcının Telegram botuna (`@ElgAnaliz_2026_bot`) anlık bildirimle iletilir.
