# Violet V6.1 — Fatih / Lenovo Yoga 7

Kurulum: `bash ~/İndirilenler/violet-v6-kur.sh`

Script sudo ister, mevcut dosyaları yedekler ve ayrı dizinde derler. Derleme
başarılı olduktan sonra yapılandırmayı ve sistem neslini uygular. Flake kilidi
güncellenmez. Arşivden sonra değişen hedef dosyalarda durur; üzerine yazmaz.
İşlem sonunda yeniden başlat. Firefox temasını görmek için Firefox’u kapatıp aç.

## 21 isteğin karşılığı

| # | Eklenen / değiştirilen davranış |
|---|---|
| 1 | GRUB’da firmware çözünürlüğü, gfxterm ve video modülleri; ölçeklenen Violet menüsü ve kurtarma girdisi. |
| 2 | AMD sürücüsü initrd’de erken yüklenir; mevcut 48 kareli rün animasyonu Plymouth üzerinden çalışır. |
| 3 | Alt+Tab’da Quickshell pencere kartları; seçili pencere vurgusu, ters geçiş ve Alt bırakma algılaması. Kartlar pencere adlarını gösterir, ekran görüntüsü içermez. |
| 4 | Neovim Violet renkleri, rün çerçevesi, animasyonlu açılış, durum çubuğu ve dosya haritası. |
| 5 | Üst bara birleşen içbükey omuzlar, 32px köşeler ve yumuşak panel geçişleri; Buds paneli daha dar açılır. |
| 6 | MyBrain yerel çizilen başlık, daha rahat boşluklar, Violet kontrol yüzeyleri ve okunaklı tipografi. Kasa formatı aynı. |
| 7 | İlk yan tuş halka menü; ikinci tuş varsayılan silgi. Masaüstü ayarlarında ikinci tuş için seçenekler. |
| 8 | Temel işlemler için tek sahipli Super kısayolları; Türkçe klavyedeki slash yerine harf tuşu. |
| 9 | Bazaar Flathub’dan kullanıcı düzeyinde kurulur; kurulum sonundaki ağ sorunu için tekrar komutu var. |
| 10 | Komut paleti daha geniş arama alanı ve ayrılmış sonuçlar; Super+P. |
| 11 | Var olan Firefox profillerine eklenen Violet userChrome/userContent; diğer kullanıcı kuralları korunur. |
| 12 | Atlas’ta görünür ← ↑ ↓ → düğmeleri; dört yönde kart seçimi. |
| 13 | Sistem profilleri: hardware, boot, services, desktop. Home Manager profilleri: desktop, services. Göreli kaynak yolları korunur. |
| 14 | Krallığın akışı Super+K ile üst bara bağlı panelde açılır. |
| 15 | Sistem ayarları Super+I; kalem/kısayol ve AI/uzaktan kontrol bağlantıları. |
| 16 | Qtile içinde yatay kayan HyruleScroll ve klasik MonadTall arasında geçiş. Ctrl+Alt basılıyken Super’a bas veya Super+Ctrl+Space. Gerçek Niri/Hyprland oturumu kurulmaz; compositor değiştirmek açık pencereleri koruyamaz. |
| 17 | Anahtarlı SSH sunucusu ve ayrı Telegram yapılandırma arayüzü. Bot kimlikler girilip başlatılmadan çalışmaz. |
| 18 | Nautilus varsayılan dosya yöneticisi; GTK4/GTK3 Violet renkleri ve Papirus simgeleri. |
| 19 | Hareket eden, tıklanınca ifade değiştiren ASCII Link; etkin uygulamaya tepki ve kısa kara mizah cümleleri. Ayarlardan kapatılabilir. |
| 20 | GPT-5.6 Luna varsayılanlı ayrı AI GUI; kısa sohbet ve sınırlı yerel işlemler. |
| 21 | Kitty varsayılan terminal; kısa rün açılışı ve Link ASCII Fastfetch. |

## Kısayollar

Super = Windows / Meta tuşu.

| Tuş | İşlem |
|---|---|
| Super+Enter | Kitty |
| Super+D | Uygulama başlatıcı |
| Super+P | Komut paleti |
| Super+A | Kontrol merkezi |
| Super+N | Bildirim paneli |
| Super+I | Sistem ayarları |
| Super+K | Krallığın akışı |
| Super+M | MyBrain |
| Super+B | Firefox |
| Super+E | Nautilus |
| Super+R | Kalem halka menüsü |
| Super+W | Pencere atlası |
| Super+Shift+A | AI yardımcısı |
| Super+Shift+S | Telegram / SSH |
| Super+Shift+N | Neovim |
| Super+Shift+B | Bazaar |
| Super+Ctrl+Space | Yatay / klasik döşeme |
| Ctrl+Alt basılıyken Super | Yatay / klasik döşeme |
| Super+← ↑ ↓ → | Pencere odağı |
| Super+Shift+← ↑ ↓ → | Döşemedeki pencereyi taşı |
| Super+1…9 | Çalışma alanı |
| Super+Shift+1…9 | Pencereyi çalışma alanına gönder |
| Super+Q | Pencereyi kapat |
| Super+F | Tam ekran |
| Alt+Tab / Alt+Shift+Tab | Pencereler arasında geç |
| Super+F1 | Tüm yüklenmiş kısayolların rehberi |

Eski yardımcı araçların Super+Alt ve Super+Ctrl kısayolları da korunur.
Kalem/kısayol sayfası: Super+I → Kalem / kısayollar → Panel / hareket.
Kalem tuş kodları 331 ve 332’dir. Fiziksel tuşlar tersse halka düğmesini
bu sayfadan değiştir. İkinci tuş seçimi diğer fiziksel tuşa uygulanır.
İlk kurulumda eski V5 `penButton:0` değeri 331’e taşınır; sonraki değişikliklerin korunur.

## AI

Super+Shift+A → Ayarlar → OpenAI API anahtarı → Kaydet.
Model varsayılanı `gpt-5.6-luna`; başka bir model kimliği yazabilirsin.
Responses API, `store:false`, 800 çıktı token sınırı, son 8 mesaj kullanılır.
Model cevabı bir işlem öneriyorsa “Uygula” düğmesi gösterilir. Rastgele shell
komutu çalıştırılmaz. Desteklenenler: sistem durumu, Firefox, Nautilus,
Kitty, MyBrain, medya denetimi, ses/parlaklık ve oturum kilitleme isteği.
API anahtarı `~/.config/violet-agent/openai.json` içinde 600 izniyle saklanır;
Nix dosyasına veya /nix/store’a yazılmaz. ChatGPT aboneliğinden bağımsız API kullanımı gerekir.

## Telegram / SSH

Super+Shift+S → bot token, Telegram kullanıcı ID ve sohbet ID → Kaydet → Başlat.
Birden çok ID’yi virgülle ayır. Kullanıcı ve sohbet eşleşmesi birlikte zorunludur.
Başlangıçta birikmiş, çalışma sırasında 60 saniyeden eski komutlar çalıştırılmaz.
Otomatik başlatma GUI’den ayrıca açılır. Token `remote.json` içinde 600 izniyle saklanır.

Bot komutları: `/status`, `/play`, `/next`, `/previous`, `/volume 30`,
`/brightness 60`, `/lock`, `/help`. Telegram kontrolü SSH tüneli gerektirmez;
bilgisayar Telegram API’ye dışarı doğru bağlanır. SSH ayrı anahtarlı erişim alanıdır.
`/lock`, sistemdeki kilitleyici oturuma bağlıysa ekranı kilitler; sonuç cihazda doğrulanmalıdır.

Açık SSH anahtarını arayüzden ekle. Parolalı ve root giriş kapalıdır.
LAN’dan SSH erişimi istersen `modules/violet-v6-remote.nix` içindeki
`openFirewall = false` değerini `true` yapıp aşağıdaki derleme komutunu çalıştır.

```bash
sudo nixos-rebuild switch --flake path:/etc/nixos#nixos
```

## Uygulamalar

Firefox profili daha sonra oluşturulursa `violet-firefox-theme` çalıştırıp Firefox’u yeniden başlat.
Bazaar indirmesi yarım kalırsa `violet-bazaar-install` çalıştır.
Nautilus GTK teması bazı libadwaita sürümlerinde sınırlı uygulanabilir; pencereyi yeniden aç.
Neovim: Space+E dosya haritası, Space+P dosya aç, Space+W kaydet, `:Hyrule` açılış kartı.
Kitty açılışını susturmak için `VIOLET_REDUCED_MOTION=1 kitty`.

## Geri dönüş

Kurulumun verdiği `sudo bash /var/lib/violet-v6/.../geri-al.sh` komutunu çalıştır.
Son başarılı kurulum için kısa yol:

```bash
sudo bash /var/lib/violet-v6/latest/geri-al.sh
```

Sistem açılmazsa GRUB’daki önceki nesli seç. Ardından geri dönüş scriptini çalıştır.
Geri dönüş sistem yapılandırmasını ve değiştirilen Firefox/kalem ayarlarını geri getirir;
Flatpak Bazaar, sonradan girilen API/bot anahtarları ve yeni eklenen SSH anahtarlarını silmez.

## Doğrulama kapsamı

Hazırlama ortamında Python ve Lua sözdizimi; 39 Nix dosyasının ayrıştırılması;
Quickshell QML dosyalarının ayrıştırılması; Qtile 0.37.1 kaynaklarına dört native
yamanın uygulanması; yatay düzen geometrisi/fokus/klonlama; kısayol sahipliği;
AI işlem sınırları; Telegram ID ve eski komut denetimi; Firefox eklemelerinin
tekrarlanabilirliği; MyBrain/AI/uzaktan kontrol arayüzlerinin Qt ile açılması kontrol edildi.

Bu ortam NixOS değildir. Gerçek NixOS değerlendirmesi ve toplevel derlemesi,
scriptin dosyaları uygulamadan önce çalıştırdığı `nix build` ile cihazında yapılır.
EFI/GRUB geçişi, fiziksel kalem tuşları, Quickshell’in gerçek Wayland yüzeyleri ve
OpenAI/Telegram ağ çağrıları burada çalıştırılmadı. Siyah ekranın tamamen kalktığı
iddia edilmiyor; erken AMD yükleme ve gfxterm değişikliği cihazda kontrol edilmeli.

Kaynaklar: [OpenAI GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[NixOS erken KMS](https://wiki.nixos.org/wiki/Graphics),
[Bazaar / Flathub](https://flathub.org/en/apps/io.github.kolunmi.Bazaar).

## V6.1 düzeltmesi

NixOS’ta bulunmayan `boot.loader.grub.terminalOutput` kaldırıldı. Mevcut font/tema yapılandırmasının ürettiği gfxterm korunur. V6 değerlendirme sırasında durduysa mevcut sisteme hiçbir değişiklik yapılmamıştır; güncel kurulum scriptini tekrar çalıştır.
