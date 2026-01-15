from datetime import datetime, timedelta

def ultra_ncst_base_datetime(now: datetime | None = None):
    now = now or datetime.now()
    target = now - timedelta(minutes=40)
    base_date = target.strftime("%Y%m%d")
    base_time = target.strftime("%H") + "00"
    return base_date, base_time

def short_fcst_base_datetime(now: datetime | None = None):
    """
    단기예보는 발표 주기가 촘촘하지만,
    안전하게 '직전 정시' 기준으로 맞춰줌.
    (필요하면 규칙 더 정교화 가능)
    """
    now = now or datetime.now()
    target = now - timedelta(minutes=30)
    base_date = target.strftime("%Y%m%d")
    base_time = target.strftime("%H") + "00"
    return base_date, base_time

def latest_mid_tmfc(now: datetime | None = None):
    """
    중기(tmFc) 기본값: 06:00 또는 18:00 기준으로 가장 최근 발표시각.
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

