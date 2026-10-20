# Güvenlik ve aktarım

Bu paket **GitHub'a hazırlanmış bir inceleme kopyasıdır**; otomatik tarama gizli bilgi bulunmadığını garanti etmez.

Dışarıda bırakılanlar:
- `diagnostics/status.txt`: kullanıcı, donanım, seri numaraları, çalışan süreçler ve oturum ayrıntıları.
- `source/etc/nixos/hardware-configuration.nix`: gerçek disk kimlikleri ve cihaza özgü mount yapılandırması.
- `source/etc/nixos/modules/grub-enable.nix`: sabit disk UUID'si içeren makineye özel açılış tanımı.
- Önceki kaynak MANIFEST/uyarı dosyaları (bu paket yeni bir türevdir).

Bu dosyalar **orijinal yerel ZIP içerisinde korunmaktadır**. Eksik dosyalar yüzünden kaynak paket birebir dağıtım olarak derlenmeyebilir. Açılış ayarlarına rastgele UUID yazmayın; makinede doğrulayarak üretin.

### GitHub öncesi kullanıcı kontrolü

1. `git diff --cached` ile tüm dosyaları kontrol edin.
2. `rg -n -i 'password|secret|token|api.?key|private.?key|authorization|client_secret' .` ile eşleşmeleri inceleyin (kod değişkenleri de eşleşir).
3. E-posta, kullanıcı adı, host adları, özel URL, ev dizini yolları, Wi-Fi isimleri, cihaz kimlikleri ve kişisel tercihleri ayrıca inceleyin.
4. Önce PRIVATE GitHub deposu kullanın. Herhangi bir kimlik bilgisi paylaşılmışsa sadece Git'ten silmek yetmez; anahtarı iptal edip yenileyin.
5. ZIP dosyasını kaynak depoya commit etmeyin.

**Kurulum uyarısı:** Ortamı doğrudan başka bilgisayara kurmak için hardware-configuration ve boot modüllerinin yeniden uyarlanması gerekir.
