import smtplib
import time
import os

import pandas as pd

from email.mime.text import MIMEText
from EmQuantAPI import c


def c_get_trade_dates(start, end):
    c.start("ForceLogin=1")
    c_data = c.tradedates(start, end, "period=1").Data
    trade_dates = pd.to_datetime(c_data).strftime('%Y%m%d')
    c.stop()
    return list(trade_dates)


def transfer_to_jy_ticker(universe, inverse=False):
    """
    input: [601919.SH, 000333.SZ]
    output: [sh601919, sz000333]
    """
    if inverse:
        return [x[-6:] + '.' + x[:2].upper() for x in universe]
    else:
        return [x.split('.')[-1].lower() + x.split('.')[0] for x in universe]


def send_email(subject, content, receiver):
    # 配置第三方 SMTP 服务
    host = "smtp.163.com"
    mail_user = "13671217387@163.com"
    mail_pwd = 'YDIDWQVKNSKJHGYT'

    # 配置发送方、接收方信息
    sender = '13671217387@163.com'
    receivers = receiver

    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
    # content_html = markdown.markdown(content)
    message = MIMEText(content, "html", "utf-8")

    # message = MIMEText(content_html, 'html', 'utf-8')
    message['From'] = sender  # 发送者
    message['To'] = ','.join(receivers)  # 接收者
    message['Subject'] = subject  # 邮件主题
    try:
        smtp0bj = smtplib.SMTP()  # 建立和SMTP邮件服务器的连接
        smtp0bj.connect(host, 25)  # 25 为 SMTP 端口号
        smtp0bj.set_debuglevel(1)
        smtp0bj.login(mail_user, mail_pwd)
        smtp0bj.sendmail(sender, receivers, message.as_string())
        print(subject, '邮件发送成功')
        smtp0bj.quit()

    except smtplib.SMTPException as e:
        print(e)


def retry_save_excel(wb, file_path):
    try:
        wb.save(file_path)
        print(f'{file_path} has been saved')
    except Exception as e:
        print(e)
        print(f'{file_path} cannot be saved, wait for 10 seconds')
        time.sleep(10)
        retry_save_excel(wb, file_path)


def retry_remove_excel(file_path):
    try:
        os.remove(file_path)
        print(f'{file_path} has been removed')
    except Exception as e:
        print(e)
        print(f'{file_path} cannot be removed, wait for 10 seconds')
        time.sleep(10)
        retry_remove_excel(file_path)


class SendEmailInfo:
    department = {
        'research': ['zhou.sy@yz-fund.com.cn', 'wu.yw@yz-fund.com.cn'],
        'tech': ['liu.ch@yz-fund.com.cn', 'ling.sh@yz-fund.com.cn']
    }
