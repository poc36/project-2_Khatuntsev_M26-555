from primitive_db.decorators import confirm_action, handle_db_errors, log_time

VALID_TYPES = {"int", "str", "bool"}
TYPE_MAP = {"int": int, "str": str, "bool": bool}


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу"""
    if not table_name.isidentifier():
        print(f"Некорректное значение: {table_name}. Попробуйте снова.")
        return metadata
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    table_columns = {"ID": "int"}
    for column in columns:
        name, sep, col_type = column.partition(":")
        if not sep or not name.isidentifier() or col_type not in VALID_TYPES:
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


@handle_db_errors
@confirm_action("удаление таблицы")
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


def _matches(record, where_clause):
    """Проверяет, подходит ли запись под условие {'столбец': значение}"""
    return all(record.get(col) == val for col, val in where_clause.items())


@handle_db_errors
def validate_clause(metadata, table_name, clause):
    """Проверяет, что столбцы есть в таблице и значения нужного типа"""
    columns = metadata[table_name]
    for col, val in clause.items():
        if col not in columns or type(val) is not TYPE_MAP[columns[col]]:
            print(f"Некорректное значение: {col} = {val}. Попробуйте снова.")
            return False
    return True


@handle_db_errors
@log_time
def insert(metadata, table_name, values, table_data):
    """Добавляет запись. values — значения всех столбцов, кроме ID"""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return table_data

    columns = [(n, t) for n, t in metadata[table_name].items() if n != "ID"]
    if len(values) != len(columns):
        print(
            f"Некорректное значение: ожидается {len(columns)} значений, "
            f"получено {len(values)}. Попробуйте снова."
        )
        return table_data

    for (name, col_type), value in zip(columns, values):
        if type(value) is not TYPE_MAP[col_type]:
            print(f"Некорректное значение: {value}. Попробуйте снова.")
            return table_data

    new_id = max((r["ID"] for r in table_data), default=0) + 1
    record = {"ID": new_id}
    for (name, _), value in zip(columns, values):
        record[name] = value

    table_data.append(record)
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает все записи или только подходящие под условие"""
    if not where_clause:
        return table_data
    return [r for r in table_data if _matches(r, where_clause)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет поля в записях, подходящих под условие"""
    for record in table_data:
        if _matches(record, where_clause):
            record.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data, where_clause):
    """Удаляет записи, подходящие под условие"""
    return [r for r in table_data if not _matches(r, where_clause)]


@handle_db_errors
def info(metadata, table_name, table_data):
    """Выводит структуру таблицы и количество записей"""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return
    columns_str = ", ".join(f"{n}:{t}" for n, t in metadata[table_name].items())
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {columns_str}")
    print(f"Количество записей: {len(table_data)}")