import os
import logging
import asyncio
from datetime import datetime, time

from vkbottle.bot import Bot, Message

from config import (
    BOT_TOKEN,
    GROUP_ID,
    CONVERSATION_ID,
    CLIPS_DIR,
    LOG_LEVEL,
    LOG_FORMAT,
    CLEANUP_INTERVAL_HOURS,
    USE_YTDLP,
    START_HOUR,
    END_HOUR,
    POSTING_INTERVAL
)
from utils import (
    post_clip_to_wall,
    cleanup_old_clips, 
    download_clip, 
    generate_filename, 
    check_ytdlp_installation,
    get_vk_video_url
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Создаем директорию для клипов, если она не существует
try:
    clips_path = os.path.abspath(CLIPS_DIR)
    if not os.path.exists(clips_path):
        logger.info(f"Создаю директорию для клипов: {clips_path}")
        os.makedirs(clips_path, exist_ok=True)
    else:
        logger.info(f"Директория для клипов существует: {clips_path}")
        
    # Проверяем права на запись
    if os.access(clips_path, os.W_OK):
        logger.info(f"Директория {clips_path} доступна для записи")
    else:
        logger.warning(f"Директория {clips_path} НЕ доступна для записи!")
except Exception as e:
    logger.error(f"Ошибка при создании/проверке директории для клипов: {e}", exc_info=True)

# Проверяем установку yt-dlp, если он используется
if USE_YTDLP:
    ytdlp_installed = check_ytdlp_installation()
    if not ytdlp_installed:
        logger.warning("yt-dlp не установлен. Для работы бота необходимо установить yt-dlp.")
        logger.warning("Установите yt-dlp с помощью команды: pip install yt-dlp")

# Создаем экземпляр бота
bot = Bot(token=BOT_TOKEN)

# Флаг для отслеживания запущенной задачи очистки
cleanup_task = None

@bot.on.message()
async def message_handler(message: Message):
    """
    Обрабатывает новые сообщения и скачивает видеоклипы.
    
    Args:
        message: Объект сообщения от API ВКонтакте
    """
    try:
        # Подробное логирование входящего сообщения
        logger.info(f"Получено новое сообщение: {message.text}")
        logger.info(f"От пользователя: {message.from_id}, Peer ID: {message.peer_id}, CONVERSATION_ID: {CONVERSATION_ID}")
        
        # Проверяем, что сообщение из нужной беседы
        peer_id = message.peer_id
        if peer_id != CONVERSATION_ID:
            logger.info(f"Сообщение из другой беседы (ID: {peer_id}), игнорируем")
            return
        
        logger.info("Сообщение из целевой беседы, продолжаем обработку")
            
        # Проверяем наличие вложений
        if not message.attachments:
            logger.info("Сообщение без вложений, игнорируем")
            return
        
        # Логируем все вложения с подробной информацией
        logger.info(f"Количество вложений: {len(message.attachments)}")
        for i, att in enumerate(message.attachments):
            logger.info(f"Вложение {i+1}: Тип = {att.type}, Строковое представление = {str(att.type)}")
            
        # Обрабатываем вложения
        for attachment in message.attachments:
            # Расширенная проверка типа вложения
            attachment_type_str = str(attachment.type)
            logger.info(f"Проверка вложения: {attachment_type_str}")
            
            # Проверяем наличие слова "video" в строковом представлении типа
            if "video" not in attachment_type_str.lower():
                logger.info(f"Вложение типа {attachment_type_str} не содержит 'video', пропускаем")
                continue
            
            logger.info(f"Найдено видео-вложение: {attachment_type_str}")
                
            try:
                # Получаем данные видео
                video_data = attachment.video
                logger.info(f"Данные видео: owner_id={video_data.owner_id}, id={video_data.id}, title={video_data.title}")
                
                # Формируем URL видео для yt-dlp
                video_url = get_vk_video_url(video_data.owner_id, video_data.id)
                logger.info(f"Сформирован URL видео для yt-dlp: {video_url}")
                
                # Генерируем имя файла для сохранения
                filename = generate_filename()
                logger.info(f"Сгенерировано имя файла: {filename}")
                
                # Загружаем видео с использованием yt-dlp
                logger.info(f"Начинаем загрузку видео")
                success = await download_clip(video_url, filename)
                
                if success:
                    logger.info(f"Видео успешно загружено в файл {filename}")
                else:
                    logger.error(f"Не удалось загрузить видео")
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке видео: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)


async def scheduled_cleanup():
    """
    Запускает периодическую очистку старых клипов.
    """
    while True:
        try:
            logger.info("Запуск плановой очистки старых клипов...")
            await cleanup_old_clips()
            # Ждем указанное время перед следующей очисткой
            logger.info(f"Следующая очистка через {CLEANUP_INTERVAL_HOURS} часов")
            await asyncio.sleep(CLEANUP_INTERVAL_HOURS * 60 * 60)
        except asyncio.CancelledError:
            # Корректная обработка отмены задачи
            logger.info("Задача очистки отменена")
            break
        except Exception as e:
            logger.error(f"Ошибка при выполнении плановой очистки: {e}", exc_info=True)
            # Ждем перед повторной попыткой
            await asyncio.sleep(60)


async def scheduled_posting():
    """
    Периодический постинг клипов.
    """
    while True:
        now = datetime.now().time()
        if time(START_HOUR) <= now <= time(END_HOUR):
            logger.info(f"Запуск сессии постинга клипов длительностью {END_HOUR - START_HOUR} часа/ов (с {START_HOUR} до {END_HOUR})")
            logger.info(f"Интервал загрузки клипа в группу - {POSTING_INTERVAL} часа/ов")
            await post_clip_to_wall()
            await asyncio.sleep(POSTING_INTERVAL * 3600)
        else:
            await asyncio.sleep(60)


def run_bot():
    
    try:
        # Выводим информацию о запуске
        logger.info("Запуск бота ВКонтакте для загрузки клипов...")
        logger.info(f"ID группы: {GROUP_ID}")
        logger.info(f"ID беседы: {CONVERSATION_ID}")
        logger.info(f"Директория для клипов: {CLIPS_DIR}")
        logger.info(f"Время хранения клипов: {CLEANUP_INTERVAL_HOURS} часов")
        logger.info(f"Использование yt-dlp: {'Да' if USE_YTDLP else 'Нет'}")
        
        # Запускаем бота
        bot.run_forever()
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)


if __name__ == "__main__":
    # Запускаем очистку старых клипов при старте
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Выполняем начальную очистку
        loop.run_until_complete(cleanup_old_clips())
        
        # Запускаем задачу периодической очистки в фоне
        cleanup_task = loop.create_task(scheduled_cleanup())
        posting_task = loop.create_task(scheduled_posting())
        
        # Запускаем бота в основном потоке
        run_bot()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        # Отменяем задачу очистки при выходе
        if cleanup_task and not cleanup_task.done():
            logger.info("Отменяем задачу очистки при выходе")
            cleanup_task.cancel()
            try:
                loop.run_until_complete(cleanup_task)
            except asyncio.CancelledError:
                pass
        
        # Закрываем цикл событий
        logger.info("Закрываем цикл событий")
        loop.close()
