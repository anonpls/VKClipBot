"""
Конфиг (константы и прочая шняга)
"""

# токены и идентификаторы
#BOT_TOKEN = 
#GROUP_ID = 
#CONVERSATION_ID =  
API_VERSION = "5.199"  #версия API ВКонтакте

CLIPS_DIR = "clips"  # директория для сохранения клипов

CLEANUP_INTERVAL_HOURS = 24  #интервал проверки и удаления старых клипов в часах

#Логирование
LOG_LEVEL = "INFO"  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Формат сообщений лога

#Загрузка видео
USE_YTDLP = True  #использовать yt-dlp для загрузки видео
YTDLP_PATH = "yt-dlp"  #путь к исполняемому файлу yt-dlp
