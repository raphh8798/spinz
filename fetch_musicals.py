"""
KOPIS(공연예술통합전산망) Open API 기반 뮤지컬 정보 수집 스크립트

- 공연목록조회(pblprfr): 장르 GGGA(뮤지컬) 고정, afterdate로 증분 수집
- 신규 공연만 공연상세조회(pblprfr/{mt20id}) 추가 호출
- PostgreSQL에 upsert

실행: python fetch_musicals.py [--full] [--days N]
    --full      : afterdate 없이 전체 수집 (최초 1회 실행 시 사용)
    --days N    : 오늘 기준 N일 전부터 변경분 수집 (기본값 1, 즉 어제 이후)
"""

import requests, os, sys, argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from db import get_db_connection
import time



list_field = [
    "mt20id", "prfnm", "prfpdfrom", "prfpdto", "fcltynm",
    "poster", "area", "genrenm", "openrun", "prfstate"
]

list_field_detail = [
    "mt20id", "mt13id", "frstregdt", "prfcast", "prfcrew", "prfruntime", "prfage",
    "entrpsnm", "entrpsnmP", "entrpsnmA", "entrpsnmH", "entrpsnmS", "pcseguidance", "sty",
    "visit", "child", "daehakro", "festival", "musicallicense", "musicalcreate", "updatedate", "mt10id", "dtguidance",
    "styurls", "relates"
]

KOPIS_SERVICE_KEY = os.getenv("KOPIS_SERVICE_KEY")
BASE_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"
GENRE = "GGGA"  # 뮤지컬
ROWS_PER_PAGE = 100  # KOPIS: 페이지당 최대 100건


# 트래픽 제한 방지
def request_with_retry(url, params, tries=3, backoff=3.0):
    for i in range(tries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code < 400:
                return resp
            if i == tries - 1:
                resp.raise_for_status()
        except requests.exceptions.RequestException:
            if i == tries - 1:
                raise
        time.sleep(backoff * (i + 1))
    return resp


def parse_xml_data(stdate, eddate, afterdate=None):
    db_list = []
    cur_start = datetime.strptime(stdate, "%Y%m%d")
    end_limit = datetime.strptime(eddate, "%Y%m%d")

    while cur_start <= end_limit:
        cur_end = min(cur_start + timedelta(days=30), end_limit)  # 최대 31일
        chunk_stdate = cur_start.strftime("%Y%m%d")
        chunk_eddate = cur_end.strftime("%Y%m%d")

        cpageNo = 1
        while True:
            params = {
                    "service": KOPIS_SERVICE_KEY,
                    "stdate": chunk_stdate, "eddate": chunk_eddate,
                    "cpage": cpageNo, "rows": ROWS_PER_PAGE,
                    "shcate": GENRE,
                }
            if afterdate:
                params["afterdate"] = afterdate

            resp = request_with_retry(BASE_URL, params)
            data = ET.fromstring(resp.text).findall("db")
            if not data:
                break

            for d in data:
                db_list.append({l: d.findtext(l) for l in list_field})

            if len(data) < ROWS_PER_PAGE:
                break

            cpageNo += 1

        print(f"  [진행] {chunk_stdate}~{chunk_eddate} 완료 / 누적 {len(db_list)}건")
        cur_start = cur_end + timedelta(days=1)

    return db_list


def parse_xml_detail(cur, mt20id):
    params = { "service": KOPIS_SERVICE_KEY }
    resp = request_with_retry(f"{BASE_URL}/{mt20id}", params)

    data = ET.fromstring(resp.text).findall("db")
    if len(data) == 0:
        return None
    
    db_data = {}
    for d in data:
        for l in list_field_detail:
            if l == "styurls":
                upsert_styurl(cur, d.findtext("mt20id"), [s.text for s in d.find("styurls").findall("styurl")])
            elif l == "relates":
                relates = d.find(l).findall("relate")
                relates_list = []
                for r in relates:
                    rel_data = {}
                    rel_data["relatenm"] = r.findtext("relatenm")
                    rel_data["relateurl"] = r.findtext("relateurl")
                    relates_list.append(rel_data)

                upsert_relate(cur, d.findtext("mt20id"), relates_list)
                
            else:
                db_data[l.lower()] = d.findtext(l)

    return db_data


def upsert_perform(cur, item):
    cols = cols = ", ".join(list_field)
    placeholders = ", ".join(f"%({c.lower()})s" for c in list_field)
    # updatedate만 예외 처리 필요하면 따로 빼거나 dict 키를 API값 그대로 쓰기
    cur.execute(
    """
        INSERT INTO PERFORM_MASTER (
    """
        + cols +
    """
        ) VALUES (
    """
        + placeholders +
    """
        )
        ON CONFLICT (mt20id) DO UPDATE SET
            prfnm = EXCLUDED.prfnm,
            prfpdfrom = EXCLUDED.prfpdfrom,
            prfpdto = EXCLUDED.prfpdto,
            fcltynm = EXCLUDED.fcltynm,
            poster = EXCLUDED.poster,
            area = EXCLUDED.area,
            genrenm = EXCLUDED.genrenm,
            openrun = EXCLUDED.openrun,
            prfstate = EXCLUDED.prfstate,
            UPDATED_AT = NOW()
    """, item
    )


def upsert_detail(cur, detail):
    cols = ", ".join(("kopis_updatedate" if e == "updatedate" else e)
                      for e in list_field_detail if e not in ("styurls", "relates"))
    placeholders = ", ".join(f"%({c.lower()})s" for c in list_field_detail if c not in ("styurls", "relates"))

    cur.execute(
        """
        INSERT INTO PERFORM_DETAIL (
    """
        + cols +
    """
        ) VALUES (
    """ 
        + placeholders +
    """
        )
        ON CONFLICT (mt20id) DO UPDATE SET
            mt13id = EXCLUDED.mt13id,
            frstregdt = EXCLUDED.frstregdt,
            prfcast = EXCLUDED.prfcast,
            prfcrew = EXCLUDED.prfcrew,
            prfruntime = EXCLUDED.prfruntime,
            prfage = EXCLUDED.prfage,
            entrpsnm = EXCLUDED.entrpsnm,
            entrpsnmp = EXCLUDED.entrpsnmp,
            entrpsnmh = EXCLUDED.entrpsnmh,
            entrpsnma = EXCLUDED.entrpsnma,
            entrpsnms = EXCLUDED.entrpsnms,
            pcseguidance = EXCLUDED.pcseguidance,
            sty = EXCLUDED.sty,
            visit = EXCLUDED.visit,
            child = EXCLUDED.child,
            daehakro = EXCLUDED.daehakro,
            festival = EXCLUDED.festival,
            musicallicense = EXCLUDED.musicallicense,
            musicalcreate = EXCLUDED.musicalcreate,
            KOPIS_UPDATEDATE = EXCLUDED.kopis_updatedate,
            mt10id = EXCLUDED.mt10id,
            dtguidance = EXCLUDED.dtguidance,
            updated_at = NOW()
        """,
        detail
    )


def upsert_styurl(cur, mt20id, styurls:list):
    for i in range(0, len(styurls)):
        cur.execute(
            "INSERT INTO PERFORM_STYURL(MT20ID, NO, STYURL) VALUES (%s, %s, %s)",
            ( mt20id, i, styurls[i] )
        )


def upsert_relate(cur, mt20id, relates:list[dict]):
    for i in range(0, len(relates)):
        cur.execute(
            "INSERT INTO PERFORM_RELATE(MT20ID, NO, RELATENM, RELATEURL) VALUES (%s, %s, %s, %s)",
            (mt20id, i, relates[i]["relatenm"], relates[i]["relateurl"] )
        )


# 신규인지 확인
def is_new_perform_detail(cur, mt20id):
    cur.execute("SELECT 1 FROM PERFORM_DETAIL WHERE mt20id = %s", (mt20id,))
    return cur.fetchone() is None


def main():
    if not KOPIS_SERVICE_KEY:
        print("ERROR: KOPIS_SERVICE_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="전체 수집 (eddate 미사용)")
    parser.add_argument("--days", type=int, default=1, help="N일 전부터 변경분 수집")
    args = parser.parse_args()

    # stdate/eddate : 어느 기간 안에서 찾을지 범위 지정
    # afterdate : 지정 범위 내에서 최근에 바뀐 것만
    stdate = "20200101"
    eddate = (datetime.now() + timedelta(days=365)).strftime("%Y%m%d")
    afterdate = None if args.full else (datetime.now() - timedelta(days=args.days)).strftime("%Y%m%d")

    print(f"[시작] 뮤지컬 목록 수집 (afterdate={afterdate or '전체'})")
    items = parse_xml_data(stdate, eddate, afterdate)
    print(f"[완료] 총 {len(items)}건 수집")

    if len(items) > 0:
        conn = get_db_connection()
        cur = conn.cursor()

        new_count = 0
        for i, item in enumerate(items, 1):
            upsert_perform(cur, item)

            if i % 50 == 0:
                print(f"  [진행] {i}/{len(items)}")

            # 신규 공연만 상세조회 추가 호출
            if is_new_perform_detail(cur, item["mt20id"]):
                detail = parse_xml_detail(cur, item["mt20id"])
                if detail:
                    upsert_detail(cur, detail)
                    new_count += 1

        conn.commit()
        cur.close()
        conn.close()

        print(f"[종료] 목록 {len(items)}건 처리 / 신규 상세 {new_count}건 추가")



if __name__ == "__main__":
    main()