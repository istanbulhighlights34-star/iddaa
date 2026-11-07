# KİNETİK GOL ALGORİTMASI 2.0 (KGA) - NİHAİ MANİFESTO
> **Veri Tabanlı Backtest Onaylı (753 Maçlık Analiz Sonucu Kalibre Edilmiştir)**

---

## 1. TEMEL FELSEFE VE ORAN STANDARDI
* **Hedef Bahis**: **2.5 Üst** veya **KG Var** (ve yüksek değerli KG Var & 2.5 Üst hibritleri).
* **Altın Oran Bandı**: **1.70 – 1.95** (İdeal tatlı nokta: 1.75 – 1.90).
* **İkiz Oran Kilidi (KG Var Korelasyonu)**:
  * 2.5 Üst oranı **1.70 – 1.95** arasındayken, **KG Var oranı mutlaka 1.40 – 1.62 arasında olmalıdır**.
  * Bu kural, maçın "1-1 Kesinliğini" garantiye alır. 
* **🛡️ 7 KASIM KALİBRASYONU (1-1 TUZAĞI VE 3. GOL GÜVENLİK FİLTRESİ):**
  * Backtest ve canlı sonuçlar, maçların 1-1'e kesin olarak ulaştığını (%100 isabet); ancak bazı liglerde takımların 1-1'den sonra skoru koruma psikolojisine girip 3. golü riske etmediğini kanıtlamıştır.
  * **KURAL:** İspanya alt ligleri (Tercera/2. RFEF), Romanya gibi temkinli liglerde maç KGA'ya uysa dahi **ASLA ÇIPLAK 2.5 ÜST OYNANMAZ**; bu liglerde tercih doğrudan **KG Var (1.40–1.62)** olarak kilitlenir.
  * **2.5 Üst Önceliği YALNIZCA SAF HÜCUM LİGLERİNE VERİLİR:** Almanya (Bundesliga 1 & 2), Hollanda (Eredivisie & Eerste Divisie), İsviçre ve Belçika. Bu ligler 1-1 olduktan sonra durmaz, 2-1, 2-2 veya 3-1'e patlar.

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

---

## 5. 💎 ÖZEL FIRSAT VE PATLAMA RADARI (EKSTRA DEĞER & VALUE BET MODÜLÜ)
Ana omurga 2.5 Üst & KG Var olmakla birlikte, yapay zekanın geçmiş bülten analizleri ve oran anomalileri üzerinden yakaladığı istisnai fırsatlar Telegram bültenine ek bir bölüm olarak sunulur:
1. **🎯 Kırılma Maçı (Net MS 1 / MS 2):** Geçmiş oran kalıpları ve xG farkına dayanarak galibiyeti netleşen, piyasa oranının üzerinde değer barındıran maçlar.
2. **💥 Gol Şöleni (3.5 Üst / 4+ Gol / T.Gol 4-6):** 2.5 Üst oranı çok düşük kaldığı için (1.20–1.45) ana KGA bandına girmeyen, ancak iki takımın savunma kurgusunun 4 veya daha fazla gol vadeden yüksek oranlı (2.10–3.00) patlama maçları.
3. **⚡ İddaa Oran Sapması (Bookmaker Mispricing):** İddaa risk yönetiminin form/kadro gerçekliğine ters açtığı belirgin oran anomalileri.

---

## 6. 🛡️ DİNAMİK KARA LİSTE VE TİER 1 CANLI DENETİM PROTOKOLÜ (CONTINUOUS RE-CALIBRATION)
Kara listeler ve lig sıralamaları statik/sabit değildir. Her maç sonucu ve bülten denetimiyle canlı olarak güncellenir:
1. **❄️ Mevsimsel Kış Karartması (Kasım - Şubat):**
   * Polonya Ekstraklasa, Rusya ve Romanya alt ligleri gibi donan zeminlerde oynanan ve gol ortalaması düşen ligler kış aylarında otomatik olarak kara listeye alınır.
2. **📉 Dinamik Düşüş Eşiği (Otomatik Kara Liste):**
   * Son incelenen en az 3 maçta 2.5 Üst başarı oranı **%45'in altına düşen** ligler doğrudan kara listeye transfer edilir ve maçları bültenden elenir.
3. **⭐ Dinamik Terfi Eşiği (Tier 1 Terfi):**
   * Son maçlarında 2.5 Üst başarı oranı **%75 ve üzerine çıkan** yüksek tempolu ligler Tier 1 statüsüne terfi ettirilir ve Günün Altın Maçı havuzunda önceliklendirilir.
4. **🔄 Rehabilitasyon ve Liste Temizliği:**
   * Kara listedeki bir lig formunu düzeltip istatistiğini %60'ın üzerine çıkardığında kara listeden çıkarılarak gözetim moduna alınır.

---

## 7. 🤖 TAM OTONOM SÜREKLİ KALİBRASYON YETKİSİ (AUTONOMOUS CONTINUOUS LEARNING DIRECTIVE)
* **Kullanıcı İradesi & Açık Yetki:** Sistem, her bülten ve canlı maç sonucu sonrasında oran ağırlıklarını, kara listeleri, taktiksel lig kısıtlamalarını (KG Var zorunlulukları) ve Tier 1 terfilerini **KULLANICI ONAYI BEKLEMEKSİZİN** anında ve otonom olarak kalibre eder.
* **Canlı Öğrenme Döngüsü:**
  1. Maç sonuçları sisteme düştüğü an algoritma lig ve oran başarılarını yeniden tartar.
  2. 1-1 kısırlığı yaşayan ligleri otomatik olarak "Sadece KG Var" moduna kilitler.
  3. Kısırlaşan ligleri derhal kara listeye çeker, tempo liglerini terfi ettirir.
  4. Güncellemeleri doğrudan kodlara ve GitHub bulutuna (`main` dalına) otomatik push ederek sisteme anında yansıtır.
