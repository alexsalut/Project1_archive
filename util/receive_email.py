#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/30 9:15
# @Author  : Suying
# @Site    : 
# @File    : receive_email.py

import os
from imbox import Imbox  # pip install imbox
import traceback



# enable less secure apps on your google account
# https://myaccount.google.com/lesssecureapps

stp = smtplib.SMTP(self.send_mail_host)
# 设置发件人邮箱的域名和端口
stp.connect(self.send_mail_host, self.send_port)
# set_debuglevel(1)可以打印出和SMTP服务器交互的所有信息
# stp.set_debuglevel(1)
stp.starttls()
# 登录邮箱，传递参数1：邮箱地址，参数2：邮箱授权码
stp.login(self.account, self.mail_license)