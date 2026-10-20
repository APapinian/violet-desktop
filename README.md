# Violet Desktop — NixOS / Qtile / Hyrule

Türkçe kişiselleştirilmiş NixOS masaüstü çalışmasının **kaynak aktarımıdır**. Qtile Wayland + Quickshell ile Violet mor estetiği, Zelda/Hyrule teması, iki monitör, tablet/kalem etkileşimi, üst panel ve alt dock, kontrol merkezi, çalışma alanları ve MyBrain bileşenleri hedeflenmektedir.

> **Önemli:** Bu depo bir sistem snapshot'ından derlenmiştir, doğrulanmış ve tek komutla kurulabilir bir NixOS dağıtımı **değildir**. Önce mevcut çalışan sistemi yedekleyin; dosyaları doğrudan `/etc/nixos` üzerine kopyalayıp `nixos-rebuild switch` çalıştırmayın.

## Başlangıç noktaları

- [`VIOLET_QTILE_DEVIR_DOSYASI.md`](VIOLET_QTILE_DEVIR_DOSYASI.md): geçmiş çalışmalar, hedefler ve teknik devir notu.
- [`source/etc/nixos/flake.nix`](source/etc/nixos/flake.nix): Flake giriş noktası.
- [`source/etc/nixos/home/fatih/`](source/etc/nixos/home/fatih/): kullanıcı bileşenleri (Qtile, Quickshell, MyBrain ve servisler).
- [`source/etc/nixos/desktop/`](source/etc/nixos/desktop/): ayrı masaüstü modülü/arayüz dosyaları.
- [`GUVENLIK_VE_AKTARIM.md`](GUVENLIK_VE_AKTARIM.md): bilerek hariç tutulanlar ve GitHub öncesi kontroller.

## Bilinen durum

20 Ekim 2026 tarihli dışa aktarma sırasında Qtile 0.37.1 ve Quickshell 0.3.0 çalışıyor görünüyordu. Quickshell alt dock'un önceki sürümde etkinleşememesi ve eski kurulumlarda geri alma gereksinimi raporlanmıştı; tüm özelliklerin çalıştığı bu paketle doğrulanmış değildir.

## Devralacak geliştirici / yapay zekâ için

Öncelikle Nix ve Home Manager import zincirini, etkin Qtile yapılandırma hedefini, gerçek Quickshell giriş dosyasını ve kullanıcı systemd servislerini inceleyin. Benzer isimli dosyaları tek bir kanonik kaynak gibi varsaymayın. Parçalı/modüler yamalar, doğrulama ve geri dönüş tercih edin. SDDM/KDE kurtarma oturumunu, dokunmatik/kalem özelliklerini, disk alt birimlerini ve flake kilidini koruyun. Yeni bir yapılandırmanın çalıştığını söylemeden önce gerçek sistem üzerinde test edilmesi gerekir.
