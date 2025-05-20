"""
Утилиты для работы бота
"""
from vkbottle import Bot, VideoUploader
import os
import logging
import subprocess
import asyncio
import random
from datetime import datetime, timedelta

import aiohttp

from config import (
    USER_TOKEN,
    GROUP_ID,
    CLIPS_DIR,
    CLEANUP_INTERVAL_HOURS,
    USE_YTDLP,
    YTDLP_PATH
)

# Настройка логирования
logger = logging.getLogger(__name__)
bot = Bot(USER_TOKEN)
api = bot.api


async def cleanup_old_clips():
    """
    Удаляет клипы, которые старше установленного периода хранения.
    """
    try:
        now = datetime.now()
        cutoff = now - timedelta(hours=CLEANUP_INTERVAL_HOURS)
        deleted_files = 0
        
        if not os.path.exists(CLIPS_DIR):
            logger.warning("Директория %s не существует. Создаём...", CLIPS_DIR)
            os.makedirs(CLIPS_DIR, exist_ok=True)
            return
            
        for filename in os.listdir(CLIPS_DIR):
            filepath = os.path.join(CLIPS_DIR, filename)
            if os.path.isfile(filepath):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_mtime < cutoff:
                    try:
                        os.remove(filepath)
                        deleted_files += 1
                        logger.info("Удалён старый клип: %s", filename)
                    except Exception as e:
                        logger.error("Ошибка при удалении файла %s: %s", filename, e)
        
        logger.info("Очистка завершена. Удалено %s файлов.", deleted_files)
    except Exception as e:
        logger.error("Ошибка при очистке старых клипов: %s", e)


def get_random_clip():
    clips = [f for f in os.listdir(CLIPS_DIR) if os.path.isfile(os.path.join(CLIPS_DIR, f))]
    if not clips:
        return
    clip = os.path.join(CLIPS_DIR, random.choice(clips))
    logger.info("Выбран клип для загрузки: %s", clip)
    return clip


async def post_clip_to_wall():
        clip_path = get_random_clip()
        print(f"Выбран клип для загрузки: {clip_path}")

        video_uploader = VideoUploader(api)
        attachment = await video_uploader.upload(
            file_source=clip_path,
            name="Клип",
            description="бебебе",
            group_id=GROUP_ID,
            wallpost=True
        )
        os.remove(clip_path)

        # Публикуем видео на стене сообщества
        # await apigroup.wall.post(owner_id=f"-{GROUP_ID}", attachments=attachment, from_group=1, message=",t,hf")
        logger.info(f"Клип успешно опубликован на стене сообщества (ID группы: {GROUP_ID}).")


async def download_with_ytdlp(video_url, output_path):
    """
    Загружает видео с использованием yt-dlp.
    
    Args:
        video_url (str): URL видео для загрузки
        output_path (str): Путь для сохранения видео
        
    Returns:
        bool: True если загрузка успешна, False в противном случае
    """
    try:
        logger.info(f"Загрузка видео с использованием yt-dlp: {video_url}")
        
        # Создаем директорию для сохранения, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Формируем команду для yt-dlp
        cmd = [
            YTDLP_PATH,
            video_url,
            "--no-progress",
            "--quiet",
            "-o", output_path
        ]
        
        logger.info(f"Выполняем команду: {' '.join(cmd)}")
        
        # Запускаем процесс yt-dlp
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Ждем завершения процесса
        stdout, stderr = await process.communicate()
        
        # Проверяем результат
        if process.returncode == 0:
            logger.info(f"Видео успешно загружено в {output_path}")
            return True
        else:
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else "Нет сообщения об ошибке"
            logger.error(f"Ошибка при загрузке видео: {stderr_text}")
            return False
            
    except Exception as e:
        logger.error(f"Исключение при загрузке видео с yt-dlp: {e}", exc_info=True)
        return False


async def download_clip(url, filename):
    """
    Загружает клип по URL и сохраняет его в указанный файл.
    
    Args:
        url (str): URL для загрузки клипа
        filename (str): Путь к файлу для сохранения клипа
    
    Returns:
        bool: True если загрузка успешна, False в противном случае
    """
    try:
        if not url:
            logger.error("URL для загрузки не предоставлен")
            return False
        
        # Если настроено использование yt-dlp, используем его
        if USE_YTDLP:
            return await download_with_ytdlp(url, filename)
            
        # Иначе используем стандартный метод загрузки
        logger.info(f"Начинаем загрузку видео по URL: {url}")
        
        # Создаём директорию для клипов, если она не существует
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(filename, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024 * 8)
                            if not chunk:
                                break
                            f.write(chunk)
                    logger.info("Клип успешно загружен и сохранён в %s", filename)
                    return True
                
                logger.error("Не удалось загрузить клип, код статуса: %s", resp.status)
                return False
    except Exception as e:
        logger.error("Исключение при загрузке клипа: %s", e)
        return False


def generate_filename():
    """
    Генерирует имя файла для клипа на основе текущего времени.
    
    Returns:
        str: Путь к файлу для сохранения клипа
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(CLIPS_DIR, f"clip_{timestamp}.mp4")


def check_ytdlp_installation():
    """
    Проверяет, установлен ли yt-dlp в системе.
    
    Returns:
        bool: True если yt-dlp установлен, False в противном случае
    """
    try:
        result = subprocess.run([YTDLP_PATH, "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True, 
                               check=False)
        
        if result.returncode == 0:
            logger.info(f"yt-dlp установлен, версия: {result.stdout.strip()}")
            return True
        else:
            logger.warning("yt-dlp не установлен или не найден в системе")
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке установки yt-dlp: {e}")
        return False


def get_vk_video_url(owner_id, video_id):
    """
    Формирует URL для видео ВКонтакте.
    
    Args:
        owner_id (int): ID владельца видео
        video_id (int): ID видео
        
    Returns:
        str: URL видео ВКонтакте
    """
    return f"https://vk.com/video{owner_id}_{video_id}"
