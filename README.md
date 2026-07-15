# Yerel PDF → Markdown

PDF dosyalarını `pymupdf4llm` kullanarak tamamen yerel biçimde Markdown'a çeviren Windows uygulaması. Dosyalar hiçbir web servisine gönderilmez.

## Çalıştırma

1. Bilgisayarda Python 3.10 veya daha yenisi kurulu olmalı.
2. `run.bat` dosyasına çift tıklayın.
3. İlk çalıştırmada gerekli paketler `.venv` klasörüne kurulur; sonraki açılışlar doğrudan uygulamayı başlatır.
4. PDF'leri pencereye sürükleyip **Markdown'a Dönüştür** düğmesine basın.

Varsayılan olarak:

- OCR gerektiğinde otomatik çalışır.
- OCR dili `tur+eng` olur.
- Üstbilgi ve altbilgiler çıktıya eklenmez.
- `.md` dosyası PDF'nin bulunduğu klasöre yazılır.
- Var olan bir Markdown dosyasının üzerine yazılmaz; yeni çıktıya `_2`, `_3` gibi bir ek eklenir.

## OCR notu

Metin tabanlı PDF'lerde OCR gerekmez. Taranmış PDF'lerde PyMuPDF4LLM'in OCR altyapısı kullanılır. Türkçe OCR çalışmazsa sistemde Tesseract ve Türkçe dil verisinin (`tur`) kurulması gerekebilir. OCR kullanmayacaksan ayarlardan **OCR kullanma** seçeneğini seçebilirsin.

## EXE oluşturma

`build.bat` dosyasına çift tıklayın. Paketleme tamamlandığında uygulama şu klasörde oluşur:

```text
dist\PDF-to-Markdown\PDF-to-Markdown.exe
```

Hızlı açılması için tek dosyalık paket yerine klasör tabanlı paketleme kullanılmıştır. `dist\PDF-to-Markdown` klasörünü bütün olarak taşıyın.

## Gizlilik

Uygulama kodunda ağ isteği veya bir yapay zekâ API'si yoktur. Paketlerin ilk kurulumunda yalnızca Python paketleri internetten indirilir; PDF dönüştürme işlemi yereldir.
