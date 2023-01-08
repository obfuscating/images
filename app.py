from hashlib import sha256
from os import path, urandom, remove
from random import randint
from datetime import datetime, timezone
from imghdr import what
from flask import Flask, request, abort, jsonify, send_file, render_template, Response, send_from_directory
from werkzeug.exceptions import HTTPException
from werkzeug.datastructures import FileStorage
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw


img = Flask("too much for zblock",
            template_folder="website", static_folder='misc')
img.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///goodnight.db"
PATH = "images/"
SALT = b'$2b$10$tXjjjtymt8QIrneou6Hah.'
database = SQLAlchemy(img)


class Post(database.Model):
    id = database.Column(database.String, unique=True,
                         primary_key=True, nullable=False)
    date = database.Column(database.String, nullable=False, default=datetime.now(
        timezone.utc).strftime("%Y %m %d"))
    file = database.Column(database.String, nullable=False, unique=True)
    by = database.Column(database.String, database.ForeignKey(
        'user.username'), nullable=False)
    deletion_key = database.Column(
        database.String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"Post(id='{self.id}', date='{self.date}', file='{self.file}', by='{self.by}')"


class User(database.Model):
    username = database.Column(
        database.String, unique=True, primary_key=True, nullable=False)
    makesureimencrypted = database.Column(
        database.String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"User(username='{self.username}', makesureimencrypted=0x10)"


@img.errorhandler(HTTPException)
def handle_error(e) -> Response:
    return jsonify({"error": e.code, "description": e.description}), e.code


cache = {}  # This isn't an actual cache


def save_data(
    name: str,
    filepath: str,
    user: database.ForeignKey('user.username'),
    imgobj: FileStorage,
    del_key: str
) -> None:
    database.session.add(
        Post(
            id=name,
            date=f'{datetime.now(timezone.utc).strftime("%Y-%m-%d %I:%M %p")} UTC',
            file=filepath,
            by=user,
            deletion_key=del_key
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
            real.append(hashgened[:randint(6, 12)])
        return hashh


def send_or_404(folder: str, f: str) -> Response:
    if path.exists(folder) or path.exists(f):
        return send_from_directory(directory=folder, path=f)
    else:
        abort(404)


@img.route("/")
def index() -> Response:
    return render_template("index.html")


@img.route("/<image>")
def send_image(image):
    if image == "favicon.ico":
        return send_or_404("misc", "favicon.ico")
    if image not in cache:
        image = Post.query.get_or_404(image)
        cache[image] = {"date": image.date,
                        "file": image.file, "by": image.by}
    return render_template(
        "file.html",
        date=cache[image]['date'],
        file=cache[image]['file'],
        by=cache[image]['by']
    )


@img.route("/images/<image>")
def send_raw_image(image) -> Response:
    if image not in cache:
        image = Post.query.filter(
            Post.file == f'images/{image}').first_or_404()
        cache[image] = {"date": image.date, "file": image.file, "by": image.by}
    return send_file(
        cache[image]['file'],
        as_attachment=request.args.get("d") == "true",
    )


@img.route("/<image>/delete/<key>")
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
        return jsonify({"success": True})
    abort(401)


@img.route('/misc/')
def misc() -> Response:
    return '', 204

@img.route("/api/upload", methods=['POST'])
def upload() -> Response:
    if auth := request.headers.get("Authorization"):
        xsh = sha256(auth.encode('utf-8')).hexdigest().encode('utf-8')
        if (
            found_user := User.query.filter_by(
                makesureimencrypted=hashpw(xsh, salt=SALT).decode('utf-8')
            )
            .first()
        ):
            if imgfile := request.files.get("img"):
                if imgformat := what(imgfile.stream):
                    hashgened = urandom(
                        20) + found_user.username.encode('utf-8')
                    name = check_by_recursion(
                        sha256(hashgened).hexdigest()[:randint(6, 12)],
                        user=found_user.username.encode('utf-8')
                    )
                    filepath = path.join(
                        PATH, f"{name}.{imgformat}")
                    del_key = sha256(
                        name.encode(
                            'utf-8') + found_user.makesureimencrypted.encode('utf-8')
                    ).hexdigest()
                    save_data(
                        name,
                        filepath,
                        found_user.username,
                        request.files.get("img"),
                        del_key
                    )
                    return jsonify(
                        {
                            "url": f"{request.host_url}{name}",
                            "raw": f"{request.host_url}{filepath}",
                            "deletion": f"{request.host_url}{name}/delete/{del_key}"
                        }
                    )
                else:
                    abort(400)
            else:
                abort(400)
        else:
            abort(401)
    abort(401)


if __name__ == "__main__":
    img.run(host="0.0.0.0", port=1111)