**한국어** · [English](README.en.md)

# Clipboard Collector

복사한 텍스트와 이미지를 열린 문서에 모으는 Windows 도구입니다. 브라우저만 수집하거나 모든 앱에서 수집할 수 있고, 여러 대상에 동시에 기록할 수 있습니다.

## 시작하기

1. [최신 릴리스](../../releases/latest)에서 `Clipboard_Collector_v1.2.3.zip`을 내려받아 전부 압축 해제합니다.
2. `Clipboard Collector.exe`를 실행합니다. Windows 11 64비트에서는 Python을 별도로 설치할 필요가 없습니다. `_internal` 폴더를 EXE와 함께 보관하세요.
3. 기록할 문서를 열고 대상을 선택합니다. Excel은 시작할 빈 셀을 한 번 클릭하세요. 셀 편집 중이면 Excel에서 편집을 먼저 마칩니다.
4. 수집을 시작하고 원하는 내용을 복사합니다. Excel이나 Word에 이미지를 넣으려면 **이미지 수집**을 켜세요.

| 대상 | 텍스트 기록 위치 | 이미지 |
| --- | --- | --- |
| Notepad++ · Windows 메모장 | 활성 문서 끝 | — |
| Excel | 선택한 빈 셀부터 같은 열 아래로 | 원본 크기로 삽입 |
| Word | 문서 끝 | 원본 크기로 삽입 |
| 한컴오피스 한글(HWP) | 미리 저장해 둔 열린 문서 끝 | — |

Excel과 Word는 수집할 때마다 또는 수집을 끌 때 저장할 수 있습니다. **모아 둔 텍스트 보내기**로 기존 텍스트를 Excel이나 Word에 줄 단위로 보낼 수 있습니다. 프로그램에서 한국어와 영어를 바꾸고, 전역 단축키를 설정할 수 있습니다.

Windows 11에서 개발했습니다. Excel과 Word의 이미지 삽입 및 저장을 확인했습니다. HWP 텍스트 기록은 실기 미검증입니다.

## 소스에서 실행 및 빌드

64비트 Windows용 [Python](https://www.python.org/downloads/windows/)이 필요합니다. Office/HWP 연동 및 이미지 수집을 사용하려면 `Install_Office_HWP_Support.cmd`를 실행한 뒤 `Run.cmd`로 시작하세요. `Build_EXE.cmd`는 폴더형 Windows 실행 파일을 빌드합니다.

[한글 사용설명서](README.txt) · [English user guide](USER_GUIDE.en.txt) · [이용 및 재배포 정책](LICENSE.md)
