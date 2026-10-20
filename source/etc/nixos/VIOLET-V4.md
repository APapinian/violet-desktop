# Fatih · Violet Modern v4

Bu paket `qtile-son-durum.tar.gz` içindeki güncel NixOS yapılandırması üzerine hazırlandı. Önceki modern ZIP’te eksik kalan 14 dosyayı, servisleri ve masaüstü bağlantılarını geri getirir; Alt+Tab, üstbar, günlük panel, plaklı müzik paneli, şimdi çalıyor kartı ve açılış temasını yeniler.

## Kurulum

İndirdiğin betiğin bulunduğu dizinde:

```bash
bash violet-modern-v4-kur.sh
```

Betik gerektiğinde sudo ister. Önce arşive bağlı dosya kontrollerini yapar, `/var/backups/violet-modern-v4-*` altında değişecek dosyaları ve önceki sistem neslinin yolunu yedekler; kaynakları kurar, kilitli girdilerle Nix değerlendirmesi ve derlemesini çalıştırır, yalnızca başarıyla çıkan sistem neslini etkinleştirir. Arşivden sonra ilgili dosyalar değiştiyse durur. Nix girdilerini güncellemez. Git deposundaki yeni dosyaların dışarıda kalmaması için `path:/etc/nixos` kullanır.

Derleme günlüğü yedek dizinindeki `build.log` dosyasına yazılır. İlk derleme Qtile’nin dört yerel yaması ve uygulama bağımlılıkları nedeniyle uzun sürebilir. Derleme veya etkinleştirme hatasında kaynakları geri yüklemeyi dener; sonradan değiştirilmiş dosyayı koruyup yedek yolunu bildirir.

**Kurulumdan sonra oturumu kapatıp yeniden aç.** Yeni kalem ve Alt+Tab yerel yamaları ancak yeni Qtile sürecinde çalışır. Quickshell ve kullanıcı servisleri de yeni oturumla yüklenir. Mevcut masaüstü oturumu betik tarafından kapatılmaz.

Salt okunur dosya uyumluluğu kontrolü:

```bash
bash violet-modern-v4-kur.sh --check
```

Kaynakları kurup derlemek, sistemi henüz etkinleştirmemek:

```bash
bash violet-modern-v4-kur.sh --build
```

Bu modda kaynaklar yeni sürümde kalır. Etkinleştirmek için betiği seçeneksiz tekrar çalıştır. İlk çalıştırmanın yedeği özgün kaynakları içerir; sonraki çalışma zaten kurulu dosyaları tekrar yedeklemez.

Geri almak için betiğin sonunda yazdırdığı **gerçek yedek yolunu** kullan:

```bash
bash violet-modern-v4-kur.sh --rollback /var/backups/violet-modern-v4-TARIH-SAAT-PID
```

Bu işlem kaynakları ve yedekte belirtilen önceki Nix neslini geri getirir. Önceki nesil sonradan garbage collection ile silinmişse kaynaklar geri yüklenir, sistem etkinleştirmesi durur. `--build` ile denediğinde ilk yedek dizinini sakla. Kaynak veya sistem profili başka bir kurulum tarafından değişirse betik durabilir; eşzamanlı NixOS kurulumları yapma.

## Güncel değişiklikler

- **Alt+Tab:** son kullanılan pencere sırası; açık gruplar arasında geçiş; Alt bırakılınca seçim tamamlanır. Alt+Shift+Tab ters yöndedir. Qtile’nin kendi açılır penceresi kullanılır. Önceki çalışan Qtile’de yerel işlev henüz yoksa bir saniyelik sonlandırma kullanılır.
- **Violet üstbar:** ince mor çerçeve, ortada çalışma alanları, düzenlenebilir panel sırası, Buds şarjı ve medya erişimi. 1024 ve 1600 piksel genişlikte önizlendi.
- **Günlük panel:** takvim, saat, hava, CPU/bellek/disk halkaları ve müzik kartı. Hava için şehir seçimi gerekir.
- **Plaklı oynatıcı:** MPRIS oynatıcı seçimi, gerçek albüm kapağı, dönen plak, animasyonlu kol, süre ve kontroller. Yerel dosya ve YouTube araması mevcut müzik servisi üzerinden çalışır. Sıra yalnızca mpv’nin paylaştığı veridir; bütün uygulamaların sıraya erişimi yoktur. Bazı MPRIS oynatıcıları arama/karıştırma/tekrar komutlarını desteklemeyebilir. Küçük ekranda panel kaydırılır.
- **Şimdi çalıyor:** normal döşenen pencere yerine Quickshell üst katman kartı; odak almaz. Kontroller etkin oynatıcıya gider.
- **Nautilus/Sushi:** dosya yöneticisi varsayılanı ve kısayollar Nautilus; seçili dosyayı boşluk ile hızlı önizleme. Kurtarma Plasma masaüstünün bağımlılıkları korunur.
- **Flatpak/AppImage:** Flatpak servisi, Flatseal, AppImage çalışma desteği ve uygulama paneli. Kurulum sonunda kullanıcıya ait Flathub kaynağı eklenir; mevcut kaynak üzerine yazılmaz. Flatseal, NixOS kurulumu başarılı olduktan sonra kullanıcı hesabına Flathub üzerinden kurulur; diğer uygulamalar kendiliğinden indirilmez.
- **Galaxy Buds 3 Pro:** Bluetooth/PipeWire ve GalaxyBudsClient bağlantısı, cihazın bildirdiği sol/sağ/kutu şarjı. Bilinmeyen değer `—`; sıfır yüzde geçerli değerdir. BlueZ yalnızca genel şarjı paylaşırsa genel değer kullanılabilir. Kutu kapalıyken güncel kutu verisi gelmeyebilir. Eşleştirme ve kulaklığın takılması cihaz üzerinde yapılmalı.
- **MyBrain Python:** tek örnek, şifreli taşınabilir kasa, uygulama menüsü, açık kasada palet araması, hızlı not, OCR ve dosya ekleme. Kilitlenince arama sonuçları temizlenir. Gönderdiğin arşivde Rust kaynakları bulunmadığı için yeni Rust sürümüne karşı çapraz doğrulama yapılamadı. Mevcut Python taşınabilir kasa biçimi korunur; aynı kasayı Rust ve Python’dan eşzamanlı düzenleme. Kasa anahtarı veya kullanıcı verisi bu pakette yoktur.
- **GRUB:** daha sakin Hyrule arka planı, mat seçim paneli, okunaklı başlık ve yerel halka geri sayımı. Bu bir video oynatımı değildir. Tam hareketli ışık halkaları **Plymouth** açılışında yer alır. Mevcut EFI, bölüm UUID’leri, Btrfs düzeni ve açılış girdileri temel alınır.
- **Plymouth:** 48 karelik dönen halkalar, yumuşak ışık ve ilerleme çizgisi; parola ve soru istemleri korunur. GIF aynı karelerden üretilmiş görsel önizlemedir; gerçek açılış süresi donanıma bağlıdır.

## Geri gelen masaüstü araçları

| Alan | Araçlar |
|---|---|
| Pencere ve çalışma alanı | Genel görünüm, Hukuk/Kod/Okuma oturumları, yerleşim şablonları, taşıma ve yerleşimi geri alma |
| Dosyalar | İndirilenler kuralları ve toplu adlandırma, hızlı bakış, sürükle-bırak işlem alanı, belge geçmişi, depolama incelemesi |
| Ekran | Türkçe/İngilizce OCR, ekran kaydı ve açıkken tekrar tamponu, büyüteç, renk seçici, ekran görüntüsüne çizim |
| Telefon ve USB | KDE Connect, USB takılınca işlem, MyBrain kilitleme ve güvenli çıkarma, fotoğraf içe aktarma |
| Masaüstü | Komut paleti, bildirim geçmişi ve susturma, metin şablonları, geçici uyanık tutma, sunum, kalem halkası, monitör profilleri |
| Yönetim | Uygulama ve ses yönetimi, kısayollar/panel sırası/dock, Syncthing durumu, süreçler ve bağlantılar, tanı raporu, olay kuralları |

Ekran çizimi yakalanmış görüntünün üstünde açıklama düzenler; bütün uygulamaların üstünde sürekli canlı mürekkep değildir. Dosya otomasyonları ve geçmiş klasörleri ayarlardan seçilir; varsayılan İndirilenler otomasyonu kapalıdır. Kayıt tamponu açılmadan önceki görüntüyü geri getiremez. Syncthing cihaz/klasör eşleştirmesi ve KDE Connect telefon eşleştirmesi ayrıca yapılır.

## Kısayollar

`Super` Windows tuşudur. Eski kullanıcı kısayollarıyla çakışan ek kısayollar atlanır; mevcut kısayolları rehberden kontrol et.

| Kısayol | İşlem |
|---|---|
| Alt+Tab / Alt+Shift+Tab | Pencereler arasında ileri/geri |
| Super+Alt+Space | Masaüstü merkezi |
| Super+Alt+/ | Birleşik komut paleti |
| Super+Alt+W | Pencere genel görünümü |
| Super+Alt+Z | Yerleşimi geri al |
| Super+Alt+M | Plaklı oynatıcı |
| Super+Alt+O | Şimdi çalıyor kartı |
| Super+Alt+D | Günlük panel |
| Super+Alt+B | Buds paneli |
| Super+Alt+N | MyBrain |
| Super+Alt+E | Nautilus |
| Super+Alt+R | Kalem halka menüsü |
| Super+Alt+X | OCR |
| Super+Alt+V | Kayıt paneli |

Kalem düğmesi varsayılan kapalıdır; Masaüstü ayarlarında 331/332 düğmesini seç. Uygulamaların mevcut kalem işlemlerini istemeden değiştirmemek için halka menüsü opt-in tutulur. Eski dokunma ve yerel kalem yamaları korunmuştur.

## Doğrulama sınırı

Bu çalışma ortamında Nix ve gerçek Wayland/Qtile oturumu yoktur. NixOS değerlendirmesi, derleme, Bluetooth eşleştirme, gerçek ses ve boot testi hedef bilgisayarda yapılmalıdır. Betik sistem etkinleştirmesini derleme başarısına bağlar; derleme geçmesi donanım testi yerine geçmez.

Burada geçen kontroller: 42 Python dosyasında derleme, 30 Nix dosyasında sözdizimi, QML günlük/üstbar/medya bileşenlerinin Qt 6 ile önizlenmesi, Qtile 0.37.1 kaynağına dört yamanın sıfır fuzz ile uygulanması, MRU/ters geçiş/pencere kapanması, MyBrain şifreleme/yanlış parola/çakışma/yedek/şifreli ek, IPC işlem işleyicisinde not-arama-kilit, dosya taşıma çakışması/geri alma, geçmişi ayrı dosyaya geri yükleme ve kurulumun dosya koruma/geri alma testleri. Yerel ortam Unix socket açılmasına izin vermediğinden gerçek socket aktarımı burada sınanamadı. Önizlemelerde örnek sistem/medya verisi kullanılır; senin canlı verilerin değildir. GRUB görüntüsü yerleşim taslağıdır, boot ekranından alınmış fotoğraf değildir.

Kaynaklar: [Qtile 0.37.1](https://github.com/qtile/qtile/tree/v0.37.1), [GNU GRUB temaları](https://www.gnu.org/software/grub/manual/grub/html_node/Theme-file-format.html), [GalaxyBudsClient](https://github.com/timschneeb/GalaxyBudsClient), [KDE Connect](https://userbase.kde.org/KDEConnect/en), [Sushi](https://github.com/GNOME/sushi).

## v4 Flatseal düzeltmesi

Kilitli Nixpkgs girdisinde `flatseal` paketi olmadığı için v4 kurulumunun değerlendirmesi duruyordu. Nix araç listesinde yerel bir Flatseal başlatıcısı kullanılır; uygulama, başarılı sistem kurulumundan sonra Flathub’dan kullanıcı hesabına eklenir. İlk hatada betik kaynakları geri yüklediyse yeniden kurulum için eski yedeği ayrıca geri alman gerekmez.
