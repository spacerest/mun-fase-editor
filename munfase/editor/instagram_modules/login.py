from InstagramAPI import InstagramAPI

sn='mun_fases'
pw='Dr0w**ap!!'

def login():
    ig = InstagramAPI(sn, pw)
    ig.login()
    return ig

def post_image(image_path, caption):
    ig = login()
    photo_path = image_path
    ig.uploadPhoto(photo_path, caption=caption)

