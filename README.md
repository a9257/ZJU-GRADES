# ZJU-GPA
A script to get ZJUer's grades on http://jwbinfosys.zju.edu.cn/default2.aspx
## 使用说明
1. 配置文件

    替换`config.py`中下列信息
    ```
    USERNAME = '123456789'  # 填入学号
    PASSWORD = '123456'  # 填入密码
    MAIL_HOST = 'smtp.qq.com'  # SMTP服务器
    MAIL_USER = '123456789@qq.com'  # 邮箱用户名
    MAIL_PASS = '****************'  # 邮箱密码
    SENDER = '123456789@qq.com'  # 发件人
    RECEIVER = '123456789@qq.com'  # 收件人
    ```
2. 运行

    ```updated.json```用来保存已更新的成绩信息，请不要更改

    使用`python score.py`来运行脚本

    可以在服务器上使用crontab定时自动执行实现实时监控成绩信息
