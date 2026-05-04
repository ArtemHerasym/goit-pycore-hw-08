from collections import UserDict
from datetime import datetime, timedelta
import pickle
from abc import ABC, abstractmethod


class UserView(ABC):

    @abstractmethod
    def exit(self):
        pass

    @abstractmethod
    def greet(self):
        pass

    @abstractmethod
    def show_contacts(self, contacts):
        pass

    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_phone(self, phone):
        pass

    @abstractmethod
    def show_birthday(self, birthday):
        pass

    @abstractmethod
    def birthdays(self, upcoming_birthdays):
        pass

    @abstractmethod
    def help(self):
        pass

    @abstractmethod
    def invalid_command(self, command):
        pass

class ConsoleView(UserView):
    def exit(self):
        print("Goodbye!")

    def greet(self):
        print("How can I help you?")

    def help(self):
        print("=" * 40)
        print("🤖 COMMAND GUIDE")
        print("=" * 40)

        commands = {
            "hello": "Say hello",
            "add": "Add a new contact",
            "change": "Change a contact",
            "phone": "Show phone numbers",
            "all": "Show all contacts",
            "add-birthday": "Add a birthday",
            "show-birthday": "Show a birthday",
            "birthdays": "Show upcoming birthdays",
            "exit / close": "Exit the program"
        }

        for cmd, desc in commands.items():
            print(f"{cmd:<15} - {desc}")

        print("=" * 40)

    def show_message(self, message):
        print(message)

    def show_contacts(self, contacts):
        print(contacts)

    def show_phone(self, phone):
        print(phone)

    def show_birthday(self, birthday):
        print(birthday)

    def birthdays(self, upcoming_birthdays):
        print(upcoming_birthdays)

    def invalid_command(self):
        print("Invalid command.")

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
	pass

#phone parsing
class Phone(Field):
    def __init__(self, value):
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Phone number must be exactly 10 digits")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

#one record
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def remove_phone(self, phone_number):
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_number, new_number):
        old_phone_obj = self.find_phone(old_number)
        if not old_phone_obj:
            raise ValueError("Phone number not found")
        new_phone_obj = Phone(new_number)
        index = self.phones.index(old_phone_obj)
        self.phones[index] = new_phone_obj

    def add_birthday(self, birthday_string):
        self.birthday = Birthday(birthday_string)


    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        if self.birthday:
            return f"Contact name: {self.name.value}, phones: {phones}, birthday: {self.birthday}"
        return f"Contact name: {self.name.value}, phones: {phones}"

#Book with all the records
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        return self.data.pop(name, None)

    def get_upcoming_birthdays(self,days=7):
        today = datetime.today().date()
        result = []

        for record in self.data.values():
            if not record.birthday:
                continue
            b_day = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
            birthday_this_year = b_day.replace(year=today.year)
            if birthday_this_year < today:
                birthday_this_year = b_day.replace(year=today.year+1)


            diff = (birthday_this_year - today).days
            if 0 <= diff <= 7:
                congratulation_date = birthday_this_year
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)
                result.append({"name": record.name.value, "birthday": congratulation_date.strftime("%d.%m.%Y")})

        return result

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())

#error handler
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Not enough information"
        except ValueError as e:
            return "Provide old and new numbers."
        except KeyError:
            return "Contact not found."
        except AttributeError:
            return "Contact not found."
    return inner

#commands handlers
@input_error
def add_contact(args, book):
    name, phone = args[0], args[1]
    record = book.find(name)
    if record is None:
        new_record = Record(name)
        book.add_record(new_record)
        new_record.add_phone(phone)
        return "Contact added."

    record.add_phone(phone)
    return "Contact updated."

@input_error
def change_contact(args, book):
    name, old_phone, new_phone, *_= args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."

@input_error
def show_contact(args, book):
    name = args[0]
    record = book.find(name)
    return "; ".join(phone.value for phone in record.phones)

@input_error
def remove_contact(args, book):
    name = args[0]
    record = book.find(name)
    if record is None:
        return "Contact not found."
    book.delete(name)
    return "Contact removed."

@input_error
def show_all_contacts(args, book):
    return str(book)

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if not record.birthday:
        return "Birthday not set."
    else:
        return record.birthday.value


@input_error
def add_birthday(args, book):
    name, birthday = args[0], args[1]
    record = book.find(name)

    if record.birthday:
        return "Birthday is already set."

    record.add_birthday(birthday)
    return "Birthday added."

@input_error
def birthdays(args, book):
    return book.get_upcoming_birthdays()


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError):
        return AddressBook()



#main logic execution
def main():
    book = AddressBook()
    book = load_data("addressbook.pkl")
    view = ConsoleView()
    print("Welcome to the OOP assistant")
    print("Type 'help' and I show all the commands I understand")

    while True:
        user_input = input("Enter your command: ")
        if not user_input.strip():
            print("Please enter a command.")
            continue
        command, args = parse_input(user_input)


        if command in ["close", "exit"]:
            view.exit()
            break

        elif command == "hello":
            view.greet()

        elif command == "add":
            result = add_contact(args, book)
            view.show_message(result)

        elif command == "change":
            result = change_contact(args, book)
            view.show_message(result)

        elif command == "phone":
            result = show_contact(args, book)
            view.show_phone(result)

        elif command in ["remove", "delete"]:
            result = remove_contact(args, book)
            view.show_message(result)

        elif command == "all":
            result = show_all_contacts(args, book)
            view.show_contacts(result)

        elif command == "add-birthday":
            result = add_birthday(args, book)
            view.show_birthday(result)

        elif command == "show-birthday":
            result = show_birthday(args, book)
            view.show_birthday(result)

        elif command == "birthdays":
            result = birthdays(args, book)
            view.birthdays(result)

        elif command == "help":
            view.help()

        else:
            view.invalid_command()

    save_data(book)


#check and start
if __name__ == "__main__":
    main()
