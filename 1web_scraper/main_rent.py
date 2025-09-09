import requests
from fake_useragent import UserAgent
import json
from lxml import etree
import re
import logging
import math
import time
import random
import os
import csv
import datetime
#输入关键词
#输入地点（省份或者城市，如果没有该城市，报错）列表
#开始爬取,用lxml提取信息
sess = requests.session()
logging.basicConfig(
        level=logging.DEBUG,
        format='[%(filename)s:%(lineno)s - %(funcName)s %(asctime)s;%(levelname)s] %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S'
)
#在当前路径下创建data文件夹
if(not os.path.exists('./data')): #如果当前路径下没有data文件夹 则创建
    os.mkdir('./data')
current_time = datetime.datetime.now()
date_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
filename = ''.join(re.findall(r'\d+', date_str))


def get_url(areas):#将用户的地点列表（省或城市）全部转为城市
    urls = []
    with open('city_rent.json','r',encoding="utf-8") as f:
        city_json = json.load(f)
    #对于每一个地点，先判断是不是省，如果是，直接加到目标set里。如果不是，再遍历
    for area in areas:
        if area in city_json.keys():
            for url in city_json[area].values():
                urls.append(url)
        else:
            for urldict in city_json.values():
                if area in urldict:
                    urls.append(urldict.get(area))
                    break
    return urls

def get_info(url,html):
    root = etree.HTML(html)
    panel = root.xpath('//div[@class="content__list"]')[0]
    # 计算当前页有多少岗位
    position_count = len(root.xpath('//div[@class="content__list--item"]'))
    for i in range(position_count):
        region = '' #小区
        position = '' #地点
        district = '' #行政区
        is_subway_house = ''

        #筛选出链家自营的房源，其他房源格式不齐
        brand = panel.xpath(f'(//p[@class="content__list--item--brand oneline"])[{i + 1}]//text()')
        if(len(brand) > 3 and '链家' not in brand[1]):
            continue
        try:
            is_subway_house = str(panel.xpath(f'(//i[contains(@class, "content__item__tag--is_subway_house")])[{i + 1}]/text()')[0]).strip()
        except:
            pass
        # 标题
        title = str(panel.xpath(f'(//p[contains(@class, "content__list--item--title")])[{i + 1}]/a/text()')[0]).strip()
        logging.info(f'标题：{title}')

        # 价格
        totalPrice = str(panel.xpath(f'(//span[@class="content__list--item-price"])[{i + 1}]/em/text()')[0])
        logging.info(f'价格：{totalPrice}')

        # 房子信息
        houseIcons = ''.join(panel.xpath(f'(//p[@class="content__list--item--des"])[{i + 1}]//text()')).replace('\n','').split('/')
        logging.info(f'详细信息：{houseIcons}')

        district = houseIcons[0].split('-')[0].replace(' ','')
        position = houseIcons[0].split('-')[1].replace(' ','')
        region = houseIcons[0].split('-')[2].replace(' ','')
        houseSize = houseIcons[1].replace(' ','')
        direction = houseIcons[2].strip()
        houseType = houseIcons[3].replace(' ','')
        level = houseIcons[4].replace(' ','')
        #houseType = houseIcons[0].strip()
        #houseSize = houseIcons[1].strip()
        #direction = houseIcons[2].strip()
        #fittings = houseIcons[3].strip()
        #level = houseIcons[4].strip()
        #buildTime = ''
        #struct = ''

        items = {
            '标题': title,
            '行政区': district,
            '小区': region,
            '地点': position,
            '户型': houseType,
            '面积': houseSize,
            '朝向': direction,
            #'装修': fittings,
            '楼层': level,
            '价格': totalPrice,
            '地铁': is_subway_house
            #'均价': unitPrice
        }
        write_csv(items, filename) #默认为运行程序的时间精确到秒，可以改成自己想要的其他名字


def get_areas():
    areas = ['郑州']
    urls = get_url(areas) #获取地点的全部url
    for url in urls:
        ua = UserAgent()
        headers = {
            'User-Agent': ua.chrome,
            'Referer': f'https://bj.lianjia.com/'}
        html = sess.get(url, headers=headers).text
        parse(url, html)

def parse(url,html):
    try:
        house_num = re.findall('共找到<span> (.*?) </span>套.*', html)[0].strip()
        logging.info(f'{url}共有{house_num}套')
    except:
        pass
    total_page = int(re.search(r'data-totalPage=(\d+)', html).group(1))
    #通过逐步翻页
    for i in range(total_page):
        if(i == 0):
            get_info(url,html)
        else:
            new_url = url + f'/pg{i+1}/'
            ua = UserAgent()
            headers = {
                'User-Agent': ua.chrome,
                'Referer': url}
            html = sess.get(new_url,headers=headers).text
            get_info(url, html)
        logging.info(f'第{i+1}页已爬完')
        time.sleep(random.uniform(5, 8)) #随机休眠5-8秒，不要短过5秒，会很快封ip
#将数据写入csv文件
def write_csv(items, job_name):
    file_name = job_name + '.csv'
    has_header = os.path.exists('./data/' + file_name)  # 文件头
    with open('./data/' + file_name, 'a', encoding='utf-8_sig',newline='') as file:
        writer = csv.DictWriter(file, fieldnames=items.keys())
        if not has_header:
            writer.writeheader()  # 写入文件头
        writer.writerow(items)

if __name__ == "__main__":
    get_areas()