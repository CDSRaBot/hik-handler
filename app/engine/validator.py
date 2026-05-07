import logging
from lxml import etree
from defusedxml import lxml as safe_lxml

# Инициализация логгера модуля для отслеживания операций валидации
logger = logging.getLogger(__name__)


class XMLValidator:
    """
    Класс-сервис для проверки XML-документов на соответствие XSD-схеме.
    Обеспечивает кэширование скомпилированной схемы для повышения
    производительности при массовой обработке модулей.
    """

    def __init__(self, xsd_path: str):
        """
        Инициализирует экземпляр валидатора и подготавливает схему.
        
        :param xsd_path: Путь к файлу XSD-схемы (напр. /schema/module_schema.xsd).
        """
        self._xsd_path = xsd_path
        self._schema = None
        
        # Предварительная загрузка и компиляция схемы в память
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """
        Внутренний метод для загрузки и компиляции XSD-схемы в объект lxml.
        Выполняется один раз при создании экземпляра.
        """
        logger.debug(f"Загрузка и компиляция XSD-схемы: {self._xsd_path}")
        try:
            with open(self._xsd_path, 'rb') as f:
                # Чтение сырых байтов для корректной обработки кодировок
                schema_doc = etree.XML(f.read())
                # Компиляция в объект XMLSchema (тяжелая операция)
                self._schema = etree.XMLSchema(schema_doc)
            logger.info(f"Схема {self._xsd_path} успешно загружена в память")
        except Exception as e:
            # Критическая ошибка: без схемы работа системы невозможна
            logger.critical(f"Сбой инициализации схемы {self._xsd_path}: {e}")
            raise

    def validate(self, xml_path: str) -> tuple[bool, str]:
        """
        Выполняет валидацию XML-файла по скомпилированной схеме из памяти.
        
        :param xml_path: Путь к проверяемому XML-файлу модуля.
        :return: Кортеж (bool, str), где второй элемент — описание ошибки.
        """
        logger.info(f"Начата валидация модуля: {xml_path}")
        
        if not self._schema:
            logger.error("Попытка валидации без инициализированной схемы")
            return False, "Валидатор не инициализирован: отсутствует схема"

        try:
            # Безопасный парсинг XML (защита от XXE и внешних сущностей)
            logger.debug(f"Безопасный парсинг {xml_path}")
            tree = safe_lxml.parse(xml_path)

            # Проверка документа на соответствие правилам XSD
            self._schema.assertValid(tree)
            
            logger.info(f"Модуль {xml_path} прошел проверку успешно")
            return True, ""

        except (etree.XMLSyntaxError, etree.DocumentInvalid) as e:
            # Ошибки структуры XML или несоответствие схеме
            error_msg = f"Ошибка структуры или схемы в {xml_path}: {str(e)}"
            logger.debug(f"Технические детали ошибки: {error_msg}")
            return False, error_msg

        except FileNotFoundError as e:
            # Файл модуля отсутствует на диске
            error_msg = f"Файл модуля не найден: {e.filename}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            # Прочие системные исключения
            error_msg = f"Критический сбой при валидации {xml_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg