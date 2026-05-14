"""
File: exporter.py
Path: app/engine/exporter.py
Context: XML to CSV Conversion Service
Version: 1.1.0

Модуль для парсинга XML-ответов устройств Hikvision и их экспорта в CSV.
Обеспечивает автоматическое «уплощение» (flattening) вложенных структур.
"""

import logging
import csv
import io
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

# Инициализация логгера для модуля экспорта.
logger = logging.getLogger(f"hik_handler.{__name__}")

class XMLExporter:
    """
    Конвертер XML-данных в формат CSV.
    Очищает теги от пространств имен и преобразует иерархию в плоский вид.
    """

    def _flatten_element(self, element: ET.Element) -> Dict[str, str]:
        """
        Рекурсивно преобразует XML-структуру в плоский словарь.
        
        Args:
            element: Корневой элемент для уплощения.
        """
        result = {}

        def _walk(node: ET.Element, prefix: str = ""):
            # Очистка тега от пространства имен {http://...}tag -> tag
            tag = node.tag.split('}')[-1] if '}' in node.tag else node.tag
            current_path = f"{prefix}{tag}" if prefix else tag
            
            # Если у узла есть текст и нет детей — это значение
            if node.text and node.text.strip() and len(node) == 0:
                result[current_path] = node.text.strip()
            
            # Рекурсивный обход детей
            for child in node:
                _walk(child, prefix=f"{current_path}_")

        # Начинаем обход со всех детей переданного элемента
        for child in element:
            _walk(child)
            
        return result

    def export_to_csv(self, xml_string: str, output_file: Optional[str] = None) -> str:
        """
        Парсит XML и возвращает CSV данные.
        
        Args:
            xml_string: Raw XML текст.
            output_file: Путь для сохранения файла (опционально).
        """
        logger.info("Запуск процесса конвертации XML в CSV.")
        
        try:
            root = ET.fromstring(xml_string)
            data_rows: List[Dict[str, str]] = []

            # Определение: список объектов или одиночный объект
            # Если в корне есть дети, которые сами являются контейнерами
            is_list = len(root) > 0 and any(len(child) > 0 for child in root)

            if is_list:
                logger.debug("Обнаружен список объектов.")
                for item in root:
                    data_rows.append(self._flatten_element(item))
            else:
                logger.debug("Обнаружен одиночный объект.")
                data_rows.append(self._flatten_element(root))

            if not data_rows:
                logger.warning("Нет данных для экспорта.")
                return ""

            # Сбор всех уникальных ключей для заголовка CSV
            fieldnames = sorted({key for row in data_rows for key in row.keys()})

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
            
            csv_data = output.getvalue()
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    f.write(csv_data)
                logger.info(f"Данные сохранены в {output_file}")

            return csv_data

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML: {e}")
            raise ValueError(f"Некорректный XML: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при экспорте: {e}")
            raise
