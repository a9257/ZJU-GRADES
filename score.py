import requests
import re
import os
import json
import smtplib
from PIL import Image
from lxml import etree
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

import config
from config import log


def captcha(image_page):
    """识别验证码"""
    num_captcha = []

    # 保存验证码图片
    with open(config.PATH_CAPTCHA_GIF, 'wb') as f:
        for chunk in image_page.iter_content(chunk_size=1024 * 16):
            if chunk:
                f.write(chunk)
    img = Image.open(config.PATH_CAPTCHA_GIF)
    img = img.convert('1')
    img.save(config.PATH_CAPTCHA_BMP)
    img.close()

    # 识别验证码
    img_captcha = Image.open(config.PATH_CAPTCHA_BMP)
    for i in range(0, 5):
        distance = [0 for j in range(0, 9)]
        img_part = img_captcha.crop((5 + i * 9, 5, 13 + i * 9, 17))
        pixels = img_part.load()
        lst_pixles = [0 if pixels[j, i] is 0 else 1 for i in range(0, 12) for j in range(0, 8)]
        for j in range(0, 9):
            for index, value in enumerate(lst_pixles):
                distance[j] += abs(value - config.LIST_RECO[j][index])
        min_index = 0
        min_value = distance[0]
        for dindex, value in enumerate(distance):
            if min_value > value:
                min_index = dindex
                min_value = value
        num_captcha.append(str(min_index))
    img_captcha.close()

    # print(''.join(num_captcha))
    return ''.join(num_captcha)


def get_grades(session):
    data_grade = {
        '__VIEWSTATE': '',
        'ddlXN': '',
        'ddlXQ': '',
        'txtQSCJ': '',
        'txtZZCJ': '',
        'Button2': '在校学习成绩查询',
    }

    try:
        res = session.get(config.URL_GRADE)
        data_grade['__VIEWSTATE'] = re.findall(r'name="__VIEWSTATE" value="(\S*)"', res.text)[0]
        res = session.post(config.URL_GRADE, data=data_grade)

        html = etree.HTML(res.text)
        table = html.xpath('//table[@id="DataGrid1"]/tr')

        updated_list = []
        with open(config.UPDATED, 'r') as f:
            course_list = json.load(f)

        for tr in table[1:]:
            line = tr.xpath('td/text()')
            if line[0] in course_list:
                continue
            course_list.append(line[0])
            updated_list.append('<td>' + '</td><td>'.join(line[1:5]) + '</td>')

        with open(config.UPDATED, 'w') as f:
            json.dump(course_list, f)

        if len(updated_list):
            log.info('Updated {} grades'.format(len(updated_list)))
            msgText = '<table border="1" rules="all"><tr>' \
                      '<td>课程名称</td><td>成绩</td><td>学分</td><td>绩点</td>' \
                      '</tr><tr>' + \
                      '</tr><tr>'.join(updated_list) + '</tr></table>'
            message = MIMEText(msgText, 'html', 'utf-8')
            message['From'] = formataddr([config.SENDER, config.SENDER])
            message['To'] = formataddr([config.RECEIVER, config.RECEIVER])
            message['Subject'] = Header('成绩更新%d门' % len(updated_list), 'utf-8')
            send_email(config.SENDER, config.RECEIVER, message)
        else:
            log.info('No update')

    except:
        # 获取成绩失败
        log.error('System error')
        message = MIMEText('系统出错，请检查程序', 'plain', 'utf-8')
        message['From'] = formataddr([config.SENDER, config.SENDER])
        message['To'] = formataddr([config.RECEIVER, config.RECEIVER])
        message['Subject'] = Header('自动查绩点系统出错', 'utf-8')
        send_email(config.SENDER, config.RECEIVER, message)


def send_email(sender, receiver, message):
    try:
        smtpObj = smtplib.SMTP_SSL(config.MAIL_HOST, 465)
        # smtpObj.set_debuglevel(1)
        smtpObj.login(config.MAIL_USER, config.MAIL_PASS)
        smtpObj.sendmail(sender, [receiver], message.as_string())
    except smtplib.SMTPException:
        log.error('Unable to send email')


if __name__ == '__main__':

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    session = requests.Session()

    # 登录首页
    # http://jwbinfosys.zju.edu.cn/default2.aspx
    data_login_index = {
        '__EVENTTARGET': 'Button1',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': '',
        'TextBox1': config.USERNAME,
        'TextBox2': config.PASSWORD,
        'TextBox3': '',
        'RadioButtonList1': '学生',
        'Text1': ''
    }
    res = session.get(config.URL_LOGIN_INDEX)
    data_login_index['__VIEWSTATE'] = re.findall(r'name="__VIEWSTATE" value="(\S*)"', res.text)[0]

    # 获取验证码
    img_page = session.get(config.URL_CAPTCHA)
    data_login_index['TextBox3'] = captcha(img_page)

    # 登录
    data_login_first = {
        'strXh': config.USERNAME,
        'strMm': config.PASSWORD,
        'strLx': '学生'
    }
    session.post(config.URL_LOGIN_FIRST, data=data_login_first)
    login_page = session.post(config.URL_LOGIN_INDEX, data=data_login_index)
    if login_page.url is not config.URL_INDEX:
        session.get(login_page.url)
    session.get(config.URL_INDEX)

    # 获取成绩并发送邮件
    get_grades(session)
