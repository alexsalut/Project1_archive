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
import imaplib
import email
# 负责将多个对象集合起来
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os


class Mail(object):
    def __init__(self):
        self.send_mail_host = "smtp.feishu.cn"  # SMTP服务器
        self.receive_mail_host = "imap.feishu.cn"
        self.send_port = 25  # 端口号465
        self.receive_port = 993
        self.account = 'zhou.sy@yz-fund.com.cn'
        self.mail_license = 'FIhxF55WGb84C17V'

    def send(self, subject, body_content, attachs=[], pics=[], pic_disp=[], receivers=[]):
        mm = MIMEMultipart('related')  # 构建MIMEMultipart对象代表邮件本身，可以往里面添加文本、图片、附件等
        # 设置发送者,注意严格遵守格式,里面邮箱为发件人邮箱
        mm["From"] = self.account
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
        stp = smtplib.SMTP(self.send_mail_host)
        # 设置发件人邮箱的域名和端口
        stp.connect(self.send_mail_host, self.send_port)
        # set_debuglevel(1)可以打印出和SMTP服务器交互的所有信息
        # stp.set_debuglevel(1)
        stp.starttls()
        # 登录邮箱，传递参数1：邮箱地址，参数2：邮箱授权码
        stp.login(self.account, self.mail_license)
        # 发送邮件，传递参数1：发件人邮箱地址，参数2：收件人邮箱地址，参数3：把邮件内容格式改为str
        stp.sendmail(self.account, receivers, mm.as_string())
        print("邮件发送成功")
        # 关闭SMTP对象
        stp.quit()


    def receive(self, save_dir, date_range=[3,1]):
        import imaplib
        import email
        import os
        from email.header import decode_header
        from datetime import datetime, timedelta


        # Directory to save attachments

        # Set the time range to select emails after 5 PM yesterday
        now = datetime.now()
        last = now - timedelta(days=date_range[0])
        next = now + timedelta(days=date_range[1])

        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(self.receive_mail_host)
        mail.login(self.account, self.mail_license)
        mail.select('INBOX')

        # Construct the search criteria with the date format '17-Jul-2022'
        search_criteria = f'(SINCE "{last.strftime("%d-%b-%Y")}" BEFORE "{next.strftime("%d-%b-%Y")}")'

        # Search for emails within the specified time range
        status, email_ids = mail.search(None, search_criteria)
        email_ids = email_ids[0].split()

        # Download attachments from selected emails
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')

            if status == 'OK':
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    filename, encoding = decode_header(filename)[0]

                    if isinstance(filename, bytes):
                        filename = filename.decode(encoding or 'utf-8')

                    if filename:
                        # Construct the full path to save the attachment
                        full_path = os.path.join(save_dir, filename)
                        with open(full_path, 'wb') as attachment:
                            attachment.write(part.get_payload(decode=True))
                            print(f'{full_path} has been saved')

        # Close the connection
        mail.logout()
        print('邮件下载成功')


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
        'admin': ['chen.zf@yz-fund.com.cn']

    }


if __name__ == '__main__':
    Mail().receive(save_dir=r'C:\Users\Yz02\Desktop\Data\Save\账户对账单')