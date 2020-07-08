# -*- coding: utf-8 -*-
from io import open
import os
import re
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from random import randint
from scipy import optimize

# 获取词频
def get_word_freq_cnki(browser, word="按捺", year_from=1949, year_to=1979):
    word = str(word)
    # word="懂都都东西"
    # url_access ="https://kns.cnki.net/kns/request/SearchHandler.ashx?action=&NaviCode=*&ua=1.21&isinEn=1&PageName=ASP.brief_result_aspx&DbPrefix=CJFQ&DbCatalog=中国学术期刊网络出版总库&ConfigFile=CJFQ.xml&db_opt=CJFQ&db_value=中国学术期刊网络出版总库&year_from=1949&year_to=1979&year_type=echar&txt_1_sel=AB&txt_1_value1=觉醒&txt_1_relation=#CNKI_AND&txt_1_special1==&his=0&db_cjfqview=中国学术期刊网络出版总库,WWJD&db_cflqview=中国学术期刊网络出版总库&__=Mon Jul 06 2020 16:41:28 GMT+0800 (中国标准时间)"
    # 一次访问，词+年份
    url_access_1 = "https://kns.cnki.net/kns/request/SearchHandler.ashx?action=&NaviCode=*&ua=1.21&isinEn=1&PageName=ASP.brief_result_aspx&DbPrefix=CJFQ&DbCatalog=中国学术期刊网络出版总库&ConfigFile=CJFQ.xml&db_opt=CJFQ&db_value=中国学术期刊网络出版总库&year_from=" + str(
        year_from) + "&year_to=" + str(year_to) + "&year_type=echar&txt_1_sel=AB&txt_1_value1="
    url_access_2 = "&txt_1_relation=#CNKI_AND&txt_1_special1==&his=0&db_cjfqview=中国学术期刊网络出版总库,WWJD&db_cflqview=中国学术期刊网络出版总库&__=Mon Jul 06 2020 16:41:28 GMT+0800 (中国标准时间)"
    # 二次访问
    url_check = "https://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_result_aspx&isinEn=1&dbPrefix=CJFQ&dbCatalog=中国学术期刊网络出版总库&ConfigFile=CJFQ.xml&research=off&t=1594023997062&keyValue=" + word + "&S=1&sorttype="

    browser.get(url_access_1 + word + url_access_2)
    browser.get(url_check)
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('div', class_="pagerTitleCell")
    if content is None:
        return None
    content = content.text
    print("\r" + word + str(year_from) + " content:" + str(content), end="")
    nums = re.findall(r"找到\s*(.*?)\s*条结果", content)
    if nums and len(nums) > 0:
        num = nums[0].replace(",", "")
        if num.isdigit():
            return num
        else:
            print("非数字错误：" + word + "(" + str(year_from) + "-" + str(year_to) + ")")
            return None
    else:
        return None


# 获取某词所有年份的词频列表
def get_freq_list(browser, word, years):
    freq_list = []
    for year in years:
        year_from = year_to = year
        #time.sleep(randint(1, 5))
        try:
            freq = get_word_freq_cnki(browser, word, year_from, year_to)
            while freq is None:
                freq = get_word_freq_cnki(browser, word, year_from, year_to)
            freq_list.append(int(freq) + 1)  # 加1平滑

        except RuntimeError as err:
            print(err)
            print("failed")
            break
        except IndexError as err:
            print(err)
            print("failed")
            break

    return freq_list

# 直线方程
def f(x, A, B):
    return A*x + B

# 返回斜率、截距、拟合度
def fit_line(pair_rate, years, year_from, year_to):
    start_idx = year_from - 1956
    end_idx = year_to - 1956 - 1

    y = pair_rate[start_idx:end_idx]
    x = years[start_idx:end_idx]
    # 获得斜率、截距
    A, B = optimize.curve_fit(f, x, y)[0]
    # 计算拟合度
    calc_y = [f(i, A, B) for i in x]
    res_y = np.array(y) - np.array(calc_y)
    ss_res = np.sum(res_y ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    return A, B, r_squared

# 向文件中写入斜率、截距、拟合度
def mywrite(out_file, A, B, R2):
    out_file.write(str(A) + '\t' + str(B) + '\t' + str(R2) + '\t')
    out_file.flush()

# 获得斜率、截距、拟合度并存入txt
def get_pair_gradient(pair, out_file, pair_rate, years): # years 0-64 years[47]=2003
    out_file.write(pair + "\t")
    # 1956-2019/1956-2001/2003-2019/1985-2001/2003-2019（重复）/1985-2002/2002-2019
    A, B, R2= fit_line(pair_rate, years, 1956, 2019)
    mywrite(out_file, A, B, R2)
    A, B, R2= fit_line(pair_rate, years, 1956, 2001)
    mywrite(out_file, A, B, R2)
    A, B, R2= fit_line(pair_rate, years, 2003, 2019)
    mywrite(out_file, A, B, R2)
    A, B, R2= fit_line(pair_rate, years, 1985, 2001)
    mywrite(out_file, A, B, R2)
    A, B, R2= fit_line(pair_rate, years, 2003, 2019)
    mywrite(out_file, A, B, R2)
    A, B, R2= fit_line(pair_rate, years, 1985, 2002)
    mywrite(out_file, A, B, R2)
    A, B, R2= fit_line(pair_rate, years, 2002, 2019)
    mywrite(out_file, A, B, R2)
    out_file.write("\n")

# 获取词组的词频列表、占比率、拟合直线
def download_pair(browser, out_file, pair, years ):
    pair_ = int(len(pair) / 2)
    word_prop = pair[0:pair_]   # 推荐词
    word_unprop = pair[pair_+1:]   # 非推荐词


    print("正在处理：" + pair)

    prop_list = get_freq_list(browser, word_prop, years)
    unprop_list = get_freq_list(browser, word_unprop, years)
    pair_rate = np.array(prop_list) / (np.array(unprop_list) + np.array(prop_list))
    print("\n")
    get_pair_gradient(pair,out_file, pair_rate, years)





if __name__ == '__main__':


    out_file_name = "知网期刊摘要词频斜率-截距-拟合度.txt"
    read_file_name = "test.txt"

    # 文件不存在则创建文件
    if not os.path.exists(out_file_name):
        open(out_file_name, mode='w', encoding='utf-8')
    # 读取已写入的内容
    content = open(out_file_name, mode='r', encoding='utf-8')
    content = content.read()
    # 读取词语列表
    words_pair = open(read_file_name, encoding='utf-8').read().strip().split('\n')
    years = range(1956, 2020, 1)

    browser = webdriver.Chrome()
    pair_pos = 0
    pair_idx = 0
    print("searching the pair in txt...")
    for idx in range(len(words_pair)):
        pos = content.find(words_pair[idx])
        if pos != -1:  # 该词已记录
            pair_idx = idx  #
            pair_pos = pos  # 上次查询时，已记录的词的位置
    content = content[:pair_pos]  # 将已记录的内容截取到上一词完整部分，即词+斜率、截距、拟合度
    # 词频输出文件 打开会清除txt内容 在此处打开
    out_file = open("知网期刊摘要词频斜率-截距-拟合度.txt", mode='w', encoding='utf-8')
    # 写入已记录的有效内容
    out_file.write(content)
    out_file.flush()
    print("开始处理:",words_pair[pair_idx])

    # 开始读取新的词对信息并写入txt
    for idx_raw in range(pair_idx, len(words_pair)):
        download_pair(browser, out_file, words_pair[idx_raw], years)
        #get_pic

    out_file.close()
    browser.quit()

