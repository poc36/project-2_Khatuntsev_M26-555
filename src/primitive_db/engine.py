import prompt


def print_help():
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")


def welcome():
    print("Первая попытка запустить проект!\n\n***")
    print_help()

    while True:
        command = prompt.string("Введите команду: ").strip()
        print()
        if command == "exit":
            break
        elif command == "help":
            print_help()
        else:
            print(f"Команда {command} не найдена. Попробуйте снова.")