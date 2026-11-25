# 해금 초견 라운지 (Haegeum Sight-Reading Lounge)

해금 초견 교본 150곡 프로젝트의 **시범 30곡**과, 그것을 바로 연습할 수 있는 정적 웹 라운지입니다.

- 기초 1~10 · 중급 51~60 · 고급 101~110
- 각 곡 **8단 × 4마디 = 32마디**, 한 페이지
- 음역 **A3~C6**, 조표 E♭(11) · B♭(7) · A♭(6) · F(3) · D♭(3)
- 악보 PNG(고해상) + 인쇄용 PDF(A4 1장)

## 구성

```
index.html            라운지 화면 (탭 · 악보 모달 · 150곡 목차)
assets/style.css      화면 스타일
assets/app.js         탭/모달/확대/내비게이션
data/pieces.js        30곡 메타데이터 (자동 생성)
pieces.json           같은 데이터의 JSON
scores/001.png ...    악보 원본 (2132×3436)
scores/001.pdf ...    인쇄용 PDF
scores/thumb/         카드용 썸네일
tools/                악보 생성기 (Python)
```

## 악보 제작 방식

`tools/gen_scores.py`가 MusicXML을 만들고, Verovio(Bravura)로 조판한 뒤 resvg_py로 래스터화하고
PyMuPDF로 PDF를 씁니다. 조판 규칙:

- 여백 테두리 없음, 좌상단 번호 박스
- 우상단 `LEE SEUNG CHUL (with AI)` 크레딧
- 하단 `무단 복제 및 배포를 절대 금합니다.`
- 템포는 벡터로 그린 4분음표/점4분음표 + `= BPM`
- 1음 장식음은 슬래시, 2음 이상은 16분음표로 묶어 빔
- 박자·조표가 바뀌는 마디 앞에는 겹세로줄
- `divisions=12` 기준으로 모든 마디 길이를 프로그램으로 검증 (4/4=48, 3/4=36, 2/4=24, 12/8=72, 9/8=54, 6/8=36, 5/8=30, 7/8=42)

다시 만들기:

```bash
cd tools
python make_all.py            # 30곡 전체
python make_all.py 51 101     # 특정 곡만
```

## 저작권

악보와 화면의 저작권은 LEE SEUNG CHUL 에게 있습니다.
**무단 복제 및 배포를 절대 금합니다.**
