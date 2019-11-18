## Summary

This is a simple helper script written in Python used for uploading Android apps to Google Play. It can also handle some image and track status updates. 

## Dependencies

The script requires the following modules to be installed:

```bash
pip install google-api-python-client
pip install httpimport
pip install oauth2client
pip install argparse
```

## Usage

For help (with all the script can do):
```bash
py GooglePlayUpload.py [--help]
py GooglePlayUpload.py <command> [--help]
```


To upload an APK, APK with OBB or an AAB file to Google Play, respectively:
```bash
py GooglePlayUpload.py --packageName "com.myorg.myapp" --clientSecretUri filePathOrUrlToClientSecret.json uploadBuild --aabOrApkPath myApp.apk 
py GooglePlayUpload.py --packageName "com.myorg.myapp" --clientSecretUri filePathOrUrlToClientSecret.json uploadBuild --aabOrApkPath myApp.apk  --obbPath myApp.obb
py GooglePlayUpload.py --packageName "com.myorg.myapp" --clientSecretUri filePathOrUrlToClientSecret.json uploadBuild --aabOrApkPath myApp.aab
```

To upload an image for your app:
```bash
py GooglePlayUpload.py --packageName "com.myorg.myapp" --clientSecretUri filePathOrUrlToClientSecret.json uploadImage --imageType promoGraphic --imagePath myInfoGraphic.png
```

To promote a released app from one track to another
```bash
py GooglePlayUpload.py --packageName "com.myorg.myapp" --clientSecretUri filePathOrUrlToClientSecret.json --trackName 'internal' promoteTo --targetTrack 'alpha' --promoteStatus 'draft'
```
