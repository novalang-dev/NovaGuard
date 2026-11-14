<div align="center">
  <h1>🛡️ NovaGuard Ultimate</h1>
  <p><b>Hafif, Hızlı ve Akıllı 4 Katmanlı Yerel Antivirüs</b></p>

  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
 ![Platform](https://img.shields.io/badge/Platform-Windows%208.1%20%7C%2010%20%7C%2011-lightgrey?logo=windows)
  ![License](https://img.shields.io/badge/License-MIT-green)
</div>

---

## 📖 NovaGuard Nedir?
**NovaGuard**, Python ile sıfırdan geliştirilmiş, düşük donanımlı (5GB RAM) Windows bilgisayarlar için özel olarak optimize edilmiş hibrit bir güvenlik yazılımıdır. Bulut bağımlılığı olmadan, tamamen yerel (offline) olarak çalışır ve bilgisayarınızı sıfır kasma ile korur.

## 🚀 Öne Çıkan Özellikler
- 🦠 **Katman 1 (İmza):** SHA-256 özetleri ile bilinen zararlıları milisaniyeler içinde yakalar.
- 🔍 **Katman 2 (Sezgisel):** Çift uzantılı dosyaları (`fatura.pdf.exe`) ve şüpheli kodları tespit eder.
- 👁️ **Katman 3 (Davranışsal):** Arka planda çalışan şüpheli süreçleri (`psutil`) canlı izler.
- 🔒 **Katman 4 (Karantina):** Tehditleri şifreleyerek çalıştırılamaz hale getirir.
- 🎯 **Risk Skoru:** Her dosyayı 0-100 arası puanlar, şüpheli dosyalarda Windows Defender tarzı uyarı verir.
- 🌐 **VirusTotal Entegrasyonu:** Dosyalara sağ tıklayarak anında hash sorgusu yapar.
- 🎮 **Oyun Modu:** Oyun oynarken FPS düşürmemek için arka plan taramalarını askıya alır.

## 📥 Kurulum
1. Sağ taraftaki **Releases** sekmesinden en son `NovaGuard.exe` dosyasını indirin.
2. Bilgisayarınızda `C:\` sürücüsüne girin ve yeni bir **`NovaGuard`** klasörü oluşturun.
3. İndirdiğiniz exe dosyasını bu klasörün (`C:\NovaGuard`) içine taşıyın.
4. `NovaGuard.exe` dosyasına **sağ tıklayıp "Yönetici olarak çalıştır"** deyin.

*(Program ilk çalıştığında kendini başlangıca ekleyecek ve sağ tık menüsüne VirusTotal özelliğini kuracaktır).*

## 🛠️ Geliştirici Kurulumu (Kaynak Koddan)
Eğer projeyi kendiniz derlemek isterseniz:
```bash
git clone https://github.com/novalang-dev/NovaGuard.git
cd NovaGuard
pip install -r requirements.txt
python run.py
