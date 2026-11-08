# KGA 2.0 & 100X KASA YÖNETİMİ - SOHBET VE PROJE KAYDI
> **Tarih:** 8 Kasım 2026  
> **Depo:** https://github.com/istanbulhighlights34-star/iddaa  
> **Konum:** `/Users/cuneytelgin/Desktop/adsız klasör/kga_system`  

---

## 1. HEDEF VE STRATEJİ
* **Sermaye Büyütme Hedefi:** 1.000 TL başlangıç kasası ile başlayıp parçalı kuponlarla **100.000 TL ve üzerine** (tavansız bileşik büyüme) ulaşmak.
* **Model:** 30 günde 10–12 temiz basamak (1.60x ortalama bileşik getiri).
* **Günlük Kasa Dağılımı (Kuruşu Kuruşuna):**
  * 🔹 **Kupon 1 (Ana Taşıyıcı %50):** 500 TL (Hedef Oran: 1.65 – 1.80)
  * 🔹 **Kupon 2 (Kademeli %30):** 300 TL (Saat Çakışmasız Akşam Maçı)
  * 🔹 **Kupon 3 (Güvenlik Zırhı %20):** 200 TL (Sistem / Skor Koruması)

---

## 2. KGA 2.0 ALGORİTMA KURALLARI
* **İkiz Oran Kilidi:** 2.5 Üst (1.70 – 1.95) iken KG Var (1.40 – 1.62) kuralı.
* **1-1 Skora Yatma Tuzağı Koruması:** Romanya, İspanya alt ligleri gibi 1-1'den sonra kapanan liglerde düz 2.5 Üst yasaklandı; KG Var önceliği verildi.
* **Düz 2.5 Üst İzni:** Sadece 1-1'den sonra durmayan saf hücum liglerine (Almanya 1-2, Hollanda 1-2, İsviçre, Belçika) tahsis edildi.
* **Mevsimsel Kış Karartması:** Kasım-Şubat arası zemin kısırlığı olan Polonya Ekstraklasa, Rusya ve Romanya alt ligleri otomatik elenir.
* **Tam Otonom Kalibrasyon Yetkisi:** Sistem kullanıcı onayı beklemeksizin maç skorlarına göre ligleri kara listeye alır, terfi ettirir veya KG Var korumasına çeker.

---

## 3. KURULAN 7/24 BULUT ALTYAPISI
1. **GitHub Actions (`.github/workflows/kga_daily.yml`):**
   * Her sabah saat 09:00'da (TSİ) bilgisayar kapalıyken bile çalışır.
   * Günlük bülteni çeker, 2.785+ maçlık kümülatif geçmiş arşivle çapraz analiz yapar.
   * Günün kuponlarını TL tutarlarıyla üretir, Telegram'a gönderir ve hafızayı depoya geri kaydeder.
2. **Render.com Web Service (`kga_interactive_bot.py`):**
   * Bilgisayar kapalıyken 7/24 Telegram dinleyicisidir.
   * Kullanıcı Telegram'dan:
     * `kasa`: Anlık bakiye, kâr ve günün TL yatırım emirleri.
     * `durum`: Canlı veya biten maçların skorları ve kupon neticeleri.
     * `bülten`: Günün analiz raporu.

---

## 4. TELEGRAM BİLGİLERİ
* **Bot:** `@ElgAnaliz_2026_bot`
* **Token:** `9082147299:AAEQubL7YIyr4NPS_MAoT02xixUjQ_RtiD0`
* **Yetkili Chat ID:** `664321983`

### [8 Kasım 2026 Pazar 12:10 TSİ] Kritik Takvim ve Bülten Düzeltmesi (Pazar Maçları Ayrıştırması)
- **Sorun:** 6-9 Kasım ortak bülteni tek bir PDF'te (1-3. sayfalar Cuma, 4-7. sayfalar Cumartesi, 8-10. sayfalar Pazar) yer aldığı ve kod sayfa başlığındaki gün filtresini denetlemediği için ilk sayfalardaki geçmiş Cuma/Cumartesi maçları (Farul, Lucena) bültene girmişti.
- **Kökten Çözüm:**
  1.  içine sayfa başlığı gün denetçisi () eklendi. Yalnızca 8 Kasım Pazar gününe ait maçlar (20 aday) çekildi.
  2. Eski güne ait statik yedek metin mekanizması tamamen kaldırıldı; yerine bugünün gerçek Pazar maçlarından anlık dinamik rapor üreten  kuruldu.
  3. Günün Altın Maçı olarak Fransa Ligue 1 **Brest - Lyon (19:15)**, Kasa Katlama zinciri olarak saatleri çakışmayan **Estoril - Maritimo (18:30)**, **CE Manresa - Barcelona B (20:00)** ve **SD Aucas - Independiente del Valle (21:45)** seçildi.
  4. Telegram bülteni anında @ElgAnaliz_2026_bot kanalına iletildi.
  5. Tüm düzeltmeler GitHub  dalına commit edilip pushlandı.
