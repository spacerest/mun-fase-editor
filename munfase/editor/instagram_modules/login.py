from InstagramAPI import InstagramAPI

sn='mun_fases'
pw='Dr0w**ap!!'

def login():
    ig = InstagramAPI(sn, pw)
    ig.login()
    return ig

def post_image(obj):
    ig = login()
    caption = "test"
    photo_path = obj.image
    ig.uploadPhoto(photo_path, caption=caption)

