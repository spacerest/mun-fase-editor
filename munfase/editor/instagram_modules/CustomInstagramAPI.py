from InstagramAPI import InstagramAPI
import requests
from io import BytesIO
import __keys__

class CustomInstagramAPI():

    def __init__(self, test=False):
        if test:
            self.ig = InstagramAPI(__keys__.TEST_INSTAGRAM_SN, __keys__.TEST_INSTAGRAM_PW)
        else:
            self.ig = InstagramAPI(__keys__.INSTAGRAM_SN, __keys__.INSTAGRAM_PW)

    #todo check if user is already logged in before logging in again

    def post_image(self, image_path, caption, usertags=[], test=False):
        self.ig.login()
        photo_path = image_path
        self.ig.uploadPhoto(image_path, caption=caption, usertags=usertags)

    def get_image_info(self, post_url):
        self.ig.login()
        info = {}
        info['media_id'] = self.get_media_id(post_url)
        self.ig.mediaInfo(info['media_id'])
        media_info = self.ig.LastJson
        info['url'] = media_info['items'][0]['image_versions2']['candidates'][0]['url']
        info['user_id'] = media_info['items'][0]['user']['pk']
        return info

    def get_media_id(self, url):
        req = requests.get('https://api.instagram.com/oembed/?url={}'.format(url))
        media_id = req.json()['media_id']
        return media_id

    def get_username(self, media_id):
        if not media_id:
            return None
        self.ig.login()
        self.ig.mediaInfo(media_id)
        return self.ig.LastJson['items'][0]['user']['username']

