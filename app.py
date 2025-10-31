import os
import asyncio
import subprocess
import datetime
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_DB = os.getenv("POSTGRES_DB")
BACKUP_PATH = "/backups"
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", 14))
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


async def send_telegram_message(text: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    async with ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        )


async def run_backup():
    date = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{BACKUP_PATH}/db_backup_{date}.dump"
    print(f"[INFO] Starting backup -> {filename}")

    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASSWORD

    cmd = [
        "pg_dump",
        "-h", PG_HOST,
        "-U", PG_USER,
        "-d", PG_DB,
        "-F", "c",
        "-f", filename,
    ]

    try:
        subprocess.run(cmd, env=env, check=True)
        print("[OK] Backup complete.")
        await send_telegram_message(f"✅ Backup successful: {filename}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Backup failed: {e}")
        await send_telegram_message(f"❌ Backup failed: {e}")
    finally:
        await cleanup_old_backups()


async def cleanup_old_backups():
    now = datetime.datetime.now()
    for file in os.listdir(BACKUP_PATH):
        full_path = os.path.join(BACKUP_PATH, file)
        if os.path.isfile(full_path):
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
            if (now - mtime).days > RETENTION_DAYS:
                os.remove(full_path)
                print(f"[INFO] Deleted old backup: {file}")


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_backup, "cron", hour=2, minute=0)  # каждый день в 2:00
    scheduler.start()
    print("[INFO] Backup service started. Waiting for schedule...")
    while True:
        await asyncio.sleep(3600)  # просто держим контейнер живым


if __name__ == "__main__":
    asyncio.run(main())
