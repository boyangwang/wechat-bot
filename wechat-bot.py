import sys
import shutil
sys.defaultencoding = 'utf-8'
import itchat
import urllib
import urllib.request
import json
from itchat.content import TEXT
import argparse
import imghdr
import threading

def setup_args():
    parser = argparse.ArgumentParser(description='WeChat bot')
    parser.add_argument('-n', '--target-nickname', metavar='target-nickname',
        help='the contact\'s nickname that you want to auto-reply to')
    return parser.parse_args()

def setup_auto_reply(target_nickname):
    if target_nickname is not None:
        target = username=itchat.search_friends(nickName=user)[0]
        print('Auto reply to: ', target['NickName'], target['UserName'])
    else:
        target = None
        print('Auto reply to ALL')

    @itchat.msg_register(TEXT)
    def auto_reply(msg):
        def get_secret():
            if get_secret.secret is not None:
                return get_secret.secret
            try:
                get_secret.secret = open('secret.txt', 'r').read()
                return get_secret.secret
            except Exception as e:
                print('You don\'t have a secret.txt file!', e)
        get_secret.secret = None
        def download_and_send_img(response, to_user_name):
            try:
                img_result_url = response['url'].replace('m.image.so.com/i', 'm.image.so.com/j') + '&pn=50'
                print('img_result_url: ', img_result_url)
                img_result_req = urllib.request.Request(url=img_result_url)
                img_result_req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36')
                img_result_req.add_header('Cookie', 'PHPSESSID=s8lhq62rai0sr352ci6ps8uis2; __guid=100021698.309740684622375200.1504443870366.3638; count=2')
                img_result_req.add_header('Host', 'm.image.so.com')
                with urllib.request.urlopen(img_result_req) as img_f:
                    img_result = json.load(img_f)
                    print('img_result: ', img_result)
                    img_url_list = img_result['list']
                    if len(img_url_list) == 0:
                        print('No image found!', img_url_list)
                        return '人工智障: 没有找到图片！'
                    target_jpg_url = None
                    target_gif_url = None
                    for img_url in img_url_list:
                        if '.jpg' in img_url['thumb']:
                            target_jpg_url = img_url['thumb'].replace('\/', '/')
                        elif '.gif' in img_url['thumb']:
                            target_gif_url = img_url['thumb'].replace('\/', '/')
                        if (target_jpg_url is not None) and (target_gif_url is not None):
                            break
                    print('target_jpg_url and target_gif_url: ', target_jpg_url, target_gif_url)

                    def send_img_later(task):
                        filename = task['filename']
                        url = task['url']
                        urllib.request.urlretrieve(url, filename)
                        itchat.send_image(filename, toUserName=to_user_name)
                    img_queue = []
                    if target_jpg_url is not None:
                        img_queue.append({ 'url': target_jpg_url,
                            'filename': target_jpg_url[target_jpg_url.rfind('/') + 1:]})
                    if target_gif_url is not None:
                        img_queue.append({ 'url': target_gif_url,
                            'filename': target_gif_url[target_gif_url.rfind('/') + 1:]})
                    delay = 0.5
                    for task in img_queue:
                        threading.Timer(delay, send_img_later, args=[task]).start()
                        delay += 0.5
            except Exception as e:
                print('Error when downloading img', e)
                return '人工智障: 下载图片时发生错误！'

        if (target is not None) and (msg['FromUserName'] != target['UserName']):
            return
        secret = get_secret()
        if secret is None:
            return
        request_data = bytes('{{"key": "{}", "userid": 1, "info": "{}"}}'
            .format(secret, msg['Content']), 'utf-8')
        req = urllib.request.Request(url='http://www.tuling123.com/openapi/api', data=request_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as f:
            response = json.load(f)
            print('Loaded response: ', response)
            if response['code'] in range(40000, 49999):
                print('Response returned error: ', response)
                return
            if response['code'] == 200000:
                msg = download_and_send_img(response, msg['FromUserName'])
                if msg is not None:
                    return msg
            return '人工智障: ' + response['text']

def logout_callback():
    print('Logging out...')

def main():
    args = setup_args()
    itchat.auto_login(hotReload=True, enableCmdQR=True, exitCallback=logout_callback)
    setup_auto_reply(args.target_nickname)
    itchat.run()

main()