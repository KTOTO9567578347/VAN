import logging
import csv

class CSVInfoLogger:
    def __init__(self, filename):
        self.filename = filename

        # Настройка логгера
        self.logger = logging.getLogger("csv_info_logger")
        self.logger.setLevel(logging.INFO)  # Устанавливаем уровень INFO

        # Создаем CSV-обработчик
        self.csv_handler = self._create_csv_handler()
        self.logger.addHandler(self.csv_handler)

    def _create_csv_handler(self):
        """Создает и настраивает CSV-обработчик."""
        handler = logging.FileHandler(self.filename, mode='a', encoding='utf-8')
        handler.setLevel(logging.INFO)

        # Устанавливаем форматтер для времени
        formatter = logging.Formatter("%(asctime)s")
        handler.setFormatter(formatter)

        # Добавляем заголовки в CSV-файл, если он пустой
        with open(self.filename, mode='r', newline='', encoding='utf-8') as file:
            if not file.read(1):  # Проверяем, пуст ли файл
                with open(self.filename, mode='w', newline='', encoding='utf-8') as new_file:
                    writer = csv.writer(new_file)
                    writer.writerow(["Timestamp", "Level", "Message"])  # Заголовки столбцов

        return handler

    def log_info(self, message):
        """Логирует сообщение уровня INFO."""
        self.logger.info(message)

    def close(self):
        """Закрывает обработчики логгера."""
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)