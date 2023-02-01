from hashlib import sha256
from os import path, urandom, remove
from random import randint
from datetime import datetime, timezone
from flask import (
    Flask,
    request,
    abort,
    jsonify,
    send_file,
    render_template,
    Response,
    send_from_directory,
)
from werkzeug.exceptions import HTTPException
from werkzeug.datastructures import FileStorage
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw


img = Flask(__name__, template_folder='website', static_folder='misc')
img.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///goodnight.db'
PATH = 'images/'
SALT = b'$2b$10$tXjjjtymt8QIrneou6Hah.'
DEFAULT_FOLDER = 'misc/'
database = SQLAlchemy(img)

# make a nice looking datatime
def nice_date() -> str:
    return datetime.now(timezone.utc).strftime('%d/%m/%Y %I:%M %p')


class Post(database.Model):
    id = database.Column(
        database.String, unique=True, primary_key=True, nullable=False
    )
    date = database.Column(
        database.String,
        nullable=False,
        default=nice_date,
    )
    file = database.Column(database.String, nullable=False, unique=True)
    by = database.Column(
        database.String, database.ForeignKey('user.username'), nullable=False
    )
    deletion_key = database.Column(
        database.String, unique=True, nullable=False
    )

    def __repr__(self) -> str:
        return f"Post(id='{self.id}', date='{self.date}', file='{self.file}', by='{self.by}')"   # noqa


class User(database.Model):
    username = database.Column(
        database.String, unique=True, primary_key=True, nullable=False
    )
    password = database.Column(database.String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"User(username='{self.username}', password=0x10)"


@img.errorhandler(HTTPException)
def handle_error(e) -> Response:
    return jsonify({'error': e.code, 'description': e.description}), e.code


cache = {}


def save_data(
    name: str,
    filepath: str,
    user: database.ForeignKey('user.username'),  # noqa
    imgobj: FileStorage,
    del_key: str,
) -> None:
    database.session.add(
        Post(
            id=name,
            date=nice_date(),
            file=filepath,
            by=user,
            deletion_key=del_key,
        )
    )
    imgobj.save(filepath)
    database.session.commit()


def check_by_recursion(hashh, **kwargs) -> str:
    real = [hashh]
    while real:
        real.pop()
        hashgened = sha256(urandom(20) + kwargs['user']).hexdigest()
        if Post.query.filter(Post.id == hashh).first():
            real.append(hashgened[: randint(6, 12)])
        return hashh


def send_or_404(folder: str, f: str) -> Response:
    folder = folder if path.exists(folder) else DEFAULT_FOLDER
    if path.exists(path.join(folder, f)):
        return send_from_directory(directory=folder, path=f)
    else:
        abort(404)


@img.route('/')
def index() -> Response:
    return render_template('index.html')


@img.route('/<image>')
def send_image(image):
    if image == 'favicon.ico':
        return send_or_404(folder='misc', f='favicon.ico')
    if image not in cache:
        image = Post.query.get_or_404(image)
        cache[image] = {'date': image.date, 'file': image.file, 'by': image.by}
    return render_template(
        'file.html',
        date=cache[image]['date'],
        file=cache[image]['file'],
        by=cache[image]['by'],
    )


@img.route('/images/<image>')
def send_raw_image(image) -> Response:
    if image not in cache:
        image = Post.query.filter(
            Post.file == f'images/{image}'
        ).first_or_404()
        cache[image] = {'date': image.date, 'file': image.file, 'by': image.by}
    return send_file(
        cache[image]['file'],
        as_attachment=request.args.get('dl') == 'true',
    )


@img.route('/<image>/delete/<key>')
def delete_image(image, key) -> Response:
    post = Post.query.get_or_404(image)
    if key == post.deletion_key:
        if image in cache:
            del cache[image]
        database.session.delete(post)
        try:
            remove(post.file)
        except FileNotFoundError:
            img.logger.warn(f'File not found still removing entry {image}.')
        database.session.commit()
        return jsonify({'success': True})
    abort(401)


@img.route('/api/upload', methods=['POST'])
def upload() -> Response:
    if auth := request.headers.get('Authorization'):
        xsh = sha256(auth.encode('utf-8')).hexdigest().encode('utf-8')
        if found_user := User.query.filter_by(
            password=hashpw(xsh, salt=SALT).decode('utf-8')
        ).first():
            if imgfile := request.files.get('img'):
                hashgened = urandom(20) + found_user.username.encode('utf-8')
                name = check_by_recursion(
                    sha256(hashgened).hexdigest()[: randint(6, 12)],
                    user=found_user.username.encode('utf-8'),
                )
                filepath = path.join(
                    PATH, f'{name}.{imgfile.filename.split(".")[-1]}'
                )
                del_key = sha256(
                    name.encode('utf-8') + found_user.password.encode('utf-8')
                ).hexdigest()
                save_data(
                    name,
                    filepath,
                    found_user.username,
                    request.files.get('img'),
                    del_key,
                )
                return jsonify(
                    {
                        'url': f'{request.host_url}{name}',
                        'raw': f'{request.host_url}{filepath}',
                        'deletion': f'{request.host_url}{name}/delete/{del_key}',
                    }
                )
            abort(400)
        abort(401)
    abort(401)


if __name__ == '__main__':
    if not path.exists('.ignore'):
        print("run 'python3 first_run.py' to setup the server")
        input()
        exit(-1)
    img.run(host='0.0.0.0', debug=False, port=8080)
