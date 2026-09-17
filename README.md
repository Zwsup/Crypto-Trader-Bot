# Crypto Breakout & Momentum Scanner Bot

Yüksek frekanslı (scalping) kripto para piyasaları için geliştirilmiş, kurumsal düzeyde risk filtreleri ve gerçek zamanlı CustomTkinter GUI arayüzü içeren masaüstü ticaret botu.

Sistem, Binance genel API'si üzerinden 1 dakikalık zaman diliminde 20 volatil kripto varlığı tarar; sahte kırılımları (fakeout) elemek için Göreceli Hacim (RVOL), Hareketli Ortalama (SMA) ve Bitcoin pazar korelasyonu filtrelerini kullanır.

---

## Temel Özellikler

* **Çoklu Varlık Taraması:** 20 volatil kripto çifti (BTC, ETH, SOL, PEPE, WIF, DOGE vb.) üzerinde 2-3 saniyelik aralıklarla asenkron veri analizi.
* **Göreceli Hacim (RVOL) Filtresi:** Fiyat artışının son mumların ortalama hacmine kıyasla doğrulanması (Hacimsiz ani sıçramalara karşı koruma).
* **SMA Trend Analizi:** Fiyatın kısa vadeli hareketli ortalama üzerinde olup olmadığını kontrol ederek düşüş trendindeki sahte yükselişleri engelleme.
* **BTC Güvenlik Kalkanı:** Bitcoin ani düşüş trendindeyse altcoin alımlarını otomatik dondurma.
* **Dinamik & Kademeli İzüren Stop (Trailing Stop):** Kâr arttıkça stop mesafesini daraltarak maksimum kârı koruyan akıllı çıkış mekanizması.
* **Ceza & Soğuma Süresi (Cooldown):** Stop patlatan veya kapanan pozisyonun hemen ardından aynı paritede intikam işlemi açılmasını engelleyen zaman kilidi.
* **Thread-Safe Modern GUI:** `customtkinter` tabanlı, donma veya çökme yapmayan, canlı piyasa radarı ve açık pozisyon kartları sunan karanlık mod arayüzü.
* **Kalıcı İşlem Günlüğü (Audit Logger):** Kapanan tüm işlemleri, giriş/çıkış fiyatlarını, kâr/zarar yüzdelerini ve komisyonları `trades_history.csv` dosyasına otomatik kaydetme.

---

## Mimari & Dosya Yapısı

* **`config.json`:** Taranacak semboller, tetikleyici yüzdeler, stop limitleri ve zaman aşımı süreleri gibi operasyonel parametrelerin yönetimi.
* **`strategy.py`:** Pozisyon takibi, dinamik izüren stop ve cooldown mantığını barındıran strateji motoru.
* **`scanner.py`:** `ccxt` kütüphanesi ile borsa bağlantısı, piyasa taraması, RVOL/SMA hesaplamaları ve CSV raporlama çekirdeği.
* **`main.py`:** Çoklu iş parçacığı (multithreading) ile arka plan motorunu çalıştıran CustomTkinter masaüstü arayüzü.

---

## Kurulum

1. **Depoyu Klonlayın:**
   ```bash
   git clone https://github.com/Zwsup/Crypto-Trader-Bot.git
   cd Crypto-Trader-Bot


Gerekli Kütüphaneleri Yükleyin:
pip install ccxt customtkinter

Uygulamayı Başlatın:
python main.py


---

## ⚖️ Yasal Uyarı ve Sorumluluk Reddi (Legal Disclaimer)

Bu yazılım **yalnızca eğitim, araştırma ve deneysel amaçlarla** geliştirilmiş bir **simülasyon (Paper Trading) aracıdır**. 

* **Yatırım Tavsiyesi Değildir:** Bu depoda yer alan hiçbir kod, algoritma, strateji veya varsayılan parametre finansal, yasal veya yatırım tavsiyesi niteliği taşımaz.
* **Finansal Risk:** Kripto para ve finansal türev piyasaları yüksek derecede sermaye kaybı riski içerir. Geçmiş piyasa hareketleri veya simülasyon sonuçları, gelecekteki performansı garanti etmez.
* **Sorumluluk Reddi:** Yazılım "olduğu gibi" (AS IS) sağlanmaktadır. Geliştirici(ler); bu yazılımın kullanımından, çalışmasından, üçüncü taraf kütüphanelerin (API, ağ bağlantısı vb.) aksamasından veya kullanıcıların bu kodu kısmen/tamamen gerçek sermaye ile canlı piyasalara entegre etmesinden doğabilecek hiçbir doğrudan, dolaylı veya maddi/manevi zarardan sorumlu tutulamaz.
* **Kullanıcı İnisiyatifi:** Yazılımı çalıştıran veya üzerinde değişiklik yapan her kullanıcı, tüm riskin ve yasal yükümlülüğün tamamen kendisine ait olduğunu kabul eder.
