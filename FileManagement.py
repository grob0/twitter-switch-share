from os import mkdir, path
from requests import get

class Local:
    def _get_filename_photo(self, url):
        name = url[url.rfind('/')+1:len(url)]
        return name

    def _get_filename_video(self, url):
        name = url[url.rfind('/')+1:url.rfind('.')+4]
        return name
    
    def get_file_name(self, url, Type):
        if Type == 'photo':
                file_name = self._get_filename_photo(url)
        elif Type == 'video':
                file_name = self._get_filename_video(url)
        return file_name

    def download_media(self, media_links, media_type):
        if not path.exists('media/'):
            mkdir('media/')
            print("Directory media/ created")
        for i in range(0,len(media_links)):
            url = media_links[i]
            Type = media_type[i]
            file_name = self.get_file_name(url,Type)
            r = get(url, allow_redirects=True)
            file_path = 'media/' + file_name
            open(file_path, 'wb').write(r.content)
