# encoding=utf-8
import os
import re
import time
import threading
import requests
from selenium import webdriver


class crawlCar(object):
    def __init__(self):
        self.driver = webdriver.PhantomJS(executable_path='phantomjs.exe')
        self.source_page = 'https://car.autohome.com.cn'
        self.source_folder = './download'
        self.count = 0
        self.start()


    def start(self):
        main_list = self.main_page()
        print("汽车之家图片库中，车品牌个数：",len(main_list))
        for i, ml in enumerate(main_list):
            if i != 16:  # 只爬取奥迪的，如果爬取所有的，这两行删掉
                continue
            sub_url = self.source_page + ml[0]
            sub_name = ml[1]
            sub_path = os.path.join(self.source_folder, sub_name)
            print(">>>>>第{}个品牌[{}],图片存储路径：{}".format(i+1, sub_name, sub_path))
            self.sub_page(sub_url, sub_path)


    # 获取汽车之家左侧产品库 从A-Z（图片栏）
    def main_page(self):
        self.driver.get(self.source_page + "/pic")
        html = self.driver.page_source
        html_match = '<li.*?<a href="(.*?)">.*?</i>(.*?)<em>.*?</li>'
        html_groups = re.findall(html_match, html)
        return html_groups


    # 从左侧栏进入某品牌汽车页面，如奥迪 https://car.autohome.com.cn/pic/brand-33.html
    # 获取奥迪 每个车系页面地址
    def sub_page(self, sub_url, sub_path):
        self.driver.get(sub_url)
        sub_html = self.driver.page_source
        sub_html_match = '<div><span class="fn-left"><a href="(.*?)" title=.*?>(.*?)</a>.*?</span>(.*?)</div>'
        sub_html_groups = re.findall(sub_html_match, sub_html)
        # 遍历，获取每个车系页面，如 奥迪A6L新能源，并判断是否上市，在售
        for shg in sub_html_groups:
            shg_url = self.source_page + shg[0]
            shg_name = shg[1]
            shg_icon = shg[2]
            if shg_icon:
                _icon = re.findall('icon-(.+?)">', shg_icon)
                shg_name = "{}（{}）".format(shg_name, _icon[0])
            shg_path = os.path.join(sub_path, shg_name)
            print(">>>>>车系：", shg_name)
            self.subsub_page(shg_url, shg_path)


    # 进入具体车系页面，如 shg_url = 'https://car.autohome.com.cn/pic/series/4526.html#pvareaid=2042214'
    # 获取 车身外观、中控方向盘、车厢座椅...等页面地址
    def subsub_page(self, shg_url, shg_path):
        self.driver.get(shg_url)
        subsub_html = self.driver.page_source
        subsub_html_match = '<div class="uibox-title"><a href="(.*?)">(.*?)</a>.*?</div>'
        subsub_html_groups = re.findall(subsub_html_match, subsub_html)
        for sshg in subsub_html_groups:
            sshg_url = self.source_page + sshg[0]
            sshg_name = sshg[1]
            sshg_path = os.path.join(shg_path, sshg_name)
            print(">>>>>{}图获取中...".format(sshg_name))
            self.count = 0 # 重置为0
            self.subsubsub_page(sshg_url, sshg_path)
            self.is_more_page(sshg_url, sshg_path)

    # 分析 sshg_url 是否需要分页，如 https://car.autohome.com.cn/pic/series/4526-12.html#pvareaid=2042220 需要分页
    def is_more_page(self, sshg_url, sshg_path):
        self.driver.get(sshg_url)
        subsubsub_html = self.driver.page_source
        is_more_page_match = '<div class="page">.*?<a href="(.*?)">(.*?)</a>.*?</div>'
        page_groups = re.findall(is_more_page_match, subsubsub_html)
        if not page_groups.__len__() == 0:
            for pg in page_groups:
                next_page_url = self.source_page + pg[0]
                self.subsubsub_page(next_page_url, sshg_path)


    # 进入具体图片类型页面，如进入 奥迪A6L新能源 的车身外观页面 sshg_url = 'https://car.autohome.com.cn/pic/series/4526-1.html#pvareaid=2042222'
    # 获取每个具体图片地址，可以将多线程放在这一步（能按照品牌--车系--照片类型 依次爬取）
    def subsubsub_page(self, sshg_url, sshg_path):
        self.driver.get(sshg_url)
        subsubsub_html = self.driver.page_source
        subsubsub_html_match = '<li><a href="(.*?)" title="(.*?)".*?<img src="(.*?)".*? title="(.*?)"></a>.*?</li>'
        subsubsub_html_groups = re.findall(subsubsub_html_match, subsubsub_html)
        for ssshg in subsubsub_html_groups:
            ssshg_url = self.source_page + ssshg[0]
            ssshg_name = ssshg[1]
            ssshg_pic_simple = self.source_page + ssshg[2]
            ssshg_name_simple = ssshg[3]
            ssshg_path = os.path.join(sshg_path, ssshg_name)
            self.get_download_url(ssshg_url,sshg_path)
            #download_thread = threading.Thread(target=self.get_download_url, args=(ssshg_url, sshg_path,))
            #download_thread.start()

    # 获取具体图片的下载地址，只会有一张图片
    def get_download_url(self, ssshg_url, sshg_path):
        self.driver.get(ssshg_url)
        pic_html = self.driver.page_source
        pic_match = '<img id="img" src="(.*?)".*?>'
        pic_groups = re.findall(pic_match, pic_html)
        pic_url = 'https:' + pic_groups[0]
        self.save_pic(pic_url, sshg_path)


    # 下载图片,超时时间设置为30秒
    def save_pic(self, pic_url, sshg_path, timeout=30):
        pic_name = str(time.time()) + '.jpg'
        file_path = os.path.join(sshg_path, pic_name)
        if not os.path.exists(sshg_path):
            os.makedirs(sshg_path)
        try:
            re_get = requests.get(pic_url, timeout=timeout)
            with open(file_path, "wb") as file:
                file.write(re_get.content)
        except requests.ConnectTimeout:
            print("connect time out")
        except Exception:
            print("download failed")
        self.count = self.count + 1
        print(">>>>>>>>>>>下载第{}张图片，下载地址：{}".format(self.count, pic_url))




if __name__ == '__main__':
    car = crawlCar()
    #download_url = 'https://car3.autoimg.cn/cardfs/product/g28/M01/AE/64/1024x0_1_q95_autohomecar__ChsEfV2nDz-AONc7AAr3mLyi1Qs175.jpg'
    #car.save_pic(download_url,"./download")