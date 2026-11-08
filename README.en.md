[한국어](README.md) · **English**

# Clipboard Collector

A Windows tool that collects text copied in a browser and appends it to an open editor. Press F8 to toggle collection. Multiline text is flattened to a single line, and copying the same text again adds another entry.

This program was developed on Windows 11. Operation on Linux, macOS, or other environments is not guaranteed.

## Getting started

1. Download `Clipboard_Collector_v0.2.1.zip` from [Releases](../../releases) and extract it.
2. Install [64-bit Python 3.9 or later](https://www.python.org/downloads/windows/) on Windows x64. To use Excel, Word, or Hancom Hangul, run `Install_Office_HWP_Support.cmd` once to install pywin32.
   If you're unsure which Python version to install, we recommend **[Python 3.13.17 (Windows 64-bit)](https://www.python.org/downloads/release/python-31317/#files)**.
3. Open the destination document or tab, then run `Run.cmd`.
4. Select the destination and press F8. Copy text in your browser with Ctrl+C or a page's copy button.
5. Press F8 again to stop collection. Check the results and save them in the destination app.

| Destination | Where text is added |
| --- | --- |
| Notepad++ | At the end of the active tab |
| Windows Notepad | At the end of the open editor |
| Excel | One entry per row, starting at the selected empty cell and moving down the same column |
| Word | One paragraph at a time at the end of the current document |
| Hancom Hangul (HWP) | One paragraph at a time at the end of an open, previously saved document |

Collection runs only while a supported browser is in the foreground. Supported browsers include Chrome, Edge, Firefox, Brave, Vivaldi, and Opera. Excel collection stops when it reaches an occupied cell. Hancom Hangul requires a setup that supports COM automation. If F8 conflicts with another app, use the on-screen toggle.

Collection was verified on Windows 11 in Notepad++, Windows Notepad, Excel, and Word. Hancom Hangul (HWP) has yet to be tested. Try unverified destinations with a test document first and save the collected text in the destination app.

## Building an EXE

Run `Build_EXE.cmd` to install PyInstaller and pywin32 and build `dist/NotepadPP_ClipboardCollector.exe`. The release ZIP contains the Python source and launch scripts.

[Detailed guide (Korean)](README.txt) · [Changelog (Korean)](CHANGELOG.txt)

## Permission

You may use and modify this software and redistribute original or modified copies free of charge. You may not sell original or modified copies or charge for downloading or providing them. [Full permission notice](LICENSE.md)
