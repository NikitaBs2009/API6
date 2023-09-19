import os
from dotenv import load_dotenv
import requests
import random
import dotenv
from urllib.parse import urlparse


def download_image(name, img_url):
    filepath = f"{name}{get_extension(img_url)}"

    response = requests.get(img_url)
    response.raise_for_status()

    with open(filepath, "wb") as file:
        file.write(response.content)
    return filepath


def get_extension(img_url):
    parsed_url = urlparse(img_url)
    extension = os.path.splitext(parsed_url.path)[1]
    return extension


def get_comic_info(comic_num):
    comic_info_url = "https://xkcd.com/{comic}/info.0.json"
    response = requests.get(comic_info_url.format(comic=comic_num))
    response.raise_for_status()
    answer = response.json()
    image = answer["img"]
    comment = answer["alt"]
    name = answer["title"]
    return image, comment, name, comic_num


def upload_to_server(token, group_id, version, file_name):
    photo_upload_url = get_upload_url(token, group_id, version)

    
    with open(file_name, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(photo_upload_url, files=files)
    response.raise_for_status()
    unswer = response.json()
    server = unswer["server"]
    response_hash = unswer["hash"]
    photo = unswer["photo"]
    return server, response_hash, photo


def get_upload_url(token, group_id, version):
    url = "https://api.vk.com/method/photos.getWallUploadServer"
    params = {"access_token": token, 'v': version, 'group_id': group_id}
    response = requests.get(url, params=params)
    response.raise_for_status()
    photo_upload_url = response.json()["response"]["upload_url"]
    return photo_upload_url


def save_to_wall(token, group_id, version, file_name):
    server, response_hash, photo = upload_to_server(token, group_id, version, file_name)
    url = "https://api.vk.com/method/photos.saveWallPhoto"
    params = {"access_token": token, 'photo': photo, 'v': version, 'group_id': group_id, 'server': server, 'hash': response_hash}
    response = requests.post(url, params=params)
    response.raise_for_status()
    unswer = response.json()
    return unswer


def publish_to_group(token, group_id, version, file_name, comment, comic_num):
    url = "https://api.vk.com/method/wall.post"
    save_info_photo = save_to_wall(token, group_id, version, file_name)
    owner_id = save_info_photo["response"][0]["owner_id"]
    media_id = save_info_photo["response"][0]["id"]
    attachments = f'photo{owner_id}_{media_id}'
    params = {"access_token": token, 'attachments':attachments, 'v': version,'owner_id':-int(group_id),  'message':comment, 'from_group':'1'}
    response = requests.post(url, params=params)
    response.raise_for_status()
    return f'комикс{comic_num} загружен групп{group_id}'


def get_comics_num():
    last_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(last_comic_url)
    response.raise_for_status()
    return response.json()['num']

def generate_random_comic():
    total_comics = get_comics_num()
    random_comic_num = random.randint(1, total_comics)
    img_url, comment, title, comic_num = get_comic_info(random_comic_num)
    return img_url, comment, title, comic_num


def main(): 
    load_dotenv()
    version = 5.131
    group_id = os.environ['GROUP_ID']
    token = os.environ['TOKEN']
    img_url, comment, title, comic_num = generate_random_comic()
    COMIC_FILEPATH = download_image(title, img_url)
    print(publish_to_group(token, group_id, version, COMIC_FILEPATH, comment, comic_num))
    os.remove(COMIC_FILEPATH)

                  
if __name__ == "__main__":
    main()