# Some image host made in 10 minutes

## How to setup
```python
from app import database, img, User, SALT
from bcrypt import hashpw
from hashlib import sha256

key = bytes(
  sha256(bytes('Your key', 'utf-8')).hexdigest(), 
  'utf-8'
)
key = hashpw(key, salt=SALT)

img.app_context().push()
database.create_all()
newuser = User(username='imaginary', makesureimencrypted=key)
database.session.add(newuser)
database.session.commit()
```

## ShareX
```json
{
  "Version": "14.1.0",
  "Name": "z",
  "DestinationType": "ImageUploader",
  "RequestMethod": "POST",
  "RequestURL": "https://HOST/api/upload",
  "Headers": {
    "Authorization": "KEY"
  },
  "Body": "MultipartFormData",
  "FileFormName": "img",
  "URL": "{json:url}",
  "ThumbnailURL": "{json:raw}",
  "DeletionURL": "{json:deletion}"
}
```