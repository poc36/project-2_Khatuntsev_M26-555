import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import META_FILE
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    info,
    insert,
    list_tables,
    select,
    update,
    validate_clause,
)
from primitive_db.decorators import create_cacher
from primitive_db.parser import parse_condition, parse_values
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

select_cache = create_cacher()


def print_help():
    """Выводит справку по командам."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def table_exists(metadata, table_name):
    """Проверяет, что таблица есть, иначе печатает ошибку"""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return False
    return True


def print_records(metadata, table_name, records):
    """Выводит записи таблицей prettytable"""
    if not records:
        print("Записи не найдены.")
        return
    columns = list(metadata[table_name])
    table = PrettyTable(columns)
    for record in records:
        table.add_row([record[col] for col in columns])
    print(table)


def handle_insert(metadata, user_input):
    """insert into <таблица> values (...)"""
    parts = user_input.split(maxsplit=3)
    if len(parts) < 4 or parts[1] != "into" or not parts[3].startswith("values"):
        raise ValueError(user_input)
    table_name = parts[2]
    values = parse_values(parts[3][len("values") :])
    if not table_exists(metadata, table_name):
        return
    data = insert(metadata, table_name, values, load_table_data(table_name))
    if data is not None:
        save_table_data(table_name, data)


def handle_select(metadata, user_input):
    """select from <таблица> [where <столбец> = <значение>]"""
    head, sep, where_text = user_input.partition(" where ")
    parts = head.split()
    if len(parts) != 3 or parts[1] != "from":
        raise ValueError(user_input)
    table_name = parts[2]
    if not table_exists(metadata, table_name):
        return
    where = parse_condition(where_text) if sep else None
    if where and not validate_clause(metadata, table_name, where):
        return
    data = load_table_data(table_name)
    key = (table_name, repr(where), repr(data))
    records = select_cache(key, lambda: select(data, where))
    if records is not None:
        print_records(metadata, table_name, records)


def handle_update(metadata, user_input):
    """update <таблица> set <столбец> = <значение> where <столбец> = <значение>"""
    head, sep, where_text = user_input.partition(" where ")
    parts = head.split(maxsplit=3)
    if not sep or len(parts) != 4 or parts[2] != "set":
        raise ValueError(user_input)
    table_name = parts[1]
    if not table_exists(metadata, table_name):
        return
    set_clause = parse_condition(parts[3])
    where = parse_condition(where_text)
    if "ID" in set_clause:
        print("Ошибка: Столбец ID нельзя изменить.")
        return
    if not validate_clause(metadata, table_name, set_clause):
        return
    if not validate_clause(metadata, table_name, where):
        return

    data = load_table_data(table_name)
    ids = [record["ID"] for record in select(data, where)]
    if not ids:
        print("Записи не найдены.")
        return
    data = update(data, set_clause, where)
    if data is None:
        return
    save_table_data(table_name, data)
    for record_id in ids:
        print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')


def handle_delete(metadata, user_input):
    """delete from <таблица> where <столбец> = <значение>"""
    head, sep, where_text = user_input.partition(" where ")
    parts = head.split()
    if not sep or len(parts) != 3 or parts[1] != "from":
        raise ValueError(user_input)
    table_name = parts[2]
    if not table_exists(metadata, table_name):
        return
    where = parse_condition(where_text)
    if not validate_clause(metadata, table_name, where):
        return

    data = load_table_data(table_name)
    ids = [record["ID"] for record in select(data, where)]
    if not ids:
        print("Записи не найдены.")
        return
    data = delete(data, where)
    if data is None:
        return
    save_table_data(table_name, data)
    for record_id in ids:
        print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')


def run():
    """Основной цикл программы"""
    print("***База данных***")
    print_help()

    while True:
        metadata = load_metadata(META_FILE)
        user_input = prompt.string(">>>Введите команду: ").strip()

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        if not args:
            continue

        command = args[0]
        try:
            match command:
                case "create_table" if len(args) >= 3:
                    metadata = create_table(metadata, args[1], args[2:])
                    if metadata is not None:
                        save_metadata(META_FILE, metadata)
                case "drop_table" if len(args) == 2:
                    metadata = drop_table(metadata, args[1])
                    if metadata is not None:
                        save_metadata(META_FILE, metadata)
                case "insert":
                    handle_insert(metadata, user_input)
                case "select":
                    handle_select(metadata, user_input)
                case "update":
                    handle_update(metadata, user_input)
                case "delete":
                    handle_delete(metadata, user_input)
                case "info" if len(args) == 2:
                    if table_exists(metadata, args[1]):
                        info(metadata, args[1], load_table_data(args[1]))
                case "create_table" | "drop_table" | "info":
                    print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                case "list_tables":
                    list_tables(metadata)
                case "help":
                    print_help()
                case "exit":
                    break
                case _:
                    print(f"Функции {command} нет. Попробуйте снова.")
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
