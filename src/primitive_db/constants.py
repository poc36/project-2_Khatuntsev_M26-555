"""Константы проекта."""

META_FILE = "db_meta.json"  # файл с метаданными таблиц
DATA_DIR = "data"  # директория с данными таблиц
VALID_TYPES = {"int", "str", "bool"}  # допустимые типы столбцов
TYPE_MAP = {"int": int, "str": str, "bool": bool}  # тип столбца -> тип Python
