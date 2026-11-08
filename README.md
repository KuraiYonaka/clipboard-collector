**한국어** · [English](README.en.md)

# Clipboard Collector

브라우저에서 복사한 텍스트를 열려 있는 편집기에 한 줄씩 모으는 Windows 도구입니다. F8로 수집을 켜고 끌 수 있습니다. 여러 줄은 한 줄로 정리되며, 같은 텍스트를 다시 복사해도 기록됩니다.

이 프로그램은 Windows 11 환경에서 개발했습니다. Linux, macOS 등 다른 환경에서의 동작은 보장하지 않습니다.

## 시작하기

1. [Releases](../../releases/latest)에서 `Clipboard_Collector_v1.0.0.zip`을 내려받아 압축을 풉니다.
2. `Clipboard Collector.exe`를 실행합니다. Windows 11 64비트에서 Python이나 pywin32를 따로 설치할 필요가 없습니다.
3. 기록할 문서나 탭을 대상 앱에서 열어 둡니다.
4. 프로그램 창에서 대상을 선택하고 F8을 눌러 켭니다. 브라우저에서 Ctrl+C나 웹페이지의 복사 버튼으로 텍스트를 복사합니다.
5. F8로 수집을 끈 뒤 대상 앱에서 결과를 확인하고 직접 저장합니다.

| 대상 | 기록 위치 |
| --- | --- |
| Notepad++ | 활성 탭 끝 |
| Windows 메모장 | 열려 있는 편집기 끝 |
| Excel | 선택한 빈 셀부터 같은 열 아래로 한 항목씩 |
| Word | 현재 문서 끝에 한 문단씩 |
| 한컴오피스 한글 | 열려 있는 저장된 문서 끝에 한 문단씩 |

브라우저가 전면에 있을 때만 수집합니다. 지원 브라우저는 Chrome, Edge, Firefox, Brave, Vivaldi, Opera입니다. Excel에서는 기존 데이터가 있는 셀에 도달하면 수집을 멈춥니다. 한글은 COM 자동화가 가능한 설치 환경이 필요합니다. F8이 다른 프로그램과 겹치면 화면의 버튼을 사용하세요.

Windows 11에서 Notepad++, 기본 메모장, Excel, Word의 수집 동작을 확인했습니다. 한컴오피스 한글(HWP)은 아직 실기 검증하지 않았습니다. 먼저 테스트 문서에서 확인해 주세요. 수집 내용은 대상 앱에서 직접 저장합니다.

## 소스에서 실행하거나 빌드하기

`Clipboard_Collector_v1.0.0.zip`에는 EXE와 한·영 상세 설명서 외에 Python 소스와 실행 스크립트도 들어 있습니다. 소스에서 실행하려면 Windows용 64비트 Python 3.9 이상을 설치하고 `Run.cmd`를 실행하세요. Excel, Word, 한글 연동을 쓰려면 먼저 `Install_Office_HWP_Support.cmd`를 한 번 실행합니다.

Python 버전 선택이 어려우신 분께는 **[Python 3.13.17 (Windows 64-bit)](https://www.python.org/downloads/release/python-31317/#files)** 설치를 추천합니다.

`Build_EXE.cmd`를 실행하면 PyInstaller와 pywin32를 설치하고 `dist/NotepadPP_ClipboardCollector.exe`를 만듭니다.

[상세 사용설명서](README.txt) · [영문 상세 사용설명서](USER_GUIDE.en.txt) · [변경 이력](CHANGELOG.txt)

## 이용 허가

이 프로그램을 사용하거나 수정(개조)할 수 있으며, 원본과 수정본을 무료로 재배포할 수 있습니다. 원본이나 수정본을 판매하거나, 다운로드 또는 제공의 대가로 요금을 받는 것은 허용하지 않습니다. [이용 허가 전문](LICENSE.md)
