# utils/logger.py
"""
راهنمایی برای ایجاد لاگ‌های امن و خودکار با پشتیبانی از پوشه‌های تودرتو
"""
import os
from pathlib import Path
import logging

def setup_logger(name, log_file, level=logging.INFO):
    """
    ایجاد یک لاگر با پشتیبانی از ایجاد خودکار پوشه‌ها
    """
    # ایجاد پوشه‌های والد فایل لاگ
    dir_path = Path(log_file).parent
    dir_path.mkdir(parents=True, exist_ok=True)

    # تنظیم فرمت
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    # ایجاد handler
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    # ایجاد لاگر
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
