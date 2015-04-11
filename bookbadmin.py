from urllib import parse
import re
import http.client
import sys
import datetime
import Queue

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
    conn.close()
    if match:
        return True,match
    else:
        return False,[]

def get_Time_Avail(cookie, contentid, Date, t_list):
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

def sleepToNext():
    curTime = datetime.datetime.now()
    if curTime.time() > datetime.time(12,40):
        nextTime = curTime + datetime.timedelta(days = 1)
        nextTime = nextTime.replace(hour = 12, minute = 25, second = 0)
        deltaT = nextTime - curTime
        sleep(deltaT.total_seconds())
    elif curTime.time() < datetime.time(12,25):
        nextTime = curTime.replace(hour = 12, minute = 25, second = 0)
        deltaT = nextTIme - curTime
        sleep(deltaT.total_seconds())
    else:
        pass

def get_Config_File(furl = '/etc/bookbadmin.conf'):
    ifcorrect = True
    optword1 = ("place","time","day")
    optword2 = ("user","password","depart","name","mobile")
    optdict = {
            "place":("bqymq","zdymq"),\
            "time":(8,9,10,11,12,13,14,15,16,17,18,19,20,21),\
            "day":("Mon","Tue","Wed","Thu","Fri","Sat","Sun")}
    #Todo file exist control...
    opt = {}
    with open(furl,'r') as fh:
        for line in fh:
            if re.match(r"^\s*#",line):
                pass
            else:
                str_list = line.split(":")
                if len(str_list) <= 1:
                    ifcorrect = False
                    break
                else:
                    if str_list[0] in optword1:
                        opt_list = []
                        for dw in str_list[1]:
                            if dw in optdict[str_list[0]]:
                                opt_list.append(dw)
                            else:
                                ifcorrect = False
                                break
                        opt[str_list[0]] = opt_list
                    elif str_list[0] in optword2:
                        opt[str_list[0]] = str_list[2]
                    else:
                        ifcorrect = False
                        break
    return ifcorrect,opt


def get_Today_Date():
    td = datetime.date.today()
    y = td.year
    m = td.month
    d = td.day
    return "%s-%s-%s"%(y,m,d)

def get_Today_Task(opt):
    '''return a Today's Task Queue,
    every element in the Queue is a list, elements like following.
    for example, ["bqymq", 19 ]
    '''
    place_list = opt["place"]
    time_list = opt["time"]
    day_list = opt["day"]
    #parsing opt
    strtowd = {"Mon":0, "Tue":1, "Wed":2, "Thu":3, "Fri":4, "Sat":5, "Sun":6 }
    td = datetime.date.today()
    cur_wd = td.weekday()
    zdymq_t_list = []
    bqymq_t_list = []
    for d in day_list:
        if strtowd[d] == cur_wd:
            for p in place_list:
                if p == 'zdymq':
                    for t in time_list:
                        zdymq_t_list.append(int(t))
                elif p == 'bqymq':
                    for t in time_list:
                        bqymq_t_list.append(int(t))
            break
    return { "zdymq": zdymq_t_list, "bqymq":bqymq_t_list }

def get_Task_Q(bq_avail_t_list, zd_avail_t_list):
    '''
    elements int task_q is ['bqymq',t]
    '''
    #todo....
    return task_q

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
    cookie = ''
    while True:
        sleepToNext()
        iscorrect,opt = get_Config_File()
        user = opt["user"]
        name = opt["name"]
        password = opt["password"]
        mobile = opt["mobile"]
        depart = opt["depart"]
        if iscorrect:
            gtt = get_Today_Task(opt)
            zdymq_t_list = gtt["zdymq"]
            bqymq_t_list = gtt["bqymq"]
            Date = get_Today_Date()
            if len(bqymq_t_list) != 0 or len(zdymq_t_list) != 0:
                # bqymq or zdymq has task
                # login
                #todo login not success
                cookie = user_login(user, password)
                # check whether has available
                if len(bqymq_t_list) != 0:
                    bqymq_avail_t = get_Time_Avail(cookie, str_To_ContentID["bqymq"], bqymq_t_list)
                if len(zdymq_t_list) != 0:
                    zdymq_avail_t = get_Time_Avail(cookie, str_To_ContentID["zdymq"], zdymq_t_list)
                if len(bqymq_avail_t) != 0 or len(zdymq_avail_t) != 0:
                    task_q = get_Task_Q(bqymq_avail_t, zdymq_avail_t)
                    cur_task = task_q.get()
                    if_avail,book_data = check_Avail(cookie, cur_task, Date)
                    while True:
                        if if_avail:
                            book_res1 = book(cookie, book_data["resourcesID"], book_data["contentID"], Date, book_data["endTime"], book_data["beginTime"], name, mobile, depart)
                            if book_res1:
                                print("Book success")
                                # todo:send email
                                break
                        elif not task_q.empty()
                            cur_task = task_q.get()
                            if_avail,book_data = check_Avail(cookie, cur_task, Date)
                        else:
                            print("book failure")
                            break
        else:
            print "configure file is not correct"
if __name__ == '__main__':
    main()
    #get_config_file(furl = '/Users/wuzehui/Documents/bookbadmin.txt')
