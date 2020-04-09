import re
import requests
import os
from Crypto.Cipher import AES
import logging
import sys

"""
用到的插件:pycrypto，需要将site-packages中的crypto改成Crypto
"""


class TestM3u8Downloader:
    logging.basicConfig(level=logging.INFO)

    def setup(self):
        """
        step0.各种初始化工作
        """
        logging.info("开始初始化...")

        # m3u8文件地址
        self.m3u8_url = "https://www.zhongyuguozi.com//20200101/Q8Y06CNz/1000kb/hls/index.m3u8"
        # m3u8文件存储路径
        self.m3u8_file = os.getcwd() + '/index.m3u8'

        # 检查是否存在老旧的ts文件夹和mp4文件夹，有就删掉重建，没有就直接新建
        self.ts_folder = os.getcwd() + '/ts/'
        self.mp4_folder = os.getcwd() + '/mp4/'
        if not os.path.exists(self.ts_folder):
            os.mkdir(self.ts_folder)
        else:
            os.system("rm -rf " + self.ts_folder)
            os.mkdir(self.ts_folder)
        logging.info("创建ts文件夹成功!")

        if not os.path.exists(self.mp4_folder):
            os.mkdir(self.mp4_folder)
        else:
            os.system("rm -rf " + self.mp4_folder)
            os.mkdir(self.mp4_folder)
        logging.info("创建mp4文件夹成功!")

        # ts列表，用来存放m3u8中提取的ts文件名
        self.ts_list = []
        # key变量，用来存放从key.key中解析出来的keycode
        self.key = ""

    def test_download_m3u8(self):
        """
        step1.下载m3u8文件
        """
        # 删掉老旧的m3u8文件
        if os.path.exists(self.m3u8_file):
            os.system("rm -rf " + self.m3u8_file)

        # 下载m3u8文件，并保存到本地index.m3u8文件
        req_m3u8 = requests.get(self.m3u8_url, verify=False)
        with open('index.m3u8', 'w') as f:
            f.write(req_m3u8.text)
        logging.info("下载index.m3u8成功!")

        """
        step2.提取ts文件名到ts列表
        """
        with open('index.m3u8') as g:
            for line in g.readlines():
                if '.ts' in line:
                    # 去掉尾部的回车符
                    line = line.rstrip().split('/')[-1]
                    self.ts_list.append(line)
        logging.info("提取ts文件名成功！共计%d个文件" % len(self.ts_list))

        """
        step3.获取key值
        """
        with open('index.m3u8') as h:
            for line in h:
                # 如果存在关键字'EXT-X-KEY'，则用双引号作为分隔符，取倒数第二个
                if 'EXT-X-KEY' in line:
                    key_uri = line.split('"')[-2]
        # 正则匹配self.m3u8_url的域名，需要用group转换成string，才能赋值给变量
        domain = re.match('http.*com', self.m3u8_url).group()
        # 拼接key_url，并请求，获取key
        key_url = domain + key_uri
        req_key_url = requests.get(key_url, verify=False)
        self.key = str(req_key_url.content, 'utf-8')
        logging.info("转换keycode成功，keycode=%s" % self.key)

        """
        step4.下载ts文件
        """
        # for i in range(len(self.ts_list)):
        for i in range(50):
            # 拼接ts地址
            ts_url = self.m3u8_url.replace("index.m3u8", self.ts_list[i])
            # 调用ts地址
            req_ts = requests.get(url=ts_url, verify=False)
            ts_file = self.ts_folder + '00' + str(i) + '.ts'
            # 将ts文件下载到本地文件夹
            with open(ts_file, 'w+') as q:
                q.write(req_ts.text)
            # 进度提示
            # sys.stdout.write("ts文件下载进度已完成: %.3f%%" % float(i / len(self.ts_list)) + '\r')

            """
            step5.解密ts文件，并转换成mp4
            """
            # 如果key存在
            if len(self.key):
                # 通过AES解密ts文件，并转换成mp4文件输出
                cryptor = AES.new(self.key, AES.MODE_CBC, self.key)
                with open(os.path.join(self.mp4_folder, '00' + str(i) + '.ts' + '.mp4'), 'wb') as j:
                    j.write(cryptor.decrypt(req_ts.content))
            else:
                # 如果key不存在，则不解密，直接转换成mp4文件输出
                with open(os.path.join(self.mp4_folder, '00' + str(i) + '.ts' + '.mp4'), 'wb') as j:
                    j.write(req_ts.content)
            # 进度提示
            # sys.stdout.write("mp4转换进度已完成: %.3f%%" % float(i / len(self.ts_list)) + '\r')

        """
        step6.合并mp4
        """
        # 切换到下载文件目录
        os.chdir(self.mp4_folder)
        # 获取ts目录下所有文件
        mp4_list = os.listdir(self.mp4_folder)
        # 排序
        mp4_list.sort()
        # 合并文件输出
        os.system("cat *.mp4 > all.mp4")

    """
    step7.清理无用数据
    """
    def teardown(self):
        # cmd_rm_ts = "rm -rf " + self.ts_folder + "*.ts"
        # cmd_rm_ts_mp4 = "rm -rf " + self.mp4_folder + "*.ts.mp4"
        # os.system(cmd_rm_ts)
        # os.system(cmd_rm_ts_mp4)
        logging.info('视频合并完成！')
