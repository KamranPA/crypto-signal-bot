# مسیر فایل: ml/threshold.py
"""
انتخاب واقعی آستانه‌ی تأیید ML از روی منحنی precision-recall مدل train‌شده،
به‌جای مقدار ثابت حدسی (که تا الان همیشه ۰.۵۵ بود و عملاً همه‌ی سیگنال‌ها را رد می‌کرد).

چرا اینجا و نه در ml/optimize.py:
انتخاب آستانه فقط پس از train شدن مدل معنا دارد (چون به خروجی احتمالاتی مدل روی
داده‌ی validation نیاز دارد) — بر خلاف پارامترهای ریسک که مستقل از مدل، مستقیم
روی بک‌تست بهینه می‌شوند.
"""
from __future__ import annotations
import numpy as np


def select_ml_threshold(precision: list[float], recall: list[float], thresholds: list[float],
                         min_recall: float = 0.05, default: float = 0.5) -> float:
    """
    آستانه‌ای را انتخاب می‌کند که F1-score (میانگین هارمونیک precision و recall) را
    بیشینه می‌کند، مشروط به این‌که حداقل min_recall حفظ شود — تا آستانه‌ای انتخاب
    نشود که عملاً همه‌ی سیگنال‌ها را رد کند (recall نزدیک صفر).

    precision, recall, thresholds: خروجی مستقیم sklearn.metrics.precision_recall_curve
    (طول precision/recall یک واحد بیشتر از thresholds است؛ اینجا هم‌طول می‌شوند).
    """
    precision = np.array(precision)
    recall = np.array(recall)
    thresholds = np.array(thresholds)

    if len(thresholds) == 0:
        return default

    precision = precision[:len(thresholds)]
    recall = recall[:len(thresholds)]

    valid = recall >= min_recall
    if not valid.any():
        # هیچ آستانه‌ای حداقل recall را حفظ نمی‌کند — به‌جای گمانه‌زنی، پیش‌فرض محافظه‌کارانه
        return default

    denom = precision + recall
    f1 = np.zeros_like(precision)
    nonzero = denom > 0
    f1[nonzero] = 2 * precision[nonzero] * recall[nonzero] / denom[nonzero]

    f1_masked = np.where(valid, f1, -1.0)
    best_idx = int(np.argmax(f1_masked))
    return float(thresholds[best_idx])
