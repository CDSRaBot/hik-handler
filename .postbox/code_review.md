# Отчет по Code Review проекта Hik-handler

## 1. Общий обзор архитектуры
Проект представляет собой модульную CLI-утилиту на Python. Архитектура построена на разделении ответственности (Separation of Concerns):
- **Configuration Layer**: `ConfigManager`, `SecureContext`.
- **Engine/Business Logic**: `Orchestrator` (Медиатор), `ModuleManager`, `XMLValidator`, `ArgumentResolver`.
- **Communication Layer**: `HikvisionClient` (на базе `requests`).
- **UI Layer**: `CLITerminal` (на базе `prompt_toolkit`).

Код написан с использованием современных практик (Type Hinting, Dataclasses, Logging hierarchy). Однако выявлен ряд критических несоответствий в контрактах методов, которые приведут к сбоям при выполнении.

---

## 2. Анализ контрактов и интерфейсов

### 2.1. Ошибка в Orchestrator vs ModuleManager (Критическая)
В методе `Orchestrator.run_command` (файл `app/engine/orchestrator.py`, строка 134) вызывается:
```python
module_data = self._loader.get_module(context.module_name)
```
**Проблема**: В классе `ModuleManager` (файл `app/engine/loader.py`) **отсутствует** метод `get_module`. Существует только `get_module_path`, который возвращает объект `Path`, а не содержимое файла.
**Результат**: `AttributeError` при попытке выполнения любой команды.

### 2.2. Несоответствие типов в Orchestrator vs XMLValidator (Критическая)
В методе `Orchestrator.run_command` (строка 140) вызывается:
```python
self._validator.validate(module_data)
```
**Проблема**:
1. `XMLValidator.validate` ожидает `xml_path` (строку-путь к файлу), а получает `module_data` (содержимое XML или объект Path, в зависимости от исправления ошибки 2.1).
2. `XMLValidator.validate` возвращает кортеж `(bool, str)`. В Python кортеж `(False, "error")` является истинным (`True`).
**Результат**: Проверка `if not self._validator.validate(...)` никогда не сработает как ожидается. Система будет считать валидацию успешной даже при наличии ошибок.

### 2.3. Ошибка вызова в CLITerminal vs Orchestrator (Критическая)
В методе `CLITerminal._cmd_run` (файл `app/user_interface/cli_terminal.py`, строка 158):
```python
self._orchestrator.execute_headless(module_name, **params)
```
**Проблема**: `params` передается как именованные аргументы (`**params`), в то время как `Orchestrator.execute_headless` ожидает словарь в качестве второго позиционного аргумента.
**Результат**: `TypeError: execute_headless() got an unexpected keyword argument...`.

---

## 3. Заглушки (Stubs) и незавершенный код

### 3.1. Дублирование методов в CLITerminal
В файле `app/user_interface/cli_terminal.py` метод `_cmd_list` определен дважды:
- Строки 114-118: Заглушка `print("Available modules: [mocked]")`.
- Строки 120-131: Реальная реализация.
**Рекомендация**: Удалить строки 114-118.

### 3.2. Безопасность в ArgumentResolver
В файле `app/engine/resolver.py` (строка 62) используется стандартный `xml.etree.ElementTree`. 
**Заглушка/Комментарий**: "replacement with lxml/defusedxml is possible in the future".
**Риск**: Уязвимость к XXE-атакам, если XML-модули будут загружаться из недоверенных источников. Хотя `XMLValidator` использует `defusedxml`, сам парсинг в резолвере остается менее защищенным.

### 3.3. Пустые пароли в ConfigManager
Метод `ConfigManager.get_secure_context` принудительно устанавливает пароль из конфига, даже если он пустой. При этом в `SecureContext.from_dict` заложена логика обязательности пароля, которая в данном случае обходится.

### 3.4. Отсутствие реализации Sandbox
В `config.toml` объявлена директория `sandbox`, но в текущей реализации `Orchestrator` и `HikvisionClient` она никак не используется. Сохранение ответов камер в файлы на данный момент не реализовано.

---

## 4. Резюме и рекомендации

1. **Синхронизация контрактов**:
   - Добавить метод `read_module(name)` в `ModuleManager`.
   - Исправить проверку возвращаемого значения `XMLValidator.validate` (проверять первый элемент кортежа).
   - Привести вызов `execute_headless` в терминале к соответствию сигнатуре метода.
2. **Чистка кода**: Удалить дубликаты методов в `cli_terminal.py`.
3. **Безопасность**: Заменить `ElementTree` на `defusedxml` в `resolver.py` для консистентности с валидатором.
4. **Устойчивость**: Добавить создание директории `sandbox` при инициализации, если она предполагается для использования.
