#!/usr/bin/env python3
import os
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
from datetime import datetime
from datetime import timedelta

def setup_args():
    parser = argparse.ArgumentParser(description='WeChat bot')
    parser.add_argument('-n', '--target-nickname', metavar='target-nickname',
                        help='the contact\'s nickname that you want to auto-reply to')
    return parser.parse_args()


def get_secret():
    if get_secret.secret is not None:
        return get_secret.secret
    try:
        get_secret.secret = open('secret.txt', 'r').read()
        return get_secret.secret
    except Exception as e:
        print('You don\'t have a secret.txt file!', e)


get_secret.secret = None


def create_news_response_msg(response):
    msg = '人工智障: ' + response['text'] + '\n\n'
    for item in response['list']:
        if ('article' in item) and item['article'] != '':
            msg += '标题: ' + item['article'] + \
                '\n链接: ' + item['detailurl'] + '\n\n'
    return msg


def download_and_send_img(response, to_user_name):
    def send_img_later(task):
        filename = task['filename']
        url = task['url']
        urllib.request.urlretrieve(url, './imgs/' + filename)
        itchat.send_image('./imgs/' + filename, toUserName=to_user_name)
    if not os.path.exists('./imgs'):
        os.makedirs('./imgs')
    try:
        img_result_url = response['url'].replace(
            'm.image.so.com/i', 'm.image.so.com/j') + '&pn=30'
        print('img_result_url: ', img_result_url)
        itchat.send_msg('人工智障: 亲，已帮你找到图片，正在下载。如果我卡壳了，就再换一个图片要求发给我试试吧。',
                        toUserName=to_user_name)
        img_result_req = urllib.request.Request(url=img_result_url)
        img_result_req.add_header(
            'User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36')
        img_result_req.add_header('Host', 'm.image.so.com')
        img_f = urllib.request.urlopen(img_result_req, timeout=12)
        img_result = json.load(img_f)
        print('img_result: ', img_result)
        img_url_list = img_result['list']
        if len(img_url_list) == 0:
            print('No image found!', img_url_list)
            return '人工智障: 没有找到图片！'
        img_url_list = [url['thumb'].replace(
            '\/', '/') for url in img_url_list]
        target_urls = img_url_list[:2]
        for img_url in img_url_list:
            if '.gif' in img_url:
                target_urls.append(img_url)
                break
        print('target urls: ', target_urls)
        img_queue = [
            {'url': url, 'filename': url[url.rfind('/') + 1:]} for url in target_urls]
        delay = 0.5
        for task in img_queue:
            threading.Timer(delay, send_img_later, args=[task]).start()
            delay += 2
    except Exception as e:
        print('Error when downloading img', e)
        return '人工智障: 下载图片时发生错误！'


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
        global should_reply
        print('Received message from and type: ',
              msg['FromUserName'], msg['MsgType'])
        itchat.send_msg('人工智障: 收到，您稍等我反应慢...', toUserName=msg['FromUserName'])
        if (target is not None) and (msg['FromUserName'] != target['UserName']):
            return
        
        if msg['Content'] == 'open':
            print('in open')
            should_reply = True
            return
        elif msg['Content'] == 'close':
            print('in close')
            should_reply = False
            return
        
        if not should_reply:
            print('not should reply')
            return

        secret = get_secret()
        if secret is None:
            return
        if msg['MsgType'] == 3:
            msg['Content'] = '给我可爱小动物图片'
        msg['Content'] = msg['Content'].strip('\'"“')
        request_data = bytes('{{"key": "{}", "userid": 1, "info": "{}"}}'
                             .format(secret, msg['Content']), 'utf-8')
        req = urllib.request.Request(
            url='http://www.tuling123.com/openapi/api', data=request_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        try:
            f = urllib.request.urlopen(req, timeout=10)
            import codecs
            reader = codecs.getreader("utf-8")
            response = json.load(reader(f))
            print('Loaded response: ', response)
            if response['code'] in range(40000, 49999):
                print('Response returned error: ', response)
                return
            elif response['code'] == 200000:
                if '找到图片' in response['text']:
                    return download_and_send_img(response, msg['FromUserName'])
                else:
                    msg = '人工智障: {}\n'.format(response['text'])
                    if 'url' in response:
                        msg = (msg + 'URL: {}').format(response['url'])
                    return msg
            elif response['code'] == 302000:
                return create_news_response_msg(response)
            return '人工智障: ' + response['text']
        except Exception as e:
            print('Err: ', e)
            return '人工智障: 我卡壳了，再跟我说别的试试'

def setup_daily_news():
    secret = get_secret()
    if secret is None:
        return

    def get_next_delta_t():
        now_time = datetime.today()
        next_time = (now_time + timedelta(days=0)
                     ).replace(hour=10, minute=30, second=0)
        return (next_time - now_time).seconds + 1

    def send_daily_news():
        friend = itchat.search_friends(nickName='Boyang')[0]
        # for friend in itchat.get_friends(update=True):
        itchat.send_msg('人工智障: 我要给你发新闻了，回复TD退订...',
                        toUserName=friend['UserName'])
        request_data = bytes('{{"key": "{}", "userid": 1, "info": "{}"}}'
                             .format(secret, '给我发新闻'), 'utf-8')
        req = urllib.request.Request(
            url='http://www.tuling123.com/openapi/api', data=request_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        try:
            f = urllib.request.urlopen(req, timeout=30)
            response = json.load(f)
            print('Loaded response: ', response)
            if response['code'] in range(40000, 49999):
                print('Response returned error: ', response)
                itchat.send_msg('人工智障: 我卡壳了，今儿算了',
                                toUserName=friend['UserName'])
            elif response['code'] == 302000:
                itchat.send_msg(create_news_response_msg(
                    response), toUserName=friend['UserName'])
            else:
                itchat.send_msg(
                    '人工智障: ' + response['text'], toUserName=friend['UserName'])
        except Exception as e:
            print('Err when sending news: ', e)
            itchat.send_msg('人工智障: 我卡壳了，今儿算了', toUserName=friend['UserName'])
        threading.Timer(get_next_delta_t(), send_daily_news)
    print('Setting up daily news, now datetime: ', str(datetime.today()))
    threading.Timer(get_next_delta_t(), send_daily_news).start()


def main():
    args = setup_args()
    itchat.auto_login(hotReload=True)
    setup_auto_reply(args.target_nickname)
    # setup_daily_news()
    itchat.run()


main()
