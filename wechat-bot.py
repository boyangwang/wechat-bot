#!/usr/bin/env python3
import sys
import shutil
sys.defaultencoding = 'utf-8'
import itchat
import urllib
import urllib.request
import json
from itchat.content import TEXT, PICTURE
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
        target = itchat.search_friends(nickName=user)[0]
        print('Auto reply to: ', target['NickName'], target['UserName'])
    else:
        target = None
        print('Auto reply to ALL')

    @itchat.msg_register(PICTURE)
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
                img_result_url = response['url'].replace('m.image.so.com/i', 'm.image.so.com/j') + '&pn=30'
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
                    img_url_list = [url['thumb'].replace('\/', '/') for url in img_url_list]
                    target_urls = img_url_list[:2]
                    for img_url in img_url_list:
                        if '.gif' in img_url:
                            target_urls.append(img_url)
                            break
                    print('target urls: ', target_urls)

                    def send_img_later(task):
                        filename = task['filename']
                        url = task['url']
                        urllib.request.urlretrieve(url, filename)
                        itchat.send_image(filename, toUserName=to_user_name)
                    img_queue = [{ 'url': url, 'filename': url[url.rfind('/') + 1:]} for url in target_urls]
                    delay = 0.5
                    for task in img_queue:
                        threading.Timer(delay, send_img_later, args=[task]).start()
                        delay += 2
            except Exception as e:
                print('Error when downloading img', e)
                return '人工智障: 下载图片时发生错误！'

        print('Received message from and type: ', msg['FromUserName'], msg['MsgType'])
        if (target is not None) and (msg['FromUserName'] != target['UserName']):
            return
        secret = get_secret()
        if secret is None:
            return
        if msg['MsgType'] == 3:
            msg['Content'] = '给我可爱小动物图片'
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

def main():
    args = setup_args()
    itchat.auto_login(hotReload=True, enableCmdQR=True)
    setup_auto_reply(args.target_nickname)
    itchat.run()

main()