"""Local settings and Tk interface for Clipboard Collector."""
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from strings import TEXT, translate_error

VERSION = '1.2.3'
SETTINGS_PATH = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ClipboardCollector' / 'phase2-preview-settings.json'
DEFAULTS = {'source': 'browser', 'save': 'manual', 'mode': 0,
            'hotkey_enabled': False, 'hotkey_mods': 0, 'hotkey_vk': 0x77, 'hotkey_name': 'F8',
            'extra_modes': [], 'images': False}


def load_settings():
    import ctypes
    settings = dict(DEFAULTS)
    settings['language'] = 'KO' if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3ff == 0x12 else 'EN'
    try:
        path = SETTINGS_PATH if SETTINGS_PATH.exists() else SETTINGS_PATH.with_name('preview-settings.json')
        saved = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(saved, dict):
            return settings
        for key, choices in [('source', ('browser', 'all')), ('save', ('manual', 'each', 'stop')), ('language', ('KO', 'EN'))]:
            if saved.get(key) in choices:
                settings[key] = saved[key]
        for key, low, high in [('mode', 0, 4), ('hotkey_mods', 0, 15), ('hotkey_vk', 1, 254)]:
            value = saved.get(key)
            if type(value) is int and low <= value <= high:
                settings[key] = value
        if type(saved.get('hotkey_enabled')) is bool:
            settings['hotkey_enabled'] = saved['hotkey_enabled']
        if type(saved.get('images')) is bool:
            settings['images'] = saved['images']
        if isinstance(saved.get('extra_modes'), list):
            settings['extra_modes'] = sorted({
                mode for mode in saved['extra_modes']
                if type(mode) is int and 0 <= mode <= 4 and mode != settings['mode']
            })
        if isinstance(saved.get('hotkey_name'), str) and 0 < len(saved['hotkey_name']) < 80:
            settings['hotkey_name'] = saved['hotkey_name']
    except (OSError, ValueError):
        pass
    return settings


def save_settings(settings):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=SETTINGS_PATH.parent, delete=False) as file:
        temporary = Path(file.name)
        json.dump(settings, file, ensure_ascii=False, indent=2)
    try:
        temporary.replace(SETTINGS_PATH)
    finally:
        temporary.unlink(missing_ok=True)


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text = widget, text
        self.timer = None
        self.popup = None
        widget.bind('<Enter>', self.schedule, add='+')
        widget.bind('<Leave>', self.hide, add='+')
        widget.bind('<ButtonPress>', self.hide, add='+')
        widget.bind('<Destroy>', self.hide, add='+')

    def schedule(self, event=None):
        self.hide()
        self.timer = self.widget.after(500, self.show)

    def show(self):
        self.timer = None
        self.popup = tk.Toplevel(self.widget)
        self.popup.wm_overrideredirect(True)
        self.popup.attributes('-topmost', True)
        x = min(self.widget.winfo_pointerx() + 12, max(0, self.widget.winfo_screenwidth() - 370))
        y = min(self.widget.winfo_pointery() + 20, max(0, self.widget.winfo_screenheight() - 110))
        self.popup.geometry(f'+{x}+{y}')
        tk.Label(self.popup, text=self.text(), wraplength=340, justify='left',
                 bg='#fff8d6', fg='#202020', padx=10, pady=7).pack()

    def hide(self, event=None):
        if self.timer:
            self.widget.after_cancel(self.timer)
            self.timer = None
        if self.popup:
            self.popup.destroy()
            self.popup = None


class Application:
    def __init__(self, root, collector, events, settings):
        self.root, self.collector, self.events = root, collector, events
        self.settings = settings
        self.active = False
        self.pending = True
        self.closing = False
        self.count = 0
        self.destination = ''
        self.totals = ''
        self.notice = ('ready', {})
        self.bindings = []
        self.tooltips = []
        root.title(f'Clipboard Collector v{VERSION}')
        root.geometry('760x740')
        root.minsize(720, 710)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', font=('Malgun Gothic', 10))
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        top = ttk.Frame(frame)
        top.pack(fill='x')
        ttk.Label(top, text='Clipboard Collector', font=('Malgun Gothic', 17, 'bold')).pack(side='left')
        ttk.Label(top, text='언어 / Language').pack(side='right', padx=6)
        self.language = tk.StringVar(value=settings['language'])
        lang = ttk.Combobox(top, values=('KO', 'EN'), textvariable=self.language, state='readonly', width=5)
        lang.pack(side='right')
        lang.bind('<<ComboboxSelected>>', self.change_language)
        self.tip(lang, 'tip_language')
        self.label(frame, 'subtitle').pack(anchor='w', pady=(6, 12))
        self.label(frame, 'target').pack(anchor='w')
        self.mode = ttk.Combobox(frame, state='readonly')
        self.mode.pack(fill='x', pady=(4, 10))
        self.mode.bind('<<ComboboxSelected>>', self.change_options)
        self.tip(self.mode, 'tip_target')
        extras = self.group(frame, 'extra_targets')
        self.extra_vars = [tk.BooleanVar(value=i in settings['extra_modes']) for i in range(5)]
        self.extra_buttons = []
        for variable in self.extra_vars:
            button = ttk.Checkbutton(extras, variable=variable, command=self.change_options)
            button.pack(side='left', padx=(0, 9))
            self.tip(button, 'tip_extra_targets')
            self.extra_buttons.append(button)
        sources = self.group(frame, 'source')
        self.source = tk.StringVar(value=settings['source'])
        self.source_buttons = [self.radio(sources, key, self.source, key, 'tip_' + key) for key in ('browser', 'all')]
        self.images = tk.BooleanVar(value=settings['images'])
        self.image_button = self.bind_text(
            ttk.Checkbutton(sources, variable=self.images, command=self.change_options), 'images'
        )
        self.image_button.pack(side='left', padx=8)
        self.tip(self.image_button, 'tip_images')
        saving = self.group(frame, 'save')
        self.saving = tk.StringVar(value=settings['save'])
        self.save_buttons = [self.radio(saving, key, self.saving, key, 'tip_' + key) for key in ('each', 'stop', 'manual')]
        self.label(frame, 'save_note', wraplength=700, foreground='#7d4a14').pack(fill='x', pady=(4, 10))
        shortcuts = ttk.Frame(frame)
        shortcuts.pack(fill='x', pady=(0, 5))
        self.hotkey = tk.BooleanVar(value=settings['hotkey_enabled'])
        toggle = ttk.Checkbutton(shortcuts, variable=self.hotkey, command=self.change_hotkey)
        self.bind_text(toggle, 'hotkey')
        toggle.pack(side='left')
        self.tip(toggle, 'tip_hotkey')
        change = ttk.Button(shortcuts, command=self.capture_shortcut)
        self.bind_text(change, 'change')
        change.pack(side='right')
        self.tip(change, 'tip_change')
        self.key_label = ttk.Label(frame)
        self.key_label.pack(anchor='w', pady=(0, 12))
        self.state_label = ttk.Label(frame, font=('Malgun Gothic', 13, 'bold'))
        self.state_label.pack(anchor='w')
        self.target_label = ttk.Label(frame, wraplength=700)
        self.target_label.pack(fill='x', pady=5)
        self.count_label = ttk.Label(frame)
        self.count_label.pack(anchor='w')
        self.totals_label = ttk.Label(frame, wraplength=690)
        self.totals_label.pack(fill='x')
        self.notice_label = ttk.Label(frame, wraplength=700, justify='left')
        self.notice_label.pack(fill='x', pady=8)
        actions = ttk.Frame(frame)
        actions.pack(fill='x', side='bottom')
        self.transfer_button = self.bind_text(ttk.Button(actions, command=self.transfer_text), 'transfer')
        self.transfer_button.pack(side='right', padx=(8, 0), ipady=7)
        self.tip(self.transfer_button, 'tip_transfer')
        self.button = ttk.Button(actions, command=self.toggle)
        self.button.pack(fill='x', expand=True, side='left', ipady=7)
        self.tip(self.button, 'tip_toggle')
        self.render()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(50, self.poll)

    def tr(self, message_key, **values):
        return TEXT[message_key][0 if self.settings['language'] == 'KO' else 1].format(**values)

    def bind_text(self, widget, key):
        self.bindings.append((widget, key))
        return widget

    def label(self, parent, key, **kwargs):
        return self.bind_text(ttk.Label(parent, **kwargs), key)

    def group(self, parent, key):
        group = self.bind_text(ttk.LabelFrame(parent, padding=8), key)
        group.pack(fill='x', pady=(0, 8))
        return group

    def tip(self, widget, key):
        self.tooltips.append(Tooltip(widget, lambda: self.tr(key)))

    def radio(self, parent, key, variable, value, tip):
        button = self.bind_text(ttk.Radiobutton(parent, variable=variable, value=value, command=self.change_options), key)
        button.pack(side='left', padx=(0, 15))
        self.tip(button, tip)
        return button

    def persist(self):
        try:
            save_settings(self.settings)
        except OSError:
            self.notice = ('settings_failed', {})

    def change_language(self, event=None):
        self.settings['language'] = self.language.get()
        self.persist()
        for tip in self.tooltips:
            tip.hide()
        self.render()

    def change_options(self, event=None):
        self.settings.update(mode=self.mode.current(), source=self.source.get(), save=self.saving.get())
        self.extra_vars[self.settings['mode']].set(False)
        self.settings['extra_modes'] = [i for i, variable in enumerate(self.extra_vars) if variable.get()]
        self.settings['images'] = self.images.get()
        self.persist()
        self.render()

    def change_hotkey(self):
        self.settings['hotkey_enabled'] = self.hotkey.get()
        self.collector.configure_hotkey(self.settings)
        self.persist()
        self.render()

    def capture_shortcut(self):
        dialog = tk.Toplevel(self.root)
        dialog.title(self.tr('change'))
        dialog.transient(self.root)
        ttk.Label(dialog, text=self.tr('capture_key'), padding=20).pack()
        ttk.Button(dialog, text=self.tr('cancel'), command=dialog.destroy).pack(pady=(0, 12))
        # Temporarily release our shortcut so its key press can reach this dialog.
        self.collector.configure_hotkey(dict(self.settings, hotkey_enabled=False))

        def restore(event):
            if event.widget is dialog:
                self.collector.configure_hotkey(self.settings)

        def capture(event):
            if event.keysym == 'Escape':
                dialog.destroy()
                return 'break'
            if event.keycode in (16, 17, 18, 91, 92) or not 1 <= event.keycode <= 254:
                return 'break'
            import ctypes
            held = lambda vk: bool(ctypes.windll.user32.GetKeyState(vk) & 0x8000)
            mods = int(held(18)) | (int(held(17)) << 1) | (int(held(16)) << 2) | (int(held(91) or held(92)) << 3)
            labels = [name for flag, name in [(2, 'Ctrl'), (1, 'Alt'), (4, 'Shift'), (8, 'Win')] if mods & flag]
            labels.append(event.keysym.upper() if len(event.keysym) == 1 else event.keysym)
            self.settings.update(hotkey_mods=mods, hotkey_vk=event.keycode, hotkey_name='+'.join(labels))
            self.persist()
            dialog.destroy()
            self.render()
            return 'break'

        dialog.bind('<KeyPress>', capture)
        dialog.bind('<Destroy>', restore)
        dialog.grab_set()
        dialog.focus_force()

    def toggle(self):
        if not self.pending:
            self.pending = True
            self.collector.toggle_from_ui(self.settings)
            self.render()

    def transfer_text(self):
        dialog = tk.Toplevel(self.root)
        dialog.title(self.tr('transfer'))
        dialog.transient(self.root)
        dialog.minsize(520, 360)
        body = ttk.Frame(dialog, padding=14)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=self.tr('transfer_instructions'), wraplength=500).pack(anchor='w', pady=(0, 8))
        editor = tk.Text(body, height=10, width=60, wrap='word')
        editor.pack(fill='both', expand=True)
        notice = ttk.Label(body, wraplength=500)
        notice.pack(anchor='w', pady=6)
        row = ttk.Frame(body)
        row.pack(fill='x')
        self.collector.configure_hotkey(dict(self.settings, hotkey_enabled=False))

        def submit():
            text = editor.get('1.0', 'end-1c')
            lines = [line for line in text.splitlines() if line.strip()]
            if not lines or len(lines) > 1000 or len(text) > 500_000:
                notice.configure(text=self.tr('transfer_limit'))
                return
            self.pending = True
            self.collector.send_text(self.settings, lines)
            dialog.destroy()
            self.render()

        def restore(event):
            if event.widget is dialog:
                self.collector.configure_hotkey(self.settings)

        ttk.Button(row, text=self.tr('cancel'), command=dialog.destroy).pack(side='right')
        ttk.Button(row, text=self.tr('send'), command=submit).pack(side='right', padx=8)
        dialog.bind('<Destroy>', restore)
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        dialog.grab_set()
        editor.focus_set()

    def render(self):
        for widget, key in self.bindings:
            widget.configure(text=self.tr(key))
        modes = ('Notepad++', 'Windows 메모장', 'Excel', 'Word', '한컴오피스 한글 (HWP)') if self.settings['language'] == 'KO' else ('Notepad++', 'Windows Notepad', 'Excel', 'Word', 'Hancom Hangul (HWP)')
        self.mode.configure(values=modes, state='disabled' if self.active or self.pending else 'readonly')
        self.mode.current(self.settings['mode'])
        idle = not (self.active or self.pending or self.closing)
        office_selected = any(mode in (2, 3) for mode in [self.settings['mode'], *self.settings['extra_modes']])
        for i, button in enumerate(self.extra_buttons):
            button.configure(text=('Notepad++', modes[1], 'Excel', 'Word', 'HWP')[i],
                             state='normal' if idle and i != self.settings['mode'] else 'disabled')
        self.image_button.configure(state='normal' if idle and office_selected else 'disabled')
        self.transfer_button.configure(state='normal' if idle and office_selected else 'disabled')
        for button in self.source_buttons:
            button.configure(state='disabled' if self.active or self.pending else 'normal')
        for button in self.save_buttons:
            button.configure(state='normal' if idle and office_selected else 'disabled')
        key = self.settings['hotkey_name'] if self.settings['hotkey_enabled'] else self.tr('disabled')
        self.key_label.configure(text=self.tr('configured', key=key))
        self.state_label.configure(text=self.tr('busy' if self.pending else 'on' if self.active else 'off'))
        self.target_label.configure(text=self.tr('destination', name=self.destination or self.tr('none')))
        self.count_label.configure(text=self.tr('count', count=self.count))
        self.totals_label.configure(text=self.totals)
        key, values = self.notice
        values = dict(values)
        if 'error' in values:
            values['error'] = translate_error(values['error'], self.settings['language'])
        self.notice_label.configure(text=self.tr(key, **values))
        button_key = 'end' if self.active else 'start'
        if self.pending and key == 'excel_starting':
            button_key = 'starting'
        self.button.configure(text=self.tr(button_key), state='disabled' if self.pending or self.closing else 'normal')

    def poll(self):
        import queue
        changed = False
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'closed':
                    self.root.destroy()
                    return
                if kind == 'state':
                    self.active, self.destination = data
                    self.pending = False
                elif kind == 'busy':
                    self.pending = True
                elif kind == 'count':
                    self.count = data
                elif kind == 'totals':
                    self.totals = data
                elif kind == 'notice':
                    self.notice = data
                elif kind == 'close_failed':
                    self.closing = False
                    self.pending = False
                elif kind == 'ready':
                    self.pending = False
                    self.collector.configure_hotkey(self.settings)
                elif kind == 'transfer_rejected':
                    self.pending = False
                    self.notice = ('transfer_rejected', {})
                changed = True
        except queue.Empty:
            pass
        if changed:
            self.render()
        self.root.after(50, self.poll)

    def close(self):
        if not self.closing:
            self.closing = True
            self.pending = True
            self.collector.close()
            self.render()
