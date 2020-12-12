# coding:utf-8

import requests
from bs4 import BeautifulSoup 
import re
import datetime,smtplib,time
from urllib import unquote
from email.mime.text import MIMEText


dict_hkjss=dict()
dict_hkjss["main"]="https://hkjss.cn/"
dict_hkjss["dologin_url"]="dologin.php"
dict_hkjss["auth"]={"username":"623712611@qq.com","password":"ztz479803242641"}
dict_hkjss["headers"]={'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
num_used_now=0
num_use=0

def fun_id_date(response):
    str_utf8_response_text=response.text.encode("utf-8")
    BeautifulSoup_response=BeautifulSoup(str_utf8_response_text,"html.parser")

    dict_date_url={}
    for link in BeautifulSoup_response.find_all("tr"):
        str_link=str(link)
        if "有效的" in str_link:
            re_date=re.findall("<td>([0-9]{4}-[0-9]{2}-[0-9]{2})</td>",str_link)
            a_link=re.findall("<a class=\"btn\" href=\"(.*?)\">.*icon-list-alt",str_link)
            dict_date_url[re_date[0]]=str(a_link[0]).replace("&amp;","&")
    return fun_date_compare(dict_date_url)
   

def fun_date_compare(dict_date_url):
    list_dates=dict_date_url.keys()
    dict_new_date={}
    dict_new_date["str_new_date"]=list_dates[0]
    dict_new_date["date_new_date"]=datetime.datetime.strptime(list_dates[0], "%Y-%m-%d").date()
    for date in list_dates:
        date_this=datetime.datetime.strptime(date, "%Y-%m-%d").date()
        if date_this > dict_new_date["date_new_date"]:
            dict_new_date["date_new_date"] = date_this
            dict_new_date["str_new_date"]=date
        else:
            pass
    
    return dict_date_url[dict_new_date["str_new_date"]]
 
def fun_get_infor(response):
    str_utf8_infor_text=response.text.encode("utf-8")

    # list_gb=list()
    BeautifulSoup_infor=BeautifulSoup(str_utf8_infor_text,"html.parser")
    list_tr=BeautifulSoup_infor.find_all("tr")
    for i in list_tr:
        if re.findall(".*<td>已经使用</td>.*",str(i)):
            list_re_used=re.findall("<td>(.*? GB)</td>",str(i))
            # print list_re_used
    return str(list_re_used[0]).split(" ")[0]
 
    # print len(list_tr),[str(i)+"\n" for i in list_tr]



def send_email(title,content,recive_email='623712611@qq.com'):
    '''
    发送邮件，  
    参数为title、content和email(default)，  
    无返回，操作成功会直接写入log文件'''
    msg_from = '497309060@qq.com'  # 发送方邮箱地址。
    password = 'qsehffovhadubjjc'  # 发送方QQ邮箱授权码，不是QQ邮箱密码。
    #msg_to = '623712611@qq.com'  # 收件人邮箱地址。

    subject = "VPN Monitor  %s" % (title)  # 主题。
    # content = json.dump(gen_content(key))  # 邮件正文内容。
    content=str(content)
    msg = MIMEText(content, 'plain', 'utf-8')
 
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = recive_email
 
    try:
        client = smtplib.SMTP_SSL('smtp.qq.com', smtplib.SMTP_SSL_PORT)
        fun_log("连接到邮件服务器成功");

        client.login(msg_from, password);
        fun_log("登录成功")

        client.sendmail(msg_from, recive_email, msg.as_string())
        fun_log("发送成功","[title] %s" % (title),"[content] %s" % (content));
    except smtplib.SMTPException as e:
        fun_log("发送邮件异常",str(e))
    
    finally:
        fun_log("退出邮件客户端")
        client.quit()


def fun_get_used():
    try:
        session=requests.session()
        fun_log("Session 创建成功")
        fun_log("模拟用户登陆中....")
        response_dologin=session.post(url=dict_hkjss["main"]+dict_hkjss["dologin_url"],data=dict_hkjss['auth'],headers=dict_hkjss["headers"])
        fun_log("模拟用户登陆成功","服务器响应时长为%.3f秒 " % (response_dologin.elapsed.total_seconds()))
        dict_hkjss["str_new_id_url"]=fun_id_date(response_dologin)
        fun_log("以获取到最新服务页面url为%s" % (dict_hkjss["str_new_id_url"]))
        # print dict_hkjss
        fun_log("尝试获取服务详情页...")
        response_infor=session.get(url=dict_hkjss['main']+dict_hkjss['str_new_id_url'])
        fun_log("详情页获取成功，服务器响应时长为%.3f秒" % (response_infor.elapsed.total_seconds()))
        num_used=float(fun_get_infor(response_infor))
        return num_used
    except requests.exceptions.ConnectionError as e:
        fun_log("Connection refused",e)
        send_email("Error_Connection_Refused",e)





def fun_use_compare(num_used,send=False):
    
    global num_used_now
    global num_use
    if num_used_now < num_used:
        num_use = num_used - num_used_now
        num_used_now = num_used
    elif num_used_now == num_used:
        fun_log("流量消耗正常，短时间-流量消耗%.3fGB" % (num_use))
        num_use = 0

    if num_use >= 0.1:
        fun_log("流量告警","短时间-流量检查 消耗%.3fGB流量" % (num_use))
        send_email("流量告警","短时间-流量检查 消耗%.3fGB流量" % (num_use))
    if send:
        fun_log("例行检查汇报流量使用情况","目前共计已经消耗%.3fGB流量" % (num_used_now))
        send_email("例行检查汇报流量使用情况","目前共计已经消耗%.3fGB流量" % (num_used_now))
        

def fun_log(*content):
    str_time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    str_content = str()
    for i in content:
        str_content += i+" "
    str_log = "[ log ] %s %s \n" % (str_time_now,str_content)
    with open("vpn_monitor_log","a+") as f:
        f.write(str_log)


def main():
    fun_log("\n%s\nVPN_Monitor 启动\n%s\n\n" % ("+"+"---"*20+"+","+"+"---"*20+"+"))
    while 1:
        for i in range(3):
            fun_log("短时间-流量检查","第%s次" % (str(i+1)))
            fun_use_compare(fun_get_used())
            # print str(i)+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            fun_log("\n\n")
            time.sleep(1200)
        # print "send"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        fun_log("每小时例行检查")
        fun_use_compare(fun_get_used(),send=True)
        fun_log("\n\n%s\n" % ("+"+"---"*20+"+"))
        
if __name__ == "__main__":
    with open("vpn_monitor_log","w") as f:
        pass
    main()
    # fun_log("dfd","ddddd")