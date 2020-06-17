from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from googleapiclient.http import MediaIoBaseUpload

from requests import get, post
from io import BytesIO

class DriveAPI:
    def connect(self):
        try :
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None
        SCOPES = 'https://www.googleapis.com/auth/drive.file'
        store = file.Storage('creds/storage.json')
        creds = store.get()
        if not creds or creds.invalid:
            print('make new storage data file ')
            flow = client.flow_from_clientsecrets('creds/client_secret.json', SCOPES)
            creds = tools.run_flow(flow, store, flags) \
                    if flags else tools.run_flow(flow, store)
        service = build('drive', 'v3', http=creds.authorize(Http()))
        return service

    def _search_folder(self,service, drive_folder_name):
        page_token = None
        while True:
            response = service.files().list(q="mimeType='application/vnd.google-apps.folder' and name='" + drive_folder_name + "'",
                                                spaces='drive',
                                                fields='nextPageToken, files(id, name)',
                                                pageToken=page_token).execute()
            
            folder_list = response.get('files', [])
            if page_token is None:
                break
        if folder_list:
            folder_id = folder_list[0].get('id')
            return folder_id

    def _create_folder(self, service, drive_folder_name):
        file_metadata = {
            'name': drive_folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        return folder_id

    def routine_folder(self, service, drive_folder_name):
        print('Searching "' + drive_folder_name + '" folder on Google Drive...')
        folder_id = self._search_folder(service, drive_folder_name)
        while not folder_id:
            print('Folder not found. Creating folder...')
            folder_id = self._create_folder(service, drive_folder_name)
        print('Folder created.')
        return folder_id

    def search_file(self, service, file_name):
        page_token = None
        query = "name='" + file_name +"'"
        while True:
            response = service.files().list(q= query,
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)',
                                            pageToken=page_token).execute()
            file_list = response.get('files', [])
            if page_token is None:
                break
        if file_list:
            return True
        else:
            return False
    
    def _get_file_type(self, file_name):
        f = file_name[file_name.rfind('.')+1:len(file_name)]
        if f == 'jpg' or f == 'jpeg':
            file_type = 'photo'
        elif f == 'mp4':
            file_type = 'video_mp4'
        else:
            file_type = 'unsupported'
        return file_type

    def get_IOBase_content(self, url):
        r = get(url) # from requests library
        f = BytesIO(r.content) # from io library
        return f 

    def _photo_file_upload(self, f_io):
        media = MediaIoBaseUpload(f_io, mimetype='image/jpeg')
        return media
    
    def _video_file_upload(self, f_io):
        media = MediaIoBaseUpload(f_io, mimetype='video/mp4')
        return media

    def upload_file(self, service, file_name, f_io, folder_id):
        file_metadata = {'name': file_name,
                         'parents': [folder_id]}
        file_type = self._get_file_type(file_name)
        if file_type == 'photo':
            media = self._photo_file_upload(f_io)
        elif file_type == 'video':
            media = self._video_file_upload(f_io)
        elif file_type == 'unsupported':
            print('Not supported format')
            return
        file = service.files().create(body=file_metadata, media_body=media).execute()
        print('%s uploaded' % file_name)
        return file

class PhotosAPI:

    def connect(self):
        try :
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None

        creds = self._get_credentials()
        service = build('photoslibrary', 'v1', http=creds.authorize(Http()))
        return service

    def _get_credentials(self):
        SCOPES = 'https://www.googleapis.com/auth/photoslibrary'
        store = file.Storage('creds/storage_photos.json')
        creds = store.get()
        if not creds or creds.invalid:
            print('make new storage data file ')
            flow = client.flow_from_clientsecrets('creds\client_secret.json', SCOPES)
            creds = tools.run_flow(flow, store, flags) \
                    if flags else tools.run_flow(flow, store)
        return creds

    def _search_album(self, service, album_title):
        page_token = None
        album_list = [];
        while True:
            response = service.albums().list(pageSize=50,
                                                fields='nextPageToken,albums(id,title)',
                                                pageToken=page_token).execute()

            album_list.extend(response.get('albums', []))
            page_token = response.get('nextPageToken')
            if page_token is None:
                break

        if album_list:
            for album in album_list:
                if album.get('title') == album_title:
                    return album.get('id')

    def _create_album(self, service, album_title):
        album_body = {
            'album': {
                'title': album_title,
                'isWriteable': True
                }
            }
        response = service.albums().create(body=album_body, fields='id').execute()
        return response.get('id')

    def routine_album(self, service, album_title):
        print('Searching "' + album_title + '" album on Google Photos...')
        album_id = self._search_album(service, album_title)
        while not album_id:
           print('Album not found. Creating album...')
           album_id = self._create_album(service, album_title)
        print('Album found.')
        return album_id

    def get_album_filenames(self, service, album_id):
        page_token = None
        media_items = []
        filenames = []
        while True:
            response = service.mediaItems().search(
                fields = 'nextPageToken,mediaItems(filename)',
                body = {"pageSize": 100, "albumId": album_id, "pageToken": page_token}).execute()

            media_items.extend(response.get('mediaItems', []))
            page_token = response.get('nextPageToken')
            if page_token is None:
                break

        for media_item in media_items:
            filenames.append(media_item.get('filename'))
        return filenames

    def get_IOBase_content(self, url):
        r = get(url) # from requests library
        f = BytesIO(r.content) # from io library
        return f

    def upload_file(self, file_name, f_io):
        creds = self._get_credentials()
        token = creds.access_token

        upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-type': 'application/octet-stream',
            'X-Goog-Upload-Protocol': 'raw',
            'X-Goog-Upload-File-Name': file_name
        }
        response = post(upload_url, data=f_io, headers=headers) # from requests library

        return response.content.decode('utf-8')

    def batch_create(self, service, album_id, upload_tokens):
        new_media_items = []
        for token in upload_tokens:
            simple_media_item = {
                    'simpleMediaItem': {
                        'uploadToken': token
                    }
                }
            new_media_items.append(simple_media_item)

        request_body  = {
            'albumId': album_id,
            'newMediaItems': new_media_items
        }

        upload_response = service.mediaItems().batchCreate(body=request_body).execute()
        return upload_response
