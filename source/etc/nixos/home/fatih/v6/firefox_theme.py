"""Install an additive theme into current Firefox profiles, never replace profiles."""
import configparser,os,re,sys
from pathlib import Path
START='/* VIOLET_V6_START */';END='/* VIOLET_V6_END */'

def managed(path,content):
    if path.is_symlink():raise ValueError('Tema hedefi sembolik bağ: '+str(path))
    old=path.read_text() if path.exists() else ''
    old=re.sub(re.escape(START)+r'.*?'+re.escape(END), '', old, flags=re.S).rstrip()
    new=(old+'\n' if old else '')+START+'\n'+content+'\n'+END+'\n'
    if path.exists() and not path.with_name(path.name+'.before-violet-v6').exists():
        path.with_name(path.name+'.before-violet-v6').write_text(path.read_text())
    path.write_text(new)

def install(root,chrome,content):
    ini=root/'profiles.ini'
    if not ini.exists():return 0
    cp=configparser.ConfigParser();cp.read(ini);count=0
    for section in cp.sections():
        if not section.startswith('Profile'):continue
        value=cp[section].get('Path','')
        if not value:continue
        profile=(root/value if cp[section].get('IsRelative','1')=='1' else Path(value)).resolve()
        # Themes only touch existing profiles under the logged-in user's home.
        if not profile.is_dir() or not profile.is_relative_to(Path.home().resolve()):continue
        directory=profile/'chrome'
        if directory.is_symlink():continue
        directory.mkdir(exist_ok=True)
        managed(directory/'userChrome.css',chrome);managed(directory/'userContent.css',content)
        managed(profile/'user.js','user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);')
        count+=1
    return count

if __name__=='__main__':
    chrome=Path(sys.argv[1]).read_text();content=Path(sys.argv[2]).read_text()
    for root in [Path.home()/'.mozilla/firefox',Path.home()/'.var/app/org.mozilla.firefox/.mozilla/firefox']:
        count=install(root,chrome,content)
        print(f'Firefox Violet teması: {count} profil')
