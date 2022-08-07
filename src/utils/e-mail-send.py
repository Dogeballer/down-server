import smtplib
from email.mime.text import MIMEText
from email.header import Header


# from_addr = 'fishballer_xufan@163.com'
# password = 'CLWZDRQJYCCDOIWK'
# # 输入收件人地址:
# to_addr = '752841090@qq.com'
# # 输入SMTP服务器地址:
# smtp_server = 'smtp.163.com'
#
# message = MIMEText('test', 'plain', 'utf-8')
# message['From'] = "fishballer_xufan@163.com"
# message['To'] = "752841090@qq.com"
# subject = 'test email'
# message['Subject'] = Header(subject, 'utf-8')
# server = smtplib.SMTP(smtp_server, 25)  # SMTP协议默认端口是25
# server.set_debuglevel(1)
# server.login(from_addr, password)
# server.sendmail(from_addr, [to_addr], message.as_string())
# server.quit()


def error_proxy_email_send(proxy):
    from_addr = 'fishballer_xufan@163.com'
    password = 'CLWZDRQJYCCDOIWK'
    # 输入收件人地址:
    to_addr = ['752841090@qq.com', '517593256@qq.com']
    # 输入SMTP服务器地址:
    smtp_server = 'smtp.163.com'

    text = str(proxy) + '连接异常，请检查网络状态！！'
    message = MIMEText(text, 'plain', 'utf-8')
    message['From'] = "fishballer_xufan@163.com"
    message['To'] = "752841090@qq.com"
    subject = text
    message['Subject'] = Header(subject, 'utf-8')
    try:
        server = smtplib.SMTP(smtp_server, 25)  # SMTP协议默认端口是25
        server.set_debuglevel(1)
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, message.as_string())
        server.quit()
    except:
        print("连接邮件服务异常，请检查！")



if __name__ == '__main__':
    error_proxy_email_send(proxy={'https': 'https://47.115.149.136:4111', 'http': 'http://47.115.149.136:4111'},
                           )
