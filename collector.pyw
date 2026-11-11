# -*- coding: utf-8 -*-
"""Clipboard Collector — multi-destination clipboard collection.
Windows x64, Python 3.9+. Notepad++/Notepad stdlib; Office/HWP optional pywin32.
"""
import ctypes as ct
import ctypes.wintypes as wt
import os
import queue
import re
import struct
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

if os.name != 'nt':
    raise SystemExit('This application is for Windows.')

user32 = ct.WinDLL('user32', use_last_error=True)
kernel32 = ct.WinDLL('kernel32', use_last_error=True)

LRESULT = ct.c_ssize_t
ULONG_PTR = ct.c_size_t
WNDPROC = ct.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
ENUMPROC = ct.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

class WNDCLASSEXW(ct.Structure):
    _fields_ = [
        ('cbSize', wt.UINT), ('style', wt.UINT), ('lpfnWndProc', WNDPROC),
        ('cbClsExtra', ct.c_int), ('cbWndExtra', ct.c_int), ('hInstance', wt.HINSTANCE),
        ('hIcon', wt.HICON), ('hCursor', wt.HANDLE), ('hbrBackground', wt.HBRUSH),
        ('lpszMenuName', wt.LPCWSTR), ('lpszClassName', wt.LPCWSTR), ('hIconSm', wt.HICON),
    ]

# ctypes pointer sizes matter on x64. Explicit declarations protect every HANDLE.
user32.GetAncestor.argtypes = [wt.HWND, wt.UINT]
user32.GetAncestor.restype = wt.HWND
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.FindWindowW.restype = wt.HWND
user32.IsWindow.argtypes = [wt.HWND]
user32.IsWindow.restype = wt.BOOL
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ct.c_int]
user32.GetWindowTextW.restype = ct.c_int
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ct.c_int]
user32.GetClassNameW.restype = ct.c_int
user32.GetParent.argtypes = [wt.HWND]
user32.GetParent.restype = wt.HWND
user32.EnumChildWindows.argtypes = [wt.HWND, ENUMPROC, wt.LPARAM]
user32.EnumChildWindows.restype = wt.BOOL
user32.SendMessageTimeoutW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM, wt.UINT, wt.UINT, ct.POINTER(ULONG_PTR)]
user32.SendMessageTimeoutW.restype = LRESULT
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wt.HWND
user32.EnumWindows.argtypes = [ENUMPROC, wt.LPARAM]
user32.EnumWindows.restype = wt.BOOL
user32.IsWindowVisible.argtypes = [wt.HWND]
user32.IsWindowVisible.restype = wt.BOOL
user32.GetClientRect.argtypes = [wt.HWND, ct.POINTER(wt.RECT)]
user32.GetClientRect.restype = wt.BOOL
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ct.POINTER(wt.DWORD)]
user32.GetWindowThreadProcessId.restype = wt.DWORD
user32.RegisterClassExW.argtypes = [ct.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wt.ATOM
user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ct.c_int, ct.c_int, ct.c_int, ct.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
user32.CreateWindowExW.restype = wt.HWND
user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterHotKey.argtypes = [wt.HWND, ct.c_int, wt.UINT, wt.UINT]
user32.RegisterHotKey.restype = wt.BOOL
user32.UnregisterHotKey.argtypes = [wt.HWND, ct.c_int]
user32.UnregisterHotKey.restype = wt.BOOL
user32.AddClipboardFormatListener.argtypes = [wt.HWND]
user32.AddClipboardFormatListener.restype = wt.BOOL
user32.RemoveClipboardFormatListener.argtypes = [wt.HWND]
user32.RemoveClipboardFormatListener.restype = wt.BOOL
user32.GetClipboardSequenceNumber.argtypes = []
user32.GetClipboardSequenceNumber.restype = wt.DWORD
user32.IsClipboardFormatAvailable.argtypes = [wt.UINT]
user32.IsClipboardFormatAvailable.restype = wt.BOOL
user32.OpenClipboard.argtypes = [wt.HWND]
user32.OpenClipboard.restype = wt.BOOL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wt.BOOL
user32.GetClipboardData.argtypes = [wt.UINT]
user32.GetClipboardData.restype = wt.HANDLE
user32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.PostMessageW.restype = wt.BOOL
user32.DestroyWindow.argtypes = [wt.HWND]
user32.DestroyWindow.restype = wt.BOOL
user32.GetMessageW.argtypes = [ct.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT]
user32.GetMessageW.restype = ct.c_int
user32.TranslateMessage.argtypes = [ct.POINTER(wt.MSG)]
user32.TranslateMessage.restype = wt.BOOL
user32.DispatchMessageW.argtypes = [ct.POINTER(wt.MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.PostQuitMessage.argtypes = [ct.c_int]
user32.PostQuitMessage.restype = None
kernel32.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID, ct.c_size_t, ct.POINTER(ct.c_size_t)]
kernel32.ReadProcessMemory.restype = wt.BOOL
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
kernel32.GetModuleHandleW.restype = wt.HMODULE
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.CloseHandle.argtypes = [wt.HANDLE]
kernel32.CloseHandle.restype = wt.BOOL
kernel32.VirtualAllocEx.argtypes = [wt.HANDLE, wt.LPVOID, ct.c_size_t, wt.DWORD, wt.DWORD]
kernel32.VirtualAllocEx.restype = wt.LPVOID
kernel32.VirtualFreeEx.argtypes = [wt.HANDLE, wt.LPVOID, ct.c_size_t, wt.DWORD]
kernel32.VirtualFreeEx.restype = wt.BOOL
kernel32.WriteProcessMemory.argtypes = [wt.HANDLE, wt.LPVOID, wt.LPCVOID, ct.c_size_t, ct.POINTER(ct.c_size_t)]
kernel32.WriteProcessMemory.restype = wt.BOOL
kernel32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ct.POINTER(wt.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = wt.BOOL
kernel32.GlobalLock.argtypes = [wt.HGLOBAL]
kernel32.GlobalLock.restype = wt.LPVOID
kernel32.GlobalSize.argtypes = [wt.HGLOBAL]
kernel32.GlobalSize.restype = ct.c_size_t
user32.RegisterClipboardFormatW.argtypes = [wt.LPCWSTR]
user32.RegisterClipboardFormatW.restype = wt.UINT
kernel32.GlobalUnlock.argtypes = [wt.HGLOBAL]
kernel32.GlobalUnlock.restype = wt.BOOL
kernel32.GetACP.argtypes = []
kernel32.GetACP.restype = wt.UINT

WM_HOTKEY = 0x0312
WM_CLIPBOARDUPDATE = 0x031D
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_APP_TOGGLE = 0x8001
WM_APP_MODE = 0x8002
WM_APP_EXIT = 0x8003
WM_APP_SEND = 0x8004
MAX_IMAGE_BYTES = 32 * 1024 * 1024
IMAGE_REPEAT_SECONDS = 2.0
HOTKEY_ID = 9088
VK_F8 = 0x77
HWND_MESSAGE = wt.HWND(-3)
SMTO_ABORTIFHUNG = 2
CF_UNICODETEXT = 13
WM_GETTEXTLENGTH = 0x000E
EM_GETLINECOUNT = 0x00BA
EM_LINEINDEX = 0x00BB
EM_LINELENGTH = 0x00C1
EM_SETSEL = 0x00B1
EM_REPLACESEL = 0x00C2
# Notepad++ / Scintilla messages
NPPM_GETCURRENTVIEW = 2112
SCI_GETLENGTH = 2006
SCI_GETCHARAT = 2007
SCI_GETEOLMODE = 2030
SCI_GETCODEPAGE = 2137
SCI_GETREADONLY = 2140
SCI_GETDOCPOINTER = 2357
SCI_APPENDTEXT = 2282
SCI_GOTOPOS = 2025
MEM_COMMIT_RESERVE = 0x1000 | 0x2000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
BROWSERS = {'chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'vivaldi.exe', 'opera.exe'}


def send_msg(hwnd, msg, wparam=0, lparam=0, timeout=1500):
    result = ULONG_PTR()
    ok = user32.SendMessageTimeoutW(hwnd, msg, wparam, lparam, SMTO_ABORTIFHUNG, timeout, ct.byref(result))
    if not ok:
        raise RuntimeError('The editor did not respond or the message could not be delivered.')
    return result.value


def window_title(hwnd):
    buf = ct.create_unicode_buffer(1024)
    user32.GetWindowTextW(hwnd, buf, 1024)
    return buf.value


def browser_is_foreground():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ct.byref(pid))
    process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not process:
        return False
    try:
        buf = ct.create_unicode_buffer(32768)
        size = wt.DWORD(len(buf))
        if not kernel32.QueryFullProcessImageNameW(process, 0, buf, ct.byref(size)):
            return False
        return os.path.basename(buf.value).lower() in BROWSERS
    finally:
        kernel32.CloseHandle(process)


def get_scintilla(npp):
    """Select the current Scintilla view; only direct Notepad++ Scintilla children count."""
    view = send_msg(npp, NPPM_GETCURRENTVIEW)
    if view not in (0, 1):
        raise RuntimeError('Could not identify the active Notepad++ editor.')
    children = []
    def callback(hwnd, unused):
        name = ct.create_unicode_buffer(128)
        user32.GetClassNameW(hwnd, name, 128)
        if name.value == 'Scintilla' and user32.GetParent(hwnd) == npp:
            children.append(hwnd)
        return True
    cb = ENUMPROC(callback)
    user32.EnumChildWindows(npp, cb, 0)
    if len(children) <= view:
        raise RuntimeError('Could not find the Notepad++ editor (Scintilla).')
    return children[view]


def get_npp_target():
    npp = user32.FindWindowW('Notepad++', None)
    if not npp:
        raise RuntimeError('Open Notepad++ and select the text tab to collect into.')
    sci = get_scintilla(npp)
    if send_msg(sci, SCI_GETREADONLY):
        raise RuntimeError('The active Notepad++ tab is read-only.')
    return npp, sci, send_msg(sci, SCI_GETDOCPOINTER)


def append_to_scintilla(npp, sci, docptr, text):
    if not user32.IsWindow(npp) or not user32.IsWindow(sci):
        raise RuntimeError('Notepad++ closed. Start collection again.')
    if get_scintilla(npp) != sci or send_msg(sci, SCI_GETDOCPOINTER) != docptr:
        raise RuntimeError('The Notepad++ tab changed. Collection stopped.')
    if send_msg(sci, SCI_GETREADONLY):
        raise RuntimeError('The target document is read-only.')
    codepage = send_msg(sci, SCI_GETCODEPAGE)
    if codepage == 65001:
        encoding = 'utf-8'
    elif codepage == 0:
        encoding = 'cp' + str(kernel32.GetACP())
    else:
        encoding = 'cp' + str(codepage)
    try:
        text_bytes = text.encode(encoding, errors='strict')
    except (UnicodeError, LookupError):
        raise RuntimeError('Some characters cannot be written in this encoding. Switch the document to UTF-8.')
    length = send_msg(sci, SCI_GETLENGTH)
    eol_mode = send_msg(sci, SCI_GETEOLMODE)
    eol = (b'\r\n', b'\r', b'\n')[eol_mode] if eol_mode in (0, 1, 2) else b'\r\n'
    last = (send_msg(sci, SCI_GETCHARAT, length - 1) & 0xff) if length else None
    prefix = b'' if not length or last in (10, 13) else eol
    payload = prefix + text_bytes
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(sci, ct.byref(pid))
    proc = kernel32.OpenProcess(PROCESS_VM_OPERATION | PROCESS_VM_WRITE, False, pid.value)
    if not proc:
        raise RuntimeError('Could not access the Notepad++ editor. Check that both apps have the same permission level.')
    remote = None
    try:
        remote = kernel32.VirtualAllocEx(proc, None, len(payload), MEM_COMMIT_RESERVE, PAGE_READWRITE)
        if not remote:
            raise RuntimeError('Could not allocate a temporary buffer in Notepad++.')
        buf = ct.create_string_buffer(payload, len(payload))
        written = ct.c_size_t(0)
        if not kernel32.WriteProcessMemory(proc, remote, buf, len(payload), ct.byref(written)) or written.value != len(payload):
            raise RuntimeError('Could not send text to Notepad++.')
        send_msg(sci, SCI_APPENDTEXT, len(payload), remote, timeout=3000)
    finally:
        if remote:
            kernel32.VirtualFreeEx(proc, remote, 0, MEM_RELEASE)
        kernel32.CloseHandle(proc)
    new_length = send_msg(sci, SCI_GETLENGTH)
    if new_length == length + len(payload):
        # Keep the newest clipboard entry visible in Notepad++ without focusing it.
        send_msg(sci, SCI_GOTOPOS, new_length)
    if new_length != length + len(payload):
        raise RuntimeError('Could not verify the new text length in Notepad++.')


def read_clipboard(hwnd):
    for retry in range(6):
        if user32.OpenClipboard(hwnd):
            try:
                if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                    return None
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    return None
                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    return None
                try:
                    return ct.wstring_at(pointer)
                finally:
                    kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()
        time.sleep(0.025)
    return None


def read_picture(hwnd, sequence, formats):
    for _ in range(6):
        if not user32.OpenClipboard(hwnd):
            time.sleep(0.025)
            continue
        try:
            if user32.GetClipboardSequenceNumber() != sequence:
                return None, sequence
            for clipboard_format, image_format in formats:
                if not user32.IsClipboardFormatAvailable(clipboard_format):
                    continue
                handle = user32.GetClipboardData(clipboard_format)
                size = kernel32.GlobalSize(handle) if handle else 0
                if size > MAX_IMAGE_BYTES:
                    raise ValueError('The copied image exceeds 32 MiB.')
                pointer = kernel32.GlobalLock(handle) if size else None
                if pointer:
                    try:
                        picture = image_format, ct.string_at(pointer, size)
                        return picture, user32.GetClipboardSequenceNumber()
                    finally:
                        kernel32.GlobalUnlock(handle)
            return None, sequence
        finally:
            user32.CloseClipboard()
    return None, sequence



MODES = ('Notepad++', 'Windows Notepad', 'Excel', 'Word', 'Hancom Hangul (HWP)')


def process_name(hwnd):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ct.byref(pid))
    if not pid.value:
        return ''
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ''
    try:
        path = ct.create_unicode_buffer(32768)
        size = wt.DWORD(len(path))
        if kernel32.QueryFullProcessImageNameW(handle, 0, path, ct.byref(size)):
            return os.path.basename(path.value).lower()
        return ''
    finally:
        kernel32.CloseHandle(handle)


def winclass(hwnd):
    buf = ct.create_unicode_buffer(128)
    user32.GetClassNameW(hwnd, buf, 128)
    return buf.value


def visible_windows():
    items = []
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd) and window_title(hwnd):
            items.append(hwnd)
        return True
    cb = ENUMPROC(callback)
    user32.EnumWindows(cb, 0)  # in z-order, front to back
    return items


def notepad_target():
    """Pick most-recently raised Notepad, then visible editable control."""
    for top in visible_windows():
        if process_name(top) != 'notepad.exe' and winclass(top) != 'Notepad':
            continue
        edit = notepad_editor_for_window(top)
        if edit is not None:
            return {'kind':'notepad','window':top,'editor':edit,'title':window_title(top)}
    raise RuntimeError('Open Windows Notepad and select a document to edit.')


def normalize_notepad_title(title):
    # Unsaved-change indicator may appear after the first appended item.
    return title.strip().lstrip('*●• ').strip()


def append_to_notepad(target, text):
    top = target['window']
    edit = target['editor']
    if not user32.IsWindow(top) or not user32.IsWindow(edit):
        raise RuntimeError('The Notepad window closed. Collection stopped.')
    if normalize_notepad_title(window_title(top)) != normalize_notepad_title(target['title']):
        raise RuntimeError('The Notepad title or tab changed. Collection stopped to protect the other document.')
    # If app changes editing tab/window, don't silently write into another buffer.
    last = notepad_editor_for_window(top)
    if last != edit:
        raise RuntimeError('The Notepad editing tab changed. Collection stopped.')
    old_len = send_msg(edit, WM_GETTEXTLENGTH)
    lines = send_msg(edit, EM_GETLINECOUNT)
    line_start = send_msg(edit, EM_LINEINDEX, max(0, lines - 1))
    last_line_len = send_msg(edit, EM_LINELENGTH, line_start)
    prefix = '\r\n' if old_len and last_line_len else ''
    # EM_REPLACESEL is a system message. Windows marshals the caller's buffer.
    body = ct.create_unicode_buffer(prefix + text)
    send_msg(edit, EM_SETSEL, old_len, old_len)
    send_msg(edit, EM_REPLACESEL, 1, ct.addressof(body))
    new_len = send_msg(edit, WM_GETTEXTLENGTH)
    if new_len <= old_len:
        raise RuntimeError('Could not verify the text inserted into Notepad.')


def notepad_editor_for_window(top):
    candidates = []
    def callback(hwnd, _):
        cls = winclass(hwnd).lower()
        if user32.IsWindowVisible(hwnd) and (cls == 'edit' or cls.startswith('richedit')):
            rect = wt.RECT()
            user32.GetClientRect(hwnd, ct.byref(rect))
            area = max(rect.right - rect.left, 0) * max(rect.bottom - rect.top, 0)
            score = area + (1_000_000 if cls.startswith('richeditd2d') else 0)
            candidates.append((score, hwnd))
        return True
    cb = ENUMPROC(callback)
    user32.EnumChildWindows(top, cb, 0)
    return max(candidates)[1] if candidates else None


def require_com():
    try:
        import pythoncom
        import win32com.client as win32
    except ImportError as exc:
        raise RuntimeError('Excel, Word, and Hancom Hangul require pywin32. Run Install_Office_HWP_Support.cmd and try again.') from exc
    return pythoncom, win32


def acquire_excel():
    from office_calls import retry_excel
    _, win32 = require_com()

    def read_selection():
        app = win32.GetActiveObject('Excel.Application')
        book = app.ActiveWorkbook
        sheet = app.ActiveSheet
        cell = app.ActiveCell
        if not book or not sheet or not cell or sheet.Type != -4167:
            raise ValueError('There is no active worksheet.')
        if book.ReadOnly or sheet.ProtectContents:
            raise ValueError('The worksheet is read-only or protected.')
        col, row = int(cell.Column), int(cell.Row)
        # Never overwrite existing content. User first selects an empty cell.
        if cell.Value2 is not None:
            raise ValueError('Select an empty starting cell in Excel, then start collection.')
        return {'kind':'excel','app':app,'book':book,'sheet':sheet,'col':col,'next_row':row,
                'book_name':str(book.FullName),'sheet_name':str(sheet.Name),
                'label':f'{book.Name} / {sheet.Name} / {cell.Address}'}
    try:
        return retry_excel(read_selection, timeout=10.0)
    except Exception as exc:
        raise RuntimeError('Select an empty starting cell in the open Excel workbook. (' + str(exc) + ')') from exc


def append_to_excel(target, text):
    from office_calls import retry_excel

    retry_excel(lambda: write_excel_cell(target, text))


def write_excel_cell(target, text):
    book, sheet = target['book'], target['sheet']
    if str(book.FullName) != target['book_name'] or str(sheet.Name) != target['sheet_name']:
        raise RuntimeError('The target Excel workbook changed.')
    row, col = target['next_row'], target['col']
    if row > 1048576 or len(text) > 32767:
        raise RuntimeError('The Excel row limit or cell text limit (32,767 characters) was exceeded.')
    cell = sheet.Cells(row, col)
    if cell.Value2 is not None:
        raise RuntimeError(f'Excel cell {cell.Address} already contains data. Collection stopped to avoid overwriting it.')
    if bool(sheet.ProtectContents) or bool(book.ReadOnly):
        raise RuntimeError('The Excel worksheet is protected or read-only.')
    # Literal text only; avoid formula execution from untrusted copied strings.
    cell.NumberFormat = '@'
    cell.Value2 = text
    target['next_row'] = row + 1


def acquire_word():
    _, win32 = require_com()
    try:
        app = win32.GetActiveObject('Word.Application')
        doc = app.ActiveDocument
        if not doc or doc.ReadOnly or doc.ProtectionType != -1:
            raise ValueError('The document is read-only or protected.')
        return {'kind':'word','app':app,'doc':doc,'path':str(doc.FullName),
                'label':str(doc.Name),'added':0}
    except Exception as exc:
        raise RuntimeError('Select an editable document in the open Word window. (' + str(exc) + ')') from exc


def append_to_word(target, text):
    doc = target['doc']
    if str(doc.FullName) != target['path'] or doc.ReadOnly or doc.ProtectionType != -1:
        raise RuntimeError('The target Word document changed or is no longer editable.')
    end = int(doc.Content.End)
    # A blank Word document contains only its final paragraph mark.
    has_text = end > 1
    inserted = ('\r' if has_text else '') + text
    doc.Range(end - 1, end - 1).InsertAfter(inserted)
    target['added'] += 1


def acquire_hwp():
    pythoncom, win32 = require_com()
    # ROT lookup attaches to an existing HWP window. Never launch a new HWP.
    rot = pythoncom.GetRunningObjectTable()
    context = pythoncom.CreateBindCtx(0)
    objects = []
    for moniker in rot.EnumRunning():
        try:
            label = moniker.GetDisplayName(context, moniker)
            if label.startswith('!HwpObject'):
                objects.append(win32.Dispatch(rot.GetObject(moniker).QueryInterface(pythoncom.IID_IDispatch)))
        except Exception:
            continue
    if not objects:
        try:
            objects = [win32.GetActiveObject('HWPFrame.HwpObject')]
        except Exception as exc:
            raise RuntimeError('Could not connect to a running Hancom Hangul (HWP) instance.') from exc
    if len(objects) > 1:
        raise RuntimeError('Multiple Hancom Hangul (HWP) instances are open. Close the others and try again.')
    hwp = objects[0]
    try:
        path = str(hwp.Path or '')
        if not path:
            raise ValueError('Open a previously saved Hancom Hangul document first.')
        if int(hwp.EditMode) != 1:
            raise ValueError('The Hancom Hangul document is not in normal editing mode.')
        # Read once at start only, to avoid an unwanted blank first paragraph.
        body = hwp.GetTextFile('TEXT', 'saveall')
        has_content = bool(str(body or '').strip('\r\n\t \x00'))
        return {'kind':'hwp','hwp':hwp,'path':path,'has_content':has_content,
                'label':os.path.basename(path)}
    except Exception as exc:
        raise RuntimeError('Could not select an editable Hancom Hangul document. (' + str(exc) + ')') from exc


def append_to_hwp(target, text):
    hwp = target['hwp']
    if str(hwp.Path or '') != target['path'] or int(hwp.EditMode) != 1:
        raise RuntimeError('The target Hancom Hangul document changed or is no longer editable.')
    if not hwp.HAction.Run('MoveDocEnd'):
        raise RuntimeError('Could not move to the end of the Hancom Hangul document.')
    if target['has_content']:
        if not hwp.HAction.Run('BreakPara'):
            raise RuntimeError('Could not add a paragraph to the Hancom Hangul document.')
    pset = hwp.HParameterSet.HInsertText
    hwp.HAction.GetDefault('InsertText', pset.HSet)
    pset.Text = text
    if not hwp.HAction.Execute('InsertText', pset.HSet):
        raise RuntimeError('Could not insert text in Hancom Hangul. Check the last entry.')
    target['has_content'] = True


def acquire_target(mode):
    if mode == 0:
        npp, sci, docptr = get_npp_target()
        return {'kind':'npp', 'npp':npp,'sci':sci,'docptr':docptr,
                'label':window_title(npp).replace(' - Notepad++','')}
    if mode == 1:
        target = notepad_target()
        target['label'] = target['title']
        return target
    if mode == 2:
        return acquire_excel()
    if mode == 3:
        return acquire_word()
    if mode == 4:
        return acquire_hwp()
    raise RuntimeError('Unknown target application.')


def append_to_target(target, text):
    k = target['kind']
    if k == 'npp':
        return append_to_scintilla(target['npp'], target['sci'], target['docptr'], text)
    if k == 'notepad':
        return append_to_notepad(target, text)
    if k == 'excel':
        return append_to_excel(target, text)
    if k == 'word':
        return append_to_word(target, text)
    if k == 'hwp':
        return append_to_hwp(target, text)
    raise RuntimeError('Unsupported target.')


def normalize_line(value):
    line = re.sub(r'[\r\n\u2028\u2029\t]+', ' ', value).replace('\x00', '').strip()
    return line


def target_window(target):
    kind = target['kind']
    if kind == 'npp':
        return target['npp']
    if kind == 'notepad':
        return target['window']
    if kind == 'excel':
        return int(target['app'].ActiveWindow.Hwnd)
    if kind == 'word':
        return int(target['doc'].ActiveWindow.Hwnd)
    return int(target['hwp'].XHwpWindows.Item(0).WindowHandle)


def save_target(target):
    from strings import TEXT
    kind = target['kind']
    obj = target['book'] if kind == 'excel' else target['doc']
    expected = target['book_name'] if kind == 'excel' else target['path']
    def save():
        if not str(obj.Path or ''):
            raise RuntimeError(TEXT['save_first'][1])
        if str(obj.FullName) != expected or obj.ReadOnly:
            raise RuntimeError(TEXT['save_changed'][1])
        obj.Save()

    if kind == 'excel':
        from office_calls import retry_excel
        retry_excel(save)
        saved = retry_excel(lambda: obj.Saved)
    else:
        save()
        saved = obj.Saved
    if not saved:
        raise RuntimeError(TEXT['save_cancelled'][1])


def prepare_targets(settings, transfer=False):
    from strings import TEXT
    from office_calls import retry_excel

    targets = []
    modes = [settings['mode'], *settings.get('extra_modes', [])]
    for mode in dict.fromkeys(modes):
        if transfer and mode not in (2, 3):
            continue
        try:
            target = acquire_target(mode)
            target['entries'] = 0
            target['saving'] = settings['save'] if mode in (2, 3) else 'manual'
            if target['saving'] != 'manual':
                obj = target['book'] if mode == 2 else target['doc']
                def writable_file():
                    return bool(str(obj.Path or '')) and not obj.ReadOnly

                writable = retry_excel(writable_file) if mode == 2 else writable_file()
                if not writable:
                    raise RuntimeError(TEXT['save_first'][1])
            if not transfer and settings['source'] == 'all':
                handle = retry_excel(lambda: target_window(target)) if mode == 2 else target_window(target)
                root = user32.GetAncestor(handle, 2) if handle else 0
                if not root:
                    raise RuntimeError('The destination window could not be identified.')
                target['window_handle'] = root
        except Exception as exc:
            raise RuntimeError(f'{MODES[mode]}: {exc}') from exc
        targets.append(target)
    if not targets:
        raise RuntimeError('Select Excel or Word before sending text.')
    return targets


class SaveFailure(RuntimeError):
    pass


def write_entry(targets, kind, value):
    if kind == 'image':
        from pictures import OFFICE_KINDS, insert_picture

    for target in targets:
        if kind == 'image' and target['kind'] not in OFFICE_KINDS:
            continue
        try:
            if kind == 'image':
                insert_picture(target, value)
            else:
                append_to_target(target, value)
            target['entries'] += 1
        except Exception as exc:
            raise RuntimeError(f"{target['label']}: {exc}") from exc
        if target['saving'] == 'each':
            try:
                save_target(target)
            except Exception as exc:
                raise SaveFailure(f"{target['label']}: Text or image was added but saving failed. {exc}") from exc


def save_at_end(targets):
    errors = []
    for target in targets:
        if target['saving'] == 'stop' and target['entries']:
            try:
                save_target(target)
            except Exception as exc:
                errors.append(f"{target['label']}: Text or image was added but saving failed. {exc}")
    return errors


def entry_totals(targets):
    return ' · '.join(f"{target['label']} ({target['entries']})" for target in targets)


class Collector:
    """Capture clipboard promptly; serialize destination COM work on one STA."""
    def __init__(self, events, settings):
        self.events = events
        self.settings = settings
        self.hwnd = None
        self.collecting = False
        self.transitioning = False
        self.close_requested = False
        self.session = 0
        self.excluded_windows = set()
        self.picture_formats = [(value, kind) for value, kind in
                                ((user32.RegisterClipboardFormatW('PNG'), 'PNG'), (17, 'DIB'), (8, 'DIB'))
                                if value]
        self.picture_slots = threading.BoundedSemaphore(4)
        self.transfers = queue.Queue()
        self.last_sequence = 0
        self.jobs = queue.Queue()
        self.controls = queue.Queue()
        self.callback = WNDPROC(self._wndproc)
        self.worker = threading.Thread(target=self._work, daemon=True)
        self.listener = threading.Thread(target=self._run, daemon=True)
        self.worker.start()
        self.listener.start()

    def emit(self, kind, data):
        self.events.put((kind, data))

    def notice(self, key, **values):
        self.emit('notice', (key, values))

    def _run(self):
        try:
            klass = WNDCLASSEXW()
            klass.cbSize = ct.sizeof(klass)
            klass.hInstance = kernel32.GetModuleHandleW(None)
            klass.lpfnWndProc = self.callback
            klass.lpszClassName = 'ClipboardCollectorPreview_' + str(os.getpid())
            if not user32.RegisterClassExW(ct.byref(klass)):
                raise RuntimeError('Could not register the Windows message window.')
            self.hwnd = user32.CreateWindowExW(0, klass.lpszClassName, 'ClipboardCollector', 0,
                                              0, 0, 0, 0, HWND_MESSAGE, None, klass.hInstance, None)
            if not self.hwnd:
                raise RuntimeError('Could not create the Windows message window.')
            if not user32.AddClipboardFormatListener(self.hwnd):
                raise RuntimeError('Could not register for clipboard updates.')
            self.emit('ready', None)
            if self.close_requested:
                user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
            message = wt.MSG()
            while user32.GetMessageW(ct.byref(message), None, 0, 0) > 0:
                user32.TranslateMessage(ct.byref(message))
                user32.DispatchMessageW(ct.byref(message))
        except Exception as exc:
            self.notice('failed', error=str(exc))
            self.emit('state', (False, ''))
            self.jobs.put(('close', self.session, None))
        finally:
            if self.hwnd:
                user32.UnregisterHotKey(self.hwnd, HOTKEY_ID)
                user32.RemoveClipboardFormatListener(self.hwnd)

    def _toggle(self):
        if self.transitioning or self.close_requested:
            return
        self.transitioning = True
        self.emit('busy', None)
        if self.collecting:
            self.collecting = False
            self.jobs.put(('stop', self.session, None))
        else:
            self.session += 1
            self.capture_settings = dict(self.settings)
            if 2 in (self.settings['mode'], *self.settings.get('extra_modes', [])):
                self.notice('excel_starting')
            self.jobs.put(('start', self.session, self.capture_settings))

    def _copy_event(self):
        if not self.collecting:
            return
        seq = user32.GetClipboardSequenceNumber()
        if not seq or seq == self.last_sequence:
            return
        self.last_sequence = seq
        foreground = user32.GetForegroundWindow()
        if self.capture_settings['source'] == 'browser':
            if not browser_is_foreground():
                return
        elif foreground and user32.GetAncestor(foreground, 2) in self.excluded_windows:
            return
        if self.jobs.qsize() >= 1000:
            self.capture_error('overflow')
            return
        if self.capture_settings.get('images') and any(
            mode in (2, 3) for mode in [self.capture_settings['mode'], *self.capture_settings.get('extra_modes', [])]
        ) and any(user32.IsClipboardFormatAvailable(value) for value, _ in self.picture_formats):
            if not self.picture_slots.acquire(blocking=False):
                self.capture_error('picture_queue_full')
                return
            queued = False
            try:
                picture, actual_sequence = read_picture(self.hwnd, seq, self.picture_formats)
                if picture is None:
                    self.capture_error('capture_failed')
                    return
                self.last_sequence = actual_sequence
                self.jobs.put(('copy', self.session, ('image', picture, time.monotonic())))
                queued = True
            finally:
                if not queued:
                    self.picture_slots.release()
            return
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return
        value = read_clipboard(self.hwnd)
        if value is None or user32.GetClipboardSequenceNumber() != seq:
            self.capture_error('capture_failed')
            return
        line = normalize_line(value)
        if not line:
            return
        if len(line) > 500_000:
            self.notice('too_long')
            return
        self.jobs.put(('copy', self.session, ('text', line)))

    def capture_error(self, reason):
        self.collecting = False
        self.transitioning = True
        self.jobs.put(('capture_error', self.session, reason))

    def _wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_HOTKEY and wparam == HOTKEY_ID or msg == WM_APP_TOGGLE:
                self._toggle()
                return 0
            if msg == WM_APP_MODE:
                while not self.controls.empty():
                    settings = self.controls.get_nowait()
                    user32.UnregisterHotKey(hwnd, HOTKEY_ID)
                    if settings['hotkey_enabled']:
                        user32.RegisterHotKey(hwnd, HOTKEY_ID, settings['hotkey_mods'] | 0x4000, settings['hotkey_vk'])
                return 0
            if msg == WM_CLIPBOARDUPDATE:
                self._copy_event()
                return 0
            if msg == WM_CLOSE:
                self.close_requested = True
                self.transitioning = True
                self.collecting = False
                self.jobs.put(('close', self.session, None))
                return 0
            if msg == WM_APP_SEND:
                settings, lines = self.transfers.get_nowait()
                if self.collecting or self.transitioning or self.close_requested:
                    self.emit('transfer_rejected', None)
                    return 0
                self.transitioning = True
                self.session += 1
                self.emit('busy', None)
                self.jobs.put(('transfer', self.session, (settings, lines)))
                return 0
            if msg == WM_APP_EXIT:
                user32.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
        except Exception as exc:
            self.capture_error(str(exc))
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _work(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pythoncom = None
        targets = []
        current = 0
        count = 0
        unsaved_failure = False
        last_picture = None
        try:
            while True:
                try:
                    action, session, data = self.jobs.get(timeout=0.05)
                except queue.Empty:
                    if pythoncom:
                        pythoncom.PumpWaitingMessages()
                    continue
                image_job = action == 'copy' and data[0] == 'image'
                try:
                    if action in ('start', 'transfer'):
                        current, count = session, 0
                        unsaved_failure = False
                        last_picture = None
                        self.emit('count', 0)
                        self.emit('totals', '')
                        options, lines = data if action == 'transfer' else (data, [])
                        targets = prepare_targets(options, transfer=action == 'transfer')
                        self.emit('totals', entry_totals(targets))
                        if action == 'start':
                            self.excluded_windows = {t['window_handle'] for t in targets if 'window_handle' in t}
                            self.last_sequence = user32.GetClipboardSequenceNumber()
                            self.collecting = not self.close_requested
                            self.emit('state', (True, ', '.join(t['label'] for t in targets)))
                            self.notice('started')
                            self.transitioning = False
                        else:
                            for line in lines:
                                before = sum(t['entries'] for t in targets)
                                try:
                                    write_entry(targets, 'text', line)
                                finally:
                                    count += sum(t['entries'] for t in targets) > before
                            errors = save_at_end(targets)
                            self.emit('count', count)
                            self.emit('totals', entry_totals(targets))
                            targets = []
                            if errors:
                                unsaved_failure = True
                                self.notice('failed', error='\n'.join(errors))
                            else:
                                self.notice('transfer_done', count=count)
                            self.emit('state', (False, ''))
                            self.transitioning = False
                    elif action == 'copy' and session == current and targets:
                        if image_job:
                            from pictures import picture_signature
                            captured_at = data[2]
                            signature = picture_signature(data[1])
                            if (last_picture is not None and signature == last_picture[0]
                                    and captured_at - last_picture[1] <= IMAGE_REPEAT_SECONDS):
                                continue
                            last_picture = signature, captured_at
                        else:
                            last_picture = None
                        before = sum(t['entries'] for t in targets)
                        try:
                            write_entry(targets, data[0], data[1])
                        finally:
                            count += sum(t['entries'] for t in targets) > before
                            self.emit('count', count)
                            self.emit('totals', entry_totals(targets))
                        self.notice('written', count=count)
                    elif action in ('stop', 'close', 'capture_error'):
                        had_targets = bool(targets)
                        saved_names = ', '.join(
                            t['label'] for t in targets if t['saving'] == 'stop' and t['entries']
                        )
                        errors = save_at_end(targets)
                        targets = []
                        if errors:
                            unsaved_failure = True
                        if action == 'capture_error' and had_targets:
                            from strings import TEXT
                            if errors:
                                self.notice('failed', error='\n'.join(errors))
                            elif data in TEXT:
                                self.notice(data)
                            else:
                                self.notice('failed', error=data)
                        elif errors:
                            self.notice('failed', error='\n'.join(errors))
                        elif saved_names:
                            self.notice('saved', name=saved_names)
                        elif had_targets:
                            self.notice('stopped')
                        if action == 'close':
                            if not unsaved_failure:
                                break
                            unsaved_failure = False
                            self.close_requested = False
                            self.emit('close_failed', None)
                        self.emit('state', (False, ''))
                        self.transitioning = False
                except Exception as exc:
                    self.collecting = False
                    self.transitioning = True
                    errors = [str(exc), *save_at_end(targets)]
                    unsaved_failure = len(errors) > 1 or isinstance(exc, SaveFailure)
                    self.emit('count', count)
                    self.emit('totals', entry_totals(targets))
                    targets = []
                    self.notice('failed', error='\n'.join(errors))
                    self.emit('state', (False, ''))
                    self.transitioning = False
                finally:
                    if image_job:
                        self.picture_slots.release()
                if pythoncom:
                    pythoncom.PumpWaitingMessages()
        finally:
            targets.clear()
            if pythoncom:
                pythoncom.CoUninitialize()
            if self.hwnd:
                user32.PostMessageW(self.hwnd, WM_APP_EXIT, 0, 0)
            self.emit('closed', None)

    def send_text(self, settings, lines):
        self.transfers.put((dict(settings), lines))
        user32.PostMessageW(self.hwnd, WM_APP_SEND, 0, 0)


    def toggle_from_ui(self, settings):
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_APP_TOGGLE, 0, 0)

    def configure_hotkey(self, settings):
        self.controls.put(dict(settings))
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_APP_MODE, 0, 0)

    def close(self):
        self.close_requested = True
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)


def main():
    from interface import Application, load_settings
    if struct.calcsize('P') != 8:
        messagebox.showerror('환경 오류 / Environment error', '64-bit Python is required. / 64비트 Python이 필요합니다.')
        return
    root = tk.Tk()
    events = queue.Queue()
    settings = load_settings()
    collector = Collector(events, settings)
    Application(root, collector, events, settings)
    root.mainloop()


if __name__ == '__main__':
    main()
