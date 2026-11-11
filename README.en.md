**English** · [한국어](README.md)

# Clipboard Collector

Collect copied text and pictures in open documents on Windows. Collect from browsers or all apps, and send entries to multiple destinations at once.

## Getting started

1. Download `Clipboard_Collector_v1.2.3.zip` from the [latest release](../../releases/latest) and extract the entire archive.
2. Run `Clipboard Collector.exe`. The 64-bit Windows 11 build includes its Python runtime. Keep the `_internal` folder next to the EXE.
3. Open your documents and select the destinations. In Excel, click an empty starting cell once. Finish any active cell edit first.
4. Start collection and copy the items you want to keep. Turn on **Collect pictures** to insert images in Excel or Word.

| Destination | Text placement | Pictures |
| --- | --- | --- |
| Notepad++ and Windows Notepad | End of the active document | — |
| Excel | Down the same column from the selected empty cell | Inserted at original size |
| Word | End of the document | Inserted at original size |
| Hancom Hangul (HWP) | End of a previously saved, open document | — |

Excel and Word support saving after each entry or when stopping collection. Use **Send collected text** to send existing text to Excel or Word one line at a time. The app supports Korean and English and an optional global shortcut.

Developed on Windows 11. Picture insertion and saving were tested in Excel and Word. HWP text collection has not been tested in Hancom Hangul.

## Running from source and building

Install [64-bit Python for Windows](https://www.python.org/downloads/windows/). For Office/HWP integration and picture collection, run `Install_Office_HWP_Support.cmd` before starting with `Run.cmd`. `Build_EXE.cmd` builds the folder-based Windows package.

[English user guide](USER_GUIDE.en.txt) · [한국어 사용설명서](README.txt) · [Use and redistribution policy](LICENSE.md)
