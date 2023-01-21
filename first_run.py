def main():
    try:
        from os import remove
        from os.path import exists
        from hashlib import sha256
        from contextlib import suppress
        from getpass import getpass
        from bcrypt import hashpw
        from app import database, img, User, SALT
    except ImportError:
        _extracted_from_main_10(
            "Failed to import a module, install it from pip install -r requirements.txt then rerun it\nPress enter to exit..."
        )
    if exists(".ignore"):
        _extracted_from_main_10('already ran, run app.py\nPress enter to exit...')
    s = 'abcdefghijklmnopqrstuvwxyz. '
    with suppress(FileNotFoundError):
        remove('images/​')
    if username := input('Username: '):
        if key := getpass(prompt="Key (hidden): "):
            key = bytes(
                sha256(bytes(key, 'utf-8')).hexdigest(),
                'utf-8'
            )
            key = hashpw(key, salt=SALT).decode('utf-8')

            img.app_context().push()
            database.create_all()
            newuser = User(username=username, makesureimencrypted=key)
            database.session.add(newuser)
            database.session.commit()
            with open('.ignore', 'w') as f:
                f.write(s[12]+s[24]+s[27]+s[8]+s[13]+s[18]+s[0]+s[13]+s[4]+s[27]+s[19]+s[7]+s[14]+s[20]+s[6]+s[7]+s[19]+s[18]+s[27]+s[8]+s[13]+s[27]+s[12]+s[24]+s[27]+s[7]+s[4]+s[0]+s[3])
            print("success")


# TODO Rename this here and in `main`
def _extracted_from_main_10(arg0):
    print(arg0)
    input()
    exit(-1)

if __name__ == '__main__':
    main()
