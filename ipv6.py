# -*- coding: utf-8 -*-
"""
Created on Wed May  9 20:20:03 2018

@author: Kumius
"""


"""
部分网站不支持CURL（可能是为了反爬虫），
因此HTTP(S)需要合法的AGENT-HEADER，可以用CURL -A "" 选项来伪造

例如：
curl https://jandan.net/ -A "Mozilla/5.0 (Windows NT 6.1; WOW64)
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36"

curl https://www.baidu.com/ -A "Chrome/66.0.3359.181"

call(["curl", "-A 'Chrome/66.0.3359.181'",  "https://www.baidu.com"])



测试IPV6的规模（规模尽量大）
性能测量（选取部分网站）
差异化（与性能测量部分一致）
"""


import os
import subprocess
from subprocess import call
import threading

'''
一般指编码造成的错误
'''
HTML_ERROR = "###ERROR###"


def curl_os(url, args=None):
    '''
    需要考虑到 agent-header，超时时间，编码等问题
    curl ... | iconv -f gbk
    '''
    cmd = "curl -A 'Chrome/66.0.3359.181' -L --connect-timeout 3 --max-time 6 "
    cmd += url
    if args != None:
        cmd += " " + args
    cmd += " -w '\n'%{time_namelookup}::%{time_connect}::%{time_starttransfer}::%{time_total}::%{speed_download}"
    print("cmd = " + cmd)
    pipe = os.popen(cmd)
    #print(pipe.read())
    try:
        '''可能有编码错误'''
        html = pipe.read()
    except Exception as e:
        html = HTML_ERROR
    #html = ""
    pipe.close()
    return html

def curl_call(url):
    
    cmd = "curl"
    args = "-A 'Chrome/66.0.3359.181'"
    call([cmd, args, url])

def curl_popen(url):
    
    cmd = "curl -A 'Chrome/66.0.3359.181' " + url
    output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(output.stdout.read())


def analyze(htmls):
    '''
    ["http-ipv4", "http-ipv6", "https-ipv4", "https-ipv6"]
    分析不同html之间的区别：
    
    [http/ip支持情况（4种，包括时间），是否支持IPV4/6, 建链时间差异，传输速度差异，页面是否有差异]
    [{0, 0.0 * 5} * 4, 0, 0, 0, 0]
    
    内容为HTML_ERROR，一般是编码错误，
    内容只有时间栏的话，一般是访问不通，时间为最大等待时间
    如果网站支持HTTPS，则只分析HTTPS的内容。
    '''
    result = []
    for i, html in enumerate(htmls):
        html_len = len(html)
        if html == HTML_ERROR:
            '''可访问，但编码错误'''
            result.append(-1)
            result.extend([0.0] * 5)
        else:
            if html_len <= 1024 and html.count('\n') <= 1:
                '''访问超时，没有实际内容，只有时间信息'''
                result.append(0)
            else:
                result.append(1)
            st = html.rfind('\n')
            if st == -1:
                print("ERROR")
                result.extend([-1] * 5)
                continue
            times = html[st+1: -1]
            htmls[i] = html[:st]
            times = times.split("::")
            for time in times:
                result.append(float(time))
    
    '''
    http-ipv6 or https-ipv6都证明支持IPV6
    编码出错，说明已经读取了内容了，只是编码有问题
    IPV_46 = IPV4 | IPV6
    '''
    IPV_4 = 0
    IPV_6 = 0
#    if result[0] == 1 or result[12] == 1:
    if result[0] != 0 or result[12] != 0:
        IPV_4 = 1
    if result[6] != 0 or result[18] != 0:
        IPV_6 = 2
    IPV_46 = IPV_4 | IPV_6
    result.append(IPV_46)


    '''
    1、计算时间差异，包括建链时间、传输时间
    
    2、计算页面差异，如果有差异，可以保留原始html
    这里不对具体的页面差异进行分析，只输出[0,1]，其中1表示页面有差异
    '''
    index_v6 = -1
    index_v4 = -1
    
    time_connect_v6 = -1
    time_connect_v4 = -1
    time_total_v6 = -1
    time_total_v4 = -1
    
    if result[18] == 1:
        index_v6 = 18
    elif result[6] == 1:
        index_v6 = 6
    
    if result[12] == 1:
        index_v4 = 12
    elif result[0] == 1:
        index_v4 = 0

    if index_v4 == -1 or index_v6 == -1:
        time_connect_diff = 0
        time_total_diff = 0
        page_diff = 0
    else:
        time_connect_v6 = result[index_v6 + 1]
        time_total_v6 = result[index_v6 + 3]
        time_connect_v4 = result[index_v4 + 1]
        time_total_v4 = result[index_v4 + 3]
        
        '''防止除0溢出'''
        if time_connect_v4 == 0:
            time_connect_v4 = 0.0001
        if time_total_v4 == 0:
            time_total_v4 = 0.0001
        
        time_connect_diff = time_connect_v6 - time_connect_v4
        time_connect_diff = time_connect_diff / time_connect_v4
        
        time_total_diff = time_total_v6 - time_total_v4
        time_total_diff = time_total_diff / time_total_v4
        
        if htmls[index_v6 // 6] == htmls[index_v4 // 6]:
            page_diff = 0
        else:
            page_diff = 1
    
    result.append(time_connect_diff)
    result.append(time_total_diff)
    result.append(page_diff)
    
    
    return result

def handle(filename, scope):
    file = open(filename)
    path = "result/"
    #folders = ["http-ipv4", "http-ipv6", "https-ipv4", "https-ipv6"]
    ip_modes = ["4", "6"]
    #ip_modes = ["4"]
    http_modes = ["http", "https"]
    #http_modes = ["https"]
    
    foutname = "output/output-" + str(scope[0]) + "-" + str(scope[1]) + ".csv"
    fout = open(foutname, "w")

    for line in file:
        num, url = line.split(",")
        
        num_int = int(num)
        if num_int < scope[0] or num_int > scope[1]:
            continue
        
        url = url.strip()
        htmls = []
        for http_mode in http_modes:
            for ip_mode in ip_modes:
#                to_save = path + http_mode + "-ipv" + ip_mode + "/" + url + ".save"
#                print("save: " + to_save)
                try:
                    html = curl_os(http_mode + "://www." + url, "-" + ip_mode)
                    htmls.append(html)
#                    fsave = open(to_save, "w")
#                    fsave.write(html)
#                    fsave.close()
                except Exception as e:
                    pass
        '''
        ["http-ipv4", "http-ipv6", "https-ipv4", "https-ipv6"]
        分析不同html之间的区别
        '''
        result = analyze(htmls)
        print(num, result, sep=": ")
        '''
        如果页面有差异，则保存全部页面，留待后续分析
        '''
        if result[-1] == 1:
            i = 0
            for http_mode in http_modes:
                for ip_mode in ip_modes:
                    html = htmls[i]
                    to_save = path + http_mode + "-ipv" + ip_mode + "/" + url + ".save"
                    print("save: " + to_save)
                    fsave = open(to_save, "w")
                    fsave.write(html)
                    fsave.close()
                    i += 1
        print('----------\n')
        fout.write(num)
        for item in result:
            fout.write("," + str(item))
        fout.write("\n")
        fout.flush()
        
    fout.close()




if __name__ == "__main__":
    #curl_os("https://www.baidu.com")
    #curl_popen("https://www.baidu.com")
    #handle("top-1m.csv")
    #handle("test.txt")
    thds = []
    for it in range(4, 4 + 10):
        args = ("test.txt", [5000 * it + 1, 5000 * (it+1)])
        thd = threading.Thread(target=handle, args=args)
        thds.append(thd)
        thd.start()
    for it in range(10):
        thds[it].join()
    
#    handle("test.txt", [1,10_000])
#    handle("test.txt", [10_001,20_000])
#    handle("test.txt", [15367, 20000])
#
#    handle("test.txt", [1,1000_000])















