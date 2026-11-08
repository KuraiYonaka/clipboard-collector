[한국어](README.md) · **English**

# Clipboard Collector

A Windows tool that collects text copied in a browser and appends it to an open editor. Press F8 to toggle collection. Multiline text is flattened to a single line, and copying the same text again adds another entry.

## Getting started

1. Download `NotepadPP_ClipboardCollector_v0.2.0.zip` from [Releases](../../releases) and extract it.
2. Install 64-bit Python 3.9 or later on Windows x64. To use Excel, Word, or Hancom Hangul, run `Office_HWP_설치.cmd` once to install pywin32.
3. Open the destination document or tab, then run `실행.cmd`.
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

The Windows Notepad, Excel, Word, and Hangul modes in v0.2.0 have yet to be tested on Windows. Try them with a test document first. The collector appends to the editor, and you save the results in the destination app.

## Building an EXE

Run `EXE_빌드.cmd` to install PyInstaller and pywin32 and build `dist/NotepadPP_ClipboardCollector.exe`. The release ZIP contains the Python source and launch scripts.

[Detailed guide (Korean)](README.txt) · [Changelog (Korean)](CHANGELOG.txt)

## Permission

You may use and modify this software and redistribute original or modified copies free of charge. You may not sell original or modified copies or charge for downloading or providing them. [Full permission notice](LICENSE.md)
