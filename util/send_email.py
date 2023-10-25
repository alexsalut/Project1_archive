#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 14:47
# @Author  : Suying
# @Site    : 
# @File    : send_email.py
import smtplib
# 负责构造文本
from email.mime.text import MIMEText
# 负责构造图片
from email.mime.image import MIMEImage
# 负责将多个对象集合起来
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os


class Mail(object):
    def __init__(self):
        self.mail_host = "smtp.163.com"  # SMTP服务器
        self.port = 25  # 端口号
        self.mail_sender = "13671217387@163.com"
        self.mail_license = 'YDIDWQVKNSKJHGYT'

    def send(self, subject, body_content, attachs=[], pics=[], pic_disp=[], receivers=[]):
        mm = MIMEMultipart('related')  # 构建MIMEMultipart对象代表邮件本身，可以往里面添加文本、图片、附件等
        # 设置发送者,注意严格遵守格式,里面邮箱为发件人邮箱
        mm["From"] = self.mail_sender
        # 设置接受者,注意严格遵守格式,里面邮箱为接受者邮箱
        mm["To"] = ','.join(receivers)
        # 1. 设置邮件头部内容
        mm["Subject"] = Header(subject, 'utf-8')
        # 2. 添加正文内容
        # body_footer = '<p style="color:red">此邮件为系统自动发送，请勿在此邮件上直接回复，谢谢~</p>'
        # 3. 添加附件
        for attach_file in attachs:
            with open(attach_file, 'rb') as file_info:
                atta = MIMEText(file_info.read(), 'base64', 'utf-8')
                atta.add_header('Content-Disposition', 'attachment',
                                filename=('utf-8', '', os.path.basename(attach_file)))
                # 添加附件到邮件信息当中去
                mm.attach(atta)
        # 4. 添加图片到附件
        # for pic_file in pics:
        #     with open(pic_file, 'rb') as image:
        #         image_info = MIMEImage(image.read())
        #         image_info.add_header('Content-Disposition', 'attachment',
        #                               filename=('utf-8', '', os.path.basename(pic_file)))
        #         mm.attach(image_info)
        # 5. 添加图片到正文
        pic_inline = '<p> </p>'
        for index, pic_file in enumerate(pics):
            pic_file_name = os.path.basename(pic_file)
            with open(pic_file, 'rb') as image:
                image_info = MIMEImage(image.read())
                image_info.add_header('Content-Id', f'<image{index + 1}>')
                mm.attach(image_info)
                tmp_pic_inline = f'''
                    <!-- <br>{pic_disp[index]} {pic_file_name}:</br> -->
                    <br><center><img src="cid:image{index + 1}" width="900" height="600" alt={pic_file_name}></center></br>
                    '''
                pic_inline += tmp_pic_inline
        mm.attach(MIMEText(body_content + pic_inline, "html", "utf-8"))
        # 创建SMTP对象
        stp = smtplib.SMTP(self.mail_host)
        # 设置发件人邮箱的域名和端口
        stp.connect(self.mail_host, self.port)
        # set_debuglevel(1)可以打印出和SMTP服务器交互的所有信息
        # stp.set_debuglevel(1)
        stp.starttls()
        # 登录邮箱，传递参数1：邮箱地址，参数2：邮箱授权码
        stp.login(self.mail_sender, self.mail_license)
        # 发送邮件，传递参数1：发件人邮箱地址，参数2：收件人邮箱地址，参数3：把邮件内容格式改为str
        stp.sendmail(self.mail_sender, receivers, mm.as_string())
        print("邮件发送成功")
        # 关闭SMTP对象
        stp.quit()


class R:
    staff = {
        'zhou': 'zhou.sy@yz-fund.com.cn',
        'wu': 'wu.yw@yz-fund.com.cn',
        'liu': 'liu.ch@yz-fund.com.cn',
        'ling': 'ling.sh@yz-fund.com.cn',
        'chen': 'chen.zf@yz-fund.com.cn'
    }
    department = {
        'research': ['zhou.sy@yz-fund.com.cn', 'wu.yw@yz-fund.com.cn'],
        'tech': ['liu.ch@yz-fund.com.cn', 'ling.sh@yz-fund.com.cn',],

    }


if __name__ == '__main__':
    sub = """Python邮件测试"""
    content = """
    <h1>这是一封测试邮件 - 1级标题</h1>
    <h2>这是一封测试邮件 - 2级标题</h2>
    <h3>这是一封测试邮件 - 3级标题</h3>
    """
    attach = [fr'./data/科创50涨跌幅分布_2023-10-18.html']
    pic = [fr'./data/科创50涨跌幅分布_2023-10-18.html']
    Mail().send(sub, content, attach, pic, ['科创50涨跌幅分布'], [R.staff['zhou'], R.staff['wu']])
