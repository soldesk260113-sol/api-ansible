# app/services/air_parser.py
import re
from statistics import mean
from xml.etree import ElementTree as ET

def parse_seoul_grade(xml_text: str, target_date: str) -> dict:
    """
    예보 XML에서 informGrade 문자열 중 '서울 : 보통' 같은 부분만 추출
    """
    try:
        root = ET.fromstring(xml_text)
        items = root.findall(".//item")
        for it in items:
            inform_data = (it.findtext("informData") or "").strip()
            if inform_data != target_date:
                continue

            data_time = (it.findtext("dataTime") or "").strip()
            inform_grade = (it.findtext("informGrade") or "").strip()

            # '서울 : 보통' 패턴 추출 (쉼표로 지역 나열)
            m = re.search(r"서울\s*:\s*([^,]+)", inform_grade)
            if not m:
                return {"ok": False, "reason": "SEOUL_NOT_FOUND", "dataTime": data_time, "raw": inform_grade}

            return {"ok": True, "dataTime": data_time, "seoulGrade": m.group(1).strip()}

        return {"ok": False, "reason": "DATE_NOT_FOUND"}
    except Exception as e:
        return {"ok": False, "reason": "PARSE_ERROR", "error": str(e)}

def _to_int(v):
    # AirKorea는 '-' 같은 값이 올 수 있음
    if v is None:
        return None
    s = str(v).strip()
    if not s or s == "-":
        return None
    try:
        return int(float(s))
    except:
        return None

def parse_seoul_realtime(realtime_json: dict, kind: str, station: str | None = None) -> dict:
    """
    실시간 JSON에서 pm10/pm25 수치 추출
    - station 지정되면 그 측정소 값
    - 없으면 서울 전체 평균(avg) + 최솟값/최댓값 제공
    kind: "PM10" or "PM25"
    """
    try:
        items = realtime_json["response"]["body"]["items"]
        key = "pm10Value" if kind == "PM10" else "pm25Value"

        rows = []
        for it in items:
            if station and (it.get("stationName") != station):
                continue
            rows.append({
                "stationName": it.get("stationName"),
                "dataTime": it.get("dataTime"),
                "value": _to_int(it.get(key)),
            })

        rows = [r for r in rows if r["value"] is not None]
        if not rows:
            return {"ok": False, "reason": "NO_DATA", "kind": kind, "station": station}

        # 대표 dataTime은 첫 row 기준(대부분 동일)
        data_time = rows[0]["dataTime"]

        if station:
            return {"ok": True, "kind": kind, "dataTime": data_time, "station": station, "value": rows[0]["value"]}

        values = [r["value"] for r in rows]
        return {
            "ok": True,
            "kind": kind,
            "dataTime": data_time,
            "agg": "avg",
            "value": round(mean(values), 1),
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }
    except Exception as e:
        return {"ok": False, "reason": "PARSE_ERROR", "error": str(e)}

