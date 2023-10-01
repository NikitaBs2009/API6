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


def get_comic(comic_num):
    comic_info_url = "https://xkcd.com/{comic}/info.0.json"
    response = requests.get(comic_info_url.format(comic=comic_num))
    response.raise_for_status()
    answer = response.json()
    image = answer["img"]
    comment = answer["alt"]
    name = answer["title"]
    return image, comment, name, comic_num


def upload_to_server(file_name, photo_upload_url):
    with open(file_name, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(photo_upload_url, files=files)
    response.raise_for_status()
    answer = response.json()
    check_response(answer)
    server = answer["server"]
    response_hash = answer["hash"]
    photo = answer["photo"]
    return server, response_hash, photo


def get_upload_url(token, group_id, version):
    url = "https://api.vk.com/method/photos.getWallUploadServer"
    params = {"access_token": token, 'v': version, 'group_id': group_id}
    response = requests.get(url, params=params)
    response.raise_for_status()
    photo_upload_url = response.json()["response"]["upload_url"]
    check_response(photo_upload_url)
    return photo_upload_url


def save_to_wall(token, group_id, version, server, response_hash, photo):
    url = "https://api.vk.com/method/photos.saveWallPhoto"
    params = {"access_token": token, 'photo': photo, 'v': version, 'group_id': group_id, 'server': server,
              'hash': response_hash}
    response = requests.post(url, params=params)
    response.raise_for_status()
    answer = response.json()
    check_response(answer)
    return answer


def publish_to_group(token, group_id, version, comment, comic_num, owner_id, media_id):
    url = "https://api.vk.com/method/wall.post"
    attachments = f'photo{owner_id}_{media_id}'
    params = {"access_token": token, 'attachments': attachments, 'v': version, 'owner_id': -int(group_id),
              'message': comment, 'from_group': '1'}
    response = requests.post(url, params=params)
    response.raise_for_status()
    return comic_num, group_id


def get_comics_num():
    last_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(last_comic_url)
    response.raise_for_status()
    return response.json()['num']


def get_random_comic():
    total_comics = get_comics_num()
    random_comic_num = random.randint(1, total_comics)
    img_url, comment, title, comic_num = get_comic(random_comic_num)
    return img_url, comment, title, comic_num


def check_response(response):
    if 'error' in response:
        message = response['error']['error_msg']
        error_code = response['error']['error_code']
        raise requests.HTTPError(error_code, message)


def main():
    load_dotenv()
    version = 5.131
    vk_group_id = os.environ['VK_GROUP_ID']
    vk_token = os.environ['VK_TOKEN']
    try:
        img_url, author_comment, title, comic_num = get_random_comic()
        comic_filepath = download_image(title, img_url)
        photo_upload_url = get_upload_url(vk_token, vk_group_id, version)
        server, response_hash, photo = upload_to_server(comic_filepath, photo_upload_url)
        answer = save_to_wall(vk_token, vk_group_id, version, server, response_hash, photo)
        owner_id = answer["response"][0]["owner_id"]
        media_id = answer["response"][0]["id"]
        publish_to_group(vk_token, vk_group_id, version, author_comment, comic_num, owner_id, media_id)
        download_notification = f"Комикс №{comic_num} загружен в группу {vk_group_id}"
        print(download_notification)

    finally:
        os.remove(comic_filepath)


if __name__ == "__main__":
    main()
