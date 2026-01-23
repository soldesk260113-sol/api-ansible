# app/services/time_rules.py
from datetime import datetime, timedelta
from typing import Optional, Tuple

# KMA 동네예보(단기예보) 발표 시각 (KST 기준)
# 일반적으로 2시간 50분 전후로 생성/제공되며, 아래 8개 시각이 기준이 됨.
VILAGE_FCST_BASE_TIMES = (2, 5, 8, 11, 14, 17, 20, 23)


def _floor_to_latest_base_time(now: datetime, base_hours=VILAGE_FCST_BASE_TIMES) -> Tuple[str, str]:
    """
    now 기준으로, base_hours 중 '가장 최근' 시각을 찾아 base_date/base_time을 만든다.
    예) now=12:10 -> 11:00
        now=01:10 -> (전날) 23:00
    """
    # 오늘 날짜의 후보들을 만들고 now 이전인 것 중 가장 최근 선택
    candidates = []
    for h in base_hours:
        dt = now.replace(hour=h, minute=0, second=0, microsecond=0)
        candidates.append(dt)

    # now 이전(또는 같은 시각) 후보만 필터
    past = [dt for dt in candidates if dt <= now]

    if past:
        chosen = max(past)
    else:
        # 오늘 새벽(0~1시대)처럼 과거 후보가 없으면 전날 23시로
        chosen = (now - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)

    base_date = chosen.strftime("%Y%m%d")
    base_time = chosen.strftime("%H%M")  # "2300" 형태
    return base_date, base_time


def ultra_ncst_base_datetime(now: Optional[datetime] = None) -> Tuple[str, str]:
    """
    초단기 실황(getUltraSrtNcst)은 최근 관측/제공 타이밍을 고려해
    now에서 약간(40분) 빼고 '정시(HH00)'로 맞춘다.
    """
    now = now or datetime.now()
    target = now - timedelta(minutes=40)
    base_date = target.strftime("%Y%m%d")
    base_time = target.strftime("%H") + "00"  # "1200"
    return base_date, base_time


def short_fcst_base_datetime(now: Optional[datetime] = None) -> Tuple[str, str]:
    """
    단기예보(getVilageFcst)는 발표시각(0200/0500/0800/1100/1400/1700/2000/2300) 기준.
    now에서 약간(10~30분) 빼서 '가장 최근 발표시각'으로 내림(floor)한다.
    - NO_DATA를 줄이기 위해 now를 약간 당겨 안정적으로 계산한다.
    """
    now = now or datetime.now()

    # 데이터 반영 지연을 고려한 완충(환경에 따라 10~30분 조정 가능)
    # 너무 타이트하면 막 발표 직후 NO_DATA가 뜰 수 있음.
    safe_now = now - timedelta(minutes=20)

    return _floor_to_latest_base_time(safe_now, VILAGE_FCST_BASE_TIMES)


def latest_mid_tmfc(now: Optional[datetime] = None) -> str:
    """
    중기(tmFc) 기본값: 06:00 또는 18:00 기준으로 가장 최근 발표시각.
    반환: YYYYMMDDHHMM
    """
    now = now or datetime.now()
    hh = now.hour

    if hh < 6:
        dt = (now - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
    elif hh < 18:
        dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    else:
        dt = now.replace(hour=18, minute=0, second=0, microsecond=0)

    return dt.strftime("%Y%m%d%H%M")

