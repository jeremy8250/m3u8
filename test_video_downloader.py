import requests
import os
import sys
from Crypto.Cipher import AES


class TestVideoDownloader(object):

    def setup(self):
        # m3u8文件地址
        self.m3u8_url = "https://www.diankaiquanwen.com/20200316/j7tQIfxJ/1000kb/hls/index.m3u8"
        self.ts_folder = os.getcwd()+'/ts/'
        self.mp4_folder = os.getcwd()+'/mp4/'
        # self.ts = []
        # self.download_path = os.getcwd() + '/mp4/'
        # self.filename = "m3u8"
        # self.key = ""

    def test_downloader(self):
        """
        step1 准备下载文件夹
        """
        # 检查是否存在下载文件夹
        if not os.path.exists(self.download_path):
            # 如果没有则新建一个
            os.mkdir(self.download_path)
        else:
            # 如果有，则删除原来的
            cmd_rm_download = "rm -rf " + self.download_path
            os.system(cmd_rm_download)
            # 再新建一个
            os.mkdir(self.download_path)

        """
        step3 下载m3u8文件并提取key和ts文件
        """
        # 判断是否已经存在老版本的m3u8文件
        if not os.path.exists(os.getcwd() + self.filename):
            # 如果不存在则下载最新的（关闭SSL认证）
            req_video = requests.get(url=self.m3u8_url, verify=False)
            # 将下载的文件保存到本地，并命名为"index.m3u8"
            with open('index.m3u8', 'w') as f:
                f.write(req_video.text)
                f.flush()
                print('m3u8文件下载成功！')

        # 提取ts文件
        print('开始提取ts文件')
        with open('index.m3u8', 'r') as g:
            for line in g.readlines():
                if ".ts" in line:
                    # 去掉每个ts文件名后面的回车符号
                    ts_line = line.replace('\n', '')
                    # 将ts文件写入self.ts列表
                    self.ts.append(ts_line)
            # print(self.ts)

        # 提取key
        print('开始提取key_uri')
        with open('index.m3u8', 'r') as g:
            for line in g.readlines():
                # 查找key所在的行
                if "#EXT-X-KEY" in line:
                    # 定位URI的位置，也就是起始位置
                    uri_pos = line.find('URI')
                    # 从后往前，定位第一个双引号的位置，也就是最后一个双引号的位置
                    quot_pos = line.rfind('"')
                    # 从uri开始到最后一个双引号的位置，1️以"号分割，取第二个值，就是key.key
                    key_uri = line[uri_pos:quot_pos].split('"')[-1]
                    # print(key_uri)

        """
        # step4 下载key文件并解密其内容
        """
        print('开始解密key内容')
        # 将原来m3u8的地址替换成key.key
        key_url = self.m3u8_url.replace('/20200316/j7tQIfxJ/1000kb/hls/index.m3u8', key_uri)
        # 请求key
        req_key = requests.get(url=key_url, verify=False)
        # 获取返回内容，返回的是二进制的密码
        key = req_key.content
        # 将byte类型转换为str类型，并赋值给self.key
        self.key = str(key, 'utf-8')
        print(self.key)

        """
        # step5 下载ts文件
        """
        print('开始下载ts文件')
        # 遍历所有ts文件
        for i in range(len(self.ts)):
            # 获取ts文件名
            ts_name = self.ts[i]
            # 拼接ts地址
            ts_url = self.m3u8_url.replace("index.m3u8", ts_name)
            # 调用ts地址
            req_ts = requests.get(url=ts_url, verify=False)
            # 将ts文件下载到本地文件夹
            # ts_file_path = self.download_path + ts_name
            ts_file_path = os.getcwd() + '/ts' + ts_name
            with open(ts_file_path, 'w+') as q:
                q.write(req_ts.text)
                q.flush()

            """
            # step6 AES解密
            """
            # 如果key存在
            if len(self.key):
                # 通过AES解密ts文件，并转换成mp4文件输出
                cryptor = AES.new(self.key, AES.MODE_CBC, self.key)
                with open(os.path.join(self.download_path, ts_name + '.mp4'), 'wb') as f:
                    f.write(cryptor.decrypt(req_ts.content))
            else:
                # 如果key不存在，则不解密，直接转换成mp4文件输出
                with open(os.path.join(self.download_path, ts_name + '.mp4'), 'wb') as f:
                    f.write(req_ts.content)
                    f.flush()
            # 进度提示
            sys.stdout.write("已完成: %.3f%%" % float(i / len(self.ts)) + '\r')

        """
        # step7 合并mp4文件
        """
        # 切换到下载文件目录
        os.chdir(self.download_path)
        # 获取ts目录下所有文件
        path_list = os.listdir(self.download_path)
        # 将它们排序
        path_list.sort()
        # 合并文件输出
        cmd_merge = "cat *.mp4 > av.mp4"
        os.system(cmd_merge)

        """
        # step8 清理无用文件
        """
        # 清理所有琐碎文件
        cmd_rm_ts = "rm -rf *.ts"
        cmd_rm_ts_mp4 = "rm -rf *.ts.mp4"
        os.system(cmd_rm_ts)
        os.system(cmd_rm_ts_mp4)

        print('视频合并完成！')
