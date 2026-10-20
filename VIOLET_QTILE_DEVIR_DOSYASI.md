# VIOLET / HYRULE DESKTOP — TEKNİK DEVİR VE PROJE HAFIZASI

> Tarih: 20 Ekim 2026  
> Proje: NixOS + Qtile Wayland + Quickshell + Home Manager + Flakes  
> Amaç: Projeyi yeni bir yapay zekâya bağlam ve hedef kaybı olmadan devretmek.

## 0. Önemli güvenilirlik notu
Bu doküman önceki sohbetlerdeki taleplerden, paylaşılan komut çıktılarından ve kurulum raporlarından oluşturulmuştur. **Makinedeki dosyalar doğrudan incelenmemiştir.** Burada 'hedef', 'tasarlandı', 'denendi', 'doğrulandı' ve 'çalışıyor' kavramları birbirine karıştırılmamalıdır. Güncel gerçek durum için export ZIP içindeki dosyalar ve tanı çıktıları incelenmelidir.

## 1. Projenin vizyonu
KDE Plasma'nın bir yedeği olduğu, esas masaüstünün Qtile Wayland olduğu; NixOS üzerinde deklaratif, kararlı, oldukça özelleştirilmiş, estetik açıdan tutarlı ve tablet kullanımına uygun kişisel bir masaüstü ortamı geliştirmek.

- Temel görsel kimlik: **Violet**, mor tonlar, modern saydam/yumuşak paneller ve **The Legend of Zelda / Hyrule** atmosferi.
- Referans: **Caelestia Shell**; özellikle yumuşak animasyonlar, panellerin üst bara organik biçimde bağlanması, modern kontrol merkezi, iyi tipografi.
- Sadece tema değil: Qtile pencere yönetimi, Quickshell arayüzü, Nix modülleri, ses/güç/ekran kontrolleri, medya, kalem/dokunma, MyBrain, çalışma alanı rutinleri.
- Açılışta hedef karşılama metni: **“Krallığa hoş geldin Fatih”**.
- Kural: Var olan çalışan özellikleri silip sıfırdan başka bir şey yazmak değil, onları **koruyarak** aşamalı iyileştirmek.
- Dil: Arayüz ve kullanıcıya dönük ifadeler Türkçe.
- Prensip: Estetik kadar **işlevsel, kararlı, geri alınabilir** değişiklikler.

## 2. Bilinen donanım
| Bileşen | Bilinen bilgi |
|---|---|
| Model | Lenovo Yoga 7 2-in-1 14AHP9 (83DK) |
| İşlemci | AMD Ryzen 7 8840HS |
| Grafik | AMD Radeon 780M iGPU |
| RAM | 16 GiB LPDDR5 |
| Disk | Yaklaşık 476,9 GiB NVMe |
| Dosya sistemi | Btrfs; `/`, `/home`, `/nix` ve `/nix/store` bağlamları gözlendi |
| EFI | `/boot`, vfat, yaklaşık 1 GiB |
| Swap | Yaklaşık 14,7 GiB disk swap + 6,7 GiB zram |
| Wi-Fi | Realtek RTL8852CE / rtw89_8852ce |
| Bluetooth | 0bda:5852 |
| Giriş | Wacom 5360 kalem ve dokunma, GXTP5100 touchpad, Yoga tablet-mode switch |
| Kullanıcı / host | `fatih` / `nixos` |
| Zaman dilimi | Europe/Istanbul |
| Ekranlar (son rapor) | `eDP-1` 1920×1200, `DP-2` 1920×1080 harici MSI monitör |

**Kritik:** Yoga 2-in-1 yapısı nedeniyle ekran döndürme, tablet modu, sanal klavye, kalem, dokunma, touchpad ve çoklu ekran davranışı birinci sınıf gereksinimlerdir.

## 3. Yazılım mimarisi / sürümler
- İşletim sistemi: NixOS 26.05 olarak bildirildi.
- Window manager: Qtile **0.37.1**, **Wayland** (önceki kurulumda unstable Qtile / wlroots 0.20.2 uyumluluk yaklaşımı).
- Shell/UI: **Quickshell 0.3.0** (önceki tanılarda doğrulandı); Qtile ile paralel panel, dock, merkez ve launcher bileşenleri.
- Login manager: **SDDM**.
- Kurtarma masaüstü: **KDE Plasma 6**, kaldırılmamalı.
- Boot manager: **systemd-boot** gözlendi. Kullanıcı GRUB özelleştirmesi istedi ama GRUB'un gerçekten etkin olduğu varsayılmamalı. Önce bootloader doğrulanmalı.
- Yapılandırma: Nix Flakes + Home Manager; sistem ve kullanıcı katmanları ayrılmalı.
- Yardımcı uygulama/teknolojiler: Rofi, Foot, Mako, Neovim, Fastfetch, muhtemel `violetctl`; aktif paketler dosyalardan doğrulanmalı.

### Önceki çalışmalarda görülen yollar
- `/etc/nixos/flake.nix`
- `/etc/nixos/flake.lock`
- `/etc/nixos/configuration.nix`
- `/etc/nixos/hardware-configuration.nix`
- `/etc/nixos/home.nix` (eski düzen/varlığı kontrol edilmeli)
- `/etc/nixos/desktop/qtile/` (eski düzen)
- `/etc/nixos/home/fatih/qtile/` (planlanan düzen)
- `/etc/nixos/home/fatih/shell/` (planlanan düzen)
- `/etc/nixos/modules/` (modüler Nix hedefi)
- `~/.config/qtile/config.py` — son tanıda `/nix/store/...-hm_qtile/config.py` bağlantısı olarak görülmüştü; **doğrudan store dosyası düzenlenmemeli**.
- `~/.config/quickshell/`, `~/.config/rofi/`, `~/.config/foot/`, `~/.config/mako/`
- `~/.config/systemd/user/`
- `~/.local/state/violet-v5/backups/`
- `/var/backups/violet-modern-v4-*`
- `/var/lib/violet-v6/` (önceki V6 kurulum aday/yedek dizinleri)

Bu yolların bir bölümü eski veya hedef düzen olabilir; dosya keşfi yapılmadan kesin varsayılmamalıdır.

## 4. Görsel tasarım ve kullanıcı deneyimi
### Üst bar
- Modern, yatay, mor/violet temasına uygun panel.
- Saat, ses, pil ve diğer sistem göstergelerinin **kendi etkileşimli menüleri**.
- En sağdaki ikonun **genel kontrol merkezini** açması.
- Ağ/Bluetooth, medya, bildirimler, güç, Buds/kulaklık kontrollerinin tutarlı arayüz dili.
- Açılan kutular sert/köşeli veya ayrı yapıştırılmış hissi vermemeli; Caelestia benzeri, yumuşak köşeli, üst bara bağlı ve animasyonlu açılmalı.

### Alt dock
- Ekranın **alt kenarında, ortalanmış**, modern dock.
- **Otomatik gizlenmeli**; gereksiz sürekli alan kaplamamalı.
- Çoklu monitörde konumu/davranışı doğrulanmalı.
- V6.1'de yeni bileşenler sentaktik olarak doğrulandı ama çalışan Quickshell içinde etkinleşmedi; işlem rollback yaptı. **Aktif olduğu iddia edilmemeli**.

### Launcher, pencere değiştirme, çalışma alanları
- Birleşik uygulama/komut/dosya arama yaklaşımı ve violet görsel bütünlüğü.
- Alt+Tab: **açık pencerelerin görsel pop-up'ı** ile pencere değiştirme.
- Super+Tab / Super+Shift+Tab: masaüstü/çalışma alanı geçişi (V6 hedefi); fiilen tuşlar incelenmeli.
- Super+Shift+1…9 ve Super+Shift+Sağ/Sol: pencereleri çalışma alanına taşıma (önceki V6 niyeti).
- **Firefox kesinlikle 2. çalışma alanına zorla sabitlenmemeli**, kullanıcı istediği yere taşıyabilmeli.
- Workspace isimleri: `DEV`, `WEB`, `LAW`, `READ`, `MEDIA`, `CHAT`, `SYS`, `8`, `9`.
- Önceki talepler: Windows benzeri/estetik Alt+Tab, grup/çalışma alanı menüsü ve sezgisel mouse davranışları.

### Kilit, açılış ve oturum
- SDDM görsel olarak Violet/Hyrule diliyle uyumlu olmalı.
- Boot menüsü ve boot sonrası karşılama animasyonu isteniyor.
- **GRUB varsaymayın**: systemd-boot mevcut olabileceği için önce `boot.loader` ve `bootctl status` inceleyin.
- Tablet kalem/dokunmatik, oturum açılışı ve gerektiğinde Plasma kurtarma yolu bozulmamalı.

### Tema ayrıntıları
- Kalıcı violet/mor palet, Zelda esintili motifler, profesyonel modern görünüm.
- “Krallığa hoş geldin Fatih” karşılama.
- Gereksiz sivri köşeler yerine akışkan/geçişli yüzeyler.
- Görsel kaynaklar aşırı büyümemeli; daha önce 256 MB üzeri görsel uyarıları görüldü.
- Pencere odak kaybında ilgili medya/popup kapanışı istenmişti; ESC'ye bağımlılık azaltılmalı.

## 5. Uygulama ve servis geliştirmeleri
### MyBrain (ikinci beyin)
- Yerel bilgi/çalışma alanı; USB/taşınabilir konseptinden gelişen kişisel uygulama.
- Kullanıcı uygulamanın CSS-vari ham görünümünden memnun değildi; güçlü modern violet/Zelda tasarım istiyor.
- YouTube, YouTube Music, Reddit, X/Twitter ve Google Drive içeriklerinin uygulamada **ayrı pencere açmadan**, mümkünse gerçek içerik alanına entegre görünmesi isteniyor.
- Kullanıcı, Wikipedia içeriği örneğindeki gibi bir bütünlük istiyor. Ancak üçüncü taraf sitelerin CSP/X-Frame-Options, oturum açma, DRM ve API kısıtları göz önünde tutulmalı; çalışmayacak iframe vaadi verilmemeli.
- Premium üyelik işlevlerine giriş sonrası erişim beklentisi var, ancak teknik ve hukuki sınırları doğru açıklayın.
- Önceki V5 raporunda şifreleme/çatışma yönetimi için geliştirmeler anıldı; kaynak koduyla teyit edin.

### Neovim / terminal
- Temaya özel Neovim açılışı, Zelda/Hyrule atmosferi, dekoratif kenar çizgileri, tutarlı terminal/font/tema.
- Fastfetch ve Foot uyumu; terminal uyarıları (örn. Foot renk yapılandırması deprecation) temizlenmeli.

### Bildirim, medya ve telefon
- Bildirim merkezi ve geçmişi; Mako/Quickshell görevlendirmeleri çakışmamalı.
- Oynatılan şarkı, oynatıcı kartları, müzik/buds kontrolleri; odak kaybı popup davranışı.
- Samsung S24+ ile KDE Connect tarzı paylaşım/bildirim işlevi önerilmişti; kurulu ve çalışır olup olmadığı incelenmeli.
- Günlük panel, güç profilleri, sistem servisleri ve düzenlenebilir ayarlar menüsü.

### Kişisel çalışma alanları
- Hukuk, yazılım geliştirme, web, okuma, medya ve sohbet çalışma akışları.
- Önceden talep edilen 'çalışma düzenini tekrar aç' düşüncesi; uygulamaları ilgili workspace'e geri yükleyebilen düzenler.
- Kişisel üretkenlik entegrasyonları hedef; uygulanmış sayılmamalı.

## 6. Önceki geliştirme evreleri
| Evre | Bilinen içerik ve sonuç |
|---|---|
| Erken Qtile/Wayland | Yoga donanımı için Qtile 0.37.1, kalem/dokunma, Qtile grupları, Home Manager/Flakes |
| Caelestia/Violet ilk paket | Quickshell panel, kontrol merkezi, launcher, Rofi, Foot, Mako, wallpaper; ilk paketlerde eksik işlevler vardı |
| Violet v4 | Eksik panel/servis/bağlantıları onarma; Alt+Tab, günlük panel, medya kartı, karşılama; `--check`, `--build`, `--rollback` ve yedekleme yaklaşımı |
| Violet v5 | Qtile, Violet, Kingdom, Buds, MyBrain korunacak; Qtile/Neovim/Fastfetch/QML geliştirilmeleri; `flake.lock` korunması |
| Violet v6 | Klavye, Firefox workspace serbestliği, otogizlenen dock ve çoklu monitör onarım girişimi |
| Violet v6.1 (19 Ekim) | Qtile config ve Quickshell bileşenleri doğrulandı; **yeni alt bar aktif oturumda açılmayınca kurulum geri alındı** |

Bilinen son hata metni: `HATA: Yeni alt bar çalışan Quickshell içinde etkinleşmedi; dosyalar geri yükleniyor. Son Quickshell kaydı incelenmeli.`

## 7. Gözlenen hatalar ve açık işler
1. **En acil:** Quickshell 0.3.0 çalışan `-c fatih -d` oturumunda yeni alt dock'un neden etkinleşmediğini IPC, QML logları, config adı ve servis başlangıcından teşhis et.
2. **Çoklu ekran:** Son tanıda `eDP-1` 1920×1200 ve `DP-2` 1920×1080; Qtile yapılandırmasında `screens = [Screen()]` gözlenmişti. İkinci ekrandaki çalışma alanı/bar olaylarını doğrula.
3. **Workspace ve keybindings:** Super+Tab, Super+Shift+Tab, Alt+Tab ve pencere taşıma kombinasyonlarını gerçek `qtile` API çıktısından doğrula.
4. **Firefox:** Workspace 2'ye sabitleyen kuralı bul ve kaldır; eski kuralın Home Manager tarafından geri gelmesini engelle.
5. **Kullanıcı deneyimi:** Alt dock autohide, kontrol merkezi smooth popover'ları, grup menüsü ve bildirim/medya/earbuds panelleri.
6. **Girdi:** Önceden touchpad/libinput ile ilgili sorunlar görüldü; Wacom pen/touch ve Yoga tablet-mode switch doğrula.
7. **Güç ve yardımcı uygulamalar:** `powerprofilesctl` boş sonuç, GParted açılamaması, olası uygulama izin/yol sorunları.
8. **Boot/UI:** Siyah ekran veya imleç kalması, çift bar, saat glitch, SDDM sonrası animasyon; gerçek bootloader'a göre çöz.
9. **Nix ve kurtarma:** `violet-modern-v4`, `home-snapshot`, Nix lock/hash, aday yapılandırma hatalarının nedenlerini güncel loglarda doğrula.
10. **Performans:** Animasyonun pil/CPU maliyeti, cihazın 2-in-1 davranışı ve ekran/uyku/kapak servisleri.

## 8. Kullanıcı tarafından korunması istenen kurallar
- Çalışan Qtile Wayland oturumunu ve KDE Plasma kurtarma oturumunu kaldırma.
- Nix disk UUID'leri, Btrfs alt birimleri ve EFI/boot yapılandırmasını keyfî değiştirme.
- `flake.lock` dosyasını bilinçsizce yenileme; yükseltme ayrı işlem olsun.
- Store içindeki salt-okunur dosyaları düzenleme; asıl Nix/Home Manager kaynağını bul.
- Önce Nix değerlendirme/build kontrolü, ardından kontrollü switch; başarısızlıkta otomatik veya açık rollback.
- Tek seferde büyük ve izlenemeyen 100+ değişiklik uygulama: küçük, test edilebilir modüller kullan.
- İki monitörü, touchpad'i, dokunmatik ekranı, kalemi, kapak/tablet modunu koru.
- Türkçe arayüz ve Violet/Hyrule tasarım sürekliliği korunsun.
- Kullanıcı önceki kapsamlı özellik listesinde **118, 119, 128, 129, 133 ve 136–150** olarak numaralanan maddeleri **hariç** tutmuştu. Orijinal listenin eşlemesini görmeden bunları yeniden ekleme.
- Değişiklikleri kurulu saymadan önce gerçek oturumda çalıştığını gösteren çıktı iste/üret.

## 9. Son rapor ve tanı bilgileri
- Çalışan Qtile yapılandırması: `/home/fatih/.config/qtile/config.py`.
- Daha eski kontrolde bağlantı `.../nix/store/...-hm_qtile/config.py` idi.
- Quickshell: `0.3.0`, `qs -c fatih` yapılandırma adının kullanıldığına işaret ediyor.
- Önceki onarım scripti: `~/İndirilenler/violet-masaustu-onar-v6-1.sh`.
- Önceki script arayüzü: `--durum`, `--tani`, `--geri-al` (script mevcutsa gerçek koddan doğrulanmalı).
- Önceki tanılarda `qs -c fatih ipc call desktop violetVersion`, `violetctl workspace-status` gibi komutlar yer aldı; bunların geçerli/kurulu olduğunu varsayma.
- Son v6.1 sonuç: `Kurulum tamamlanamadı; değişiklikler geri alınıyor.`

## 10. Yeni yapay zekâ için çalışma protokolü
1. Ekli ZIP kaynak paketini listele. `MANIFEST.txt`, `diagnostics/`, `/etc/nixos`, ilgili `~/.config` dosyaları, servisler ve scriptleri oku. ZIP'te yoksa dosyayı varsayma.
2. **İlk yanıtında:** (a) gerçek mimari, (b) aktif dosya yolu, (c) kritik arızalar, (d) korunacak çalışan özellikler, (e) önerdiğin tek bir küçük değişiklik açıkça belirtilsin.
3. Önce oturum durumu, `qtile cmd-obj`, Quickshell QML log/IPC, ekran topolojisi ve Home Manager dosya bağlantılarını incele.
4. Yeni değişiklik için okunur diff, yerel ön kontrol, build doğrulaması ve rollback komutu oluştur.
5. Sadece kozmetik değil; alt dock gerçekten açılıyor mu, popup etkileşimli mi, Firefox taşınıyor mu, iki ekran çalışıyor mu? Test et.
6. Gizli değerleri, SSH anahtarlarını, parola dosyalarını veya tokenları **asla Git'e koyma**.
7. Doğrulanmış çalışma durumunu ayrı `STATUS.md` ve değişiklik günlüğünü `CHANGELOG.md` ile tut.
8. Kullanıcının son onayı olmadan çalışır sistemi riskli bootloader/partition/rebuild değişikliklerine sürükleme.

## 11. İlk incelenmesi gereken komutlar (kullanıcının makinesinde)
```bash
readlink -f ~/.config/qtile/config.py
ls -la ~/.config/quickshell
systemctl --user --no-pager --type=service | grep -Ei 'violet|quick|qtile' || true
pgrep -a quickshell || true
command -v qs && qs --version || true
command -v qtile && qtile --version || true
bootctl status 2>&1 | head -40
nixos-version
find /etc/nixos -maxdepth 3 -type f | sort | head -150
```
Bu komutlar salt-okunur niteliktedir. Özellikle bootloader ve Quickshell yapılandırma adı doğrulanmadan değiştirilmemelidir.

## 12. Nihai başarı ölçütü
Violet; tek ve çift ekranda kararlı çalışan, klavye/fare/touch/pen akışına uygun, açılış-kilit-panel-dock-uygulama boyunca tek tasarım dili kullanan, güçlü animasyonları makul kaynak tüketimiyle sunan, tamamen yedeklenebilir/deklaratif ve her sürümde kolayca geri alınabilir **kişisel masaüstü sistemi** olmalıdır.

---
**Yeni AI'ya başlangıç mesajı:** “Bu Markdown proje geçmişidir; ZIP içindeki güncel gerçek kaynaklar esas alınmalıdır. Önce mevcut Qtile/Quickshell/Nix kurulumunu analiz et, çalışan özellikleri koru ve V6.1 alt dock aktivasyon arızasını küçük, test edilebilir, geri alınabilir bir değişiklikle çöz. Hayalî dosya, doğrulanmamış özellik ya da varsayımsal başarı üretme.”
