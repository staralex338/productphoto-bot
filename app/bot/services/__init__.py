# Bot services package
from app.bot.services.storage import download_telegram_photo, download_telegram_document, cleanup_temp_file
from app.bot.services.generator import run_generation
from app.bot.services.upscaler import run_upscale
from app.bot.services.task_queue import get_task_queue, TaskQueue, TaskStatus
from app.bot.services.referrals import (
    process_referral,
    get_referral_stats,
    ReferralError,
    SelfReferralError,
    AlreadyReferredError,
    InvalidReferralCodeError,
)

__all__ = [
    "download_telegram_photo",
    "download_telegram_document",
    "cleanup_temp_file",
    "run_generation",
    "run_upscale",
    "get_task_queue",
    "TaskQueue",
    "TaskStatus",
    "process_referral",
    "get_referral_stats",
    "ReferralError",
    "SelfReferralError",
    "AlreadyReferredError",
    "InvalidReferralCodeError",
]
