# -*- coding: utf-8 -*
'''
new Env('wskey转换');
'''

import socket
import base64
import http.client
import json
import os
import sys
import logging
import time
import urllib.parse
import re

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
try:
    import requests
except Exception as e:
    logger.info(str(e) + "\n缺少requests模块, 请执行命令：pip3 install requests\n")
    sys.exit(1)
os.environ['no_proxy'] = '*'
requests.packages.urllib3.disable_warnings()
try:
    from notify import send
except:
    logger.info("无推送文件")

ver = 10114


# 登录青龙 返回值 token
def get_qltoken(username, password):
    logger.info("Token失效, 新登陆\n")
    url = "http://127.0.0.1:{0}/api/user/login".format(port)
    payload = {
        'username': username,
        'password': password
    }
    payload = json.dumps(payload)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    try:
        res = requests.post(url=url, headers=headers, data=payload)
        token = json.loads(res.text)["data"]['token']
    except:
        logger.info("青龙登录失败, 请检查面板状态!")
        te_xt = '青龙面板WSKEY转换登陆面板失败, 请检查面板状态.'
        try:
            send('WSKEY转换', te_xt)
        except:
            logger.info("通知发送失败")
        sys.exit(1)
    else:
        return token


# 返回值 Token
def ql_login():
    path = '/ql/config/auth.json'
    if os.path.isfile(path):
        with open(path, "r") as file:
            auth = file.read()
            file.close()
        auth = json.loads(auth)
        username = auth["username"]
        password = auth["password"]
        token = auth["token"]
        if token == '':
            return get_qltoken(username, password)
        else:
            url = "http://127.0.0.1:{0}/api/user".format(port)
            headers = {
                'Authorization': 'Bearer {0}'.format(token),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38'
            }
            res = requests.get(url=url, headers=headers)
            if res.status_code == 200:
                return token
            else:
                return get_qltoken(username, password)
    else:
        logger.info("没有发现auth文件, 你这是青龙吗???")
        sys.exit(0)


# 返回值 list[wskey]
def get_wskey():
    if "JD_WSCK" in os.environ:
        wskey_list = os.environ['JD_WSCK'].split('&')
        if len(wskey_list) > 0:
            return wskey_list
        else:
            logger.info("JD_WSCK变量未启用")
            sys.exit(1)
    else:
        logger.info("未添加JD_WSCK变量")
        sys.exit(0)


# 返回值 list[jd_cookie]
def get_ck():
    if "JD_COOKIE" in os.environ:
        ck_list = os.environ['JD_COOKIE'].split('&')
        if len(ck_list) > 0:
            return ck_list
        else:
            logger.info("JD_COOKIE变量未启用")
            sys.exit(1)
    else:
        logger.info("未添加JD_COOKIE变量")
        sys.exit(0)


# 返回值 bool
def check_ck(ck):
    searchObj = re.search(r'pt_pin=([^;\s]+)', ck, re.M|re.I)
    if searchObj:
        pin = searchObj.group(1)
    else:
        pin = ck.split(";")[1]
    if "QL_WSCK" in os.environ:
        logger.info("不检查账号有效性\n--------------------\n")
        return False
    elif "QL_WSCK_UPDATE_HOUR" in os.environ:
        if os.environ["QL_WSCK_UPDATE_HOUR"].isdigit():
            updateHour = int(os.environ["QL_WSCK_UPDATE_HOUR"])
        else:
            updateHour = 23
        searchObj = re.search(r'__time=([^;\s]+)', ck, re.M|re.I)
        if searchObj:
            updatedAt = float(searchObj.group(1))
        else:
            updatedAt = 0.0
            return_serch = serch_ck(pin)
            if return_serch[0]:
                updatedAt = time.mktime(time.strptime(return_serch[3], '%Y-%m-%d %H:%M:%S'))
        if time.time() - updatedAt >= (updateHour * 60 * 60) - (10 * 60):
            logger.info(str(pin) + ";已到期\n")
            return False
        else:
            logger.info(str(pin) + ";未到期\n")
            return True
    else:
        url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'
        headers = {
            'Cookie': ck,
            'Referer': 'https://home.m.jd.com/myJd/home.action',
            'user-agent': ua
        }
        try:
            res = requests.get(url=url, headers=headers, verify=False, timeout=10)
        except:
            # logger.info("JD接口错误, 切换第二接口")
            url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'
            headers = {
                'Cookie': ck,
                'user-agent': ua,
                'Referer': 'https://home.m.jd.com/myJd/home.action'
            }
            res = requests.get(url=url, headers=headers, verify=False, timeout=30)
            if res.status_code == 200:
                code = int(json.loads(res.text)['retcode'])
                if code == 0:
                    logger.info(str(pin) + ";状态正常\n")
                    return True
                else:
                    logger.info(str(pin) + ";状态失效\n")
                    return False
            else:
                logger.info("JD接口错误码: " + str(res.status_code))
                return False
        else:
            if res.status_code == 200:
                code = int(json.loads(res.text)['retcode'])
                if code == 0:
                    logger.info(str(pin) + ";状态正常\n")
                    return True
                else:
                    logger.info(str(pin) + ";状态失效\n")
                    return False
            else:
                logger.info("JD接口错误码: " + str(res.status_code))
                return False


# 返回值 bool jd_ck
def getToken(wskey):
    headers = {
        'cookie': wskey,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'charset': 'UTF-8',
        'accept-encoding': 'br,gzip,deflate',
        'user-agent': ua
    }
    params = {
        'functionId': 'genToken',
        'clientVersion': '10.2.2',
        'client': 'android',
        'uuid': uuid,
        'st': st,
        'sign': sign,
        'sv': sv
    }
    url = 'https://api.m.jd.com/client.action'
    data = 'body=%7B%22action%22%3A%22to%22%2C%22to%22%3A%22https%253A%252F%252Fplogin.m.jd.com%252Fcgi-bin%252Fm%252Fthirdapp_auth_page%253Ftoken%253DAAEAIEijIw6wxF2s3bNKF0bmGsI8xfw6hkQT6Ui2QVP7z1Xg%2526client_type%253Dandroid%2526appid%253D879%2526appup_type%253D1%22%7D&'
    try:
        res = requests.post(url=url, params=params, headers=headers, data=data, verify=False, timeout=10)
        res_json = json.loads(res.text)
        tokenKey = res_json['tokenKey']
        if tokenKey == 'xxx':
            logger.info("getToken返回了无效Token，可能是风控账户或IP被拉黑\n")
            logger.info(res.text)
            return False, null
    except:
        logger.info("WSKEY转换接口出错, 请稍后尝试, 脚本退出")
        sys.exit(1)
    else:
        return appjmp(wskey, tokenKey)


# 返回值 bool jd_ck
def appjmp(wskey, tokenKey):
    headers = {
        'User-Agent': ua,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    }
    params = {
        'tokenKey': tokenKey,
        'to': 'https://plogin.m.jd.com/cgi-bin/m/thirdapp_auth_page?token=AAEAIEijIw6wxF2s3bNKF0bmGsI8xfw6hkQT6Ui2QVP7z1Xg',
        'client_type': 'android',
        'appid': 879,
        'appup_type': 1,
    }
    url = 'https://un.m.jd.com/cgi-bin/app/appjmp'
    try:
        res = requests.get(url=url, headers=headers, params=params, verify=False, allow_redirects=False, timeout=20)
        res_set = res.cookies.get_dict()
        pt_key = 'pt_key=' + res_set['pt_key']
        pt_pin = 'pt_pin=' + res_set['pt_pin']
        jd_ck = str(pt_key) + '; ' + str(pt_pin) + '; __time=' + str(time.time())
        wskey = wskey.split(";")[0]
        if 'fake' in pt_key:
            logger.info(str(wskey) + ";WsKey状态失效\n")
            return False, jd_ck
        else:
            logger.info(str(wskey) + ";WsKey状态正常\n")
            return True, jd_ck
    except:
        logger.info("JD接口转换失败, 默认WsKey失效\n")
        wskey = "pt_" + str(wskey.split(";")[0])
        return False, wskey


# 返回值 svv, stt, suid, jign
def get_sign():
    url = str(base64.b64decode(url_t).decode()) + 'wskey'
    for i in range(3):
        try:
            headers = {
                "User-Agent": ua
            }
            res = requests.get(url=url, headers=headers, verify=False, timeout=20)
        except requests.exceptions.ConnectTimeout:
            logger.info("\n获取Sign超时, 正在重试!" + str(i))
            time.sleep(1)
            continue
        except requests.exceptions.ReadTimeout:
            logger.info("\n获取Sign超时, 正在重试!" + str(i))
            time.sleep(1)
            continue
        except Exception as err:
            logger.info(str(err) + "\n未知错误, 重试脚本!")
            continue
        else:
            try:
                sign_list = json.loads(res.text)
            except:
                logger.info("Sign Json错误")
                sys.exit(1)
            else:
                svv = sign_list['sv']
                stt = sign_list['st']
                suid = sign_list['uuid']
                jign = sign_list['sign']
                return svv, stt, suid, jign


# 返回值 None
def boom():
    ex = int(cloud_arg['code'])
    if ex != 200:
        logger.info("Check Failure")
        logger.info("--------------------\n")
        sys.exit(0)
    else:
        logger.info("Verification passed")
        logger.info("--------------------\n")


def update():
    up_ver = int(cloud_arg['update'])
    if ver >= up_ver:
        logger.info("当前脚本版本: " + str(ver))
        logger.info("--------------------\n")
    else:
        logger.info("当前脚本版本: " + str(ver) + "新版本: " + str(up_ver))
        logger.info("存在新版本, 请更新脚本后执行")
        logger.info("--------------------\n")
        text = '当前脚本版本: {0}新版本: {1}, 请更新脚本~!'.format(ver, up_ver)
        try:
            send('WSKEY转换', text)
        except:
            logger.info("通知发送失败")
        # sys.exit(0)


def ql_check(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect(('127.0.0.1', port))
    except:
        sock.close()
        return False
    else:
        sock.close()
        return True


# 返回值 bool, key, eid
def serch_ck_old(pin):
    if all('\u4e00' <= char <= '\u9fff' for char in pin):
        pin1 = urllib.parse.quote(pin)
        pin2 = pin1.replace('%', '%5C%25')
        logger.info(str(pin) + "-->" + str(pin1))
    else:
        pin2 = pin.replace('%', '%5C%25')
    # TMD 中文!
    # url = "http://127.0.0.1:5700/api/envs?searchValue={0}".format(pin)
    # res = json.loads(s.get(url, verify=False).text)
    conn = http.client.HTTPConnection("127.0.0.1", port)
    payload = ''
    headers = {
        'Authorization': 'Bearer ' + token
    }
    url = '/api/envs?searchValue={0}'.format(pin2)
    conn.request("GET", url, payload, headers)
    res = json.loads(conn.getresponse().read())
    if len(res['data']) == 0:
        logger.info(str(pin) + "检索失败\n")
        return False, 1
    elif len(res['data']) > 1:
        logger.info(str(pin) + "存在重复, 取第一条, 请删除多余变量\n")
        key = res['data'][0]['value']
        eid = res['data'][0]['_id']
        return True, key, eid
    else:
        logger.info(str(pin) + "检索成功\n")
        key = res['data'][0]['value']
        eid = res['data'][0]['_id']
        return True, key, eid


def serch_ck(pin):
    for i in range(len(envlist)):
        if pin in envlist[i]['value']:
            value = envlist[i]['value']
            id = envlist[i][ql_id]
            updatedAt = envlist[i]['updatedAt']
            logger.info(str(pin) + "检索成功\n")
            return True, value, id, updatedAt
        else:
            continue
    logger.info(str(pin) + "检索失败\n")
    return False, 1


def get_env():
    url = 'http://127.0.0.1:{0}/api/envs'.format(port)
    try:
        res = s.get(url)
    except:
        logger.info("\n青龙环境接口错误")
        sys.exit(1)
    else:
        data = json.loads(res.text)['data']
        return data


def get_version():
    url = 'http://127.0.0.1:{0}/api/system'.format(port)
    try:
        res = s.get(url)
        version = str(json.loads(res.text)['data']['version'])
    except:
        return 0
    else:
        logger.info("青龙面板版本: " + version)
        if version > '2.10.13':
            return 1
        else:
            return 0


def ql_update(e_id, n_ck):
    url = 'http://127.0.0.1:{0}/api/envs'.format(port)
    data = {
        "name": "JD_COOKIE",
        "value": n_ck,
        ql_id: e_id
    }
    data = json.dumps(data)
    res = json.loads(s.put(url=url, data=data).text)
    ql_enable(eid)


def ql_enable(e_id):
    url = 'http://127.0.0.1:{0}/api/envs/enable'.format(port)
    data = '["{0}"]'.format(e_id)
    res = json.loads(s.put(url=url, data=data).text)
    if res['code'] == 200:
        logger.info("\n账号启用\n--------------------\n")
        return True
    else:
        logger.info("\n账号启用失败\n--------------------\n")
        return False


def ql_disable(e_id):
    url = 'http://127.0.0.1:{0}/api/envs/disable'.format(port)
    data = '["{0}"]'.format(e_id)
    res = json.loads(s.put(url=url, data=data).text)
    if res['code'] == 200:
        logger.info("\n账号禁用成功\n--------------------\n")
        return True
    else:
        logger.info("\n账号禁用失败\n--------------------\n")
        return False


def ql_insert(i_ck):
    data = [{"value": i_ck, "name": "JD_COOKIE"}]
    data = json.dumps(data)
    url = 'http://127.0.0.1:{0}/api/envs'.format(port)
    s.post(url=url, data=data)
    logger.info("\n账号添加完成\n--------------------\n")


def cloud_info():
    url = str(base64.b64decode(url_t).decode()) + 'check_api'
    for i in range(3):
        try:
            headers = {
                "authorization": "Bearer Shizuku"
            }
            res = requests.get(url=url, verify=False, headers=headers, timeout=20).text
        except requests.exceptions.ConnectTimeout:
            logger.info("\n获取云端参数超时, 正在重试!" + str(i))
            time.sleep(1)
            continue
        except requests.exceptions.ReadTimeout:
            logger.info("\n获取云端参数超时, 正在重试!" + str(i))
            time.sleep(1)
            continue
        except Exception as err:
            logger.info(str(err) + "\n未知错误云端, 退出脚本!")
            sys.exit(1)
        else:
            try:
                c_info = json.loads(res)
            except:
                logger.info("云端参数解析失败")
                sys.exit(1)
            else:
                return c_info


def check_cloud():
    url_list = ['aHR0cDovLzQzLjEzNS45MC4yMy8=', 'aHR0cHM6Ly9zaGl6dWt1Lm1sLw==', 'aHR0cHM6Ly9jZi5zaGl6dWt1Lm1sLw==']
    for i in url_list:
        url = str(base64.b64decode(i).decode())
        try:
            res = requests.get(url=url, verify=False, timeout=10)
        except:
            continue
        else:
            info = ['Default', 'HTTPS', 'CloudFlare']
            logger.info(str(info[url_list.index(i)]) + " Server Check OK\n--------------------\n")
            return i
    logger.info("\n云端地址全部失效, 请检查网络!")
    try:
        send('WSKEY转换', '云端地址失效. 请检查网络.')
    except:
        logger.info("通知发送失败")
    sys.exit(1)


if __name__ == '__main__':
    logger.info("\n--------------------\n")
    if "QL_PORT" in os.environ:
        try:
            port = int(os.environ['QL_PORT'])
        except:
            logger.info("变量格式有问题...\n格式: export QL_PORT=\"端口号\"")
            sys.exit(1)
    else:
        port = 5700
    if not ql_check(port):
        logger.info(str(port) + "端口检查失败, 如果改过端口, 请在变量中声明端口 \n在config.sh中加入 export QL_PORT=\"端口号\"")
        logger.info("\n如果你很确定端口没错, 还是无法执行, 在GitHub给我发issus\n--------------------\n")
        sys.exit(1)
    else:
        logger.info(str(port) + "端口检查通过")
    # global cloud_arg
    token = ql_login()  # 获取青龙 token
    s = requests.session()
    s.headers.update({"authorization": "Bearer " + str(token)})
    s.headers.update({"Content-Type": "application/json;charset=UTF-8"})
    ql_id = ['_id', 'id'][get_version()]
    url_t = check_cloud()
    cloud_arg = cloud_info()
    update()
    boom()
    ua = cloud_arg['User-Agent']
    sv, st, uuid, sign = get_sign()
    wslist = get_wskey()
    envlist = get_env()
    for ws in wslist:
        wspin = ws.split(";")[0]
        if "pin" in wspin:
            wspin = "pt_" + wspin + ";"  # 封闭变量
            return_serch = serch_ck(wspin)  # 变量 pt_pin 搜索获取 key eid
            if return_serch[0]:  # bool: True 搜索到账号
                jck = str(return_serch[1])  # 拿到 JD_COOKIE
                if not check_ck(jck):  # bool: False 判定 JD_COOKIE 有效性
                    return_ws = getToken(ws)  # 使用 WSKEY 请求获取 JD_COOKIE bool jd_ck
                    if return_ws[0]:  # bool: True
                        nt_key = str(return_ws[1])
                        # logger.info("wskey转pt_key成功", nt_key)
                        logger.info("wskey转换成功")
                        eid = return_serch[2]  # 从 return_serch 拿到 eid
                        ql_update(eid, nt_key)  # 函数 ql_update 参数 eid JD_COOKIE
                    else:
                        # logger.info(str(wspin) + "wskey失效\n")
                        if "QL_WSCK_AUTO_DISABLE" in os.environ and os.environ["QL_WSCK_AUTO_DISABLE"] == "false":
                            text = "账号: {0} WsKey失效".format(wspin)
                        else:
                            eid = return_serch[2]
                            logger.info(str(wspin) + "账号禁用")
                            ql_disable(eid)
                            # dd = serch_ck(ws)[2]
                            # ql_disable(dd)
                            text = "账号: {0} WsKey失效, 已禁用Cookie".format(wspin)
                        try:
                            send('WsKey转换脚本', text)
                        except:
                            logger.info("通知发送失败")
                else:
                    logger.info(str(wspin) + "账号有效")
                    eid = return_serch[2]
                    ql_enable(eid)
                    logger.info("--------------------\n")
            else:
                logger.info("\n新wskey\n")
                return_ws = getToken(ws)  # 使用 WSKEY 请求获取 JD_COOKIE bool jd_ck
                if return_ws[0]:
                    nt_key = str(return_ws[1])
                    logger.info("wskey转换成功\n")
                    ql_insert(nt_key)
            logger.info("暂停3秒\n")
            time.sleep(3)
        else:
            logger.info("WSKEY格式错误\n--------------------\n")
    logger.info("执行完成\n--------------------")
    sys.exit(0)
