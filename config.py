"""
Конфиг (константы и прочая шняга)
"""
from datetime import datetime
# токены и идентификаторы
# # токен группы
BOT_TOKEN = ""

# # токен владельца
USER_TOKEN = ""

# # айди группы
GROUP_ID = 
# # айди беседы с ботом
CONVERSATION_ID = 

CLIP_NAME = ""
CLIP_DESCRIPTION = ""

CLIPS_DIR = "clips"  # директория для сохранения клипов



START_HOUR, START_MINUTE = 21, 00 #час начала запуска цикла загрузки
START = f"{START_HOUR}:{START_MINUTE}" #время запуска цикла загрузки
END_HOUR, END_MINUTE = 23, 59 #час конца запуска цикла загрузки
END = f"{END_HOUR}:{END_MINUTE}"
POSTING_INTERVAL = 1 #интервал постинга клипов в часах
CLEANUP_INTERVAL_HOURS = 24  #интервал проверки и удаления старых клипов в часах

#дата последнего поста в формате datetime(год, месяц, число, час, минута, секунда)
LAST_TIME_POST = datetime(2025, 6, 16, 21, 39, 46)

#Логирование
LOG_LEVEL = "INFO"  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Формат сообщений лога

#Загрузка видео
USE_YTDLP = True  #использовать yt-dlp для загрузки видео
YTDLP_PATH = "yt-dlp"  #путь к исполняемому файлу yt-dlp
