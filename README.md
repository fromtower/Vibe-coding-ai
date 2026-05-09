# 영남대 정보통신공학과 공지사항 검색기

영남대 ICE 학과 공지사항을 긁어와서 바로 검색할 수 있는 데스크탑 앱

## 기능
- 공지사항 자동 수집 (최대 4페이지)
- 카테고리별 필터링 (장학 / 학사 / 일반 / 취업)
- 키워드 검색
- URL 원클릭 복사

## 실행
```bash
pip install requests beautifulsoup4 pydantic
python main.py

## 구조

main.py       # 진입점
gui.py        # tkinter UI
scraper.py    # 공지 크롤러
database.py   # SQLite 저장 / 검색
models.py     # 데이터 모델
