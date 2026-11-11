from telethon.sync import TelegramClient
import os, time, logging

# показывает паузы Telegram (FloodWait) вида 'Sleeping for 300s'
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

def _load_env(path=".env"):
    """Мини-загрузчик .env, чтобы ключи не лежали в коде (без лишних зависимостей)."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


_load_env()
API_ID = int(os.environ["TG_API_ID"])     # из .env (my.telegram.org)
API_HASH = os.environ["TG_API_HASH"]      # из .env; .env в git не попадает
CHANNEL = "itmarket_uz"          # username или точное название канала
OUT_DIR = "resumes_pdfs"               # папка для файлов

os.makedirs(OUT_DIR, exist_ok=True)

client = TelegramClient("session", API_ID, API_HASH, flood_sleep_threshold=600)

def find_channel():
    # Сначала пробуем как username, затем ищем по названию среди своих чатов
    try:
        return client.get_entity(CHANNEL)
    except Exception:
        for d in client.get_dialogs():
            if d.name == CHANNEL:
                return d.entity
    raise SystemExit(f"Канал '{CHANNEL}' не найден")

with client:
    entity = find_channel()
    count = 0
    for msg in client.iter_messages(entity):
        if msg.document and msg.file.mime_type == "application/pdf":
            base = os.path.splitext(msg.file.name or str(msg.id))[0]
            base = "".join(c for c in base if c not in '\\/:*?"<>|')
            path = os.path.join(OUT_DIR, f"{base}_{msg.date:%Y-%m-%d}_{msg.id}.pdf")
            if os.path.exists(path):
                continue
            print(f"{count + 1}. {path} ({msg.file.size / 1e6:.1f} МБ)...", flush=True)
            tmp = path + ".part"            # недокачанный файл останется .part
            msg.download_media(tmp)
            os.replace(tmp, path)           # готовый файл получает имя .pdf
            count += 1
            time.sleep(0.5)
    print("Готово, скачано:", count)