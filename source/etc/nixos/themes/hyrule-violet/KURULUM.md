# Hyrule Violet: SDDM, hazırlanmış GRUB teması, kısayollar

Mevcut /etc/nixos/home/fatih düzenine ekleme yapar. Renkleri, masaüstünü,
touch/pen yamalarını ve Plasma kurtarma oturumunu değiştirmez.

## Kurulum

`bash yoga-zelda-login-shortcuts.sh`

Script önce SDDM ve bootloader durumunu doğrular. Kaynakları dış dizine
yedekler, yeni modülleri import eder ve `nixos-rebuild build` çalıştırır.
Başarılı build ardından `bash yoga-zelda-login-shortcuts.sh --preview`
ile SDDM temasını test modunda gör. Önizlemedeki giriş/güç düğmeleri gerçek
giriş veya kapatma yapmaz. Önizleme penceresini kapat.

Ardından `sudo nixos-rebuild switch --flake /etc/nixos#nixos`.
SDDM servisinin switch sırasında oturumunu kesmesini önleyen ayar vardır.
Dosyalarını kaydedip bilgisayarı yeniden başlat; yeni SDDM temasını görürsün.
Switch sonrası Qtile yeni kısayolları yeniden açılan oturumda yükler.
Script switch/reboot/SDDM restart komutunu otomatik çalıştırmaz.

SDDM: mevcut Hyrule violet duvar kâğıdı, violet Triforce, animasyonlu giriş,
parola, Caps Lock uyarısı, oturum seçimi ve güç onayı. Kimlik doğrulama SDDM
üzerindedir; script parola istemez, kaydetmez. Qt 6 greeter gerekir.

## GRUB durumu

Senin sisteminde systemd-boot kalır. GRUB kurulmaz, etkinleştirilmez;
EFI bölümü, bootloader cihazları ve timeout ayarları değiştirilmez.
Hazır tema switch sonrası `/etc/hyrule-violet/grub` altındadır.
GRUB zaten etkin olan bir sistemde kullanılırsa yalnız tema atanır.
GRUB'da masaüstü/QML animasyonları çalışmaz; bu tema statiktir.

## Kısayollar

Super = Windows tuşu. **Super+F1** rehberi açar. Rehber mevcut Qtile
kısayollarını, Super+F12 tuş dizilerini, eklenen doğrudan kısayolları ve
çakışma nedeniyle eklenmeyenleri listeler; arama vardır. Kontrol merkezinde
"Kısayol rehberi" düğmesi de bulunur.

| Tuş | İşlev |
| --- | --- |
| Super+F1 | Kısayol rehberi |
| Super+Ctrl+F1 | Qtile masaüstü ayarları |
| Super+Ctrl+F2 | Kontrol merkezi |
| Super+Ctrl+F3 / F4 / F5 | Ses / saat-takvim / pil |
| Super+Ctrl+F6 | Karşılama animasyonu |
| Super+Ctrl+F7 / F8 / F9 | Önceki / oynat-duraklat / sonraki |
| Super+Esc | Açık paneli kapat |
| Super+Ctrl+D / M / Y / V | Günlük / medya / YouTube Music / video |
| Super+Ctrl+N / P / W / B | Not / Pomodoro / hava-namaz / pano |
| Super+Ctrl+T / S / G / A | Tablet / sistem / finans / hesaplar |
| Super+Ctrl+E / O / I / H | Emoji / bağlantılar / ayarlar / komutlar |
| Super+Ctrl+K / C / F | Güç / hesap makinesi / RSS |
| Super+Alt+R | Reddit |
| Super+Ctrl+L | LinguaMap çeviri |
| Super+Ctrl+Enter | Quake terminal |
| Super+Ctrl+Sağ | Pencereyi diğer ekrana gönder |
| Super+Ctrl+U / J | Albüm kapağı / sıradaki üç şarkı |
| Print / Shift+Print / Ctrl+Print | Ekran / alan / pencere görüntüsü |
| Super+F12, sonra panelin harfi | Önceki özellik paketinin tuş dizileri |

Özellik paketine bağlı atamalar yalnız `kingdom.py` + panel IPC'si
kuruluysa eklenir. Medya kısayolları playerctl gerektirir (önceki paket
sağlar). Aynı tuş zaten atanmışsa yeni atama eklenmez; rehber bunu gösterir.
Super+Ctrl+R (reload), Super+Ctrl+Q (çıkış), Super+Enter, Super+D,
Super+1..9 ve senin diğer kısayolların korunur.

## Geri alma

Kurulumun yazdırdığı yedek dizinini kullan:

`bash yoga-zelda-login-shortcuts.sh --rollback /etc/nixos-before-hyrule-login-TARIH`

Geri alma önce dosyaları doğrular. Kurulumdan sonra değiştirdiğin dosya
varsa onun üzerine yazmaz. Kaynakları geri alır ve build çalıştırır;
başarılıysa switch komutunu yazdırır. Gerekirse önceki sistem neslinden
açılış yapabilir veya TTY'de bu komutu çalıştırabilirsin.

Git ile takip edilen flake'lerde yalnız eklenen dosyalar index'e alınır.
Commit/push yapılmaz. Kaynak değişiklikleri yedek manifestinde kayıtlıdır.

## Doğrulama sınırı

Hazırlayıcı, geri alma, çakışmalar, QML görünümü ve Nix/Python/Bash sözdizimi
hazırlama ortamında test edildi. Bu ortamda NixOS ve gerçek SDDM/PAM/EFI
bulunmadığından gerçek sistem build'i ve oturum girişi senin bilgisayarında
doğrulanır. Çalışan oturumda önce `--preview` kullan.

Kaynaklar:
- https://github.com/sddm/sddm/blob/develop/docs/THEMING.md
- https://github.com/NixOS/nixpkgs/blob/nixos-26.05/nixos/modules/services/display-managers/sddm.nix
- https://www.gnu.org/software/grub/manual/grub/html_node/Theme-file-format.html
