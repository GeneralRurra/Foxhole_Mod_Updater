"""Offline regression checks. Uses only temporary files, never installed mods."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import updater as u

def main():
    expected='War-WindowsNoEditor_UI_Label_Materials_v6.1.pak'
    assert u.download_filename({'Content-Disposition':f'attachment; filename="{expected}"'})==expected
    assert u.download_filename({'Content-Disposition':"attachment; filename*=UTF-8''"+expected})==expected
    assert u.download_filename({}) is None
    for name in ['../mod.pak','War-WindowsNoEditor.pak','mod.exe']:
        try: u.download_filename({'Content-Disposition':f'attachment; filename="{name}"'})
        except ValueError: pass
        else: raise AssertionError('Unsafe download filename accepted')

    assert u.version_compare('1.9','1.10') == 1
    assert u.version_compare('7.1','5.1') == -1
    assert u.version_compare(None,'1.3') is None
    assert u.match_file('UI_Label_Items_v5.1.pak',[
        ('old','UI_Label_Items_v5.1.pak'),('new','UI_Label_Items_v7.1.pak')])[0]=='new'
    assert u.match_file('z_BetterCompass_EN_Full_v1.3.pak',[
        ('ru','z_BetterCompass_RU_Full_v1.4.pak')]) is None
    with patch.object(u,'running',return_value=True):
        assert u.game_running_for(Path('any-test-folder')/'mod.pak')
    with tempfile.TemporaryDirectory() as directory:
        base=Path(directory); folder=base/'Paks'; folder.mkdir()
        u.BASE=base; u.CONFIG=base/'mods.json'
        original=folder/'War-WindowsNoEditor.pak'; original.write_bytes(b'protected')
        old=folder/'War-WindowsNoEditor_005_UI_Label_Items_v5.1.pak'
        old.write_bytes(b'old\xe1\x12\x6f\x5a')
        duplicate=folder/'UI_Label_Items_v7.0.pak'
        duplicate.write_bytes(b'duplicate\xe1\x12\x6f\x5a')
        newer=base/'UI_Label_Items_v7.1.pak'; newer.write_bytes(b'new\xe1\x12\x6f\x5a')
        info={'source':'https://sentsu.itch.io/foxhole-ui-label-icons'}
        u.CONFIG.write_text(json.dumps({'folder':str(folder),'mods':{
            str(old):dict(info),str(duplicate):dict(info)}}),encoding='utf-8')
        with patch.object(u,'running',return_value=False):
            root=u.tk.Tk(); root.withdraw(); app=u.App(root); root.update()
            app.ui=lambda fn:fn(); app.job=lambda fn:fn()
            assert not app.tree.exists(str(original))
            app.tree.selection_set(str(old)); app.toggle(); app.scan()
            assert not old.exists() and app.tree.set(str(old),'status')=='Deaktiviert'
            app.tree.selection_set(str(old)); app.toggle(); assert old.exists()
            app.data['mods'][str(old)]['remote']=newer.name
            app.data['mods'][str(old)]['available_version']='7.1'
            app.replace(str(old),newer,newer.name)
            target=folder/newer.name
            assert target.exists() and not old.exists() and not duplicate.exists()
            bundle=Path(app.data['mods'][str(target)]['last_backup'])
            assert (bundle/old.name).exists() and (bundle/duplicate.name).exists()
            app.restore_transaction(str(target),bundle)
            assert old.exists() and duplicate.exists() and not target.exists()
            assert app.data['mods'][str(old)]['installed_version']=='5.1'
            lower=base/'UI_Label_Items_v4.0.pak'; lower.write_bytes(newer.read_bytes())
            try: app.replace(str(old),lower,lower.name); raise AssertionError('Downgrade allowed')
            except ValueError: pass
            try: app.replace(str(original),newer); raise AssertionError('Original allowed')
            except ValueError: pass
            alias=folder/'alias.pak'; os.link(original,alias)
            try: u.protect_game_file(alias); raise AssertionError('Hardlink allowed')
            except ValueError: pass
            assert original.read_bytes()==b'protected'
            app.scan(); app.tree.selection_set(str(old)); app.find_sources(); app.backup_manager()
            app.preview_updates([(str(old),newer)],lambda:None); root.update()
            previews=[w for w in root.winfo_children() if isinstance(w,u.tk.Toplevel) and w.title()=='Updateübersicht']
            preview=previews[0]; preview.geometry('600x380'); root.update()
            buttons=[c for frame in preview.winfo_children() for c in frame.winfo_children() if isinstance(c,u.ttk.Button)]
            assert len(buttons)==2
            assert all(b.winfo_rooty()+b.winfo_height()<=preview.winfo_rooty()+preview.winfo_height() for b in buttons)
            app.download_progress(str(old),50,100)
            assert '50%' in app.progress_text.get()
            app.pending[str(old)]=newer
            app.language_choice.set('English'); app.change_language(); root.update()
            assert u.translations.LANGUAGE=='en'
            assert app.pending[str(old)]==newer and newer.exists()
            assert app.tree.heading('file','text')=='INSTALLED FILE'
            assert app.tree.set(str(old),'status')=='Waiting for installation'
            assert json.loads(u.CONFIG.read_text(encoding='utf-8'))['language']=='en'
            assert original.read_bytes()==b'protected'
            app.language_choice.set('Deutsch'); app.change_language(); root.update()
            assert app.tree.heading('file','text')=='INSTALLIERTE DATEI'
            assert app.pending[str(old)]==newer
            root.destroy()
    print('PASS: versions, downgrade block, original protection, hardlinks, toggle, replacement, backup, restore, dialogs, progress, no test bypass')

if __name__=='__main__': main()
