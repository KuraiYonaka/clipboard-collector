# -*- coding: utf-8 -*-
"""Clipboard Collector v0.2.0 — F8, browser-origin clipboard -> open document.
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
        raise RuntimeError('Notepad++ 응답 없음 또는 메시지 전송 실패')
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
        raise RuntimeError('Notepad++ 현재 편집 화면을 확인하지 못했사와요.')
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
        raise RuntimeError('Notepad++ 편집 영역(Scintilla)을 찾을 수 없습니다.')
    return children[view]


def get_npp_target():
    npp = user32.FindWindowW('Notepad++', None)
    if not npp:
        raise RuntimeError('Notepad++를 먼저 실행하고, 수집할 TXT 탭을 열어주시와요.')
    sci = get_scintilla(npp)
    if send_msg(sci, SCI_GETREADONLY):
        raise RuntimeError('Notepad++ 현재 탭이 읽기 전용입니다.')
    return npp, sci, send_msg(sci, SCI_GETDOCPOINTER)


def append_to_scintilla(npp, sci, docptr, text):
    if not user32.IsWindow(npp) or not user32.IsWindow(sci):
        raise RuntimeError('Notepad++가 닫혔습니다. F8을 눌러 다시 활성화하세요.')
    if get_scintilla(npp) != sci or send_msg(sci, SCI_GETDOCPOINTER) != docptr:
        raise RuntimeError('Notepad++의 대상 탭이 바뀌었습니다. 수집을 중지했습니다.')
    if send_msg(sci, SCI_GETREADONLY):
        raise RuntimeError('대상 문서가 읽기 전용입니다.')
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
        raise RuntimeError('문서 인코딩에서 표현할 수 없는 문자가 있습니다. UTF-8로 바꿔주세요.')
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
        raise RuntimeError('Notepad++ 편집 권한이 부족합니다. 두 프로그램의 권한 수준을 확인하세요.')
    remote = None
    try:
        remote = kernel32.VirtualAllocEx(proc, None, len(payload), MEM_COMMIT_RESERVE, PAGE_READWRITE)
        if not remote:
            raise RuntimeError('Notepad++ 임시 메모리를 할당할 수 없습니다.')
        buf = ct.create_string_buffer(payload, len(payload))
        written = ct.c_size_t(0)
        if not kernel32.WriteProcessMemory(proc, remote, buf, len(payload), ct.byref(written)) or written.value != len(payload):
            raise RuntimeError('Notepad++에 텍스트를 전달하지 못했습니다.')
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
        raise RuntimeError('Notepad++에 반영된 길이를 확인하지 못했습니다.')


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



MODES = ('Notepad++', 'Windows 메모장', 'Excel', 'Word', '한글(HWP)')


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


def remote_write_and_send(hwnd, msg, wparam, payload, timeout=3000):
    """Pass a buffer to another process; WM messages cannot read our pointer."""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ct.byref(pid))
    handle = kernel32.OpenProcess(PROCESS_VM_OPERATION | PROCESS_VM_WRITE, False, pid.value)
    if not handle:
        raise RuntimeError('편집 프로그램 메모리 접근 실패. 관리자 권한 수준을 확인하세요.')
    remote = None
    try:
        remote = kernel32.VirtualAllocEx(handle, None, len(payload), MEM_COMMIT_RESERVE, PAGE_READWRITE)
        if not remote:
            raise RuntimeError('편집기 임시 버퍼 할당 실패')
        written = ct.c_size_t()
        buf = ct.create_string_buffer(payload, len(payload))
        if not kernel32.WriteProcessMemory(handle, remote, buf, len(payload), ct.byref(written)) or written.value != len(payload):
            raise RuntimeError('편집기 텍스트 전달 실패')
        send_msg(hwnd, msg, wparam, remote, timeout)
    finally:
        if remote:
            kernel32.VirtualFreeEx(handle, remote, 0, MEM_RELEASE)
        kernel32.CloseHandle(handle)


def notepad_target():
    """Pick most-recently raised Notepad, then visible editable control."""
    for top in visible_windows():
        if process_name(top) != 'notepad.exe' and winclass(top) != 'Notepad':
            continue
        candidates = []
        def callback(hwnd, _):
            cls = winclass(hwnd).lower()
            if not user32.IsWindowVisible(hwnd):
                return True
            if cls == 'edit' or cls.startswith('richedit'):
                rect = wt.RECT()
                user32.GetClientRect(hwnd, ct.byref(rect))
                area = max(rect.right - rect.left, 0) * max(rect.bottom - rect.top, 0)
                # avoid Notepad's search bar by preferring large editing pane.
                score = area + (1_000_000 if cls.startswith('richeditd2d') else 0)
                candidates.append((score, hwnd))
            return True
        cb = ENUMPROC(callback)
        user32.EnumChildWindows(top, cb, 0)
        if candidates:
            candidates.sort(reverse=True)
            edit = candidates[0][1]
            return {'kind':'notepad','window':top,'editor':edit,'title':window_title(top)}
    raise RuntimeError('Windows 기본 메모장을 열고 편집할 문서를 선택해 주세요.')


def normalize_notepad_title(title):
    # Unsaved-change indicator may appear after the first appended item.
    return title.strip().lstrip('*●• ').strip()


def append_to_notepad(target, text):
    top = target['window']
    edit = target['editor']
    if not user32.IsWindow(top) or not user32.IsWindow(edit):
        raise RuntimeError('메모장 창이 닫혔습니다. 수집을 중지합니다.')
    if normalize_notepad_title(window_title(top)) != normalize_notepad_title(target['title']):
        raise RuntimeError('메모장 제목/탭이 변경되었습니다. 다른 문서로 기록하지 않도록 중지합니다.')
    # If app changes editing tab/window, don't silently write into another buffer.
    last = notepad_editor_for_window(top)
    if last != edit:
        raise RuntimeError('메모장 편집 탭이 바뀌었습니다. 수집을 중지합니다.')
    old_len = send_msg(edit, WM_GETTEXTLENGTH)
    lines = send_msg(edit, EM_GETLINECOUNT)
    line_start = send_msg(edit, EM_LINEINDEX, max(0, lines - 1))
    last_line_len = send_msg(edit, EM_LINELENGTH, line_start)
    prefix = '\r\n' if old_len and last_line_len else ''
    # Unicode payload; EM_REPLACESEL (Edit/RichEdit), not WM_SETTEXT.
    body = (prefix + text).encode('utf-16-le') + b'\x00\x00'
    send_msg(edit, EM_SETSEL, old_len, old_len)
    remote_write_and_send(edit, EM_REPLACESEL, 1, body)
    new_len = send_msg(edit, WM_GETTEXTLENGTH)
    if new_len <= old_len:
        raise RuntimeError('기본 메모장에서 입력 결과를 확인하지 못했습니다.')


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
        raise RuntimeError('Excel/Word/한글 연동에는 pywin32가 필요합니다. Office_HWP_설치.cmd 실행 후 다시 시도하세요.') from exc
    return pythoncom, win32


def acquire_excel():
    _, win32 = require_com()
    try:
        app = win32.GetActiveObject('Excel.Application')
        book = app.ActiveWorkbook
        sheet = app.ActiveSheet
        cell = app.ActiveCell
        if not book or not sheet or not cell or sheet.Type != -4167:
            raise ValueError('활성 워크시트가 없습니다.')
        if book.ReadOnly or sheet.ProtectContents:
            raise ValueError('읽기 전용 또는 보호된 시트입니다.')
        col, row = int(cell.Column), int(cell.Row)
        # Never overwrite existing content. User first selects an empty cell.
        if cell.Value2 is not None:
            raise ValueError('Excel에서 비어 있는 시작 셀을 선택한 후 F8을 누르세요.')
        return {'kind':'excel','app':app,'book':book,'sheet':sheet,'col':col,'next_row':row,
                'book_name':str(book.FullName),'sheet_name':str(sheet.Name),
                'label':f'{book.Name} / {sheet.Name} / {cell.Address}'}
    except Exception as exc:
        raise RuntimeError('실행 중인 Excel의 빈 시작 셀을 선택해 주세요. (' + str(exc) + ')') from exc


def append_to_excel(target, text):
    book, sheet = target['book'], target['sheet']
    if str(book.FullName) != target['book_name'] or str(sheet.Name) != target['sheet_name']:
        raise RuntimeError('Excel 대상 문서가 변경되었습니다.')
    row, col = target['next_row'], target['col']
    if row > 1048576 or len(text) > 32767:
        raise RuntimeError('Excel 셀 최대 행 또는 텍스트 길이(32,767자)를 초과했습니다.')
    cell = sheet.Cells(row, col)
    if cell.Value2 is not None:
        raise RuntimeError(f'Excel {cell.Address} 셀에 이미 내용이 있어 덮어쓰지 않고 중지했습니다.')
    if bool(sheet.ProtectContents) or bool(book.ReadOnly):
        raise RuntimeError('Excel 시트가 보호되어 있거나 읽기 전용입니다.')
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
            raise ValueError('읽기 전용 또는 보호된 문서입니다.')
        return {'kind':'word','app':app,'doc':doc,'path':str(doc.FullName),
                'label':str(doc.Name),'added':0}
    except Exception as exc:
        raise RuntimeError('실행 중인 Word의 편집 가능한 문서를 선택해 주세요. (' + str(exc) + ')') from exc


def append_to_word(target, text):
    doc = target['doc']
    if str(doc.FullName) != target['path'] or doc.ReadOnly or doc.ProtectionType != -1:
        raise RuntimeError('Word 대상 문서가 변경되었거나 편집 불가 상태입니다.')
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
            raise RuntimeError('실행 중인 한글(HWP) 자동화 객체를 찾지 못했습니다.') from exc
    if len(objects) > 1:
        raise RuntimeError('한글(HWP)이 여러 개 실행 중입니다. 오입력 방지를 위해 한 개만 열고 시도하세요.')
    hwp = objects[0]
    try:
        path = str(hwp.Path or '')
        if not path:
            raise ValueError('저장된 이름이 있는 한글 문서를 먼저 열어 주세요.')
        if int(hwp.EditMode) != 1:
            raise ValueError('현재 한글 문서가 일반 편집 모드가 아닙니다.')
        # Read once at start only, to avoid an unwanted blank first paragraph.
        body = hwp.GetTextFile('TEXT', 'saveall')
        has_content = bool(str(body or '').strip('\r\n\t \x00'))
        return {'kind':'hwp','hwp':hwp,'path':path,'has_content':has_content,
                'label':os.path.basename(path)}
    except Exception as exc:
        raise RuntimeError('한글의 편집 가능한 문서를 지정하지 못했습니다. (' + str(exc) + ')') from exc


def append_to_hwp(target, text):
    hwp = target['hwp']
    if str(hwp.Path or '') != target['path'] or int(hwp.EditMode) != 1:
        raise RuntimeError('한글 대상 문서가 변경되거나 편집 불가 상태가 되었습니다.')
    if not hwp.HAction.Run('MoveDocEnd'):
        raise RuntimeError('한글 문서 끝으로 이동하지 못했습니다.')
    if target['has_content']:
        if not hwp.HAction.Run('BreakPara'):
            raise RuntimeError('한글 문단 추가에 실패했습니다.')
    pset = hwp.HParameterSet.HInsertText
    hwp.HAction.GetDefault('InsertText', pset.HSet)
    pset.Text = text
    if not hwp.HAction.Execute('InsertText', pset.HSet):
        raise RuntimeError('한글 텍스트 삽입에 실패했습니다. 마지막 입력을 확인하세요.')
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
    raise RuntimeError('알 수 없는 대상 프로그램입니다.')


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
    raise RuntimeError('지원되지 않는 대상입니다.')


def normalize_line(value):
    line = re.sub(r'[\r\n\u2028\u2029\t]+', ' ', value).replace('\x00', '').strip()
    return line


class Collector:
    def __init__(self, events):
        self.events = events
        self.hwnd = None
        self.enabled = False
        self.count = 0
        self.mode = 0  # original behavior: Notepad++
        self.target = None
        self.last_sequence = 0
        self._callback = WNDPROC(self._wndproc)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _emit(self, kind, data=''):
        self.events.put((kind, data))

    def _run(self):
        initialized_com = False
        try:
            # COM calls remain on the one STA message-loop thread.
            try:
                import pythoncom
                pythoncom.CoInitialize()
                initialized_com = True
            except ImportError:
                pass  # Notepad++ and Notepad do not need COM
            instance = kernel32.GetModuleHandleW(None)
            class_name = 'NppClipboardCollector_Window_2'
            klass = WNDCLASSEXW()
            klass.cbSize = ct.sizeof(WNDCLASSEXW)
            klass.hInstance = instance
            klass.lpfnWndProc = self._callback
            klass.lpszClassName = class_name
            if not user32.RegisterClassExW(ct.byref(klass)):
                raise RuntimeError('Windows 메시지 창 등록 실패')
            self.hwnd = user32.CreateWindowExW(0, class_name, 'NppClipboardCollector', 0, 0, 0, 0, 0, HWND_MESSAGE, None, instance, None)
            if not self.hwnd:
                raise RuntimeError('Windows 메시지 창 생성 실패')
            clip_ok = user32.AddClipboardFormatListener(self.hwnd)
            hotkey_ok = user32.RegisterHotKey(self.hwnd, HOTKEY_ID, 0, VK_F8)
            if not clip_ok:
                raise RuntimeError('클립보드 변경 감지 등록 실패')
            if not hotkey_ok:
                self._emit('notice', 'F8이 다른 프로그램에 등록되어 있습니다. 화면 버튼으로 전환하세요.')
            else:
                self._emit('notice', '준비 완료. 대상 프로그램을 선택한 뒤 F8을 누르세요.')
            self._emit('ready', hotkey_ok)
            message = wt.MSG()
            while user32.GetMessageW(ct.byref(message), None, 0, 0) > 0:
                user32.TranslateMessage(ct.byref(message))
                user32.DispatchMessageW(ct.byref(message))
            if hotkey_ok:
                user32.UnregisterHotKey(self.hwnd, HOTKEY_ID)
            user32.RemoveClipboardFormatListener(self.hwnd)
        except Exception as exc:
            self._emit('error', str(exc))
        finally:
            if initialized_com:
                pythoncom.CoUninitialize()

    def _toggle(self):
        if self.enabled:
            self.enabled = False
            self.target = None
            self._emit('state', (False, '대기 중'))
            self._emit('notice', '자동 수집을 중지했습니다.')
            return
        try:
            self.target = acquire_target(self.mode)
            self.last_sequence = user32.GetClipboardSequenceNumber()
            self.count = 0
            self.enabled = True
            self._emit('state', (True, self.target['label']))
            self._emit('count', 0)
            self._emit('notice', '수집 ON. 브라우저에서 복사하면 지정된 문서에 한 줄씩 추가합니다.')
        except Exception as exc:
            self.enabled = False
            self.target = None
            self._emit('state', (False, '대기 중'))
            self._emit('notice', str(exc))

    def _copy_event(self):
        if not self.enabled:
            return
        seq = user32.GetClipboardSequenceNumber()
        if not seq or seq == self.last_sequence:
            return
        self.last_sequence = seq
        if not browser_is_foreground():
            return
        value = read_clipboard(self.hwnd)
        if value is None:
            return
        line = normalize_line(value)
        if not line:
            return
        if len(line) > 500_000:
            self._emit('notice', '복사 문구가 50만 자를 넘어 건너뛰었습니다.')
            return
        try:
            append_to_target(self.target, line)
            self.count += 1
            self._emit('count', self.count)
            self._emit('notice', f'{self.count}개 추가 완료. 편집기에서 저장(Ctrl+S)하세요.')
        except Exception as exc:
            self.enabled = False
            self.target = None
            self._emit('state', (False, '대기 중'))
            self._emit('notice', '수집 OFF: ' + str(exc))

    def _wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_HOTKEY and wparam == HOTKEY_ID:
                self._toggle()
                return 0
            if msg == WM_APP_TOGGLE:
                self._toggle()
                return 0
            if msg == WM_APP_MODE:
                if not self.enabled and 0 <= int(wparam) < len(MODES):
                    self.mode = int(wparam)
                    self._emit('notice', f'대상 프로그램: {MODES[self.mode]}. F8로 시작하세요.')
                return 0
            if msg == WM_CLIPBOARDUPDATE:
                self._copy_event()
                return 0
            if msg == WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
        except Exception as exc:
            self.enabled = False
            self.target = None
            self._emit('state', (False, '대기 중'))
            self._emit('notice', '오류: ' + str(exc))
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def toggle_from_ui(self):
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_APP_TOGGLE, 0, 0)

    def set_mode_from_ui(self, mode):
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_APP_MODE, mode, 0)

    def close(self):
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)


def main():
    if struct.calcsize('P') != 8:
        messagebox.showerror('실행 환경 오류', '64비트 Python으로 실행해 주세요.')
        return
    root = tk.Tk()
    root.title('NotepadPP Clipboard Collector v0.2.0')
    root.geometry('570x350')
    root.minsize(490, 335)
    root.configure(bg='#151923')
    fg, muted = '#f0f3fa', '#a8b1c5'
    frame = tk.Frame(root, bg='#151923', padx=20, pady=18)
    frame.pack(fill='both', expand=True)
    tk.Label(frame, text='Clipboard Collector', bg='#151923', fg=fg,
             font=('Malgun Gothic', 17, 'bold')).pack(anchor='w')
    tk.Label(frame, text='브라우저에서 복사 → 열린 문서에 한 줄씩 추가', bg='#151923', fg=muted,
             font=('Malgun Gothic', 10)).pack(anchor='w', pady=(4, 12))
    tk.Label(frame, text='기록 대상', bg='#151923', fg=fg,
             font=('Malgun Gothic', 10, 'bold')).pack(anchor='w')
    mode_var = tk.StringVar(value=MODES[0])
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Collector.TCombobox', font=('Malgun Gothic', 10))
    combo = ttk.Combobox(frame, textvariable=mode_var, values=MODES, state='readonly', style='Collector.TCombobox')
    combo.pack(fill='x', pady=(4, 10))
    state_var = tk.StringVar(value='● OFF  |  F8로 시작')
    state_label = tk.Label(frame, textvariable=state_var, bg='#151923', fg='#ee9e9e',
                           font=('Malgun Gothic', 14, 'bold'))
    state_label.pack(anchor='w')
    target_var = tk.StringVar(value='대상: 없음')
    tk.Label(frame, textvariable=target_var, bg='#151923', fg=muted, anchor='w',
             justify='left', wraplength=510, font=('Malgun Gothic', 9)).pack(fill='x', pady=(7, 6))
    count_var = tk.StringVar(value='추가한 항목: 0개')
    tk.Label(frame, textvariable=count_var, bg='#151923', fg=fg,
             font=('Malgun Gothic', 10)).pack(anchor='w', pady=(0, 6))
    notice_var = tk.StringVar(value='준비 중...')
    tk.Label(frame, textvariable=notice_var, bg='#151923', fg=muted,
             wraplength=510, justify='left', anchor='w', font=('Malgun Gothic', 9)).pack(fill='x')
    events = queue.Queue()
    collector = Collector(events)
    def on_mode(_=None):
        collector.set_mode_from_ui(MODES.index(mode_var.get()))
    combo.bind('<<ComboboxSelected>>', on_mode)
    btn = tk.Button(frame, text='F8  |  수집 ON / OFF', command=collector.toggle_from_ui,
                    bg='#315d91', fg='white', activebackground='#447aba', activeforeground='white',
                    font=('Malgun Gothic', 11, 'bold'), relief='flat', pady=7, cursor='hand2')
    btn.pack(fill='x', side='bottom')

    def poll():
        try:
            while True:
                kind, data = events.get_nowait()
                if kind == 'state':
                    on, title = data
                    state_var.set('● ON  |  F8로 중지' if on else '● OFF  |  F8로 시작')
                    state_label.config(fg='#81e4a5' if on else '#ee9e9e')
                    target_var.set('대상: ' + title if on else '대상: 없음')
                    combo.configure(state='disabled' if on else 'readonly')
                elif kind == 'count':
                    count_var.set(f'추가한 항목: {data}개')
                elif kind in ('notice', 'error'):
                    notice_var.set(data)
        except queue.Empty:
            pass
        root.after(100, poll)
    root.after(100, poll)

    def on_close():
        collector.close()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()

if __name__ == '__main__':
    main()
