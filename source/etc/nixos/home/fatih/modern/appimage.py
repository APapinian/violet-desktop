#!/usr/bin/env python3
import os, shutil, sys, hashlib
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

def install(source):
    source=Path(source).resolve()
    if any(ord(c)<32 for c in str(source)):raise ValueError('Dosya yolu kontrol karakteri içeriyor; dosyanın adını değiştir')
    if not source.is_file() or source.suffix.lower()!='.appimage':raise ValueError('Bir .AppImage dosyası seç')
    with source.open('rb') as f:
        header=f.read(12)
    if header[:4]!=b'\x7fELF' or header[8:11] not in (b'AI\x01',b'AI\x02'):raise ValueError('Geçerli AppImage başlığı bulunamadı')
    name=source.stem.replace('\n',' ').replace('\r',' ')
    directory=Path.home()/'Applications';directory.mkdir(exist_ok=True)
    target=directory/source.name
    if target.exists() and target.resolve()!=source:raise ValueError('Aynı adlı AppImage zaten var; önce farklı ad ver')
    if target.resolve()!=source:shutil.copy2(source,target)
    target.chmod(0o755)
    entries=Path.home()/'.local/share/applications';entries.mkdir(parents=True,exist_ok=True)
    # Desktop Exec quoting and percent escaping are separate from shell quoting.
    escaped=str(target).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')
    ident=hashlib.sha256(str(target).encode()).hexdigest()[:12]
    (entries/f'appimage-{ident}.desktop').write_text(f'[Desktop Entry]\nType=Application\nName={name}\nExec=appimage-run "{escaped}" %U\nIcon=application-x-executable\nCategories=Utility;\nTerminal=false\n')
    return target
if __name__=='__main__':
    app=QApplication(sys.argv)
    source=sys.argv[1] if len(sys.argv)>1 else QFileDialog.getOpenFileName(None,'AppImage ekle',str(Path.home()/'İndirilenler'),'AppImage (*.AppImage *.appimage)')[0]
    if source:
        try:target=install(source);QMessageBox.information(None,'AppImage eklendi',f'Uygulama menüsüne eklendi:\n{target}')
        except Exception as e:QMessageBox.warning(None,'AppImage eklenemedi',str(e))
