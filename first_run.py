import secrets
import os
import hashlib
from contextlib import suppress
from getpass import getpass
from bcrypt import hashpw
from app import database, img, User, SALT


def create_key(key):
    key = hashlib.sha256(key.encode('utf-8')).hexdigest().encode('utf-8')
    key = hashpw(key, salt=SALT).decode('utf-8')
    return key


def add_user_to_db(username, key):
    img.app_context().push()
    database.create_all()
    newuser = User(username=username, password=key)
    database.session.add(newuser)
    database.session.commit()


def write_ignore_file():
    with open('.ignore', 'w') as f:
        f.write(secrets.token_hex(16))


def main():
    if os.path.exists('.ignore'):
        return print('Already ran')

    if os.path.exists('images/'):
        with suppress(NotADirectoryError, PermissionError):
            os.remove('images/')
            os.mkdir('images/')

    username = input('Username: ')
    if not username:
        return print('Username required')

    key = getpass(prompt='Key (hidden): ')
    if not key:
        return print('Key required')

    key = create_key(key)
    add_user_to_db(username, key)
    write_ignore_file()
    print('success')


if __name__ == '__main__':
    main()
