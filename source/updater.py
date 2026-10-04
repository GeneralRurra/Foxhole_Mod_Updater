import hashlib, html, http.cookiejar, json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.error, urllib.parse, urllib.request, webbrowser
import translations
from translations import tr
from pathlib import Path
from email.message import Message
from email.utils import collapse_rfc2231_value
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

BASE = Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve().parent
CONFIG = BASE / 'mods.json'
APP_VERSION='1.0.2'

def download_filename(headers):
    """Use the server's actual download filename, never its display label."""
    disposition=Message()
    disposition['Content-Disposition']=headers.get('Content-Disposition','')
    name=disposition.get_filename()
    if isinstance(name,tuple): name=collapse_rfc2231_value(name)
    if not name: return None
    if (Path(name).name!=name or any(c in name for c in '/\\:')
            or not name.lower().endswith('.pak') or name.casefold()=='war-windowsnoeditor.pak'):
        raise ValueError(tr('Ungültiger Dateiname im Download.'))
    return name

def detect_foxhole():
    roots=[]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam') as key:
            roots.append(Path(winreg.QueryValueEx(key,'SteamPath')[0]))
    except (OSError,ImportError): pass
    for variable in ('ProgramFiles(x86)','ProgramFiles'):
        if os.environ.get(variable): roots.append(Path(os.environ[variable])/'Steam')
    libraries=set(roots)
    for root in roots:
        try:
            text=(root/'steamapps'/'libraryfolders.vdf').read_text(encoding='utf-8')
            libraries.update(Path(p.replace('\\\\','\\')) for p in re.findall(r'"path"\s+"([^"]+)"',text))
        except OSError: pass
    for library in sorted(libraries,key=str):
        candidate=library/'steamapps'/'common'/'Foxhole'/'War'/'Content'/'Paks'
        if candidate.is_dir(): return str(candidate.resolve())
    return ''

DEFAULT=detect_foxhole()

CATALOG = {
    'disui':'https://savokru.itch.io/disui',
    'wardentankflags':'https://danetello.itch.io/foxhole-warden-tank-flags-mod',
    'ui_label_':'https://sentsu.itch.io/foxhole-ui-label-icons',
    'bmsxyellow':'https://majorvictory.itch.io/foxhole-bmsx-small-gauge-retexture',
    'roadcenterlines_ff':'https://fudgelfox.itch.io/foxhole-road-center-lines',
    'highvisrailwaysign_ff':'https://fudgelfox.itch.io/foxhole-high-visibility-railway-switch',
    'z_bettercompass_':'https://kocmodecaht.itch.io/foxhole-better-compass',
    'imm_':'https://rustard.itch.io/improved-map-mod',
    'v63_kov_sad_front':'https://dkov.itch.io/foxhole-pale-front-mapmod',
}

def version_of(name):
    found=re.search(r'(?:^|[_ -])v(\d+(?:\.\d+)*[a-z]?)(?=\.|[_ ()+-]|$)',Path(name).name,re.I)
    return found[1].lower() if found else None

def version_compare(old,new):
    if not old or not new: return None
    def parts(v):
        match=re.fullmatch(r'(\d+(?:\.\d+)*)([a-z]?)',v)
        if not match: return None
        return tuple(map(int,match[1].split('.'))),match[2]
    a,b=parts(old),parts(new)
    if a is None or b is None: return None
    length=max(len(a[0]),len(b[0]))
    a=(a[0]+(0,)*(length-len(a[0])),a[1]); b=(b[0]+(0,)*(length-len(b[0])),b[1])
    return (b>a)-(b<a)

def source_candidates(name,mods):
    family=mod_name(name,True)
    urls={m['source'] for k,m in mods.items() if m.get('source') and mod_name(k,True)==family}
    urls.update(url for prefix,url in CATALOG.items() if family.startswith(prefix))
    return sorted(urls)

def game_running_for(path):
    return running()

def protect_game_file(path):
    candidate=Path(path)
    # Resolve links as well, so a differently named link cannot bypass protection.
    if any(p.name.casefold()=='war-windowsnoeditor.pak' for p in (candidate,candidate.resolve())):
        raise ValueError(tr('Geschützte Spieldatei: War-WindowsNoEditor.pak darf niemals verändert werden.'))
    for original in (candidate.parent/'War-WindowsNoEditor.pak',Path(DEFAULT)/'War-WindowsNoEditor.pak'):
        if candidate.exists() and original.exists() and os.path.samefile(candidate,original):
            raise ValueError(tr('Die Datei verweist auf die geschützte Originaldatei.'))

def mod_name(name, ignore_version=False):
    name = Path(name).name.casefold()
    name = re.sub(r'^(war-windowsnoeditor_)\d+_', r'\1', name)
    name = re.sub(r'^war-windowsnoeditor_', '', name)
    if ignore_version:
        name = re.sub(r'[_ -]v\d+(?:\.\d+)*[a-z]?(?=\.pak$)', '', name)
        # DisUI used the Foxhole update number in older releases.
        name = re.sub(r'^(disui(?:_onyx)?)(?:63|65)(?=\.pak$)', r'\1', name)
        name = re.sub(r'^(wardentankflags)\d+(?=\.pak$)',r'\1',name)
    return name

def match_file(installed, files):
    variants = [f for f in files if mod_name(f[1], True) == mod_name(installed, True)]
    if len(variants)>1 and all(version_of(f[1]) for f in variants):
        newest=variants[0]
        for f in variants[1:]:
            if version_compare(version_of(newest[1]),version_of(f[1]))==1: newest=f
        if sum(version_compare(version_of(newest[1]),version_of(f[1]))==0 for f in variants)==1: return newest
    exact = [f for f in files if mod_name(f[1]) == mod_name(installed)]
    if len(exact) == 1: return exact[0]
    return variants[0] if len(variants) == 1 else None

class NameOnlyResult(Exception):
    pass

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def source(path):
    try:
        text = Path(str(path) + ':Zone.Identifier').read_text(errors='replace')
        url = re.search(r'^ReferrerUrl=(.+)$', text, re.M)
        if url:
            p = urllib.parse.urlsplit(url[1].strip())
            route = p.path.split('/download/')[0]
            return urllib.parse.urlunsplit((p.scheme, p.netloc, route, '', ''))
    except OSError: pass
    return ''

def valid_pak(path):
    with open(path, 'rb') as f:
        f.seek(max(0, path.stat().st_size-512))
        tail = f.read()
    if b'\xe1\x12\x6f\x5a' not in tail:
        raise ValueError(tr('Keine unterstützte Unreal-PAK-Datei. ZIP-Dateien bitte zuerst entpacken.'))

def running():
    r = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True,
                       creationflags=0x08000000)
    if r.returncode: raise RuntimeError(tr('Laufende Prozesse konnten nicht geprüft werden.'))
    return any(x in r.stdout.lower() for x in ('war-win64', 'foxhole.exe', 'war.exe'))

class App:
    def __init__(self, root):
        try: translations.LANGUAGE=json.loads(CONFIG.read_text(encoding='utf-8')).get('language','de')
        except (OSError,ValueError): translations.LANGUAGE='de'
        self.root = root
        root.title('Foxhole Mod Updater '+APP_VERSION)
        screen_width=root.winfo_screenwidth(); screen_height=root.winfo_screenheight()
        root.geometry(f'{min(1480,screen_width-80)}x{min(980,screen_height-120)}')
        root.minsize(min(1000,screen_width-80),min(640,screen_height-120))
        root.configure(bg='#10151c')
        root.option_add('*Font', ('Segoe UI',10))
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('.',background='#10151c',foreground='#e8edf4',font=('Segoe UI',10))
        style.configure('TFrame',background='#10151c')
        style.configure('Card.TFrame',background='#19212c')
        style.configure('TLabel',background='#10151c',foreground='#e8edf4')
        style.configure('Muted.TLabel',foreground='#94a3b8')
        style.configure('Card.TLabel',background='#19212c',foreground='#94a3b8')
        style.configure('Title.TLabel',font=('Segoe UI',26,'bold'))
        style.configure('TButton',background='#263243',foreground='#e8edf4',borderwidth=0,padding=(16,11))
        style.map('TButton',background=[('active','#35465c'),('disabled','#1b2430')],foreground=[('disabled','#69788d')])
        style.configure('Accent.TButton',background='#62dbb3',foreground='#102b24',font=('Segoe UI',10,'bold'))
        style.map('Accent.TButton',background=[('active','#8be8cb'),('disabled','#294f45')])
        style.configure('Language.TCombobox',fieldbackground='#101923',background='#263243',foreground='#e8edf4',arrowcolor='#94a3b8',bordercolor='#35465c',lightcolor='#35465c',darkcolor='#35465c',padding=8)
        style.map('Language.TCombobox',fieldbackground=[('readonly','#101923')],foreground=[('readonly','#e8edf4')],background=[('active','#35465c'),('readonly','#263243')],selectbackground=[('readonly','#254b49')],selectforeground=[('readonly','#bafbe4')])
        root.option_add('*TCombobox*Listbox.background','#19212c')
        root.option_add('*TCombobox*Listbox.foreground','#e8edf4')
        root.option_add('*TCombobox*Listbox.selectBackground','#254b49')
        root.option_add('*TCombobox*Listbox.selectForeground','#bafbe4')
        style.configure('TEntry',fieldbackground='#101923',foreground='#e8edf4',insertcolor='#e8edf4',borderwidth=0,padding=10)
        style.configure('Treeview',background='#151d27',fieldbackground='#151d27',foreground='#dae3ef',rowheight=42,borderwidth=0,font=('Segoe UI',10))
        style.configure('Treeview.Heading',background='#202b39',foreground='#94a3b8',font=('Segoe UI',9,'bold'),padding=(10,14),relief='flat')
        style.map('Treeview',background=[('selected','#254b49')],foreground=[('selected','#bafbe4')])
        style.map('Treeview.Heading',background=[('active','#2b394b')])
        style.configure('Vertical.TScrollbar',background='#35465c',troughcolor='#151d27',borderwidth=0,arrowsize=12)
        style.configure('Horizontal.TScrollbar',background='#35465c',troughcolor='#151d27',borderwidth=0,arrowsize=12)
        style.configure('TProgressbar',background='#62dbb3',troughcolor='#19212c',borderwidth=0)
        try: self.data = json.loads(CONFIG.read_text(encoding='utf-8'))
        except (OSError, ValueError): self.data = {'folder': DEFAULT, 'mods': {}}
        translations.LANGUAGE=self.data.get('language','de') if self.data.get('language','de') in ('de','en') else 'de'
        self.pending = {}
        self.busy = False
        shell=ttk.Frame(root,padding=18); shell.pack(fill='both',expand=True)
        header=ttk.Frame(shell); header.pack(fill='x',pady=(0,24))
        self.language_choice=tk.StringVar(value='English' if translations.LANGUAGE=='en' else 'Deutsch')
        self.language_picker=ttk.Combobox(header,style='Language.TCombobox',textvariable=self.language_choice,values=('Deutsch','English'),state='readonly',width=12)
        self.language_picker.pack(side='right',padx=(12,0))
        self.language_picker.bind('<<ComboboxSelected>>',self.change_language)
        titles=ttk.Frame(header); titles.pack(side='left')
        ttk.Label(titles,text='FOXHOLE',style='Muted.TLabel',font=('Segoe UI',10,'bold')).pack(anchor='w')
        ttk.Label(titles,text=tr('Deine Mods. Auf einen Blick.'),style='Title.TLabel').pack(anchor='w',pady=(6,4))
        ttk.Label(titles,text=tr('Quellen finden, Änderungen prüfen und sicher aktualisieren.'),style='Muted.TLabel').pack(anchor='w')
        self.summary=tk.StringVar(value=tr('MOD-BIBLIOTHEK'))
        ttk.Label(header,textvariable=self.summary,foreground='#62dbb3',font=('Segoe UI',12,'bold')).pack(side='right')
        bar = ttk.Frame(shell,style='Card.TFrame',padding=16); bar.pack(fill='x')
        ttk.Label(bar,text=tr('SPIELORDNER'),style='Card.TLabel',font=('Segoe UI',9,'bold')).pack(anchor='w',pady=(0,8))
        folderbar=ttk.Frame(bar,style='Card.TFrame'); folderbar.pack(fill='x')
        self.folder = tk.StringVar(value=self.data['folder'])
        self.folder_entry=ttk.Entry(folderbar,textvariable=self.folder)
        self.folder_entry.pack(side='left', fill='x', expand=True)
        self.folder_buttons=[]
        for text,fn in [(tr('Ordner wählen'),self.choose),(tr('Neu einlesen'),self.scan)]:
            b=ttk.Button(folderbar,text=text,command=fn); b.pack(side='left',padx=(10,0)); self.folder_buttons.append(b)
        toolbar=ttk.Frame(shell); toolbar.pack(fill='x',pady=(22,12))
        ttk.Label(toolbar,text=tr('Installierte Mods'),font=('Segoe UI',15,'bold')).pack(side='left')
        self.buttons=[]
        b=ttk.Button(toolbar,text=tr('Alle auf Updates prüfen'),style='Accent.TButton',command=lambda:self.check(True)); b.pack(side='right'); self.buttons.append(b)
        b=ttk.Button(toolbar,text=tr('Alle Updates installieren'),style='Accent.TButton',command=self.install_all); b.pack(side='right',padx=(0,10)); self.buttons.append(b)
        content=ttk.Frame(shell); content.pack(fill='both',expand=True)
        table=ttk.Frame(content); table.pack(side='left',fill='both',expand=True)
        self.tree = ttk.Treeview(table, columns=('file','version','available','source','remote','status'), show='headings', selectmode='browse')
        for col, title, width in [('file',tr('INSTALLIERTE DATEI'),300),('version',tr('INSTALLIERT'),95),('available',tr('VERFÜGBAR'),95),('source',tr('QUELLE'),220),('remote',tr('VERFÜGBARER DOWNLOAD'),280),('status','STATUS',245)]:
            self.tree.heading(col, text=title); self.tree.column(col, width=width)
        self.tree.grid(row=0,column=0,sticky='nsew')
        table.rowconfigure(0,weight=1); table.columnconfigure(0,weight=1)
        sy=ttk.Scrollbar(table,orient='vertical',command=self.tree.yview); sy.grid(row=0,column=1,sticky='ns')
        sx=ttk.Scrollbar(table,orient='horizontal',command=self.tree.xview); sx.grid(row=1,column=0,sticky='ew')
        self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        self.tree.tag_configure('even',background='#19232f')
        self.tree.bind('<<TreeviewSelect>>', self.explain)
        actions_host=ttk.Frame(content,style='Card.TFrame',width=260); actions_host.pack(side='right',fill='y',padx=(18,0)); actions_host.pack_propagate(False)
        actions_canvas=tk.Canvas(actions_host,bg='#19212c',highlightthickness=0,width=240)
        actions_scroll=ttk.Scrollbar(actions_host,orient='vertical',command=actions_canvas.yview)
        actions_scroll.pack(side='right',fill='y'); actions_canvas.pack(side='left',fill='both',expand=True)
        actions_canvas.configure(yscrollcommand=actions_scroll.set)
        actions=ttk.Frame(actions_canvas,style='Card.TFrame',padding=12)
        actions_window=actions_canvas.create_window((0,0),window=actions,anchor='nw')
        actions.bind('<Configure>',lambda e:actions_canvas.configure(scrollregion=actions_canvas.bbox('all')))
        actions_canvas.bind('<Configure>',lambda e:actions_canvas.itemconfigure(actions_window,width=e.width))
        style.configure('Compact.TButton',padding=(12,5))
        ttk.Label(actions,text=tr('MOD VERWALTEN'),style='Card.TLabel',font=('Segoe UI',9,'bold')).pack(anchor='w')
        self.selection_title=tk.StringVar(value=tr('Wähle eine Mod'))
        ttk.Label(actions,textvariable=self.selection_title,background='#19212c',foreground='#e8edf4',font=('Segoe UI',11,'bold'),wraplength=220).pack(anchor='w',pady=(6,8))
        for text, fn in [(tr('Update prüfen'),self.check),(tr('Update installieren'),self.install),(tr('Aktivieren / Deaktivieren'),self.toggle),(tr('Quellen finden'),self.find_sources),(tr('Mod-Seite öffnen'),self.open),(tr('Quelle zuordnen'),self.assign),(tr('PAK importieren'),self.local),(tr('Sicherungen verwalten'),self.backup_manager),(tr('Letzte Sicherung herstellen'),self.restore)]:
            b=ttk.Button(actions,text=text,command=fn,style='Compact.TButton'); b.pack(fill='x',pady=(0,4)); self.buttons.append(b)
        footer=ttk.Frame(shell,style='Card.TFrame',padding=16); footer.pack(fill='x',pady=(18,0))
        ttk.Label(footer,text=tr('DETAILS & AKTIVITÄT'),style='Card.TLabel',font=('Segoe UI',9,'bold')).pack(anchor='w',pady=(0,8))
        self.status = tk.StringVar(value=tr('Datei auswählen, dann Update prüfen. Downloads werden vor der Installation zwischengespeichert.'))
        self.detail_label=ttk.Label(footer,textvariable=self.status,background='#19212c',foreground='#dbe5f1',wraplength=1250)
        self.detail_label.pack(anchor='w',fill='x')
        footer.bind('<Configure>',lambda e:self.detail_label.configure(wraplength=max(300,e.width-32)))
        self.progress=ttk.Progressbar(shell,mode='indeterminate'); self.progress.pack(fill='x',pady=(10,0))
        self.progress_text=tk.StringVar(value=tr('Bereit'))
        ttk.Label(shell,textvariable=self.progress_text,style='Muted.TLabel').pack(anchor='w',pady=(6,0))
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.scan()

    def change_language(self,event=None):
        language='en' if self.language_choice.get()=='English' else 'de'
        if self.busy:
            self.language_choice.set('English' if translations.LANGUAGE=='en' else 'Deutsch')
            messagebox.showinfo(tr('Bitte warten'),tr('Ein Vorgang läuft noch.'))
            return
        selection=self.tree.selection()
        selected=selection[0] if selection else None
        pending=self.pending
        self.data['language']=language
        self.save()
        for widget in self.root.winfo_children(): widget.destroy()
        self.__init__(self.root)
        self.pending=pending
        for key in pending:
            if self.tree.exists(key): self.tree.set(key,'status',tr('Wartet auf Installation'))
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
            self.explain()

    def close(self):
        if self.busy: return messagebox.showinfo(tr('Bitte warten'),tr('Ein Vorgang läuft noch.'))
        shutil.rmtree(BASE / 'cache', ignore_errors=True)
        self.root.destroy()

    def save(self):
        if threading.current_thread() is threading.main_thread(): self.data['folder']=self.folder.get()
        tmp=CONFIG.with_suffix('.tmp'); tmp.write_text(json.dumps(self.data,indent=2,ensure_ascii=False),encoding='utf-8'); os.replace(tmp,CONFIG)

    def choose(self):
        if self.busy: return
        p=filedialog.askdirectory(title=tr('Foxhole War/Content/Paks auswählen'))
        if p: self.folder.set(p); self.scan()

    def scan(self):
        if self.busy: return
        if not self.folder.get().strip():
            self.status.set(tr('Foxhole wurde nicht automatisch gefunden. Bitte den Ordner War/Content/Paks auswählen.'))
            return
        folder=Path(self.folder.get())
        if not folder.is_dir(): return messagebox.showerror(tr('Ordner fehlt'),tr('Bitte den Foxhole-Paks-Ordner auswählen.'))
        self.pending.clear()
        for i in self.tree.get_children(): self.tree.delete(i)
        paths=list(folder.glob('*.pak'))
        paths.extend(Path(k) for k,m in self.data['mods'].items() if m.get('disabled') and Path(k).parent==folder.resolve() and Path(m.get('disabled_path','')).is_file())
        for p in sorted(set(paths)):
            if p.name.lower()=='war-windowsnoeditor.pak': continue
            key=str(p.resolve())
            m=self.data['mods'].setdefault(key,{'source':source(p)})
            m['installed_version']=m.get('installed_version') or version_of(p.name)
            if not m.get('source'):
                candidates=set(source_candidates(p.name,self.data['mods']))
                if len(candidates)==1:
                    m['source']=candidates.pop()
                    m.pop('last_error',None)
            self.tree.insert('', 'end', iid=key, values=(p.name,m.get('installed_version') or tr('Unbekannt'),m.get('available_version') or tr('Unbekannt'),m['source'],m.get('remote',''),tr('Deaktiviert') if m.get('disabled') else tr(m.get('install_status')) or (tr('Bereit') if m['source'] else tr('Quelle fehlt'))),tags=('even',) if len(self.tree.get_children())%2==0 else ())
        self.save()
        self.summary.set(f"{len(self.tree.get_children())}{tr(' MOD-DATEIEN')}")
        self.status.set(f"{len(self.tree.get_children())}{tr(' PAK-Dateien erkannt. Mehrfach installierte Varianten bitte einzeln prüfen.')}")

    def selected(self):
        s=self.tree.selection()
        if not s: messagebox.showinfo(tr('Auswahl'),tr('Bitte eine Mod auswählen.')); return None
        return s[0]

    def explain(self, event=None):
        selected=self.tree.selection()
        if not selected: return
        key=selected[0]
        self.selection_title.set(re.sub(r'^War-WindowsNoEditor_(?:\d+_)?','',Path(key).stem))
        label=self.tree.set(key,'status')
        info=self.data['mods'].get(key,{})
        if label in (tr('Quelle nicht erreichbar (404)'),tr('Quelle fehlt'),tr('Zuordnung erforderlich'),tr('Installation fehlgeschlagen')):
            self.status.set(Path(key).name+' — '+tr(info.get('last_error',label)))
            return
        explanations={
            tr('Abweichender Download'):tr('Eine andere Datei wurde heruntergeladen. „Update installieren“ installiert sie und sichert die alte Version. Andere Bytes bedeuten nicht zwingend eine neuere Version.'),
            tr('Versionsname geändert'):tr('Auf der Mod-Seite steht eine andere Version im Dateinamen. Über „Mod-Seite öffnen“ herunterladen und anschließend „PAK importieren“.'),
            tr('Name gleich · Inhalt ungeprüft'):tr('Der Dateiname passt. Diese Seite gibt den Download erst nach „Download Now“ frei; der Dateiinhalt wurde deshalb noch nicht verglichen. „Mod-Seite öffnen“, herunterladen und „PAK importieren“.'),
            tr('Aktuell (identisch)'):tr('Der heruntergeladene Inhalt ist identisch mit deiner installierten Datei. Keine Installation erforderlich.'),
            tr('Prüfung fehlgeschlagen'):'Fehler: '+info.get('last_error',tr('Bitte diese Datei erneut einzeln prüfen, um den Grund zu ermitteln.')),
        }
        self.status.set(Path(key).name+' — '+explanations.get(label,label))

    def assign(self):
        if self.busy: return
        key=self.selected()
        if not key: return
        u=simpledialog.askstring(tr('Mod-Quelle'),tr('Adresse der Mod-Seite:'),initialvalue=self.data['mods'][key]['source'])
        if u is None: return
        if urllib.parse.urlsplit(u).scheme not in ('http','https'): return messagebox.showerror(tr('Adresse'),tr('Bitte eine HTTP/HTTPS-Adresse eingeben.'))
        self.data['mods'][key]={'source':u}; self.save(); self.scan()

    def open(self):
        key=self.selected()
        if key and self.data['mods'][key]['source']: webbrowser.open(self.data['mods'][key]['source'])

    def ui(self, fn): self.root.after(0,fn)

    def job(self,fn):
        if self.busy: return
        self.data['folder']=self.folder.get()
        self.busy=True
        self.progress.configure(mode='indeterminate',maximum=100,value=0)
        self.progress_text.set(tr('Vorgang läuft …'))
        self.progress.start(12)
        self.folder_entry.state(['disabled'])
        for b in self.buttons+self.folder_buttons: b.state(['disabled'])
        def work():
            try: fn()
            except Exception as e:
                msg=str(e); self.ui(lambda: messagebox.showerror(tr('Vorgang fehlgeschlagen'),msg))
            finally: self.ui(self.done)
        threading.Thread(target=work,daemon=True).start()

    def done(self):
        self.busy=False
        self.progress.stop()
        self.progress_text.set(getattr(self,'batch_progress_summary',None) or tr('Vorgang abgeschlossen'))
        self.batch_progress_summary=None
        self.folder_entry.state(['!disabled'])
        for b in self.buttons+self.folder_buttons: b.state(['!disabled'])
        if getattr(self, 'needs_refresh', False):
            self.needs_refresh=False
            self.scan()
            self.status.set(tr('Update abgeschlossen. Ersetzte alte Dateien und identische Dubletten sind gesichert und aus dem Spielordner entfernt.'))
        if getattr(self,'batch_summary',None):
            self.status.set(self.batch_summary)
            self.batch_summary=None

    def pick(self,files):
        event=threading.Event(); answer=[]
        def dialog():
            w=tk.Toplevel(self.root); w.title(tr('Download-Variante auswählen')); w.geometry('700x360'); w.grab_set()
            w.configure(bg='#10151c')
            ttk.Label(w,text=tr('Welche PAK-Datei gehört zu dieser installierten Mod?')).pack(pady=12)
            box=tk.Listbox(w,bg='#19212c',fg='#e8edf4',selectbackground='#254b49',selectforeground='#bafbe4',borderwidth=0,highlightthickness=0,font=('Segoe UI',11)); box.pack(fill='both',expand=True,padx=12)
            for _,name in files: box.insert('end',name)
            def finish():
                if box.curselection(): answer.append(files[box.curselection()[0]][0])
                w.destroy(); event.set()
            ttk.Button(w,text=tr('Auswählen'),command=finish).pack(pady=12)
            w.protocol('WM_DELETE_WINDOW',lambda:(w.destroy(),event.set()))
        self.ui(dialog); event.wait(); return answer[0] if answer else None

    def fetch(self,key):
        m=self.data['mods'][key]; url=m['source']
        if m.get('disabled'): raise NameOnlyResult(tr('Deaktiviert'))
        if not url: raise NameOnlyResult(tr('Quelle fehlt'))
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        opener.addheaders=[('User-Agent','FoxholeModUpdater/1.0')]
        if (urllib.parse.urlsplit(url).hostname or '').endswith('.itch.io'):
            page=opener.open(url,timeout=30).read().decode('utf-8')
            files=re.findall(r'data-upload_id="(\d+)".*?class="name"[^>]*>(.*?)</strong>',page,re.S)
            files=[(i,html.unescape(re.sub('<[^>]+>','',n))) for i,n in files if n.lower().endswith('.pak')]
            # Free/name-your-own-price pages expose upload IDs on a generated
            # download page, reached by the same action as "No thanks".
            if not files and re.search(r'"min_price"\s*:\s*0\s*[,}]',page):
                token=re.search(r'name="csrf_token"\s+value="([^"]+)"',page)
                if token:
                    req=urllib.request.Request(url.rstrip('/')+'/download_url',
                        data=urllib.parse.urlencode({'csrf_token':html.unescape(token[1])}).encode(),
                        headers={'Referer':url,'Accept':'application/json'})
                    reply=json.loads(opener.open(req,timeout=30).read())
                    download_page=reply.get('url')
                    if download_page:
                        parsed=urllib.parse.urlsplit(urllib.parse.urljoin(url,download_page))
                        if parsed.scheme!='https' or parsed.hostname!=urllib.parse.urlsplit(url).hostname:
                            raise ValueError(tr('Unerwartete Adresse der itch.io-Downloadseite.'))
                        page=opener.open(parsed.geturl(),timeout=30).read().decode('utf-8')
                        files=re.findall(r'data-upload_id="(\d+)".*?class="name"[^>]*>(.*?)</strong>',page,re.S)
                        files=[(i,html.unescape(re.sub('<[^>]+>','',n))) for i,n in files if n.lower().endswith('.pak')]
            if not files:
                names = re.findall(r'class="name"[^>]*>(.*?)</strong>', page, re.S)
                names = [html.unescape(re.sub('<[^>]+>','',n)) for n in names]
                visible = [(None,n) for n in names if n.lower().endswith('.pak')]
                matched = match_file(Path(key).name, visible)
                if matched:
                    m['remote'] = matched[1]
                    self.ui(lambda k=key,n=matched[1]:self.tree.set(k,'remote',n))
                    label = tr('Name gleich · Inhalt ungeprüft') if mod_name(Path(key).name)==mod_name(matched[1]) else tr('Versionsname geändert')
                    raise NameOnlyResult(label)
                raise NameOnlyResult(tr('Zuordnung erforderlich'))
            matched = match_file(Path(key).name, files)
            ident=matched[0] if matched else m.get('upload')
            if ident not in [i for i,n in files]:
                ident=matched[0] if matched else self.pick(files)
            if not ident: raise ValueError(tr('Auswahl abgebrochen.'))
            remote = next(n for i,n in files if i==ident)
            m['remote'] = remote
            m['available_version']=version_of(remote)
            comparison=version_compare(m.get('installed_version') or version_of(key),m['available_version'])
            if comparison is not None and comparison<0:
                raise NameOnlyResult(tr('Älterer Download · übersprungen'))
            self.ui(lambda k=key,n=remote:self.tree.set(k,'remote',n))
            self.ui(lambda k=key,v=m['available_version']:self.tree.set(k,'available',v or tr('Unbekannt')))
            token=re.search(r'name="csrf_token"\s+value="([^"]+)"',page)
            if not token: raise ValueError(tr('Downloadformular nicht erkannt.'))
            req=urllib.request.Request(url.rstrip('/')+'/file/'+ident,data=urllib.parse.urlencode({'csrf_token':html.unescape(token[1])}).encode(),headers={'Referer':url,'Accept':'application/json'})
            reply=json.loads(opener.open(req,timeout=30).read())
            url=reply.get('url')
            if not url: raise ValueError(tr('itch.io hat keinen Download freigegeben. Bitte über die Mod-Seite herunterladen.'))
            m['upload']=ident
        cache=BASE/'cache'; cache.mkdir(exist_ok=True)
        fd,name=tempfile.mkstemp(suffix='.pak',dir=cache); os.close(fd); dest=Path(name)
        try:
            with opener.open(url,timeout=60) as response, dest.open('wb') as f:
                actual_name=download_filename(response.headers)
                if actual_name:
                    m['remote']=actual_name
                    m['available_version']=version_of(actual_name)
                    self.ui(lambda k=key,n=actual_name:self.tree.set(k,'remote',n))
                    self.ui(lambda k=key,v=m['available_version']:self.tree.set(k,'available',v or tr('Unbekannt')))
                try: total=int(response.headers.get('Content-Length','0'))
                except (ValueError,TypeError): total=0
                self.ui(lambda k=key,t=total:self.download_progress(k,0,t))
                size=0
                last_report=0
                while True:
                    b=response.read(1024*1024)
                    if not b: break
                    size+=len(b)
                    if size>1024**3: raise ValueError(tr('Download überschreitet 1 GB.'))
                    f.write(b)
                    now=time.monotonic()
                    if now-last_report>=0.15:
                        self.ui(lambda k=key,s=size,t=total:self.download_progress(k,s,t))
                        last_report=now
                self.ui(lambda k=key,s=size,t=total:self.download_progress(k,s,t,True))
            valid_pak(dest)
            if digest(dest)==digest(key) and (not m.get('remote') or Path(key).name==m['remote']):
                dest.unlink(); return None
            return dest
        except Exception:
            dest.unlink(missing_ok=True); raise

    def download_progress(self,key,size,total,complete=False):
        if total>0:
            self.progress.stop()
            self.progress.configure(mode='determinate',maximum=total,value=min(size,total))
            progress=f'{min(100,size/total*100):.0f}% · {size/1024**2:.1f} / {total/1024**2:.1f} MB'
        else:
            if str(self.progress.cget('mode'))!='indeterminate':
                self.progress.configure(mode='indeterminate'); self.progress.start(12)
            progress=f'{size/1024**2:.1f} MB geladen · Gesamtgröße unbekannt'
        if complete: progress=f'Download abgeschlossen · {size/1024**2:.1f} MB · Inhalt wird verglichen'
        self.progress_text.set(f'{getattr(self,"check_position","")} Download · {Path(key).name} · {progress}')

    def check(self,all=False):
        keys=list(self.tree.get_children()) if all else [self.selected()]
        keys=[k for k in keys if k]
        def work():
            for index,key in enumerate(keys,1):
                self.check_position=f'[{index}/{len(keys)}]'
                self.ui(lambda k=key,i=index:self.check_progress(k,i,len(keys)))
                self.ui(lambda k=key:self.status.set(tr('Prüfe ')+Path(k).name))
                try:
                    old=self.pending.pop(key,None)
                    if old: old.unlink(missing_ok=True)
                    p=self.fetch(key)
                    if p: self.pending[key]=p
                    label=tr('Abweichender Download') if p else tr('Aktuell (identisch)')
                    self.data['mods'][key].pop('last_error',None)
                except NameOnlyResult as e:
                    label=str(e)
                    self.data['mods'][key].pop('last_error',None)
                    if label==tr('Quelle fehlt'): self.data['mods'][key]['last_error']=tr('Bitte über „Quelle zuordnen“ eine Mod-Seite hinterlegen.')
                    if label==tr('Zuordnung erforderlich'): self.data['mods'][key]['last_error']=tr('Die Seite ist erreichbar, aber es gibt keinen eindeutig passenden PAK-Dateinamen. Über „Mod-Seite öffnen“ die richtige Variante prüfen.')
                    self.ui(lambda:self.status.set(tr('Dateiname verglichen. Download erst über „Mod-Seite öffnen“ freigeben, anschließend PAK importieren.')))
                except urllib.error.HTTPError as e:
                    label=tr('Quelle nicht erreichbar (404)') if e.code==404 else tr('Prüfung fehlgeschlagen')
                    reason=(tr('Die Mod-Seite oder der Download ist derzeit nicht erreichbar (404). Die installierte Mod bleibt erhalten.') if e.code==404 else f"{tr('Der Server antwortet mit HTTP ')}{e.code}{tr('. Die installierte Mod bleibt erhalten.')}")
                    self.data['mods'][key]['last_error']=reason+tr(' Adresse: ')+e.url
                    self.ui(lambda k=key,msg=reason:self.status.set(Path(k).name+' — '+msg))
                except Exception as e:
                    label=tr('Prüfung fehlgeschlagen')
                    self.data['mods'][key]['last_error']=str(e)
                    self.ui(lambda msg=str(e):self.status.set(msg))
                self.ui(lambda k=key,s=label:self.tree.set(k,'status',s))
            self.save()
        if keys: self.job(work)

    def check_progress(self,key,index,total):
        self.progress.stop()
        self.progress.configure(mode='indeterminate',maximum=100,value=0)
        self.progress.start(12)
        self.progress_text.set(f"{tr('Prüfung ')}{index}{tr(' von ')}{total} · {Path(key).name} · Mod-Seite abrufen")

    def replace(self,key,path,new_name=None):
        protect_game_file(key)
        protect_game_file(path)
        if game_running_for(key): raise ValueError(tr('Bitte Foxhole vor der Installation schließen.'))
        valid_pak(path)
        old=Path(key).resolve()
        if self.data['mods'][key].get('disabled'): raise ValueError(tr('Bitte Mod zuerst aktivieren.'))
        comparison=version_compare(self.data['mods'][key].get('installed_version') or version_of(key),version_of(new_name or path.name))
        if comparison is not None and comparison<0: raise ValueError(tr('Eine ältere Version wird nicht als Update installiert.'))
        new_name=new_name or old.name
        if (Path(new_name).name!=new_name or any(c in new_name for c in '/\\:')
                or not new_name.lower().endswith('.pak') or new_name.lower()=='war-windowsnoeditor.pak'):
            raise ValueError(tr('Ungültiger Mod-Dateiname.'))
        target=(old.parent/new_name).resolve()
        protect_game_file(target)
        if target.parent!=old.parent: raise ValueError(tr('Ziel liegt außerhalb des Paks-Ordners.'))
        old_hash=digest(old)
        source_url=self.data['mods'].get(key,{}).get('source')
        obsolete=[old]
        for other,info in self.data['mods'].items():
            candidate=Path(other).resolve()
            if candidate.name.casefold()=='war-windowsnoeditor.pak': continue
            if (candidate!=old and candidate.parent==old.parent and candidate.is_file()
                    and source_url and info.get('source')==source_url
                    and (mod_name(candidate.name,True)==mod_name(old.name,True) or digest(candidate)==old_hash)):
                obsolete.append(candidate)
        if target.exists() and target not in obsolete:
            raise ValueError(tr('Der neue Dateiname ist bereits belegt. Diese Datei wird nicht überschrieben.'))
        for item in obsolete:
            previous=self.data['mods'].get(str(item),{}).get('installed_version') or version_of(item.name)
            comparison=version_compare(previous,version_of(new_name) or version_of(path.name))
            if comparison is not None and comparison<0: raise ValueError(tr('Eine bereits installierte neuere Variante würde ersetzt. Update abgebrochen.'))
        new_key=str(target)
        backup=BASE/'backups'/hashlib.sha256(new_key.encode()).hexdigest()[:16]
        backup.mkdir(parents=True,exist_ok=True)
        stamp=time.strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns())
        bundle=backup/stamp; bundle.mkdir()
        for item in obsolete: shutil.copy2(item,bundle/item.name)
        (bundle/'transaction.json').write_text(json.dumps({'installed':new_name,'old':[p.name for p in obsolete],'folder':str(old.parent),'source':source_url,'created':time.strftime('%Y-%m-%d %H:%M:%S'),'old_versions':{p.name:self.data['mods'].get(str(p),{}).get('installed_version') or version_of(p.name) for p in obsolete}},indent=2),encoding='utf-8')
        fd,name=tempfile.mkstemp(prefix='.mod-update-',dir=target.parent); os.close(fd)
        try:
            shutil.copyfile(path,name)
            if game_running_for(key): raise ValueError(tr('Foxhole wurde gestartet. Installation abgebrochen.'))
            os.replace(name,target)
            for item in obsolete:
                if item!=target: item.unlink()
        except Exception:
            for item in obsolete: shutil.copy2(bundle/item.name,item)
            if target not in obsolete: target.unlink(missing_ok=True)
            raise
        finally: Path(name).unlink(missing_ok=True)
        info=dict(self.data['mods'][key]); info['last_backup']=str(bundle); info['install_status']=tr('Installiert · gesichert')
        info['installed_version']=version_of(new_name) or version_of(path.name) or info.get('installed_version')
        for item in obsolete: self.data['mods'].pop(str(item),None)
        self.data['mods'][new_key]=info
        self.save()
        self.needs_refresh=True

    def restore_transaction(self,key,bundle):
        protect_game_file(key)
        if game_running_for(key): raise ValueError(tr('Bitte Foxhole vor der Wiederherstellung schließen.'))
        target=Path(key).resolve()
        manifest=json.loads((bundle/'transaction.json').read_text(encoding='utf-8'))
        originals=manifest['old']
        if not originals: raise ValueError(tr('Leere Sicherung.'))
        if manifest.get('folder') and Path(manifest['folder']).resolve()!=target.parent: raise ValueError(tr('Diese Sicherung gehört zu einem anderen Spiel- oder Testordner.'))
        for name in originals:
            if Path(name).name!=name or any(c in name for c in '/\\:'): raise ValueError(tr('Ungültige Sicherung.'))
            valid_pak(bundle/name)
            destination=(target.parent/name).resolve()
            protect_game_file(destination)
            if destination.parent!=target.parent: raise ValueError(tr('Ungültiger Sicherungspfad.'))
            if destination!=target and destination.exists(): raise ValueError(tr('Eine wiederherzustellende Datei existiert bereits: ')+name)
        safety=bundle/('before-restore-'+str(time.time_ns())+'.pak')
        shutil.copy2(target,safety)
        restored=[]
        try:
            for name in originals:
                destination=target.parent/name
                fd,temp=tempfile.mkstemp(prefix='.mod-restore-',dir=target.parent); os.close(fd)
                try:
                    shutil.copyfile(bundle/name,temp)
                    if game_running_for(key): raise ValueError(tr('Foxhole wurde gestartet. Wiederherstellung abgebrochen.'))
                    os.replace(temp,destination); restored.append(destination)
                finally: Path(temp).unlink(missing_ok=True)
            if target.name not in originals: target.unlink()
        except Exception:
            for destination in restored:
                if destination!=target: destination.unlink(missing_ok=True)
            shutil.copy2(safety,target)
            raise
        info=dict(self.data['mods'].pop(key)); info.pop('last_backup',None)
        for name in originals:
            restored_info=dict(info); restored_info['installed_version']=manifest.get('old_versions',{}).get(name) or version_of(name); restored_info['install_status']='Wiederhergestellt'
            self.data['mods'][str(target.parent/name)]=restored_info
        self.save(); self.needs_refresh=True

    def install(self):
        key=self.selected()
        if not key: return
        p=self.pending.get(key)
        if not p: return messagebox.showinfo('Update',tr('Zuerst Update prüfen oder eine PAK importieren.'))
        self.preview_updates([(key,p)],lambda:self.job(lambda:self.replace(key,p,self.data['mods'][key].get('remote'))))

    def install_all(self):
        if self.busy: return
        # Snapshot the verified downloads. Replacement can remove duplicate keys.
        updates=list(self.pending.items())
        if not updates:
            self.status.set(tr('Keine heruntergeladenen Updates bereit. Zuerst „Alle auf Updates prüfen“ anklicken. Ungeprüfte Inhalte werden nicht installiert.'))
            return
        def work():
            if any(game_running_for(key) for key,path in updates): raise ValueError(tr('Bitte Foxhole vor der Installation schließen.'))
            total=len(updates)
            self.ui(lambda:self.begin_install_progress(updates))
            installed=0; skipped=0; errors=[]
            processed=0
            for index,(key,path) in enumerate(updates,1):
                if key not in self.data['mods'] or not Path(key).is_file():
                    skipped+=1; self.pending.pop(key,None)
                    processed=index
                    self.ui(lambda k=key,i=index:self.install_progress(k,i,total,tr('Dublette übersprungen'),True))
                    continue
                self.ui(lambda k=key,i=index:self.install_progress(k,i,total,tr('Wird installiert …')))
                try:
                    self.replace(key,path,self.data['mods'][key].get('remote'))
                    installed+=1
                    self.pending.pop(key,None)
                    self.ui(lambda k=key,i=index:self.install_progress(k,i,total,tr('Installiert · gesichert'),True))
                except Exception as e:
                    errors.append(Path(key).name+': '+str(e))
                    self.data['mods'][key]['install_status']=tr('Installation fehlgeschlagen')
                    self.data['mods'][key]['last_error']=str(e)
                    self.ui(lambda k=key,i=index:self.install_progress(k,i,total,tr('Installation fehlgeschlagen'),True))
                    processed=index
                    if game_running_for(key): break
                processed=index
            summary=f'{installed} Updates installiert · {skipped} bereits ersetzte Dubletten übersprungen · {len(errors)} Fehler.'
            if processed<total: summary+=f' {total-processed} Updates nicht ausgeführt.'
            if errors: summary+=' '+ ' | '.join(errors)
            self.save()
            self.batch_summary=summary
            self.batch_progress_summary=f"{processed}{tr(' von ')}{total} bearbeitet · {installed} installiert · {len(errors)} Fehler"
            self.ui(lambda:self.status.set(summary))
        self.preview_updates(updates,lambda:self.job(work))

    def begin_install_progress(self,updates):
        self.progress.stop()
        self.progress.configure(mode='determinate',maximum=len(updates),value=0)
        for key,path in updates:
            if self.tree.exists(key): self.tree.set(key,'status',tr('Wartet auf Installation'))
        self.progress_text.set(f'0 von {len(updates)} bearbeitet')

    def install_progress(self,key,index,total,label,complete=False):
        if self.tree.exists(key):
            self.tree.set(key,'status',label)
            self.tree.see(key)
        self.progress.configure(value=index if complete else index-1)
        self.progress_text.set(f"Mod {index}{tr(' von ')}{total} · {label} · {Path(key).name}")
        self.status.set(f'{label}: {Path(key).name}')

    def local(self):
        key=self.selected()
        if not key: return
        p=filedialog.askopenfilename(title=tr('Heruntergeladene PAK auswählen'),filetypes=[('Unreal PAK','*.pak')])
        if p and messagebox.askyesno('Import',f"{Path(key).name}{tr(' durch ')}{Path(p).name}{tr(' ersetzen?')}"):
            self.job(lambda:self.replace(key,Path(p),Path(p).name))

    def preview_updates(self,updates,proceed):
        if self.busy: return
        w=tk.Toplevel(self.root); w.title(tr('Updateübersicht')); w.configure(bg='#10151c'); w.grab_set()
        width=min(1050,max(480,w.winfo_screenwidth()-100))
        height=min(650,max(380,w.winfo_screenheight()-150))
        w.geometry(f'{width}x{height}+{max(0,(w.winfo_screenwidth()-width)//2)}+{max(0,(w.winfo_screenheight()-height)//2-35)}')
        w.minsize(min(600,width),min(380,height))
        w.columnconfigure(0,weight=1); w.rowconfigure(1,weight=1)
        ttk.Label(w,text=tr('Diese Dateien werden aktualisiert'),font=('Segoe UI',18,'bold')).grid(row=0,column=0,sticky='w',padx=20,pady=18)
        body=ttk.Frame(w); body.grid(row=1,column=0,sticky='nsew',padx=20)
        body.columnconfigure(0,weight=1); body.rowconfigure(0,weight=1)
        box=tk.Text(body,bg='#19212c',fg='#e8edf4',wrap='word',font=('Segoe UI',11),borderwidth=0,height=8)
        box.grid(row=0,column=0,sticky='nsew')
        scrollbar=ttk.Scrollbar(body,orient='vertical',command=box.yview)
        scrollbar.grid(row=0,column=1,sticky='ns'); box.configure(yscrollcommand=scrollbar.set)
        consumed=set()
        for key,path in updates:
            if key in consumed or key not in self.data['mods'] or not Path(key).exists(): continue
            info=self.data['mods'][key]; new=info.get('remote') or Path(key).name
            oldhash=digest(key)
            removed=[k for k,m in self.data['mods'].items() if Path(k).parent==Path(key).parent and Path(k).is_file() and not m.get('disabled') and m.get('source')==info.get('source') and (mod_name(k,True)==mod_name(key,True) or digest(k)==oldhash) and Path(k).name.casefold()!='war-windowsnoeditor.pak']
            consumed.update(removed)
            box.insert('end',f"{info.get('installed_version') or 'Unbekannt'} → {info.get('available_version') or version_of(new) or 'Unbekannt'}\nNEU: {new}\nSICHERN / ERSETZEN:\n"+'\n'.join('  '+Path(k).name for k in removed)+'\n\n')
        box.configure(state='disabled')
        row=ttk.Frame(w,padding=16); row.grid(row=2,column=0,sticky='ew')
        ttk.Label(row,text=tr('Alle ersetzten Dateien werden gesichert.')).pack(anchor='w',pady=(0,10))
        ttk.Button(row,text=tr('Abbrechen'),command=w.destroy).pack(side='right')
        ttk.Button(row,text=tr('Updates jetzt installieren'),style='Accent.TButton',command=lambda:(w.destroy(),proceed())).pack(side='right',padx=10)

    def toggle(self):
        if self.busy: return
        key=self.selected()
        if not key: return
        def work():
            protect_game_file(key)
            if game_running_for(key): raise ValueError(tr('Bitte Foxhole zuerst schließen.'))
            m=self.data['mods'][key]; original=Path(key).resolve()
            if m.get('disabled'):
                stored=Path(m['disabled_path']).resolve()
                expected=BASE/'disabled'/hashlib.sha256(key.encode()).hexdigest()[:16]/original.name
                if stored!=expected.resolve(): raise ValueError(tr('Ungültiger Speicherort der deaktivierten Mod.'))
                protect_game_file(stored); valid_pak(stored)
                if original.exists(): raise ValueError(tr('Der Dateiname im Spielordner ist bereits belegt.'))
                shutil.copy2(stored,original)
                if digest(original)!=digest(stored): original.unlink(); raise ValueError(tr('Dateiprüfung fehlgeschlagen.'))
                stored.unlink(); m['disabled']=False; m.pop('disabled_path',None)
            else:
                valid_pak(original)
                stored=BASE/'disabled'/hashlib.sha256(key.encode()).hexdigest()[:16]/original.name
                stored.parent.mkdir(parents=True,exist_ok=True)
                if stored.exists(): raise ValueError(tr('Es liegt bereits eine deaktivierte Datei vor.'))
                shutil.copy2(original,stored)
                if digest(original)!=digest(stored): raise ValueError(tr('Dateiprüfung fehlgeschlagen.'))
                if game_running_for(key): raise ValueError(tr('Foxhole wurde gestartet.'))
                original.unlink(); m['disabled']=True; m['disabled_path']=str(stored)
            m.pop('install_status',None); self.pending.pop(key,None); self.save(); self.needs_refresh=True
        self.job(work)

    def find_sources(self):
        if self.busy: return
        key=self.selected()
        if not key: return
        w=tk.Toplevel(self.root); w.title(tr('Quellen finden')); w.geometry('850x350'); w.configure(bg='#10151c'); w.grab_set()
        ttk.Label(w,text=tr('Passende bekannte Quellen'),font=('Segoe UI',16,'bold')).pack(anchor='w',padx=18,pady=18)
        candidates=source_candidates(key,self.data['mods'])
        box=tk.Listbox(w,bg='#19212c',fg='#e8edf4',selectbackground='#254b49',font=('Segoe UI',11),borderwidth=0)
        box.pack(fill='both',expand=True,padx=18)
        for url in candidates: box.insert('end',url)
        if candidates: box.selection_set(0)
        def use():
            if not box.curselection(): return
            self.data['mods'][key]['source']=candidates[box.curselection()[0]]
            self.data['mods'][key].pop('upload',None); self.save(); w.destroy(); self.scan()
        row=ttk.Frame(w,padding=18); row.pack(fill='x')
        ttk.Button(row,text=tr('Quelle übernehmen'),command=use).pack(side='left')
        query=mod_name(key,True).removesuffix('.pak').replace('_',' ')
        for domain,title in [('itch.io',tr('Auf itch.io suchen')),('nexusmods.com/foxhole',tr('Auf Nexus suchen'))]:
            url='https://www.bing.com/search?'+urllib.parse.urlencode({'q':'Foxhole '+query+' site:'+domain})
            ttk.Button(row,text=title,command=lambda u=url:webbrowser.open(u)).pack(side='left',padx=8)

    def backup_manager(self):
        if self.busy: return
        w=tk.Toplevel(self.root); w.title(tr('Sicherungen verwalten')); w.geometry('1100x600'); w.configure(bg='#10151c')
        ttk.Label(w,text=tr('Sicherungen · aktueller Spielordner'),font=('Segoe UI',18,'bold')).pack(anchor='w',padx=20,pady=20)
        tree=ttk.Treeview(w,columns=('date','mod','version','size'),show='headings',selectmode='browse')
        for col,label,width in [('date',tr('DATUM'),180),('mod','MOD',450),('version',tr('GESICHERTE VERSION'),190),('size',tr('GRÖSSE'),100)]: tree.heading(col,text=label); tree.column(col,width=width)
        tree.pack(fill='both',expand=True,padx=20)
        bundles={}
        def reload():
            for item in tree.get_children(): tree.delete(item)
            bundles.clear()
            for manifest_path in sorted((BASE/'backups').glob('*/*/transaction.json'),reverse=True):
                try:
                    m=json.loads(manifest_path.read_text(encoding='utf-8'))
                    if m.get('folder') and Path(m['folder']).resolve()!=Path(self.folder.get()).resolve(): continue
                    bundle=manifest_path.parent; bundles[str(bundle)]=m
                    size=sum(p.stat().st_size for p in bundle.glob('*.pak'))/1024**2
                    versions=', '.join(sorted(set(v or tr('Unbekannt') for v in m.get('old_versions',{}).values()))) or tr('Unbekannt')
                    tree.insert('','end',iid=str(bundle),values=(m.get('created',bundle.name[:15]),m['installed'],versions,f'{size:.1f} MB'))
                except (OSError,ValueError,KeyError): continue
        def restore_selected():
            if self.busy or not tree.selection(): return
            bundle=Path(tree.selection()[0]); m=bundles[str(bundle)]
            candidates=[k for k,info in self.data['mods'].items() if Path(k).parent==Path(self.folder.get()).resolve() and Path(k).is_file() and mod_name(k,True)==mod_name(m['installed'],True)]
            if len(candidates)!=1: return messagebox.showinfo(tr('Wiederherstellung'),tr('Aktuelle Datei nicht eindeutig erkannt. Bitte Mod-Dateien und Dubletten prüfen.'),parent=w)
            key=candidates[0]
            w.destroy(); self.job(lambda:self.restore_transaction(key,bundle))
        def remove_selected():
            if self.busy or not tree.selection(): return
            bundle=Path(tree.selection()[0]).resolve()
            if (BASE/'backups').resolve() not in bundle.parents: raise ValueError(tr('Ungültiger Sicherungspfad.'))
            if messagebox.askyesno(tr('Sicherung löschen'),tr('Diese Sicherung dauerhaft löschen?'),parent=w):
                shutil.rmtree(bundle)
                for m in self.data['mods'].values():
                    if m.get('last_backup')==str(bundle): m.pop('last_backup',None)
                self.save(); reload()
        row=ttk.Frame(w,padding=20); row.pack(fill='x')
        ttk.Button(row,text=tr('Ausgewählte Sicherung wiederherstellen'),command=restore_selected).pack(side='left')
        ttk.Button(row,text=tr('Ausgewählte Sicherung löschen'),command=remove_selected).pack(side='left',padx=10)
        (BASE/'backups').mkdir(exist_ok=True)
        ttk.Button(row,text=tr('Sicherungsordner öffnen'),command=lambda:os.startfile(str(BASE/'backups'))).pack(side='left')
        reload()

    def restore(self):
        key=self.selected()
        if not key: return
        bundle=self.data['mods'][key].get('last_backup')
        if bundle:
            self.job(lambda:self.restore_transaction(key,Path(bundle)))
            return
        folder=BASE/'backups'/hashlib.sha256(key.encode()).hexdigest()[:16]
        files=sorted(folder.glob('*.pak'))
        if not files: return messagebox.showinfo(tr('Sicherung'),tr('Für diese Datei gibt es noch keine Sicherung.'))
        p=filedialog.askopenfilename(title=tr('Sicherung auswählen'),initialdir=folder,filetypes=[(tr('PAK-Sicherung'),'*.pak')])
        if p and messagebox.askyesno(tr('Wiederherstellen'),tr('Ausgewählte Sicherung installieren?')):
            self.job(lambda:self.replace(key,Path(p)))

if __name__=='__main__':
    root=tk.Tk(); ttk.Style().theme_use('clam')
    if '--smoke-test' in sys.argv:
        root.withdraw()
        root.update()
        result={'tk':True,'frozen':bool(getattr(sys,'frozen',False)),'base':str(BASE),'version_check':version_compare('5.1','7.1')==1}
        Path(sys.argv[sys.argv.index('--smoke-test')+1]).write_text(json.dumps(result),encoding='utf-8')
        root.destroy()
    else:
        try:
            import msvcrt
            lock_handle=open(BASE/'updater.lock','a+b')
            lock_handle.seek(0)
            if not lock_handle.read(1): lock_handle.write(b'0'); lock_handle.flush()
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            root.withdraw(); messagebox.showinfo(tr('Bereits geöffnet'),tr('Dieser Updater ist bereits geöffnet oder der Programmordner ist nicht beschreibbar.')); root.destroy(); sys.exit(1)
        App(root); root.mainloop()
