**English** · [한국어](README.md)

# Clipboard Collector

Collect copied text and pictures in open documents on Windows. Collect from browsers or all apps, and send entries to multiple destinations at once.

## Getting started

1. Download `Clipboard_Collector_v1.2.3.zip` from the [latest release](../../releases/latest) and extract the entire archive.
2. Run `Clipboard Collector.exe`. The 64-bit Windows 11 build includes its Python runtime. Keep the `_internal` folder next to the EXE.
3. Open your documents and select the destinations. In Excel, click an empty starting cell once. Finish any active cell edit first.
4. Start collection and copy the items you want to keep. Turn on **Collect pictures** to insert images in Excel or Word.

## Features in 1.2.3

- **Choose where to collect from** — Use **Browsers only** for web research or **All apps** to also collect copies from screen capture tools and other apps.
- **Insert pictures in Excel and Word** — Insert copied images and screenshots at their original size. In Excel, the first picture is anchored at the selected empty cell, and the next entry starts in the first row below it.
- **Write to several documents** — Choose **Additional destinations** to send the same copied text to several open documents. Pictures go to Excel and Word.
- **Send collected text** — Paste text gathered in Notepad or another editor to send it to Excel or Word one line at a time. Blank lines are skipped.
- **Set saving and controls** — Choose to save Excel and Word after each entry, when stopping collection, or manually. Switch between Korean and English in the app and set an optional start/stop shortcut.

## Supported destinations

| Destination | Text placement | Pictures |
| --- | --- | --- |
| Notepad++ and Windows Notepad | End of the active document | — |
| Excel | Down the same column from the selected empty cell | Inserted at original size |
| Word | End of the document | Inserted at original size |
| Hancom Hangul (HWP) | End of a previously saved, open document | — |

Developed on Windows 11. Picture insertion and saving were tested in Excel and Word. HWP text collection has not been tested in Hancom Hangul.

## Running from source and building

Install [64-bit Python for Windows](https://www.python.org/downloads/windows/). For Office/HWP integration and picture collection, run `Install_Office_HWP_Support.cmd` before starting with `Run.cmd`. `Build_EXE.cmd` builds the folder-based Windows package.

[English user guide](USER_GUIDE.en.txt) · [한국어 사용설명서](README.txt) · [Use and redistribution policy](LICENSE.md)
