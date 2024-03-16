#!/usr/bin/env python"
# coding: utf-8
# By Threezh1
# https://threezh1.github.io/

import requests, argparse, sys, re
from requests.packages import urllib3
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor


def random_ip():
    # 这里通过传入不固定的种子数来取得随机时间
    time_clock = int(time.time() % 10000)
    # 传入时间搓生成的种子
    random.seed(time_clock)
    ip = [str((random.randint(1, 255))) for _ in range(4)]
    return '.'.join(ip)


def parse_args():
    '''
    设置对应的命令行参数配置
    :return: 返回接受到的命令行参数数据
    '''

    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython ' + sys.argv[0] + " -u http://www.baidu.com")
    parser.add_argument("-u", "--url", help="网站的url地址")
    parser.add_argument("-c", "--cookie", help="可以选择带入网站的cookie")
    parser.add_argument("-f", "--file", help="文件包含url或js")
    parser.add_argument("-ou", "--outputurl", help="Output file name. ")
    parser.add_argument("-os", "--outputsubdomain", help="Output file name. ")
    parser.add_argument("-j", "--js", help="找js文件", action="store_true")
    parser.add_argument("-d", "--deep", help="深度查找", action="store_true")
    return parser.parse_args()


# Regular expression comes from https://github.com/GerbenJavado/LinkFinder
def extract_URL(JS):
    '''
    清洗js返回js列表
    :param JS: 传入js
    :return:返回js列表
    '''
    pattern_raw = r"""
	  (?:"|')                               # 开始换行符
	  (
	    ((?:[a-zA-Z]{1,10}://|//)           # 匹配方案[a-Z]*1-10或//
	    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
	    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
	    |
	    ((?:/|\.\./|\./)                    # Start with /,../,./
	    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
	    [^"'><,;|()]{1,})                   # Rest of the characters can't be
	    |
	    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
	    [a-zA-Z0-9_\-/]{1,}                 # Resource name
	    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
	    (?:[\?|/][^"|']{0,}|))              # ? mark with parameters
	    |
	    ([a-zA-Z0-9_\-]{1,}                 # filename
	    \.(?:php|asp|aspx|jsp|json|
	         action|html|js|txt|xml)             # . + extension
	    (?:\?[^"|']{0,}|))                  # ? mark with parameters
	  )
	  (?:"|')                               # End newline delimiter
	"""
    # 进行正则匹配
    pattern = re.compile(pattern_raw, re.VERBOSE)
    # 返回清洗的js
    result = re.finditer(pattern, str(JS))
    if result == None:
        return None
    js_url = []
    return [match.group().strip('"').strip("'") for match in result
            if match.group() not in js_url]


def Extract_html(URL):
    '''
    获取页面源代码
    :param URL: 输入当前需要爬取的目标网页
    :return: 返回页面的源代码
    '''
    # 这里魔改了随机ip以及随机的请求头
    ip = random_ip()
    header = {
        "User-Agent": UserAgent().random,
        "Cookie": args.cookie, 'X-Forwarded-For': ip, 'X-Forwarded': ip,
        'Forwarded-For': ip, 'Forwarded': ip,
        'X-Requested-With': ip, 'X-Forwarded-Proto': ip,
        'X-Forwarded-Host': ip, 'X-remote-IP': ip,
        'X-remote-addr': ip, 'True-Client-IP': ip,
        'X-Client-IP': ip, 'Client-IP': ip,
        'X-Real-IP': ip, 'Ali-CDN-Real-IP': ip,
        'Cdn-Src-Ip': ip, 'Cdn-Real-Ip': ip,
        'CF-Connecting-IP': ip, 'X-Cluster-Client-IP': ip,
        'WL-Proxy-Client-IP': ip, 'Proxy-Client-IP': ip,
        'Fastly-Client-Ip': ip, 'True-Client-Ip': ip,
        'X-Originating-IP': ip, 'X-Host': ip,
        'X-Custom-IP-Authorization': ip
    }
    # 进行爬取的尝试，如果成功返回源代码
    try:
        raw = requests.get(URL, headers=header, timeout=3, verify=False)
        raw = raw.content.decode("utf-8", "ignore")
        return raw
    except:
        return None


def process_url(URL, re_URL):
    '''
    进行url 的处理
    :param URL:  传入目标网址
    :param re_URL: 需要替换的url
    :return: 返回处理号后的url
    '''
    # 这个是js中的伪协议
    black_url = ["javascript:"]  # Add some keyword for filter url.

    URL_raw = urlparse(URL)
    ab_URL = URL_raw.netloc
    host_URL = URL_raw.scheme
    if re_URL[0:2] == "//":
        result = host_URL + ":" + re_URL
    elif re_URL[0:4] == "http":
        result = re_URL
    elif re_URL[0:2] != "//" and re_URL not in black_url:
        if re_URL[0:1] == "/":
            result = host_URL + "://" + ab_URL + re_URL
        else:
            if re_URL[0:1] == ".":
                if re_URL[0:2] == "..":
                    result = host_URL + "://" + ab_URL + re_URL[2:]
                else:
                    result = host_URL + "://" + ab_URL + re_URL[1:]
            else:
                result = host_URL + "://" + ab_URL + "/" + re_URL
    else:
        result = URL
    return result


def find_last(string, str):
    positions = []
    last_position = -1
    while True:
        position = string.find(str, last_position + 1)
        if position == -1: break
        last_position = position
        positions.append(position)
    return positions


def find_by_url(url, js=False):
    # 如果不是js链接
    if js == False:
        try:
            print("url链接:" + url)
        except:
            print("请指定一个URL，比如 https://www.baidu.com")
        # 获取传入url的页面源代码
        html_raw = Extract_html(url)
        if html_raw == None:
            print("无法访问当前链接： " + url)
            return None
        # print(html_raw)
        # 清洗里面的js
        html = BeautifulSoup(html_raw, "html.parser")
        html_scripts = html.findAll("script")
        script_array = {}
        script_temp = ""
        # 循环找到的 script标签
        for html_script in html_scripts:
            # 获取js的scr链接
            script_src = html_script.get("src")
            # 如果为空。
            if script_src == None:
                script_temp += html_script.get_text() + "\n"
            else:
                # 返回处理后的url
                purl = process_url(url, script_src)
                script_array[purl] = Extract_html(purl)
        script_array[url] = script_temp
        # 创建容器，js存储的容器
        allurls = []
        for script in script_array:
            # print(script)
            # 获取到清洗后的js列表
            temp_urls = extract_URL(script_array[script])
            # 如果长度为0跳过
            if len(temp_urls) == 0: continue
            for temp_url in temp_urls:
                allurls.append(process_url(script, temp_url))
        # 创建容器
        result = []
        for singerurl in allurls:
            url_raw = urlparse(url)
            domain = url_raw.netloc
            positions = find_last(domain, ".")
            miandomain = domain
            if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
            # print(miandomain)
            suburl = urlparse(singerurl)
            subdomain = suburl.netloc
            # print(singerurl)
            if miandomain in subdomain or subdomain.strip() == "":
                if singerurl.strip() not in result:
                    result.append(singerurl)
        # 返回结果
        return result
    return sorted(set(extract_URL(Extract_html(url)))) or None


def find_subdomain(urls, mainurl):
    url_raw = urlparse(mainurl)
    domain = url_raw.netloc
    miandomain = domain
    positions = find_last(domain, ".")
    if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
    subdomains = []
    for url in urls:
        suburl = urlparse(url)
        subdomain = suburl.netloc
        # print(subdomain)
        if subdomain.strip() == "": continue
        if miandomain in subdomain:
            if subdomain not in subdomains:
                subdomains.append(subdomain)
    return subdomains


def req_code(url, type='html'):
    '''
    为自己的魔改
    对网站进行请求操作。并且返回响应码
    :param url:  传入需要进行请求的网址
    :return: 返回响应码和url
    '''
    ip = random_ip()
    header = {
        "User-Agent": UserAgent().random,
        "Cookie": args.cookie, 'X-Forwarded-For': ip, 'X-Forwarded': ip,
        'Forwarded-For': ip, 'Forwarded': ip,
        'X-Requested-With': ip, 'X-Forwarded-Proto': ip,
        'X-Forwarded-Host': ip, 'X-remote-IP': ip,
        'X-remote-addr': ip, 'True-Client-IP': ip,
        'X-Client-IP': ip, 'Client-IP': ip,
        'X-Real-IP': ip, 'Ali-CDN-Real-IP': ip,
        'Cdn-Src-Ip': ip, 'Cdn-Real-Ip': ip,
        'CF-Connecting-IP': ip, 'X-Cluster-Client-IP': ip,
        'WL-Proxy-Client-IP': ip, 'Proxy-Client-IP': ip,
        'Fastly-Client-Ip': ip, 'True-Client-Ip': ip,
        'X-Originating-IP': ip, 'X-Host': ip,
        'X-Custom-IP-Authorization': ip
    }
    if type == 'html':
        try:
            res = requests.get(url=url, headers=header, verify=False, timeout=5)
            text = re.findall('<title>(.*?)</title>', res.text)[0] if re.findall('<title>(.*?)</title>',
                                                                                 res.text) is not None else '无标题'
            print(text)
            return [res.status_code, text]
        except Exception as e:
            return ['erros', '产生了错误']
    else:
        try:
            print(f'正在请求js：{url}')
            res = requests.get(url=url, headers=header, verify=False, timeout=5)
            with open('result.html', 'a+', encoding='utf-8') as pp:
                pp.write(f'''<p>
                <a href="{url}">{url}</a> | 响应码 :{res.status_code}
                </p>''')
        except Exception as e:
            with open('result.html', 'a+', encoding='utf-8') as pp:
                pp.write(f'''<p>
                <a href="{url}">{url}</a> | 响应码 : 产生了错误
                </p>''')


def find_by_url_deep(url):
    '''
    这个函数用于进行深度查找。更好的清洗js
    :param url: 传入的网址
    :return:
    '''
    # 创建一个用于写入的文件
    f = open('result.html', 'a+', encoding='utf-8')
    f.write(f'''
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>《{url}》返回结果</title>
</head>
<body>
    ''')
    # 获取目标网页的源代码
    html_raw = Extract_html(url)
    # 如果获取网页源代码为空
    if html_raw == None:
        print(f"无法访问：{url},请在本机上检查是否能够正常访问...")
        return None
    # 数据清洗，
    html = BeautifulSoup(html_raw, "html.parser")
    # 找到里面所有的 a 标签
    html_as = html.findAll("a")
    # 创建个容器
    links = []
    # 循环遍历
    for html_a in html_as:
        # 获得a标签里面的连接
        src = html_a.get("href")
        # 如果 没有连接或者为空就跳过
        if src == "" or src == None: continue
        # 返回处理完成后的url链接（link）
        link = process_url(url, src)
        # 如果链接没有在容器里面添加
        if link not in links:
            links.append(link)
    # 如果容器为空，就返回空
    if links == []: return None
    # 将重复的链接进行去重操作
    links = list(set(links))
    print("正在写入网址")
    '''
    魔改写入爬取所有的url
    '''
    f.write(f'''
        <details open>
            <summary>{url}上爬取到的网址</summary>
        ''')

    for i in links:
        temp = req_code(i)
        f.write(f'''<p>
        网址：<a href="{i}">{i}</a> | 响应码：{temp[0]} | 标题： {temp[1]}
        </p>''')
    f.write('</details>')
    print('网址写入完成')
    f.write(f'''<details>
                <summary>爬取到的js网址</summary>
    ''')
    # 找到的所有链接
    print("所有找到的链接共计： " + str(len(links)) + "链接")
    # 准备存储的容器
    urls = []
    # 计算最大的值
    i = len(links)
    # 这里写入html标记
    for link in links:
        # 获取返回的url结果集合
        temp_urls = list(set(find_by_url(link)))
        if temp_urls == None: continue
        # print("余下： " + str(i) + " | 找到 " + str(len(temp_urls)) + " URL in " + link)
        print(f'剩下 {str(i)} | 从 {link} 中找到链接：{str(len(temp_urls))} 条')
        for temp_url in temp_urls:
            if temp_url not in urls:
                urls.append(temp_url)
        i -= 1
    #     返回所有的js链接
    js_list = list(set(urls))
    return js_list


def find_by_file(file_path, js=False):
    with open(file_path, "r") as fobject:
        links = fobject.read().split("\n")
    if links == []: return None
    print("ALL Find " + str(len(links)) + " links")
    urls = []
    i = len(links)
    for link in links:
        if js == False:
            temp_urls = find_by_url(link)
        else:
            temp_urls = find_by_url(link, js=True)
        if temp_urls == None: continue
        print(str(i) + " Find " + str(len(temp_urls)) + " URL in " + link)
        for temp_url in temp_urls:
            if temp_url not in urls:
                urls.append(temp_url)
        i -= 1
    return urls


def giveresult(urls, domian):
    # 接收到的url为空，就返回
    if urls == None:
        return None
    print("找到js的链接共计 ：" + str(len(urls)) + " 个")
    content_url = ""
    content_subdomain = ""
    for url in urls:
        content_url += url + "\n"
        print(url)
    subdomains = find_subdomain(urls, domian)
    print("\n找到的 " + str(len(subdomains)) + " 子域名：")
    with open('result.html','a+',encoding='utf-8') as f:
        f.write(f'''<details>
                        <summary>该网址下的子域名</summary>
            ''')
        for subdomain in subdomains:
            content_subdomain += subdomain + "\n"
            f.write(f'''<p>
                    子域名 ： {subdomain}
                    </p>''')
            print(subdomain)
        f.write('</details>')
    if args.outputurl != None:
        with open(args.outputurl, "a", encoding='utf-8') as fobject:
            fobject.write(content_url)
        print("\nOutput " + str(len(urls)) + " urls")
        print("Path:" + args.outputurl)
    if args.outputsubdomain != None:
        with open(args.outputsubdomain, "a", encoding='utf-8') as fobject:
            fobject.write(content_subdomain)
        print("\nOutput " + str(len(subdomains)) + " subdomains")
        print("Path:" + args.outputsubdomain)


if __name__ == "__main__":
    # 禁用警告
    urllib3.disable_warnings()
    # 检测结果文件是否存在
    if os.path.exists("result.html"):
        os.remove('result.html')
    # 获取列表参数
    args = parse_args()
    # 如果没有文件。
    if args.file == None:
        # 如果不进行深度查找
        if args.deep is not True:
            urls = find_by_url(args.url)
            giveresult(urls, args.url)
        # 如果进行深度查找
        else:
            # 这里的urls 是所有的js链接
            urls = find_by_url_deep(args.url)
            # 输出
            # 写入文件
            print('js文件开始写入，过程可能回很漫长')
            with open('result.html', mode='a+', encoding='utf-8') as f:
                with ThreadPoolExecutor(max_workers=10) as pool:
                    for js in urls:
                        pool.submit(req_code, js, 'js')
                f.write('</details>')
            print('js文件写入完成。')
            giveresult(urls, args.url)
    else:
        if args.js is not True:
            urls = find_by_file(args.file)
            giveresult(urls, urls[0])
        else:
            urls = find_by_file(args.file, js=True)
            giveresult(urls, urls[0])
