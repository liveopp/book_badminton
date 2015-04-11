from urllib import parse
import re
import http.client
import sys
import datetime
import smtplib
from email.mime.text import MIMEText

# Website info 
elife_url = "www.elife.fudan.edu.cn"
categoryid = "ff8080813a3f4447013a4351c1dd000b"
UserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36"
str_To_ContentID = {"zdymq":"ff8080813a3f43bc013a4356fdee0015","bqymq":"ff8080813dafa139013dc9c4326f010f"}
tint_To_Str = {8:"8:00",9:"9:00",10:"10:00",11:"11:00",\
        12:"12:00",13:"13:00",14:"14:00",15:"15:00",\
        16:"16:00",17:"17:00",18:"18:00",19:"19:00",\
        20:"20:00",21:"21:00",22:"22:30"}

def split_url(url):
    '''split url to get location and path dir.
    '''
    sp = parse.urlparse(url)
    loc = sp.netloc
    pat = sp.path
    paras = sp.query
    return loc,pat,paras

def user_login(username,passwd):
    # conn1 : "GET" uis login cookie
    uis_url = "uis2.fudan.edu.cn"
    uis_path = "/amserver/UI/Login"
    uis_params = parse.urlencode({"goto":"http://www.elife.fudan.edu.cn:80/cookielogin","gx_charset":"UTF-8"})
    uis_header = {"User-Agent":UserAgent}
    uis_conn = http.client.HTTPConnection(uis_url)
    uis_conn.request("GET", uis_path+('?%s'%uis_params), headers = uis_header)
    uis_res = uis_conn.getresponse()
    uis_cookie = uis_res.getheader("Set-cookie")
    # extract amlb cookie
    for ss in uis_cookie.split(','):
        if ss[:5] == " amlb":
            amlb_cookie = ss.split(";")[0]
    uis_conn.close()
    # conn2 : "POST" data to log in to uis
    uis_login_data = {
            "IDToken1":username,\
            "IDToken2":passwd,\
            "IDButton":"Submit",\
            "gx_charset":"UTF-8",\
            "goto":"aHR0cDovL3d3dy5lbGlmZS5mdWRhbi5lZHUuY246ODAvY29va2llbG9naW4=",\
            "encoded":"true"}
    uis_login_header={
            "Cookie":uis_cookie,\
            "User-Agent":UserAgent,\
            "Content-Type":"application/x-www-form-urlencoded"}
    uis_login_path = "/amserver/UI/Login"
    uis_login_conn = http.client.HTTPConnection(uis_url)
    uis_login_conn.request("POST", uis_login_path, parse.urlencode(uis_login_data), uis_login_header)
    # get location and cookie from uis login.
    uis_login_res = uis_login_conn.getresponse()
    url3 = uis_login_res.getheader("Location")#http://www.elife.fudan.edu.cn:80/cookielogin
    uis_login_cookie = uis_login_res.getheader("Set-Cookie")# iPlan cookie
    # get cookie iPlanetDirectory.
    for ss in uis_login_cookie.split(','):
        if ss[:5] == " iPla":
            iPlan_cookie = ss.split(";")[0]
    ## conn3  "GET" www.elife.fudan.edu.cn:80/cookielogin
    url3_loc,url3_path,url3_paras = split_url(url3)
    print(url3_loc)
    print("start connection...")
    conn3 = http.client.HTTPConnection(url3_loc)
    conn3_cookie = ','.join([amlb_cookie, iPlan_cookie])
    conn3_header = { "Cookie": conn3_cookie, "User-Agent":UserAgent }
    conn3.request("GET",url3_path, headers = conn3_header)
    res3 = conn3.getresponse()
    #url4 = res3.getheader('Location')# www.elife.fudan.edu.cn
    conn3_res_cookie = res3.getheader("Set-Cookie")
    # get elife jsessionID cookie
    for ss in conn3_res_cookie.split(','):
        if ss[:5] == "JSESS":
            jses_cookie = ss.split(";")[0]
    all_cookie = ','.join([amlb_cookie,iPlan_cookie,jses_cookie])
    conn3.close()
    return all_cookie

def get_resourcesID(cookie, contentid, Date):
    path = "/ordinary/meta/serviceResourceAction.action"
    data_dict ={"serviceContent.id":contentid,"currentDate":Date}
    params = parse.urlencode(data_dict)
    header = {
            "Cookie":cookie,\
            "User-Agent":UserAgent,\
            "Content-Type":"application/x-www-form-urlencoded",\
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",\
            "Accept-Encoding":"gzip, deflate, sdch",\
            "Accept-Language":"zh-CN,zh;q=0.8"}
    conn = http.client.HTTPConnection(elife_url)
    conn.request("GET", path+('?%s'%params), headers = header)
    res = conn.getresponse()
    html = res.read().decode('utf8')
    p = re.compile(r"onclick=\"checkUser\('(\w+)','([0-9:]+)','([0-9:]+)'\)")
    match = p.findall(html)
    return match

def get_Time_Avail(cookie, contentid, Date):
    path = "/ordinary/meta/serviceResourceAction.action"
    data_dict ={"serviceContent.id":contentid,"currentDate":Date}
    params = parse.urlencode(data_dict)
    header = {
            "Cookie":cookie,\
            "User-Agent":UserAgent,\
            "Content-Type":"application/x-www-form-urlencoded",\
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",\
            "Accept-Encoding":"gzip, deflate, sdch",\
            "Accept-Language":"zh-CN,zh;q=0.8"}
    conn = http.client.HTTPConnection(elife_url)
    conn.request("GET", path+('?%s'%params), headers = header)
    res = conn.getresponse()
    html = res.read().decode('utf8')
    p = re.compile(r"<font>([0:9]{1,2}):00<font>")
    match = p.findall(html)
    avail_t_list = [int(m) for m in match]
    return avail_t_list

def check_Resourcesid(cookie, resourcesID, endTime, beginTime):
    path = "/ordinary/meta/serviceResourceAction!timesLimit.action"
    data = parse.urlencode({"serviceResource.id":resourcesID,"endTime":endTime,"beginTime":beginTime})
    header = {
            "Cookie":cookie,\
            "User-Agent":UserAgent,\
            "Content-Type":"application/x-www-form-urlencoded",\
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",\
            "Accept-Encoding":"gzip, deflate, sdch"}
    conn = http.client.HTTPConnection(elife_url)
    conn.request("POST", path, data, header)
    res = conn.getresponse()
    whetherSuccess = False
    if res.read() == b"success":
        whetherSuccess = True
    conn.close()
    return whetherSuccess

def book(cookie, resourceID, contentid, Date, endTime, beginTime, name, mobile, depart):
    note=""
    phone = "021"
    path = "/order/meta/porder!doSave.action?op=order"
    post_dict={
            "serviceResource.id":resourceID,\
            "serviceOrders.appointTime":Date,\
            "endTime":endTime,\
            "beginTime":beginTime,\
            "serviceContent.id":contentid,\
            "serviceCategory.id":categoryid,\
            "orderuser":name,\
            "serviceOrders.mobile":mobile,\
            "serviceOrders.phone":phone,\
            "serviceOrders.department":depart,\
            "serviceOrders.note":note}
    post_data = parse.urlencode(post_dict)
    header = {
            "Cookie":cookie,\
            "User-Agent":UserAgent,\
            "Content-Type":"application/x-www-form-urlencoded",\
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",\
            "Accept-Encoding":"gzip, deflate, sdch",\
            "Accept-Language":"zh-CN,zh;q=0.8"}
    conn = http.client.HTTPConnection(elife_url)
    conn.request("POST", path, post_data, header)
    res = conn.getresponse()
    res_loc = res.getheader('Location')
    if res_loc != "":
        print(res_loc)
        conn.close()
        return True
    else:
        return False

def test():
    #user info
    import sys
    username = sys.argv[1]
    passwd = sys.argv[2]
    Date = "2015-03-22"
    name = "吴泽慧"
    mobile = "15201926086"
    depart = "数学科学学院"
    # log in to get Cookie
    cookie = user_login(username, passwd)
    # get Resources ID
    IDdata_list = get_resourcesID(cookie, contentid, Date)
    resourcesID = IDdata_list[0][0]
    beginTime = IDdata_list[0][1]
    endTime = IDdata_list[0][2]
    # check availability
    #tmp = check_available(cookie, resourcesID, endTime, beginTime)
    # Booking Badminton playground
    if book(cookie, resourcesID, contentid, Date, endTime, beginTime, name, mobile, depart):
        print( '%s\n%s\n%s\n%s\n%s\n Booking is Successful'%(name,username,Date,beginTime,endTime) )

def sleep_To_Day(weekday):
    weekday_dict = {"Mon":0,"Tue":1,"Wed":2,"Thu":3,"Fri":4,"Sat":5,"Sun":6}
    if weekday_dict.has_key(weekday):
        curTime = datetime.datetime.now()
        weekday_now = curTime.weekday()
        weekday_next = weekday_dict[weekday]
        if weekday_next > weekday_now:
            day_delta = weekday_next - weekday_now
        elif weekday_next == weekday_now and curTime.time() < datetime.time(12,28):
                day_delta = 0
        else:
            day_delta = weekday_next + 7 - weekday_now
        nextTime = curTime + datetime.timedelta(days = day_delta)
        nextTime = nextTime.replace(hour = 12, minute = 28, second = 0)
        deltaT = nextTime - curTime
        sleep(deltaT.total_seconds())

def get_Date_String(datet):
    y = datet.year
    m = datet.month
    d = datet.day
    return "%s-%s-%s"%(y,m,d)

def check_Avail(cookie, task, Date):
    p = task[0]
    t = task[1]
    contentid = str_To_ContentID[p]
    # todo... rebuild
    (if_get, IDdata_list) = get_resourcesID(cookie, contentid, Date)
    if_avail = False
    book_data = {}
    if if_get:
        avail_start_time = [d[1] for d in IDdata_list]
        if tint_To_Str[t] in avail_start_time:
            if_avail = True
            idx = avail_start_time.index(tint_To_Str[t])
            resID_tuple = IDdata_list[idx]
            book_data["resourcesID"] = resID_tuple[0]
            book_data["beginTime"] = resID_tuple[1]
            book_data["endTime"] = resID_tuple[2]
            book_data["contentID"] = contentid
    return if_avail,book_data

def book_badminton():
    depart = "数学科学学院"
    user_info = [{'userid':'13110180023','passwd':'5facechallenge','mobile':'15201926086','name':'吴泽慧'},\
            {'userid':'13110180026','passwd':'','mobile':'13162526856','name':'张航'}]
    task_list = [{'weekday':'Thu','beginTime':20,"location":"bqymq"}, {'weekday':'Sun','beginTime':21,'location':'zdymq'}]
    cookie = ''
    for i,t in enumerate(task_list):
        sleepToNext(t['weekday'])
        location = t["location"]
        begin_t = t["beginTime"]
        user = user_info[i]["userid"]
        password = user_info[i]["passwd"]
        name = user_info[i]['name']
        mobile = user_info[i]['mobile']
        #todo login not success
        cookie = user_login(user, password)
        date_str = get_Date_String( datetime.date.today()+datetime.timedelta(days = 7) ) 
        # check whether has available
        contentid = str_To_ContentID[location]
        avail_t = get_Time_Avail(cookie, contentid, date_str)
        beginTime = tint_To_Str[begin_t]
        if begin_t in avail_t:
            has_book = False
            is_avail = True
            while datetime.datetime.now().time() < datetime.time(12,40) and not has_book and is_avail:
                match = get_resourcesID(cookie, contentid, date_str)
                if match:
                    avail_dict = {}
                    for m in match:
                        avail_dict[m[1]] = m
                    if avail_dict.has_key(beginTime):
                        resourceid = avail_dict[beginTime][0]
                        endTime = avail_dict[beginTime][2]
                        for i in range(2):
                            book_res1 = book(cookie, resourceid, contentid, date_str, endTime, beginTime, name, mobile, depart)
                            if book_res1:
                                has_book = True
                                break
                            else:
                                sleep(1)
                    else:
                        is_avail = False
                else:
                    sleep(10)
            # send mail
            fdmail = smtplib.SMTP('mail.fudan.edu.cn')
            my_mail_addr = '13110180023@fudan.edu.cn'
            my_mail_passwd = '5facechallenge'
            fdmail.login(my_mail_addr,my_mail_passwd)
            if has_book:
                msg = MIMEText('badminton has booked for you.\nlocation:%s\nday:%s\nbeginTime:%s'%(location,date_str,beginTime))
                msg['Subject'] = 'badminton booking succeed'
                msg['From'] = my_mail_addr
                msg['To'] = user+'@fudan.edu.cn'
                fdmail.sendmail(my_mail_addr, msg['To'], msg.as_string())
            else:
                msg = MIMEText('badminton booking failure')
                msg['Subject'] = 'badminton booking failure'
                msg['From'] = my_mail_addr
                msg['To'] = user+'@fudan.edu.cn'
                fdmail.sendmail(my_mail_addr, msg['To'], msg.as_string())
            fdmail.quit()

if __name__ == '__main__':
    book_badminton()
