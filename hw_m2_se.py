from abc import ABC, abstractmethod
import copy
from collections import UserDict
from datetime import datetime, date, timedelta
import pickle


class View(ABC):

    @abstractmethod
    def display_contact(self, record):
        pass

    @abstractmethod
    def display_all_contacts(self, record):
        pass

    @abstractmethod
    def display_message(self, message):
        pass

    @abstractmethod
    def display_command(self):
        pass


class ConsoleView(View):

    def display_contact(self, record):
        print(str(record))

    def display_all_contacts(self, book):
        if not book.data:
            print("The address book is empty.")
        else:
            for record in book.data.values():
                print(record)

    def display_message(self, message):
        print(message)

    def display_command(self):
        print("Available commands:")
        print("  - add [name] [phone] - Add a new contact with a phone number.")
        print("  - change [name] [old_phone] [new_phone] - Change phone number for a contact.")
        print("  - phone [name] - Show phone numbers for a contact.")
        print("  - all - Show all contacts.")
        print("  - add-birthday [name] [DD.MM.YYYY] - Add a birthday for a contact.")
        print("  - show-birthday [name] - Show the birthday of a contact.")
        print("  - birthdays [days] - Show contacts with upcoming birthdays in next [days].")
        print("  - exit/close - Exit the application.")


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not (value.isdigit() and len(value) == 10):
            raise ValueError('The number must consist of numbers only and 10 digits!')
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone_value):
        phone_to_remove = self.find_phone(phone_value)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone_val, new_phone_val):
        phone_to_edit = self.find_phone(old_phone_val)
        if phone_to_edit:
            self.add_phone(new_phone_val)
            self.remove_phone(old_phone_val)
        else:
            raise ValueError('Old number not found!')

    def find_phone(self, phone_value):
        result = list(filter(lambda phone: phone.value == phone_value, self.phones))
        return result[0] if len(result) > 0 else None

    def value_birthday(self):
        return self.birthday.value

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones) if self.phones else "No phone numbers"
        birthday = self.value_birthday() if self.birthday else "No birthday set"
        return f"Name: {self.name.value}, phones: {phones}, birthday: {birthday}"

    def __copy__(self):
        cls = self.__class__
        new_record = cls.__new__(cls)
        new_record.__dict__.update(self.__dict__)
        return new_record

    def __deepcopy__(self, memodict):
        cls = self.__class__
        new_record = cls.__new__(cls)
        memodict[id(self)] = new_record
        for key, value in self.__dict__.items():
            setattr(new_record, key, copy.deepcopy(value, memodict))
        return new_record


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):

        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:

                birthday_this_year = datetime.strptime(record.birthday.value, '%d.%m.%Y').date().replace(
                    year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                if birthday_this_year.weekday() >= 5:
                    birthday_this_year = self.find_next_weekday(birthday_this_year, 0)

                if 0 <= (birthday_this_year - today).days <= days:
                    upcoming_birthdays.append(
                        {"name": record.name.value, "birthday": birthday_this_year.strftime('%d.%m.%Y')})
        return upcoming_birthdays

    def find_next_weekday(self, start_date, weekday):
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())

    def __copy__(self):
        cls = self.__class__
        new_book = cls.__new__(cls)
        new_book.__dict__.update(self.__dict__)
        return new_book

    def __deepcopy__(self, memodict):
        cls = self.__class__
        new_book = cls.__new__(cls)
        memodict[id(self)] = new_book
        for key, value in self.__dict__.items():
            setattr(new_book, key, copy.deepcopy(value, memodict))
        return new_book


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "There is no contact with this name."
        except ValueError:
            return "Give me name and phone, please."
        except IndexError:
            return "Enter name, please."

    return inner


def parse_input(user_input):
    cmd, *args = user_input.strip().split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_user_phone(args, book):
    name, old_phone_val, new_phone_val = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone_val, new_phone_val)
        return f"Contact {name}'s updated from {old_phone_val} to {new_phone_val}."
    return "Contact not found."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.phones:
        phones = '; '.join(phone.value for phone in record.phones)
        return f"{name}'s phone(s): {phones}"
    return "Phone number not found or contact does not exist."


@input_error
def add_birthday(args, book):
    name, date_birth, *_ = args
    record = book.find(name)
    if record:
        record.add_birthday(date_birth)
        return f"Birthday added/updated for contact {name}."
    else:
        record = Record(name)
        record.add_birthday(date_birth)
        book.add_record(record)
    return f"Contact {name} added with birthday {date_birth}."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday.value}"
    return "Birthday not found or contact does not exist."


@input_error
def birthdays(args, book):
    days = int(args[0]) if args else 7
    upcoming = book.get_upcoming_birthdays(days)
    if not upcoming:
        return "No upcoming birthdays within the next {} day(s).".format(days)
    return "\n".join([f"{entry['name']}: {entry['birthday']}" for entry in upcoming])

def save_data(book, filename="addressbook.pkl"):
    with open(filename, 'wb') as file:
        pickle.dump(book, file)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()


def main():
    book = load_data()
    view = ConsoleView()
    view.display_message("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            view.display_message("Good bye!")
            break
        elif command == "hello":
            view.display_message("How can I help you?")
        elif command == "add":
            view.display_message(add_contact(args, book))
        elif command == 'change':
            view.display_message(change_user_phone(args, book))
        elif command == 'phone':
            view.display_message(show_phone(args, book))
        elif command == 'all':
            view.display_all_contacts(book)
        elif command == 'add-birthday':
            view.display_message(add_birthday(args, book))
        elif command == 'show-birthday':
            view.display_message(show_birthday(args, book))
        elif command == 'birthdays':
            view.display_message(birthdays(args, book))
        else:
            view.display_message("Invalid command.")
    save_data(book)


if __name__ == '__main__':
    main()
