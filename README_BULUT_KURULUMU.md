# KGA 2.0 - 7/24 Bulut Otomasyon Sistemi

Bu sistem, **bilgisayarınız kapalı, uyku modunda veya çevrimdışı olsa dahi**, her sabah **09:00'da (TSİ)** KGA 2.0 analizini otomatik olarak çalıştırıp doğrudan Telegram botunuza fırlatmak üzere tasarlanmıştır.

---

## 🚀 Çalışma Mantığı
* **Altyapı:** GitHub Actions (Microsoft Cloud 7/24 Serverless).
* **Maliyet:** %100 Ücretsiz (Aylık 2.000 ücretsiz çalışma dakikası hakkından günde sadece 30 saniye harcar).
* **Tetikleyici:** Her sabah UTC 06:00 (Türkiye saatiyle **09:00**).
* **Hedef:** `@ElgAnaliz_2026_bot` üzerinden `664321983` Chat ID'sine doğrudan bildirim.

---

## 🛠️ 2 Dakikalık Kurulum Adımları

### 1. GitHub'da Yeni Bir Depo Açın
1. [github.com/new](https://github.com/new) adresine gidin.
2. Depo adını `kga-bot` (veya istediğiniz bir isim) yapın.
3. Gizlilik seçeneğini **Private** (Özel) seçin.
4. **Create repository** butonuna basın.

### 2. Bu Klasörü GitHub'a Gönderin
Bilgisayarınızın terminalini açıp şu komutları sırasıyla girin:

```bash
cd /Users/cuneytelgin/.gemini/antigravity/scratch/kga_system
git init
git add .
git commit -m "KGA 2.0 Bulut Otomasyonu Kurulumu"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADINIZ/kga-bot.git
git push -u origin main
```

*(Not: `KULLANICI_ADINIZ` yerine GitHub kullanıcı adınızı yazın).*

---

## 🎯 Test Etme (Manuel Çalıştırma)
Depoyu yükledikten sonra bilgisayarınızı hemen kapatabilirsiniz!
İstediğiniz zaman telefonunuzdan GitHub'a girip:
1. `kga-bot` deponuza gidin.
2. **Actions** sekmesine tıklayın.
3. Sol taraftan **KGA 2.0 Günlük Otomatik Analiz** iş akışını seçip **Run workflow** butonuna basın.
4. 15 saniye içinde Telegram botunuzdan mesajın anında geldiğini göreceksiniz.
