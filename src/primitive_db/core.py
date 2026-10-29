VALID_TYPES = {"int", "str", "bool"}


def create_table(metadata, table_name, columns):
    """Создаёт таблицу"""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    table_columns = {"ID": "int"}
    for column in columns:
        name, sep, col_type = column.partition(":")
        if not sep or not name or col_type not in VALID_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        if name == "ID" and col_type == "int":
            continue  # пользователь сам указал ID — не дублируем
        if name in table_columns:
            print(f'Ошибка: Столбец "{name}" указан дважды.')
            return metadata
        table_columns[name] = col_type

    metadata[table_name] = table_columns
    columns_str = ", ".join(f"{n}:{t}" for n, t in table_columns.items())
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_str}')
    return metadata


def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных"""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит список таблиц"""
    if not metadata:
        print("Таблиц пока нет")
        return
    for table_name in metadata:
        print(f"- {table_name}")