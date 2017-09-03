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

def setup_args():
    parser = argparse.ArgumentParser(description='WeChat bot')
    parser.add_argument('-n', '--target-nickname', metavar='target-nickname',
        help='the contact\'s nickname that you want to auto-reply to')
    return parser.parse_args()

def main():
    args = setup_args()
    itchat.auto_login(hotReload=True, enableCmdQR=True)
    delay = 0
    target = itchat.search_friends(nickName='Boyang')[0]
    print(target['UserName'])
    def send_img_later(task):
        itchat.send_image(task, toUserName=target['UserName'])
    for task in os.listdir():
        if '.jpg' in task:
            threading.Timer(delay, send_img_later, args=[task]).start()
            delay += 2
    itchat.run()
main()