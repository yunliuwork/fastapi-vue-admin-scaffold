"""时间统一用 13 位毫秒时间戳（epoch ms 整数）存储和传输。"""

import time

MS_PER_SECOND = 1000
MS_PER_MINUTE = 60 * MS_PER_SECOND
MS_PER_DAY = 24 * 60 * MS_PER_MINUTE


def now_ms() -> int:
    return time.time_ns() // 1_000_000
