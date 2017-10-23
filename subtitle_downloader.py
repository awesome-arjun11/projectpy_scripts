import argparse
import os
import hashlib
import urllib.request as request
import struct
import gzip
from xmlrpc.client import ServerProxy


VIDEO_FORMATS = ['.3g2', '.3gp', '.3gp2', '.3gpp', '.60d', '.ajp', '.asf', '.asx', '.avchd', '.avi', '.bik', '.bix',
                    '.box', '.cam','.divx', '.dmf', '.dv', '.dvr-ms', '.evo', '.flc', '.fli', '.flic', '.flv','.flx',
                    '.gvi', '.gvp', '.h264', '.m1v', '.m2p', '.m2ts', '.m2v', '.m4e', '.m4v', '.mjp', '.mjpeg',
                    '.mjpg', '.mkv', '.moov', '.mov', '.movhd', '.movie', '.movx', '.mp4', '.mpe', '.mpeg', '.mpg',
                    '.mpv', '.mpv2', '.mxf', '.nsv', '.nut', '.ogg', '.ogm', '.omf', '.ps', '.qt', '.ram', '.rm',
                    '.rmvb', '.swf', '.ts', '.vfw', '.vid', '.video', '.viv', '.vivo', '.vob', '.vro', '.wm', '.wmv',
                    '.wmx', '.wrap', '.wvx', '.wx', '.x264', '.xvid']


class SubDB:
    """ API Link : https://goo.gl/n9B5J4
     """

    def __init__(self):
        self.BASEURL = "http://api.thesubdb.com/?action=download&hash="
        self.HEADERS = {
            'User-Agent': 'SubDB/1.0 (PPY/0.1; https://projectpy.ml/)',
        }

    def get_hash(self,name):
        """Originally from : https://goo.gl/n9B5J4
        """
        readsize = 64 * 1024
        with open(name, 'rb') as f:
            size = os.path.getsize(name)
            data = f.read(readsize)
            f.seek(-readsize, os.SEEK_END)
            data += f.read(readsize)
        return hashlib.md5(data).hexdigest()

    def download_subtitles(self,path,lang='en'):
        """
        :param path: The video file path for which to download subs.
        :param lang: Subtitle Language
        :return:
        """
        url = self.BASEURL + self.get_hash(path) + "&language=" + lang
        req = request.Request(url, headers=self.HEADERS)
        res = request.urlopen(req)
        if res.getcode() == 200:
            with open(os.path.splitext(path)[0] + '.srt', "wb") as sub_file:
                sub_file.write(res.read())
            print("Subtitles Found for: " + path)

    def get_lang(self):
        """
        :return: List of available subtitle languages
        """
        url = 'http://api.thesubdb.com/?action=languages'
        req = request.Request(url, headers=self.HEADERS)
        res = request.urlopen(req)
        if res.getcode() == 200:
            lang = res.read().decode('utf-8').split(',')
        else:
            # currently available
            lang = ['en', 'es', 'fr', 'it', 'nl', 'pl', 'pt', 'ro', 'sv', 'tr']
        return lang


class OpenSub:
    """ Some Class Methods Are Copied From : https://goo.gl/7Yohyj
        API Link : https://goo.gl/ZN8Wc1
    """

    def __init__(self):
        self.TAGS = ['bluray', 'cam', 'dvb', 'dvd', 'hd-dvd', 'hdtv', 'ppv', 'telecine', 'telesync', 'tv', 'vhs', 'vod',
                     'web-dl',
                     'webrip', 'workprint']
        self.OPENSUBTITLES_SERVER = 'http://api.opensubtitles.org/xml-rpc'
        self.USER_AGENT = 'OSTestUserAgentTemp'                              # Only for testing
        self.xmlrpc = ServerProxy(self.OPENSUBTITLES_SERVER,
                                  allow_none=True)
        self.language = 'en'
        self.token = None
        self.user = ''
        self.passw = ''
        if self.login(self.user, self.passw):
            print("Login Successful")
        else:
            print("OpenSubtitles login Failed. This could reduce the download limit")

    def _get_from_data_or_none(self, key):
        '''Return the key recieved from data if the status is 200,
        otherwise return None.
        '''
        status = self.data.get('status').split()[0]
        return self.data.get(key) if '200' == status else None

    def login(self, username, password):
        '''Returns token is login is ok, otherwise None.
        '''
        self.data = self.xmlrpc.LogIn(username, password,
                                      self.language, self.USER_AGENT)
        token = self._get_from_data_or_none('token')
        if token:
            self.token = token
        return token

    def logout(self):
        '''Returns True is logout is ok, otherwise None.
        '''
        data = self.xmlrpc.LogOut(self.token)
        return '200' in data.get('status')

    def search_subtitles(self, params):
        '''Returns a list with the subtitles info.
        '''
        self.data = self.xmlrpc.SearchSubtitles(self.token, params)
        return self._get_from_data_or_none('data')

    def download_subtitles(self, path,lang=''):
        """
        :param path: The video file path for which to download subs.
        :param lang: Subtitle Language
        :return:
        """
        payload = [self.create_payload(path,lang)]
        search_result = self.search_subtitles(payload)
        if search_result:
            dllink = self.analyse_result(search_result)
            gzfile = request.urlopen(dllink)
            try:
                with gzip.open(gzfile, 'rb') as f:
                    with open(os.path.splitext(path)[0] + '.srt', 'wb') as sub_file:
                        sub_file.write(f.read())
                        print("Subtitles Found for: " + path)
            except PermissionError:
                print(f"Permision Error: when creating subtitles for {path}:")

    def analyse_result(self, result):
        """
        :param result: Search result to find appropriate subtitles
        :return: Download Link of best match for subtitles
        """
        score = 0
        dllink = None
        for record in result:
            if record.get('Score', 0) > score:
                score = record.get('Score', 0)
                dllink = record.get('SubDownloadLink')
        return dllink

    def get_tags(self, path):
        """
        :param path: The video file path for which to download subs.
        :return: tags on video
        """
        name = os.path.basename(path).lower()
        tags = []
        for word in self.TAGS:
            if word in name:
                tags.append(word)
        return tags

    def create_payload(self, path, lang):
        """
        :param path: The video file path for which to download subs.
        :param lang: Subtitle Language
        :return: Payload containing data about file
        """
        payload = {}
        payload['moviebytesize'] = str(os.path.getsize(path))
        payload['sublanguageid'] = 'en,' + lang
        tags = self.get_tags(path)
        if tags:
            payload['tags'] = ','.join(tags)
        payload['moviehash'] = self.get_hash(path)
        return payload

    def get_hash(self, path):
        '''Original from: http://goo.gl/qqfM0
        '''
        size = os.path.getsize(path)
        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat)

        try:
            f = open(path, "rb")
        except(IOError):
            return "IOError"

        hash = int(size)

        if int(size) < 65536 * 2:
            return "SizeError"

        for x in range(65536 // bytesize):
            buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

        f.seek(max(0, int(size) - 65536), 0)
        for x in range(65536 // bytesize):
            buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF

        f.close()
        returnedhash = "%016x" % hash
        return str(returnedhash)


def down_sub(pathlist,lang =''):
    """Driver function to find subtitles with SubDB and OpenSubtitle
    """
    downloader_subdb = SubDB()              # SUBDB
    downloader_os = OpenSub()                 # OpenSubtitles
    for path in pathlist:
        if not os.path.exists(os.path.splitext(path)[0] + '.srt'):
            try:
                downloader_subdb.download_subtitles(path, lang)
            except:
                downloader_os.download_subtitles(path,lang)


def is_video(filepath):
    ext = os.path.splitext(filepath)[1]
    if ext in VIDEO_FORMATS:
        return True
    else:
        return False


def recursive_search(directory, all_vids=[]):
    """:param directory: Path of Directory to be searched recursively
       :param all_vids:  All video files
       :return: Path string of all video files in a directory/subdirectory
    """
    try:
        for entry in os.scandir(directory):
            if entry.is_dir():
                all_vids + (recursive_search(entry.path))
            elif entry.is_file():
                if is_video(entry.path):
                    all_vids.append(entry.path)
    except PermissionError as e:
        print(e)
    return all_vids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to the file or directory', type=str)
    parser.add_argument('-l','--language', help='Language of subtitle as per ISO 639-1 codes',type=str)
    args = parser.parse_args()
    path = args.path
    lang = 'en'
    if args.language:
        lang = args.language

    if os.path.isdir(path):
        down_sub(recursive_search(path),lang)
    else:
        if is_video(path):
            down_sub([path],lang)


if __name__ == "__main__":
    main()
