#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: lenovo by XYF
@file: checker.py
@time: 2020/03/12
@function: 
"""

import re
import requests
import json
import time
from bs4 import BeautifulSoup
import colorful
import os
import yaml

DOUYU_URL = "https://www.douyu.com/betard/"
DOUYU_SEARCH_URL = "https://www.douyu.com/search/"
HUYA_URL = "https://www.huya.com/"
ZHANQI_URL = "https://www.zhanqi.tv/"
BILIBILI_URL = "https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom"
BILIBILI_DESC_URL = "https://api.live.bilibili.com/room/v1/room/get_recommend_by_room"
EGAME_URL = "https://egame.qq.com/"
EGAME_API_URL = "https://share.egame.qq.com/cgi-bin/pgg_anchor_async_fcgi"

INFO = {
    "name": "livestream-checker",
    "author": "oGsLP",
    "repository": "www.github.com/oGsLP/livestream-checker",
    "version": "0.1.0",
    "publishDate": "20-03-13"
}


class Checker:
    __list = {
        "斗鱼": [],
        "虎牙": [],
        "B站": [],
        "战旗": [],
        "企鹅": []
    }

    def __init__(self):
        # print("init")
        colorful.use_256_ansi_colors()
        self.__intro()

    def read_yml(self, _path):
        if os.path.exists(_path):
            self.__list = yaml.load(open(_path, 'r', encoding='utf-8').read(), Loader=yaml.FullLoader)
        else:
            f = open(_path, "w+")
            f.close()
            print("  文件不存在，已自动创建文件 %ds ,请在文件中配置相关信息" % _path)

    def add_to_list(self, platform, room):
        if room in self.__list[platform]:
            print("请勿重复添加 平台：%s 房间：%s !" % (platform, str(room)))
        else:
            self.__list[platform].append(room)

    def check(self):
        for room in self.__list["斗鱼"]:
            self.__douyu_check(str(room))
        for room in self.__list["虎牙"]:
            self.__huya_check(str(room))
        for room in self.__list["B站"]:
            self.__bilibili_check(str(room))
        for room in self.__list["战旗"]:
            self.__zhanqi_check(str(room))
        for room in self.__list["企鹅"]:
            self.__egame_check(str(room))

    def __douyu_check(self, room):
        room = self.__douyu_switch_id(room)
        platform = colorful.bold_yellow_on_darkOrange("斗鱼")

        res = requests.get(DOUYU_URL + room)
        dta = json.loads(res.content.decode(encoding='utf-8', errors='strict'))
        room_data = dta['room']

        category = dta['column']['cate_name']
        game = dta['game']['tag_name']
        name = room_data['nickname']
        title = room_data['room_name']
        live = False

        t_now = room_data['nowtime']
        t_end = room_data['end_time']

        if int(t_now) >= int(t_end):
            desc = "上次直播(%s - %s) | %s" % (
                self.__resolve_timestamp(room_data['show_time']), self.__resolve_timestamp(t_end), title)
        else:
            live = True
            desc = "直播开始于(%s) | %s" % (self.__resolve_timestamp(room_data['show_time']), title)

        self.__log_room(platform, category, game, name, room, live, desc)
        res.close()
        time.sleep(0.2)

        # with open("data/douyu_" + room + ".json", "w") as fp:
        #     fp.write(json.dumps(dta, indent=2))

    @staticmethod
    def __douyu_switch_id(room):

        res = requests.get(DOUYU_SEARCH_URL, params={"kw": room}, headers={
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            'accept-encoding': "gzip, deflate, br"
        })
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        true_id = soup.find("a", class_="Search-anchor is-horizon").attrs['href'][1:]

        res.close()
        return true_id

    def __huya_check(self, room):

        platform = colorful.bold_saddleBrown_on_khaki("虎牙")

        res = requests.get(HUYA_URL + room)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        # info = soup.find("div", class_="host-info")

        name = soup.find("h3", class_="host-name").string
        title = soup.find("div", class_="host-title").string
        a = soup.find_all("a", class_="host-spl clickstat")
        category = a[0].string.strip()
        game = a[-1].string
        live = False
        prev_time = soup.find("span", class_="host-prevStartTime")
        if prev_time:
            desc = prev_time.span.string + " | " + title
        else:
            live = True
            desc = title

        self.__log_room(platform, category, game, name, room, live, desc)
        res.close()
        time.sleep(0.2)

        # with open("data/huya_" + room + ".html", "w",encoding="utf-8") as fp:
        #     fp.write(str(info))

    def __bilibili_check(self, room):

        platform = colorful.bold_mintCream_on_hotPink("B站")

        res = requests.get(BILIBILI_URL, params={'room_id': room})
        dta = json.loads(res.content.decode(encoding='utf-8', errors='strict'))['data']
        room_info = dta['room_info']

        name = dta['anchor_info']['base_info']['uname']
        category = room_info['parent_area_name']
        game = room_info["area_name"]
        title = room_info['title']
        live = False

        if room_info['live_status'] == 1:
            live = True
            t_start = self.__resolve_timestamp(room_info['live_start_time'])
            desc = "直播开始于(%s) | %s" % (t_start, title)
        elif room_info["live_status"] == 2:
            desc = "作品轮播中... | " + title
        else:
            res = requests.get(BILIBILI_DESC_URL, params={
                'room_id': room,
                'count': 0,
                'rnd': 0
            })
            desc = "%s... | %s" % (json.loads(res.content.decode(encoding='utf-8'))['data']['tips'], title)
        self.__log_room(platform, category, game, name, room, live, desc)
        res.close()
        time.sleep(0.2)

        # with open("data/bilibili_" + room + ".json", "w") as fp:
        #     fp.write(json.dumps(dta, indent=2))

    def __zhanqi_check(self, room):

        platform = colorful.bold_navyBlue_on_aliceBlue("战旗")

        res = requests.get(ZHANQI_URL + room)
        # res = requests.post(ZHANQI_INFO_URL, json={'roomId': room})
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")
        # soup.prettify()

        pattern = re.compile(r"window.oPageConfig.oRoom", re.MULTILINE | re.DOTALL)
        script = soup.find("script", text=pattern)
        s = pattern.search(script.text).string
        tmp = s.split(' window.oPageConfig.oRoom = ')[1].split('window.oPageConfig.oChatNotice')[0]
        dta = json.loads(re.sub(r"\s+", "", tmp)[:-1])

        title = dta['title']
        name = dta['nickname']

        clz = dta['className'] if 'className' in dta else ""
        ftr = dta['fatherGameName']
        cld = dta['childGameName'] if 'childGameName' in dta else ""

        if clz:
            if cld:
                category = "%s > %s" % (clz, ftr)
                game = cld
            else:
                category = clz
                game = ftr
        else:
            category = ftr
            game = cld

        t_last = self.__resolve_timestamp(dta['liveTime'])
        live = False
        if dta['status'] == "0":
            desc = "上次直播时间(%s) | %s" % (t_last, title)
        else:
            live = True
            desc = "直播开始于(%s) | %s" % (t_last, title)

        # with open("data/zhanqi_" + room + ".html", "w", encoding="utf-8") as fp:
        #     fp.write(str(dta))

        # body = soup.find("div", class_="anchor-info-area clearfix")
        # print(res.content)
        # body = json.load(res.content.decode(encoding='utf-8', errors='strict'))['data']
        # with open("data/zhanqi_" + room + ".json", "w") as fp:
        #     fp.write(json.dumps(dta, indent=2))

        self.__log_room(platform, category, game, name, room, live, desc)
        res.close()
        time.sleep(0.2)

    def __egame_check(self, room):

        platform = colorful.bold_gold_on_darkSlateBlue("企鹅")

        params_data = {
            'param': '{"key":{"module":"pgg_anchor_card_svr","method":"get_anchor_card_info","param":{"anchor_uid":%s,"user_uid": 0}}}' % room,
            'app_info': '{"platform":4,"terminal_type":2,"egame_id":"egame_official","imei":"","version_code":"9.9.9.9","version_name":"9.9.9.9","ext_info":{"_qedj_t":"","ALG-flag_type":"","ALG-flag_pos":""},"pvid":"259599155220031301"}',
            'g_tk': '',
            'pgg_tk': '',
            'tt': 1,
            '_t': ''
        }

        res = requests.get(EGAME_API_URL, params=params_data)
        res.encoding = 'utf-8'
        # soup = BeautifulSoup(res.text, "html.parser")
        # soup.prettify()
        #
        # gui = soup.find("div", class_="gui-main")
        dta = json.loads(res.content.decode(encoding='utf-8'))['data']['key']['retBody']['data']
        category = "直播"
        game = dta['appname']
        name = dta['nick_name']
        title = BeautifulSoup(requests.get(EGAME_URL + room).text, "html.parser") \
            .find("div", class_="anchor-info").h4.string
        t_start = self.__resolve_timestamp(dta['start_tm'])
        live = False
        if dta['is_live'] != 0:
            live = True
            desc = "直播开始于(%s) | %s" % (t_start, title)
        else:
            desc = "上次直播时间(%s) | %s" % (t_start, title)

        # with open("data/egame_" + room + ".json", "w") as fp:
        #     fp.write(json.dumps(dta, indent=2))

        # with open("data/egame_" + room + ".html", "w", encoding="utf-8") as fp:
        #     fp.write(str(soup))
        self.__log_room(platform, category, game, name, room, live, desc)
        res.close()
        time.sleep(0.2)

    @staticmethod
    def __resolve_timestamp(timestamp):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))[2:]

    @staticmethod
    def __log_room(platform, category, game, name, room, live, desc):
        print(platform, end="  ")

        print("%s >" % category, colorful.bold(game))
        print(" ", colorful.bold(name), "(%s)" % room, end=" ")
        if live:
            print(colorful.green("● 正在直播"))
        else:
            print(colorful.dimGray("● 未直播"))
        print(desc)
        print()

    @staticmethod
    def __intro():
        print()
        print("|  %s (v%s %s)" % (INFO["name"], INFO["version"], INFO["publishDate"]))
        print("|  本程序由%s提供, %s, 喜欢的话可以给个star >_<" % (INFO["author"], INFO["repository"]))
        print()
