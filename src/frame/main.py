import logging
import sys
import arcade

from src.frame.main_window import MainWindow



def setup_logging():
    """Логирование"""
    import os
    from logging.handlers import RotatingFileHandler
    from src.core.resource_manager import resource_manager
    log_dir = resource_manager.get_full_path("logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'game.log')

    # переопределение метода создания backup
    class PrettyRotatingHandler(RotatingFileHandler):
        def doRollover(self):
            # Закрытие текущего файла
            if self.stream:
                self.stream.close()
            backup_num = 1
            while True:
                backup_name = f"{self.baseFilename}.backup{backup_num}"
                if not os.path.exists(backup_name):
                    break
                backup_num += 1

            os.rename(self.baseFilename, backup_name)

            # удаление лишних backup
            if self.backupCount > 0:
                for i in range(backup_num - self.backupCount, 0, -1):
                    old_backup = f"{self.baseFilename}.backup{i}"
                    if os.path.exists(old_backup):
                        os.remove(old_backup)
            if not self.delay:
                self.stream = self._open()

    # Использование handler
    file_handler = PrettyRotatingHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )

    # Настройка формата логирования
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Отключение логов сторонних библиотек
    for lib in ["PIL", "arcade", "pyglet"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return file_handler


def main():
    logger = logging.getLogger(__name__)
    logger.info("Начало игровой сессии...")
    logger.debug("Параметры запуска: %s", sys.argv)
    logger.debug(f"версия аркейда {arcade.__version__}")

    try:
        MainWindow()
        arcade.run()
    except Exception as e:
        logger.critical("Критическая ошибка: %s", e, exc_info=True)
        raise
    finally:
        logger.info("Конец игровой сессии...\n")


if __name__ == "__main__":
    setup_logging()
    main()
