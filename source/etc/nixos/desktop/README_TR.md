# Yoga / Caelestia esintili Qtile — ilk arayüz paketi

Bu paket Caelestia deposunun bir fork'u değildir. Qtile için bağımsız Quickshell arayüzü ve eşleşen temalar içerir. Hyprland veya Niri gerekmez.

Kapsam: yuvarlatılmış üst panel, 9 çalışma alanı, gerçek aktif pencere başlığı, saat, ses/pil; Super+A kontrol merkezi; ses/parlaklık düğmeleri; NetworkManager nmtui, Bluetooth ve ses ayarlarına erişim; playerctl medya bilgisi ve kontrolleri; rofi başlatıcı; Foot teması; mako bildirim kartları; vektör duvar kâğıdı. Kabuk yalnızca Qtile başlangıç kancasından çalıştırılır. Oturum kapanışında Quickshell ve onun mako süreci kapatılır.

Sınırlar: sistem tepsisi ve bildirim geçmişi bu sürümde yok. Wi-Fi/Bluetooth ayarları ayrı yardımcı uygulamalarda açılır. Compositor bulanıklığı, yuvarlak uygulama pencereleri ve pencere animasyonu eklenmedi. Animasyonlar kabuğun düğmeleri ve kontrol merkeziyle sınırlı. Harici ekran ve tablet modu sonraki aşamadır. Varsayılan tek ekran; ölçekleme mevcut compositor ayarını kullanır. 400 mantıksal piksel genişlikte kontrol paneli ve 64 piksel üst panel tasarlandı. Ölçek/çözünürlük cihazda doğrulanmalı.

## Kurulum

Arşivi Downloads klasöründe aç. Aşağıdaki yol, çıkan klasörün ~/Downloads/yoga-caelestia olduğunu varsayar.

```bash
cd ~/Downloads
unzip yoga-caelestia.zip
sudo cp -a /etc/nixos /etc/nixos-before-caelestia-$(date +%Y%m%d-%H%M%S)
sudo mkdir -p /etc/nixos/desktop
sudo cp -a ~/Downloads/yoga-caelestia/. /etc/nixos/desktop/
```

/etc/nixos/home.nix içinde açılış `{` parantezinin hemen altına ekle (mevcut imports varsa listeye ekle):

```nix
imports = [ ./desktop/visual.nix ];
```

Şu mevcut satırı kaldır:

```nix
xdg.configFile."qtile/config.py".source = ./qtile/config.py;
```

Yerine ekle:

```nix
xdg.configFile."qtile" = {
  source = ./desktop/qtile;
  recursive = true;
};
```

Başka Home Manager modülleri rofi veya foot dosyalarını yönetiyorsa aynı dosyanın iki tanımını birleştirmek gerekir. Paylaşılan home.nix'te bu tanımlar yoktu.

Flake.nix, configuration.nix, hardware-configuration.nix ve eski qtile/ klasörünü değiştirme. Sistem modüllerini şu anda taşımıyoruz.

Flake git deposundaysa yeni dosyalar Nix'e görünür olmalı:

```bash
cd /etc/nixos
# Yalnızca /etc/nixos bir git deposuysa:
sudo git add desktop home.nix
```

Sonra:

```bash
sudo nixos-rebuild build --flake /etc/nixos#nixos
```

Build başarılıysa:

```bash
sudo nixos-rebuild switch --flake /etc/nixos#nixos
```

Home Manager geçişi başarılı olmalı. Qtile oturumundan çıkıp SDDM'den Qtile Wayland'a yeniden gir. Eski Qtile barı yeni kabukla birlikte çalıştırılmaz.

## Doğrulama

- Super+Enter: Foot; Super+D: uygulama başlatıcı; Super+A: kontrol merkezi.
- Super+1..9 ve paneldeki numaralar çalışma alanını değiştirmeli; aktif renk ve pencere başlığı güncellenmeli.
- Ses/parlaklık düğmeleri gerçek ayarı değiştirmeli; grafik en geç birkaç saniyede güncellenmeli.
- Wi-Fi kartı gerçek wlp2s0 bağlantısını okumalı; medya yoksa uydurma bilgi göstermemeli.
- Oturum kapanınca Plasma'yı seçtiğinde kabuk kalmamalı.

Kabuk açılmazsa Super+Enter ile terminal aç:

```bash
qs -c fatih
```

Bu komut QML yükleme hatasını terminalde gösterir. Status komutu ayrıca denenebilir:

```bash
fatih-shell-status
cat "$XDG_RUNTIME_DIR/fatih-qtile.json"
```

Bildirimler görünmezse başka notification daemon'u D-Bus adını tutuyor olabilir. Onu körlemesine kapatma; mevcut configuration.nix ile birlikte kontrol et.

## Geri dönüş

home.nix içinden `./desktop/visual.nix` importunu kaldır ve directory mapping yerine eski satırı geri getir:

```nix
xdg.configFile."qtile/config.py".source = ./qtile/config.py;
```

Yine build başarılıysa switch yap ve oturumu yeniden aç. Orijinal /etc/nixos/qtile/config.py dosyası değiştirilmedi.

## Doğrulama durumu

Python dosyalarının sözdizimi ve Qtile durum köprüsü/komut çıktısı ayrıştırması yerel olarak kontrol edildi. Bu hazırlama ortamında Nix ve Qtile/Quickshell Wayland oturumu bulunmadığı için Nix evaluation, QML runtime ve donanım kontrolleri yapılmadı. İlk cihaz build'i paket/option uyumluluğunu, oturum testi QML ve layer-shell entegrasyonunu doğrulayacak. "Tam test edildi" iddiası yok.

Kaynaklar:
https://github.com/caelestia-dots/shell
https://quickshell.org/docs/v0.2.1/types/Quickshell/PanelWindow/
https://quickshell.org/docs/v0.2.1/types/Quickshell.Io/Process/
https://quickshell.org/docs/v0.2.1/types/Quickshell.Io/IpcHandler/
https://docs.qtile.org/en/latest/manual/ref/hooks.html
