# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   Author :       dangliuhui
   date：          2017/12/20
-------------------------------------------------
"""
import requests
import os
import json
import base64
import cv2
import time
import datetime
from PIL import Image
import logging
import pyautogui as pag
import configparser
import shutil


class FaceLock(object):
    """ 人脸识别锁屏类 """
    LOCK_SCREEN = False
    POINT_X = POINT_Y = GET_AT_TIME = FACE_MATCH_TIME = 0

    def __init__(self):
        # 读取配置文件
        conf = configparser.ConfigParser()
        conf.read('./conf.ini')
        self.AK = conf.get('setting', 'API_KEY')
        self.SK = conf.get('setting', 'SECRET_KEY')
        self.SCREEN_LOCK_LEVEL = float(conf.get('setting', 'SCREEN_LOCK_LEVEL'))
        self.LOCK_FACE_LIVENESS = float(conf.get('setting', 'LOCK_FACE_LIVENESS'))
        self.RETRY_TIME = int(conf.get('setting', 'RETRY_TIME'))
        if not os.path.exists('./log'):
            os.mkdir('./log')
        logName = './log/%s.log' % datetime.datetime.now().strftime('%Y_%m_%d')
        logging.basicConfig(filename=logName, level=logging.INFO,
                            format='[%(asctime)s] - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    # 获取接口access token
    def __getAccessToken(self):
        url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (
            self.AK, self.SK)
        try:
            request = requests.get(url)
            request.raise_for_status()
            res = json.loads(request.text)
            return res['access_token']
        except Exception as e:
            logging.error('获取access token失败:%s' % e)
            if self.GET_AT_TIME < self.RETRY_TIME:
                self.GET_AT_TIME += 1
                self.__getAccessToken()
            else:
                logging.error('获取access token失败,重试次数已用尽，程序退出')
                pag.alert(text='获取access token失败,重试次数已用尽，程序退出', title='人脸识别锁屏', timeout=1000 * 5)
                exit()

    # 开始检测
    def __checkIsMe(self):
        time.sleep(10)
        res = self.__match()
        logging.info('人脸识别结果：%s' % res)
        if res.get('result_num', 0) > 0:
            faceliveness = res.get('ext_info').get('faceliveness').split(',')[0]
            score = res['result'][0].get('score')
            if float(faceliveness) < self.LOCK_FACE_LIVENESS or float(score) < self.SCREEN_LOCK_LEVEL:
                logging.info('人脸相似度过小，或者不是真人识别，即将锁屏！')
                # 锁屏
                self.__lockScreen()
            else:
                logging.info('人脸相似度：%s，活体概率：%s，不锁屏' % (score, faceliveness))
        else:
            logging.error('人脸识别失败，可能没人在电脑面前，立即锁屏')
            self.__lockScreen(True)

    # 锁屏
    def __lockScreen(self, now=False):
        # 当前日期
        nowDate = datetime.datetime.now().strftime("%Y_%m_%d")
        # 当前时间
        nowTime = datetime.datetime.now().strftime("%H_%M_%S")
        # 保存导致锁屏的图片
        lock_picture_path = './picture/lock_pictures/%s' % nowDate
        if not os.path.exists(lock_picture_path):
            os.makedirs(lock_picture_path)
        new_path = '%s/%s.jpg' % (lock_picture_path, nowTime)
        shutil.move('./picture/face.jpg', new_path)
        res = 'NOW'
        if not now:
            res = pag.confirm('倒计时4秒，确定要锁屏吗?', timeout=1000 * 4, title='人脸识别锁屏')
            logging.info('confirm : %s' % res)

        if res == 'OK' or res == 'Timeout' or res == 'NOW':
            self.LOCK_SCREEN = True
            os.system('/System/Library/CoreServices/Menu\ Extras/User.menu/Contents/Resources/CGSession -suspend')
            time.sleep(7)
            x, y = pag.position()
            logging.info('锁屏前坐标：x=%d，y=%d' % (x, y))
            self.POINT_X = x
            self.POINT_Y = y

    # 人脸识别匹配
    def __match(self):
        AT = self.__getAccessToken()
        self.__getFace()
        url = 'https://aip.baidubce.com/rest/2.0/face/v2/match?access_token=%s' % AT
        img1 = base64.b64encode(open('./picture/face.jpg', 'rb').read()).decode()
        img2 = base64.b64encode(open('./picture/myFace.jpg', 'rb').read()).decode()
        data = {
            'images': img1 + ',' + img2,
            'image_liveness': 'faceliveness,',
            'types': '7,7'
        }
        try:
            request = requests.post(url, data=data)
            request.raise_for_status()
            res = request.text
            res = json.loads(res)
            err_code = res.get('error_code')
            if err_code != None:
                raise Exception(res.get('error_msg'))
            else:
                return res
        except Exception as e:
            logging.error('人脸识别错误: %s' % e)
            if self.FACE_MATCH_TIME < self.RETRY_TIME:
                self.FACE_MATCH_TIME += 1
                self.__match()
            else:
                logging.error('人脸识别失败,重试次数已用尽，程序退出')
                pag.alert('人脸识别失败,重试次数已用尽，程序退出', title='人脸识别锁屏', timeout=1000 * 5)
                exit()

    # 拍照
    def __getFace(self):
        cap = cv2.VideoCapture(0)
        while True:
            time.sleep(0.2)
            ret, frame = cap.read()
            if ret:
                # 制作缩略图
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image.thumbnail((500, 300))
                if not os.path.exists('./picture'):
                    os.mkdir('./picture')
                image.save("./picture/face.jpg", format='jpeg')
                break
            else:
                logging.error('拍照失败，重试...')
        cap.release()

    # 检查鼠标是否移动
    def __checkPointMove(self):
        # 每隔10秒检查一次
        time.sleep(10)
        x, y = pag.position()
        logging.info('鼠标坐标：x=%d,y=%d' % (x, y))
        if x == self.POINT_X and y == self.POINT_Y:
            logging.info('鼠标没动，还是锁屏状态')
        else:
            # 鼠标移动了，说明锁屏，继续运行
            self.LOCK_SCREEN = False
            logging.info('鼠标动了，继续运行人脸检测')

    # 开始执行
    def execute(self):
        while True:
            if self.LOCK_SCREEN:
                self.__checkPointMove()
            else:
                self.__checkIsMe()


if __name__ == '__main__':
    fl = FaceLock()
    print('已开启...')
    fl.execute()
