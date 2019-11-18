import sys
import os, os.path
import uuid
import httplib2
import argparse
import calendar
import time
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

class GooglePlay:
    GOOGLE_PLAY_SCOPES = ['https://www.googleapis.com/auth/androidpublisher']
   
    credentials = {}
    http = {}
    service = {}
    packageName = ''
    edit = {}
    
    def createEdit( self, expiryTimeInSeconds = 120 ):
        print( 'Creating new edit...' )
        return self.service.edits().insert(packageName=self.packageName, body={ 'id': self.edit['id'] }).execute(http=self.http)
        
    def getEdit( self, expiryTimeInSeconds = 120 ):
        try:
            self.edit = self.service.edits().get(packageName=self.packageName, editId=self.edit['id']).execute(http=self.http)
        except HttpError as error:
            self.edit = self.createEdit( expiryTimeInSeconds )
        print( 'Got edit ' + self.edit['id'] )
        
    def resetEdit( self ):
        self.edit = { 'id': str(uuid.uuid4()) }
    
    def validateEdit( self ):
        try:
            self.service.edits().validate( packageName=self.packageName, editId=self.edit['id'] ).execute(http=self.http)
            print( 'Validation successful' )
            return True
        except HttpError as error:
            print( '!! Failed to validate edit !!' )
            print( error )
        return False
    
    def commitEdit( self ):
        try:
            self.service.edits().commit( packageName=self.packageName, editId=self.edit['id'] ).execute(http=self.http)
            print( 'Commit successful' )
        except HttpError as error:
            print( '!! Failed to commit edit !!' )
            print( error )
    
    def getTrack( self, trackName ):
        try:
            return self.service.edits().tracks().get(packageName=self.packageName, editId=self.edit['id'], track=trackName).execute(http=self.http)
        except HttpError as error:
            print( error )
    
    def updateTrack( self, releaseName, versionCode, toStatus, trackName = 'internal' ):
        try:
            body = { 
                'track': trackName,
                'releases': [
                {
                    'status': toStatus,
                    'name': releaseName,
                    'versionCodes':[versionCode]
                }]
            }
            print( 'Updating {0} track with release {1} ({2})'.format( trackName, releaseName, versionCode ) )
            return self.service.edits().tracks().update(packageName=self.packageName, editId=self.edit['id'], track=trackName, body=body).execute(http=self.http)
        except HttpError as error:
            print( '!! Failed to update track !!' )
            print( error )

    def uploadAab( self, filePath ):
        try:
            print( 'Uploading APK: {0}'.format( filePath ) )
            media = MediaFileUpload( filePath, mimetype='application/octet-stream', chunksize=1000, resumable=False )
            result = self.service.edits().bundles().upload(packageName=self.packageName, editId=self.edit['id'], media_body=media ).execute(http=self.http)
            return result['versionCode']
        except HttpError as error:
            print( '!! Failed to upload aab !!' )
            print( error )
        return None
    
    def uploadApk( self, filePath ):
        try:
            print( 'Uploading APK: {0}'.format( filePath ) )
            media = MediaFileUpload( filePath, mimetype='application/octet-stream', chunksize=1000, resumable=False )
            result = self.service.edits().apks().upload(packageName=self.packageName, editId=self.edit['id'], media_body=media ).execute(http=self.http)
            return result['versionCode']
        except HttpError as error:
            print( '!! Failed to upload apk !!' )
            print( error )
        return None
    
    def uploadObb( self, filePath, apkVersionCode, fileType = 'main' ):
        try:
            print( 'Uploading OBB: {0} with versioncode {1}'.format( filePath, apkVersionCode ) )
            media = MediaFileUpload( filePath, mimetype='application/octet-stream', chunksize=1000, resumable=False )
            return self.service.edits().expansionfiles().upload(packageName=self.packageName, editId=self.edit['id'], apkVersionCode=apkVersionCode, expansionFileType=fileType, media_body=media ).execute(http=self.http)
        except HttpError as error:
            print( '!! Failed to upload obb !!' )
            print( error )
    
    def upload( self, filePath, obbFilePath = None ):
        apkResponse = ''
        if 'aab' in filePath:
            apkResponse = self.uploadAab( filePath )
        else:
            apkResponse = self.uploadApk( filePath )
            if apkResponse is None:
                return None
            if obbFilePath is not None:
                self.uploadObb( obbFilePath, apkResponse )
        return apkResponse
            
    def uploadAndAddToTrack( self, appVersion, filePath, toStatus, obbFilePath = None, trackName = 'internal' ):
        self.getEdit()
        apkVersionCode = self.upload( filePath, obbFilePath )
        print( 'APK upload returned versioncode {0}'.format( apkVersionCode ) )
        if apkVersionCode is None:
            return
        self.updateTrack( appVersion, apkVersionCode, toStatus, trackName )
        if self.validateEdit():
            self.commitEdit();
        else:
            print( 'Aborting...' )
        self.resetEdit()

    def uploadImage(self, imageType, imagePath, languageCode='en-US', trackName = 'internal'):
        self.getEdit()
        try:
            print( 'Uploading image: {0}'.format( imagePath ) )
            media = MediaFileUpload( imagePath, mimetype='image/*', chunksize=1000, resumable=False )
            result = self.service.edits().images().upload(packageName=self.packageName, editId=self.edit['id'], media_body=media, imageType=imageType, language=languageCode ).execute(http=self.http)
        except HttpError as error:
            print( '!! Failed to upload image !!' )
            print( error )

        if self.validateEdit():
            self.commitEdit();
        else:
            print( 'Aborting...' )
        self.resetEdit()

    def promote(self, sourceTrack, targetTrack, toStatus ):
        self.getEdit()
        sourceTrackInfo = self.getTrack( sourceTrack )
        targetTrackInfo = self.getTrack( targetTrack )
        sourceVersionCode = sourceTrackInfo['releases'][0]['versionCodes'][0]
        targetVersionCode = targetTrackInfo['releases'][0]['versionCodes'][0] if targetTrackInfo is not None else 'N/A'
        print( "Promoting {0} from {1} to {2}, replacing {3}".format( sourceVersionCode, sourceTrack, targetTrack, targetVersionCode ) )

        targetTrackInfo = sourceTrackInfo
        targetTrackInfo['track'] = targetTrack
        targetTrackInfo['releases'][0]['status'] = toStatus

        try:
            self.service.edits().tracks().update(packageName=self.packageName, editId=self.edit['id'], track=targetTrack, body=targetTrackInfo).execute(http=self.http)
        except HttpError as error:
            print( '!! Failed to update status !!' )
            print( error )

        if self.validateEdit():
            self.commitEdit();
        self.resetEdit()

    def __init__( self, packageName, credentialsUri ):
        self.packageName = packageName;
        if os.path.isfile(credentialsUri):
            self.credentials = ServiceAccountCredentials.from_json_keyfile_name( credentialsUri, scopes=self.GOOGLE_PLAY_SCOPES)
        else:
            h = httplib2.Http(".cache")
            resp, content = h.request( credentialsUri, "GET" )
            json_str = content.decode('utf-8')
            js = json.loads( json_str )
            self.credentials = ServiceAccountCredentials.from_json_keyfile_dict( js, scopes=self.GOOGLE_PLAY_SCOPES)
        self.http = httplib2.Http()
        self.http = self.credentials.authorize(self.http)
        self.service = build("androidpublisher", "v3", http=self.http)

availableTracks = ["internal", "alpha", "beta", "production" ]
availableStatuses = ["draft", "completed", "halted", "inProgress" ]
imageTypes = ["featureGraphic", "icon", "phoneScreenshots", "promoGraphic", "sevenInchScreenshots", "tenInchScreenshots", "tvBanner", "tvScreenshots", "wearScreenshots"]

def parseArgs():
    parser = argparse.ArgumentParser(description='Google Play Android publisher')
    parser.add_argument('--packageName', required=True, action='store', help='example: com.yourCompany.yourTitle')
    parser.add_argument('--clientSecretUrl', required=True, action='store', help='URI to download client secret json from, web or local filesystem path')
    parser.add_argument('--trackName', choices=availableTracks, default='internal', help='Track to update')
    parser.add_argument('--changeLogJson', default='', action='store', help='Filesystem path of a file with change log stored in a json array.')

    subparsers = parser.add_subparsers(dest='subparser')

    uploadParser = subparsers.add_parser( 'uploadBuild', help='Upload a build to Google Play')
    uploadParser.add_argument('--aabOrApkPath', required=True, action='store', help='Filesystem path of the Android App Bundle Or Apk')
    uploadParser.add_argument('--obbPath', action='store', help='Filesystem path of the Android OBB file')
    uploadParser.add_argument('--releaseName', default='Anonymous', help='Descriptive name of the release')
    uploadParser.add_argument('--uploadStatus', choices=availableStatuses, default='draft', help='Status of the track after upload')

    uploadImageParser = subparsers.add_parser( 'uploadImage', help='Update image to to edit.')
    uploadImageParser.add_argument('--imageType', choices=imageTypes, required=True, default='featureGraphic', help='Image type to upload')
    uploadImageParser.add_argument('--imagePath', required=True, help='Path of file to upload')
    uploadImageParser.add_argument('--languageCode', default='en-US', help='LanguageCode of the image, if specific.')

    promoteParser = subparsers.add_parser( 'promoteTo', help='Promote the current release of a track to another track.')
    promoteParser.add_argument('--targetTrack', choices=availableTracks, required=True, help='The track which to promote a release to.')
    promoteParser.add_argument('--promoteStatus', choices=availableStatuses, default='draft', help='Status of the target track after promotion')
    
    return parser.parse_args()

def main(argv):
    args = parseArgs()

    gp = GooglePlay( args.packageName, args.clientSecretUrl )
    if args.subparser == 'uploadBuild':
        gp.uploadAndAddToTrack( args.releaseName, args.aabOrApkPath, args.uploadStatus, obbFilePath=args.obbPath, trackName=args.trackName )
    elif args.subparser == 'uploadImage':
        gp.uploadImage( args.imageType, args.imagePath, args.languageCode, trackName=args.trackName  )
    elif args.subparser == 'promoteTo':
        gp.promote( args.trackName, args.targetTrack, args.promoteStatus  )

if __name__ == '__main__':
    main(sys.argv)