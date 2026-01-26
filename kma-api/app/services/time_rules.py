# app/services/time_rules.py
from datetime import datetime, timedelta
from typing import Optional, Tuple

# KMA 동네예보(단기예보) 발표 시각 (KST 기준)
VILAGE_FCST_BASE_TIMES = (2, 5, 8, 11, 14, 17, 20, 23)


def _floor_to_latest_base_time(now: datetime, base_hours=VILAGE_FCST_BASE_TIMES) -> Tuple[str, str]:
    """
    now 기준, base_hours 중 '가장 최근' 발표시각을 골라 base_date/base_time 반환.
    예) 12:10 -> 11:00
        01:10 -> (전날) 23:00
    """
    candidates = [
        now.replace(hour=h, minute=0, second=0, microsecond=0)
        for h in base_hours
    ]
    past = [dt for dt in candidates if dt <= now]
    if past:
        chosen = max(past)
    else:
        chosen = (now - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)

    return chosen.strftime("%Y%m%d"), chosen.strftime("%H%M")


def ultra_ncst_base_datetime(now: Optional[datetime] = None) -> Tuple[str, str]:
    """
    초단기 실황(getUltraSrtNcst)
    - 보통 관측/제공 지연을 고려해 now-40분 후 '정시(HH00)' 사용
    """
    now = now or datetime.now()
    target = now - timedelta(minutes=40)
    return target.strftime("%Y%m%d"), target.strftime("%H") + "00"


def short_fcst_base_datetime(now: Optional[datetime] = None) -> Tuple[str, str]:
    """
    단기예보(getVilageFcst)
    - now-20분 안전버퍼 적용 후
    - 최근 발표시각(0200/0500/...)으로 내림
    """
    now = now or datetime.now()
    safe_now = now - timedelta(minutes=20)
    return _floor_to_latest_base_time(safe_now, VILAGE_FCST_BASE_TIMES)


def latest_mid_tmfc(now: Optional[datetime] = None) -> str:
    """
    중기(tmFc) 기본값: 06:00 또는 18:00 기준 가장 최근 발표시각.
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


def prev_mid_tmfc(tmfc: str) -> str:
    """
    tmfc(YYYYMMDDHHMM)에서 직전 발표시각으로 내림:
    - 06:00 -> 전날 18:00
    - 18:00 -> 당일 06:00
    그 외 입력이면 그냥 12시간 빼는 방식으로 보정(안전장치)
    """
    dt = datetime.strptime(tmfc[:12], "%Y%m%d%H%M")
    if dt.hour == 6:
        dt = (dt - timedelta(days=1)).replace(hour=18, minute=0)
    elif dt.hour == 18:
        dt = dt.replace(hour=6, minute=0)
    else:
        dt = dt - timedelta(hours=12)
        dt = dt.replace(minute=0)

    return dt.strftime("%Y%m%d%H%M")

