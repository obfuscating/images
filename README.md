## ripped frontend from [gamesense.pub](https://gamesense.pub)

## First run
```bash
pip install -r requirements.txt
python3 first_run.py
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
#
