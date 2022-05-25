# -*- coding: utf-8 -*
'''
new Env('wskey转换');
'''
import socket  # 用于端口检测
import base64  # 用于编解码
import json  # 用于Json解析
import os  # 用于导入系统变量
import sys  # 实现 sys.exit
import logging  # 用于日志输出
import time  # 时间
import re  # 正则过滤
import hmac
import struct

WSKEY_MODE = 0
# 0 = Default / 1 = Debug!

if "WSKEY_DEBUG" in os.environ or WSKEY_MODE:  # 判断调试模式变量
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')  # 设置日志为 Debug等级输出
    logger = logging.getLogger(__name__)  # 主模块
    logger.debug("\nDEBUG模式开启!\n")  # 消息输出
else:  # 判断分支
    logging.basicConfig(level=logging.INFO, format='%(message)s')  # Info级日志
    logger = logging.getLogger(__name__)  # 主模块

try:  # 异常捕捉
    import requests  # 导入HTTP模块
except Exception as e:  # 异常捕捉
    logger.info(str(e) + "\n缺少requests模块, 请执行命令：pip3 install requests\n")  # 日志输出
    sys.exit(1)  # 退出脚本
os.environ['no_proxy'] = '*'  # 禁用代理
requests.packages.urllib3.disable_warnings()  # 抑制错误
try:  # 异常捕捉
    from notify import send  # 导入青龙消息通知模块
except Exception as err:  # 异常捕捉
    logger.debug(str(err))  # 调试日志输出
    logger.info("无推送文件")  # 标准日志输出

ver = 20524  # 版本号


# def ql_2fa():
#     ''' Demo
#     if "WSKEY_TOKEN" in os.environ:
#     url = 'http://127.0.0.1:{0}/api/user'.format(port)  # 设置 URL地址
#     try:  # 异常捕捉
#         res = s.get(url)  # HTTP请求 [GET] 使用 session
#     except Exception as err:  # 异常捕捉
#         logger.debug(str(err))  # 调试日志输出
#     else:  # 判断分支
#         if res.status_code == 200 and res.json()["code"] == 200:
#             twoFactorActivated = str(res.json()["data"]["twoFactorActivated"])
#             if twoFactorActivated == 'true':
#                 logger.info("青龙 2FA 已开启!")
#     url = 'http://127.0.0.1:{0}/api/envs?searchValue=WSKEY_Client'.format(port)  # 设置 URL地址
#     res = s.get(url)
#     if res.status_code == 200 and res.json()["code"] == 200:
#         data = res.json()["data"]
#         if len(data) == 0:
#             url = 'http://127.0.0.1:{0}/api/apps'
#             data = json.dumps({
#                 "name": "wskey",
#                 "scopes": ["crons", "envs", "configs", "scripts", "logs", "dependencies", "system"]
#             })
#             res = s.post(url, data=data)
#             if res.status_code == 200 and res.json()["code"] == 200:
#                 logger.info("OpenApi创建成功")
#                 client_id = res.json()["data"]["client_id"]
#                 client_secret = res.json()["data"]["client_secret"]
#                 wskey_value = 'client_id={0}&client_secret={1}'.format(client_id, client_secret)
#                 data = [{"value": wskey_value, "name": "WSKEY_Client", "remarks": "WSKEY_OpenApi请勿删除"}]
#                 data = json.dumps(data)  # Json格式化数据
#                 url = 'http://127.0.0.1:{0}/api/envs'.format(port)  # 设置 URL地址
#                 s.post(url=url, data=data)  # HTTP[POST]请求 使用session
#                 logger.info("\nWSKEY_Client变量添加完成\n--------------------\n")  # 标准日志输出
#     '''

def ttotp(key):
    key = base64.b32decode(key.upper() + '=' * ((8 - len(key)) % 8))
    counter = struct.pack('>Q', int(time.time() / 30))
    mac = hmac.new(key, counter, 'sha1').digest()
    offset = mac[-1] & 0x0f
    binary = struct.unpack('>L', mac[offset:offset + 4])[0] & 0x7fffffff
    return str(binary)[-6:].zfill(6)


def ql_send(text):
    if "WSKEY_SEND" in os.environ and os.environ["WSKEY_SEND"] == 'disable':
        return True
    else:
        try:  # 异常捕捉
            send('WSKEY转换', text)  # 消息发送
        except Exception as err:  # 异常捕捉
            logger.debug(str(err))  # Debug日志输出
            logger.info("通知发送失败")  # 标准日志输出


# 登录青龙 返回值 token
def get_qltoken(username, password, twoFactorSecret):  # 方法 用于获取青龙 Token
    logger.info("Token失效, 新登陆\n")  # 日志输出
    if twoFactorSecret:
        try:
            twoCode = ttotp(twoFactorSecret)
        except Exception as err:
            logger.debug(str(err))  # Debug日志输出
            logger.info("TOTP异常")
            sys.exit(1)
        url = ql_url + "api/user/login"  # 设置青龙地址 使用 format格式化自定义端口
        payload = json.dumps({
            'username': username,
            'password': password
        })  # HTTP请求载荷
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }  # HTTP请求头 设置为 Json格式
        try:  # 异常捕捉
            res = requests.post(url=url, headers=headers, data=payload)  # 使用 requests模块进行 HTTP POST请求
            if res.status_code == 200 and res.json()["code"] == 420:
                url = ql_url + 'api/user/two-factor/login'
                data = json.dumps({
                    "username": username,
                    "password": password,
                    "code": twoCode
                })
                res = requests.put(url=url, headers=headers, data=data)
                if res.status_code == 200 and res.json()["code"] == 200:
                    token = res.json()["data"]['token']  # 从 res.text 返回值中 取出 Token值
                    return token
                else:
                    logger.info("两步校验失败\n")  # 日志输出
                    sys.exit(1)
            elif res.status_code == 200 and res.json()["code"] == 200:
                token = res.json()["data"]['token']  # 从 res.text 返回值中 取出 Token值
                return token
        except Exception as err:
            logger.debug(str(err))  # Debug日志输出
            sys.exit(1)
    else:
        url = ql_url + 'api/user/login'
        payload = {
            'username': username,
            'password': password
        }  # HTTP请求载荷
        payload = json.dumps(payload)  # json格式化载荷
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }  # HTTP请求头 设置为 Json格式
        try:  # 异常捕捉
            res = requests.post(url=url, headers=headers, data=payload)  # 使用 requests模块进行 HTTP POST请求
            if res.status_code == 200 and res.json()["code"] == 200:
                token = res.json()["data"]['token']  # 从 res.text 返回值中 取出 Token值
                return token
            else:
                ql_send("青龙登录失败!")
                sys.exit(1)  # 脚本退出
        except Exception as err:
            logger.debug(str(err))  # Debug日志输出
            logger.info("使用旧版青龙登录接口")
            url = ql_url + 'api/login'  # 设置青龙地址 使用 format格式化自定义端口
            payload = {
                'username': username,
                'password': password
            }  # HTTP请求载荷
            payload = json.dumps(payload)  # json格式化载荷
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }  # HTTP请求头 设置为 Json格式
            try:  # 异常捕捉
                res = requests.post(url=url, headers=headers, data=payload)  # 使用 requests模块进行 HTTP POST请求
                token = json.loads(res.text)["data"]['token']  # 从 res.text 返回值中 取出 Token值
            except Exception as err:  # 异常捕捉
                logger.debug(str(err))  # Debug日志输出
                logger.info("青龙登录失败, 请检查面板状态!")  # 标准日志输出
                ql_send('青龙登陆失败, 请检查面板状态.')
                sys.exit(1)  # 脚本退出
            else:  # 无异常执行分支
                return token  # 返回 token值
        # else:  # 无异常执行分支
        #     return token  # 返回 token值


# 返回值 Token
def ql_login():  # 方法 青龙登录(获取Token 功能同上)
    path = '/ql/config/auth.json'  # 设置青龙 auth文件地址
    if not os.path.isfile(path):
        path = '/ql/data/config/auth.json'  # 尝试设置青龙 auth 新版文件地址
    if os.path.isfile(path):  # 进行文件真值判断
        with open(path, "r") as file:  # 上下文管理
            auth = file.read()  # 读取文件
            file.close()  # 关闭文件
        auth = json.loads(auth)  # 使用 json模块读取
        username = auth["username"]  # 提取 username
        password = auth["password"]  # 提取 password
        token = auth["token"]  # 提取 authkey
        try:
            twoFactorSecret = auth["twoFactorSecret"]
        except Exception as err:
            logger.debug(str(err))  # Debug日志输出
            twoFactorSecret = ''
        if token == '':  # 判断 Token是否为空
            return get_qltoken(username, password, twoFactorSecret)  # 调用方法 get_qltoken 传递 username & password
        else:  # 判断分支
            url = ql_url + 'api/user'  # 设置URL请求地址 使用 Format格式化端口
            headers = {
                'Authorization': 'Bearer {0}'.format(token),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38'
            }  # 设置用于 HTTP头
            res = requests.get(url=url, headers=headers)  # 调用 request模块发送 get请求
            if res.status_code == 200:  # 判断 HTTP返回状态码
                return token  # 有效 返回 token
            else:  # 判断分支
                return get_qltoken(username, password, twoFactorSecret)  # 调用方法 get_qltoken 传递 username & password
    else:  # 判断分支
        logger.info("没有发现auth文件, 你这是青龙吗???")  # 输出标准日志
        sys.exit(0)  # 脚本退出


# 返回值 list[wskey]
def get_wskey():  # 方法 获取 wskey值 [系统变量传递]
    if "JD_WSCK" in os.environ:  # 判断 JD_WSCK是否存在于环境变量
        wskey_list = os.environ['JD_WSCK'].split('&')  # 读取系统变量 以 & 分割变量
        if len(wskey_list) > 0:  # 判断 WSKEY 数量 大于 0 个
            return wskey_list  # 返回 WSKEY [LIST]
        else:  # 判断分支
            logger.info("JD_WSCK变量未启用")  # 标准日志输出
            sys.exit(1)  # 脚本退出
    else:  # 判断分支
        logger.info("未添加JD_WSCK变量")  # 标准日志输出
        sys.exit(0)  # 脚本退出


# 返回值 list[jd_cookie]
def get_ck():  # 方法 获取 JD_COOKIE值 [系统变量传递] <! 此方法未使用 !>
    if "JD_COOKIE" in os.environ:  # 判断 JD_COOKIE是否存在于环境变量
        ck_list = os.environ['JD_COOKIE'].split('&')  # 读取系统变量 以 & 分割变量
        if len(ck_list) > 0:  # 判断 WSKEY 数量 大于 0 个
            return ck_list  # 返回 JD_COOKIE [LIST]
        else:  # 判断分支
            logger.info("JD_COOKIE变量未启用")  # 标准日志输出
            sys.exit(1)  # 脚本退出
    else:  # 判断分支
        logger.info("未添加JD_COOKIE变量")  # 标准日志输出
        sys.exit(0)  # 脚本退出


# 返回值 bool
def check_ck(ck):  # 方法 检查 Cookie有效性 使用变量传递 单次调用
    searchObj = re.search(r'pt_pin=([^;\s]+)', ck, re.M | re.I)  # 正则检索 pt_pin
    if searchObj:  # 真值判断
        pin = searchObj.group(1)  # 取值
    else:  # 判断分支
        pin = ck.split(";")[1]  # 取值 使用 ; 分割
    if "WSKEY_UPDATE_HOUR" in os.environ:  # 判断 WSKEY_UPDATE_HOUR是否存在于环境变量
        updateHour = 23  # 更新间隔23小时
        if os.environ["WSKEY_UPDATE_HOUR"].isdigit():  # 检查是否为 DEC值
            updateHour = int(os.environ["WSKEY_UPDATE_HOUR"])  # 使用 int化数字
        nowTime = time.time()  # 获取时间戳 赋值
        updatedAt = 0.0  # 赋值
        searchObj = re.search(r'__time=([^;\s]+)', ck, re.M | re.I)  # 正则检索 [__time=]
        if searchObj:  # 真值判断
            updatedAt = float(searchObj.group(1))  # 取值 [float]类型
        if nowTime - updatedAt >= (updateHour * 60 * 60) - (10 * 60):  # 判断时间操作
            logger.info(str(pin) + ";即将到期或已过期\n")  # 标准日志输出
            return False  # 返回 Bool类型 False
        else:  # 判断分支
            remainingTime = (updateHour * 60 * 60) - (nowTime - updatedAt)  # 时间运算操作
            hour = int(remainingTime / 60 / 60)  # 时间运算操作 [int]
            minute = int((remainingTime % 3600) / 60)  # 时间运算操作 [int]
            logger.info(str(pin) + ";未到期，{0}时{1}分后更新\n".format(hour, minute))  # 标准日志输出
            return True  # 返回 Bool类型 True
    elif "WSKEY_DISCHECK" in os.environ:  # 判断分支 WSKEY_DISCHECK 是否存在于系统变量
        logger.info("不检查账号有效性\n--------------------\n")  # 标准日志输出
        return False  # 返回 Bool类型 False
    else:  # 判断分支
        url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'  # 设置JD_API接口地址
        headers = {
            'Cookie': ck,
            'Referer': 'https://home.m.jd.com/myJd/home.action',
            'user-agent': ua
        }  # 设置 HTTP头
        try:  # 异常捕捉
            res = requests.get(url=url, headers=headers, verify=False, timeout=10)  # 进行 HTTP请求[GET] 超时 10秒
        except Exception as err:  # 异常捕捉
            logger.debug(str(err))  # 调试日志输出
            logger.info("JD接口错误 请重试或者更换IP")  # 标准日志输出
            return False  # 返回 Bool类型 False
        else:  # 判断分支
            if res.status_code == 200:  # 判断 JD_API 接口是否为 200 [HTTP_OK]
                code = int(json.loads(res.text)['retcode'])  # 使用 Json模块对返回数据取值 int([retcode])
                if code == 0:  # 判断 code值
                    logger.info(str(pin) + ";状态正常\n")  # 标准日志输出
                    return True  # 返回 Bool类型 True
                else:  # 判断分支
                    logger.info(str(pin) + ";状态失效\n")
                    return False  # 返回 Bool类型 False
            else:  # 判断分支
                logger.info("JD接口错误码: " + str(res.status_code))  # 标注日志输出
                return False  # 返回 Bool类型 False


# 返回值 bool jd_ck
def getToken(wskey):  # 方法 获取 Wskey转换使用的 Token 由 JD_API 返回 这里传递 wskey
    try:  # 异常捕捉
        url = str(base64.b64decode(url_t).decode()) + 'api/genToken'  # 设置云端服务器地址 路由为 genToken
        header = {"User-Agent": ua}  # 设置 HTTP头
        params = requests.get(url=url, headers=header, verify=False, timeout=20).json()  # 设置 HTTP请求参数 超时 20秒 Json解析
    except Exception as err:  # 异常捕捉
        logger.info("Params参数获取失败")  # 标准日志输出
        logger.debug(str(err))  # 调试日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    headers = {
        'cookie': wskey,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'charset': 'UTF-8',
        'accept-encoding': 'br,gzip,deflate',
        'user-agent': ua
    }  # 设置 HTTP头
    url = 'https://api.m.jd.com/client.action'  # 设置 URL地址
    data = 'body=%7B%22to%22%3A%22https%253a%252f%252fplogin.m.jd.com%252fjd-mlogin%252fstatic%252fhtml%252fappjmp_blank.html%22%7D&'  # 设置 POST 载荷
    try:  # 异常捕捉
        res = requests.post(url=url, params=params, headers=headers, data=data, verify=False,
                            timeout=10)  # HTTP请求 [POST] 超时 10秒
        res_json = json.loads(res.text)  # Json模块 取值
        tokenKey = res_json['tokenKey']  # 取出TokenKey
    except Exception as err:  # 异常捕捉
        logger.info("JD_WSKEY接口抛出错误 尝试重试 更换IP")  # 标准日志输出
        logger.info(str(err))  # 标注日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    else:  # 判断分支
        return appjmp(wskey, tokenKey)  # 传递 wskey, Tokenkey 执行方法 [appjmp]


# 返回值 bool jd_ck
def appjmp(wskey, tokenKey):  # 方法 传递 wskey & tokenKey
    wskey = "pt_" + str(wskey.split(";")[0])  # 变量组合 使用 ; 分割变量 拼接 pt_
    if tokenKey == 'xxx':  # 判断 tokenKey返回值
        logger.info(str(wskey) + ";疑似IP风控等问题 默认为失效\n--------------------\n")  # 标准日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    headers = {
        'User-Agent': ua,
        'accept': 'accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'x-requested-with': 'com.jingdong.app.mall'
    }  # 设置 HTTP头
    params = {
        'tokenKey': tokenKey,
        'to': 'https://plogin.m.jd.com/jd-mlogin/static/html/appjmp_blank.html'
    }  # 设置 HTTP_URL 参数
    url = 'https://un.m.jd.com/cgi-bin/app/appjmp'  # 设置 URL地址
    try:  # 异常捕捉
        res = requests.get(url=url, headers=headers, params=params, verify=False, allow_redirects=False,
                           timeout=20)  # HTTP请求 [GET] 阻止跳转 超时 20秒
    except Exception as err:  # 异常捕捉
        logger.info("JD_appjmp 接口错误 请重试或者更换IP\n")  # 标准日志输出
        logger.info(str(err))  # 标准日志输出
        return False, wskey  # 返回 -> False[Bool], Wskey
    else:  # 判断分支
        try:  # 异常捕捉
            res_set = res.cookies.get_dict()  # 从res cookie取出
            pt_key = 'pt_key=' + res_set['pt_key']  # 取值 [pt_key]
            pt_pin = 'pt_pin=' + res_set['pt_pin']  # 取值 [pt_pin]
            if "WSKEY_UPDATE_HOUR" in os.environ:  # 判断是否在系统变量中启用 WSKEY_UPDATE_HOUR
                jd_ck = str(pt_key) + ';' + str(pt_pin) + ';__time=' + str(time.time()) + ';'  # 拼接变量
            else:  # 判断分支
                jd_ck = str(pt_key) + ';' + str(pt_pin) + ';'  # 拼接变量
        except Exception as err:  # 异常捕捉
            logger.info("JD_appjmp提取Cookie错误 请重试或者更换IP\n")  # 标准日志输出
            logger.info(str(err))  # 标准日志输出
            return False, wskey  # 返回 -> False[Bool], Wskey
        else:  # 判断分支
            if 'fake' in pt_key:  # 判断 pt_key中 是否存在fake
                logger.info(str(wskey) + ";WsKey状态失效\n")  # 标准日志输出
                return False, wskey  # 返回 -> False[Bool], Wskey
            else:  # 判断分支
                logger.info(str(wskey) + ";WsKey状态正常\n")  # 标准日志输出
                return True, jd_ck  # 返回 -> True[Bool], jd_ck


def update():  # 方法 脚本更新模块
    up_ver = int(cloud_arg['update'])  # 云端参数取值 [int]
    if ver >= up_ver:  # 判断版本号大小
        logger.info("当前脚本版本: " + str(ver))  # 标准日志输出
        logger.info("--------------------\n")  # 标准日志输出
    else:  # 判断分支
        logger.info("当前脚本版本: " + str(ver) + "新版本: " + str(up_ver))  # 标准日志输出
        logger.info("存在新版本, 请更新脚本后执行")  # 标准日志输出
        logger.info("--------------------\n")  # 标准日志输出
        text = '当前脚本版本: {0}新版本: {1}, 请更新脚本~!'.format(ver, up_ver)  # 设置发送内容
        ql_send(text)
        # sys.exit(0)  # 退出脚本 [未启用]


def ql_check(host, port):  # 方法 检查青龙端口
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Socket模块初始化
    sock.settimeout(2)  # 设置端口超时
    try:  # 异常捕捉
        sock.connect((host, port))  # 请求端口
    except Exception as err:  # 捕捉异常
        logger.debug(str(err))  # 调试日志输出
        sock.close()  # 端口关闭
        return False  # 返回 -> False[Bool]
    else:  # 分支判断
        sock.close()  # 关闭端口
        return True  # 返回 -> True[Bool]


def serch_ck(pin):  # 方法 搜索 Pin
    for i in range(len(envlist)):  # For循环 变量[envlist]的数量
        if "name" not in envlist[i] or envlist[i]["name"] != "JD_COOKIE":  # 判断 envlist内容
            continue  # 继续循环
        if pin in envlist[i]['value']:  # 判断envlist取值['value']
            value = envlist[i]['value']  # 取值['value']
            id = envlist[i][ql_id]  # 取值 [ql_id](变量)
            logger.info(str(pin) + "检索成功\n")  # 标准日志输出
            return True, value, id  # 返回 -> True[Bool], value, id
        else:  # 判断分支
            continue  # 继续循环
    logger.info(str(pin) + "检索失败\n")  # 标准日志输出
    return False, 1  # 返回 -> False[Bool], 1


def get_env():  # 方法 读取变量
    url = ql_url + 'api/envs'
    try:  # 异常捕捉
        res = s.get(url)  # HTTP请求 [GET] 使用 session
    except Exception as err:  # 异常捕捉
        logger.debug(str(err))  # 调试日志输出
        logger.info("\n青龙环境接口错误")  # 标准日志输出
        sys.exit(1)  # 脚本退出
    else:  # 判断分支
        data = json.loads(res.text)['data']  # 使用Json模块提取值[data]
        return data  # 返回 -> data


def check_id():  # 方法 兼容青龙老版本与新版本 id & _id的问题
    url = ql_url + 'api/envs'
    try:  # 异常捕捉
        res = s.get(url).json()  # HTTP[GET] 请求 使用 session
    except Exception as err:  # 异常捕捉
        logger.debug(str(err))  # 调试日志输出
        logger.info("\n青龙环境接口错误")  # 标准日志输出
        sys.exit(1)  # 脚本退出
    else:  # 判断分支
        if '_id' in res['data'][0]:  # 判断 [_id]
            logger.info("使用 _id 键值")  # 标准日志输出
            return '_id'  # 返回 -> '_id'
        else:  # 判断分支
            logger.info("使用 id 键值")  # 标准日志输出
            return 'id'  # 返回 -> 'id'


def ql_update(e_id, n_ck):  # 方法 青龙更新变量 传递 id cookie
    url = ql_url + 'api/envs'
    data = {
        "name": "JD_COOKIE",
        "value": n_ck,
        ql_id: e_id
    }  # 设置 HTTP POST 载荷
    data = json.dumps(data)  # json模块格式化
    s.put(url=url, data=data)  # HTTP [PUT] 请求 使用 session
    ql_enable(eid)  # 调用方法 ql_enable 传递 eid


def ql_enable(e_id):  # 方法 青龙变量启用 传递值 eid
    url = ql_url + 'api/envs/enable'
    data = '["{0}"]'.format(e_id)  # 格式化 POST 载荷
    res = json.loads(s.put(url=url, data=data).text)  # json模块读取 HTTP[PUT] 的返回值
    if res['code'] == 200:  # 判断返回值为 200
        logger.info("\n账号启用\n--------------------\n")  # 标准日志输出
        return True  # 返回 ->True
    else:  # 判断分支
        logger.info("\n账号启用失败\n--------------------\n")  # 标准日志输出
        return False  # 返回 -> Fasle


def ql_disable(e_id):  # 方法 青龙变量禁用 传递 eid
    url = ql_url + 'api/envs/disable'
    data = '["{0}"]'.format(e_id)  # 格式化 POST 载荷
    res = json.loads(s.put(url=url, data=data).text)  # json模块读取 HTTP[PUT] 的返回值
    if res['code'] == 200:  # 判断返回值为 200
        logger.info("\n账号禁用成功\n--------------------\n")  # 标准日志输出
        return True  # 返回 ->True
    else:  # 判断分支
        logger.info("\n账号禁用失败\n--------------------\n")  # 标准日志输出
        return False  # 返回 -> Fasle


def ql_insert(i_ck):  # 方法 插入新变量
    data = [{"value": i_ck, "name": "JD_COOKIE"}]  # POST数据载荷组合
    data = json.dumps(data)  # Json格式化数据
    url = ql_url + 'api/envs'
    s.post(url=url, data=data)  # HTTP[POST]请求 使用session
    logger.info("\n账号添加完成\n--------------------\n")  # 标准日志输出


def cloud_info():  # 方法 云端信息
    url = str(base64.b64decode(url_t).decode()) + 'api/check_api'  # 设置 URL地址 路由 [check_api]
    for i in range(3):  # For循环 3次
        try:  # 异常捕捉
            headers = {"authorization": "Bearer Shizuku"}  # 设置 HTTP头
            res = requests.get(url=url, verify=False, headers=headers, timeout=20).text  # HTTP[GET] 请求 超时 20秒
        except requests.exceptions.ConnectTimeout:  # 异常捕捉
            logger.info("\n获取云端参数超时, 正在重试!" + str(i))  # 标准日志输出
            time.sleep(1)  # 休眠 1秒
            continue  # 循环继续
        except requests.exceptions.ReadTimeout:  # 异常捕捉
            logger.info("\n获取云端参数超时, 正在重试!" + str(i))  # 标准日志输出
            time.sleep(1)  # 休眠 1秒
            continue  # 循环继续
        except Exception as err:  # 异常捕捉
            logger.info("\n未知错误云端, 退出脚本!")  # 标准日志输出
            logger.debug(str(err))  # 调试日志输出
            sys.exit(1)  # 脚本退出
        else:  # 分支判断
            try:  # 异常捕捉
                c_info = json.loads(res)  # json读取参数
            except Exception as err:  # 异常捕捉
                logger.info("云端参数解析失败")  # 标准日志输出
                logger.debug(str(err))  # 调试日志输出
                sys.exit(1)  # 脚本退出
            else:  # 分支判断
                return c_info  # 返回 -> c_info


def check_cloud():  # 方法 云端地址检查
    url_list = ['aHR0cDovL2FwaS5tb21vZS5tbC8=', 'aHR0cHM6Ly9hcGkubW9tb2UubWwv',
                'aHR0cHM6Ly9hcGkuaWxpeWEuY2Yv']  # URL list Encode
    for i in url_list:  # for循环 url_list
        url = str(base64.b64decode(i).decode())  # 设置 url地址 [str]
        try:  # 异常捕捉
            requests.get(url=url, verify=False, timeout=10)  # HTTP[GET]请求 超时 10秒
        except Exception as err:  # 异常捕捉
            logger.debug(str(err))  # 调试日志输出
            continue  # 循环继续
        else:  # 分支判断
            info = ['HTTP', 'HTTPS', 'CloudFlare']  # 输出信息[List]
            logger.info(str(info[url_list.index(i)]) + " Server Check OK\n--------------------\n")  # 标准日志输出
            return i  # 返回 ->i
    logger.info("\n云端地址全部失效, 请检查网络!")  # 标准日志输出
    ql_send('云端地址失效. 请联系作者或者检查网络.')  # 推送消息
    sys.exit(1)  # 脚本退出

def get_port():  # 方法 获取青龙端口
    logger.info("\n--------------------\n")  # 标准日志输出
    if "QL_PORT" in os.environ:  # 判断 系统变量是否存在[QL_PORT]
        try:  # 异常捕捉
            port = int(os.environ['QL_PORT'])  # 取值 [int]
        except Exception as err:  # 异常捕捉
            logger.debug(str(err))  # 调试日志输出
            logger.info("变量格式有问题...\n格式: export QL_PORT=\"端口号\"")  # 标准日志输出
            logger.info("使用默认端口5700")  # 标准日志输出
            return 5700  # 返回端口 5700
    else:  # 判断分支
        port = 5700  # 默认5700端口
    return port  # 返回->port

def get_host():  # 方法 获取青龙host
    logger.info("\n--------------------\n")  # 标准日志输出
    if "QL_HOST" in os.environ:  # 判断 系统变量是否存在[QL_HOST]
        try:  # 异常捕捉
            host = str(os.environ['QL_HOST'])  # 取值 [int]
        except Exception as err:  # 异常捕捉
            logger.debug(str(err))  # 调试日志输出
            logger.info("变量格式有问题...\n格式: export QL_HOST=\"HOST\"")  # 标准日志输出
            logger.info("使用默认host 127.0.0.1")  # 标准日志输出
            return "127.0.0.1"  # 返回host 127.0.0.1
    else:  # 判断分支
        host = "127.0.0.1"  # 默认127.0.0.1
    return host  # 返回->host

def get_ql_url():  # 方法 获取青龙地址
    logger.info("\n--------------------\n")  # 标准日志输出
    port = get_port() # 调用方法 [get_port]  并赋值 [port]
    host = get_host() # 调用方法 [get_host]  并赋值 [host]
    ql_url = 'http://{0}:{1}/'.format(host, port)
    if not ql_check(host, port):  # 调用方法 [ql_check] 传递 [host, port]
        logger.info(str(ql_url) + "地址检查失败, 如果改过端口, 请在变量中声明端口 \n在config.sh中加入 export QL_PORT=\"端口号\" \n如果青龙不在本机, 请在变量中声明host \n在config.sh中加入 export QL_HOST=\"目标青龙所在IP\"")  # 标准日志输出
        logger.info("\n如果你很确定端口没错, 还是无法执行, 在GitHub给我发issus\n--------------------\n")  # 标准日志输出
        sys.exit(1)  # 脚本退出
    else:  # 判断分支
        logger.info(str(ql_url) + "地址检查通过")  # 标准日志输出
        return ql_url  # 返回->ql_url    

if __name__ == '__main__':  # Python主函数执行入口
    ql_url = get_ql_url（） # 调用方法 [get_ql_url]  并赋值 [ql_url]
    token = ql_login()  # 调用方法 [ql_login]  并赋值 [token]
    s = requests.session()  # 设置 request session方法
    s.headers.update({"authorization": "Bearer " + str(token)})  # 增加 HTTP头认证
    s.headers.update({"Content-Type": "application/json;charset=UTF-8"})  # 增加 HTTP头 json 类型
    ql_id = check_id()  # 调用方法 [check_id] 并赋值 [ql_id]
    url_t = check_cloud()  # 调用方法 [check_cloud] 并赋值 [url_t]
    cloud_arg = cloud_info()  # 调用方法 [cloud_info] 并赋值 [cloud_arg]
    update()  # 调用方法 [update]
    ua = cloud_arg['User-Agent']  # 设置全局变量 UA
    wslist = get_wskey()  # 调用方法 [get_wskey] 并赋值 [wslist]
    envlist = get_env()  # 调用方法 [get_env] 并赋值 [envlist]
    if "WSKEY_SLEEP" in os.environ and str(os.environ["WSKEY_SLEEP"]).isdigit():  # 判断变量[WSKEY_SLEEP]是否为数字类型
        sleepTime = int(os.environ["WSKEY_SLEEP"])  # 获取变量 [int]
    else:  # 判断分支
        sleepTime = 10  # 默认休眠时间 10秒
    for ws in wslist:  # wslist变量 for循环  [wslist -> ws]
        wspin = ws.split(";")[0]  # 变量分割 ;
        if "pin" in wspin:  # 判断 pin 是否存在于 [wspin]
            wspin = "pt_" + wspin + ";"  # 封闭变量
            return_serch = serch_ck(wspin)  # 变量 pt_pin 搜索获取 key eid
            if return_serch[0]:  # bool: True 搜索到账号
                jck = str(return_serch[1])  # 拿到 JD_COOKIE
                if not check_ck(jck):  # bool: False 判定 JD_COOKIE 有效性
                    tryCount = 1  # 重试次数 1次
                    if "WSKEY_TRY_COUNT" in os.environ:  # 判断 [WSKEY_TRY_COUNT] 是否存在于系统变量
                        if os.environ["WSKEY_TRY_COUNT"].isdigit():  # 判断 [WSKEY_TRY_COUNT] 是否为数字
                            tryCount = int(os.environ["WSKEY_TRY_COUNT"])  # 设置 [tryCount] int
                    for count in range(tryCount):  # for循环 [tryCount]
                        count += 1  # 自增
                        return_ws = getToken(ws)  # 使用 WSKEY 请求获取 JD_COOKIE bool jd_ck
                        if return_ws[0]:  # 判断 [return_ws]返回值 Bool类型
                            break  # 中断循环
                        if count < tryCount:  # 判断循环次
                            logger.info("{0} 秒后重试，剩余次数：{1}\n".format(sleepTime, tryCount - count))  # 标准日志输出
                            time.sleep(sleepTime)  # 脚本休眠 使用变量 [sleepTime]
                    if return_ws[0]:  # 判断 [return_ws]返回值 Bool类型
                        nt_key = str(return_ws[1])  # 从 return_ws[1] 取出 -> nt_key
                        # logger.info("wskey转pt_key成功", nt_key)  # 标准日志输出 [未启用]
                        logger.info("wskey转换成功")  # 标准日志输出
                        eid = return_serch[2]  # 从 return_serch 拿到 eid
                        ql_update(eid, nt_key)  # 函数 ql_update 参数 eid JD_COOKIE
                    else:  # 判断分支
                        if "WSKEY_AUTO_DISABLE" in os.environ:  # 从系统变量中获取 WSKEY_AUTO_DISABLE
                            logger.info(str(wspin) + "账号失效")  # 标准日志输出
                            text = "账号: {0} WsKey疑似失效".format(wspin)  # 设置推送内容
                        else:  # 判断分支
                            eid = return_serch[2]  # 读取 return_serch[2] -> eid
                            logger.info(str(wspin) + "账号禁用")  # 标准日志输出
                            ql_disable(eid)  # 执行方法[ql_disable] 传递 eid
                            text = "账号: {0} WsKey疑似失效, 已禁用Cookie".format(wspin)  # 设置推送内容
                            ql_send(text)
                else:  # 判断分支
                    logger.info(str(wspin) + "账号有效")  # 标准日志输出
                    eid = return_serch[2]  # 读取 return_serch[2] -> eid
                    ql_enable(eid)  # 执行方法[ql_enable] 传递 eid
                    logger.info("--------------------\n")  # 标准日志输出
            else:  # 判断分支
                logger.info("\n新wskey\n")  # 标准日志分支
                return_ws = getToken(ws)  # 使用 WSKEY 请求获取 JD_COOKIE bool jd_ck
                if return_ws[0]:  # 判断 (return_ws[0]) 类型: [Bool]
                    nt_key = str(return_ws[1])  # return_ws[1] -> nt_key
                    logger.info("wskey转换成功\n")  # 标准日志输出
                    ql_insert(nt_key)  # 调用方法 [ql_insert]
            logger.info("暂停{0}秒\n".format(sleepTime))  # 标准日志输出
            time.sleep(sleepTime)  # 脚本休眠
        else:  # 判断分支
            logger.info("WSKEY格式错误\n--------------------\n")  # 标准日志输出
    logger.info("执行完成\n--------------------")  # 标准日志输出
    sys.exit(0)  # 脚本退出
    # Enjoy
