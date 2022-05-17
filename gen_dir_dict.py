#!/usr/bin/env python3
# coding=utf-8

import argparse
import textwrap
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse


class GenDirDict:
    def __init__(self, url, domain, keywords, path, year=2, level=3):
        self.suffix_list = ['tar.gz', 'zip', 'rar', 'tar', 'txt', 'log']
        self.extended_suffix_list = ['7z','bak','bz2','gz','log','mdb','rar','sql','tar','tar.bz2','tar.gz','txt','zip','old','tar.gzip']
        self.default_path_list = ['api', 'backup', 'classes', 'backup-db']
        self.url = url
        self.domain = domain
        self.keywords = keywords
        self.path = path
        self.year = year
        self.level = level
        self.dir_dict = []
        self.time_dict = []
        self.domain_dict = []
        self.keywords_dict = []
        self.path_dict = []

        if self.level >= 4:
            self.ext_list = self.extended_suffix_list
        else:
            self.ext_list = self.suffix_list

    def gen_time_list(self):
        '''
        生成时间字典可选列表, 形式: 2022, 202202, 20220202, 20220202020202
        '''
        time_list = []
        year_list = []
        year_month_list = []
        year_month_day_list = []
        last_three_month_day_hour_minute_second_list = []

        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day

        start_time = datetime(current_year - self.year, current_month, current_day)
        end_time = datetime(current_year, current_month, current_day)

        delta = end_time - start_time

        for i in range(delta.days + 1):
            year_month_day_list.append((start_time + timedelta(i)).strftime('%Y%m%d'))

        for i in range(current_year, current_year - self.year - 1, -1):
            year_list.append(str(i))

        for i in year_month_day_list:
            year_month_list.append(i[:6])
        year_month_list = list(set(year_month_list))
        
        # 时分秒与年月日及后缀其他组合数据量太大，从实战角度来说不具有暴破意义，默认不启用
        # 选用近3月年月日与时分秒组合，数据量达到700万+，谨慎使用
        if self.level == 5:
            last_three_month_day_list = []
            for i in year_month_day_list:
                if int(i[:4]) == current_year and (current_month - int(i[4:6])) <= 3:
                    last_three_month_day_list.append(i)
            
            for i in last_three_month_day_list:
                for hour in range(0, 24):
                    for minute in range(0, 60):
                        for second in range(0, 60):
                            last_three_month_day_hour_minute_second_list.append('{}{:02d}{:02d}{:02d}'.format(i, hour, minute, second))
        
        # level为4时, 将时间变形加入字典可选列表, 如: 2022-02, 2022-02-02
        elif self.level == 4:
            extended_year_month_list = []
            extended_year_month_day_list = []
            for i in year_month_list:
                extended_year_month_list.append('{}-{}'.format(i[:4], i[4:6]))
            for i in year_month_day_list:
                extended_year_month_day_list.append('{}-{}-{}'.format(i[:4], i[4:6], i[6:8]))
            year_month_list += extended_year_month_list
            year_month_day_list += extended_year_month_day_list
        
        time_list = year_list + year_month_list + year_month_day_list + last_three_month_day_hour_minute_second_list
        return time_list

    def gen_domain_list(self):
        '''
        生成域名字典可选列表
        目前针对 baidu.com, www.baidu.com, www.sgcc.com.cn, www.bj.sgcc.com.cn 这几种2-5级域名进行了适配, 可能还存在一些其他未适配情况, 可以提issue
        '''
        domain_list = []

        # 针对baidu.com
        domain_list.append(self.domain)
        domain_list.append(self.domain.split('.')[0])
        
        # 针对www.baidu.com, www.sgcc.com.cn, www.bj.sgcc.com.cn
        if len(self.domain.split('.')) > 2:
            domain_list.append(self.domain.split('.')[1])
        
        # 针对www.bj.sgcc.com.cn
        if len(self.domain.split('.')) >= 5:
            domain_list.append(self.domain.split('.')[-3])

        domain_list = list(set(domain_list))
        return domain_list
    
    def gen_keywords_list(self):
        '''
        关键词字典可选列表, 如: 工商银行, 工行, icbc
        '''
        keywords_list = []
        for k in self.keywords.split(','):
            keywords_list.append(k)
        return keywords_list

    def gen_path_list(self):
        '''
        根据站点已知路径和目录生成字典可选列表, 如: api, icbc
        '''
        path_list = []
        for p in self.path.split(','):
            path_list.append(p)
        path_list = list(set(self.default_path_list + path_list))
        return path_list
    
    def gen_time_dict(self):
        '''
        生成时间字典, 如: 2022.tar.gz, 202202.tar.gz, 20220202.tar.gz
        '''
        time_list = self.gen_time_list()
        self.time_dict += time_list
        for e in self.ext_list:
            for t in time_list:
                self.time_dict.append('{}.{}'.format(t, e))
        return self.time_dict

    def gen_domain_dict(self):
        '''
        生成域名字典及域名时间拼接字典, 如: icbc.tar.gz, icbc2022.tar.gz, icbc20220202.tar.gz, icbc-2022.tar.gz
        icbc.com.cn这种域名将不会拼接时间
        '''
        domain_list = self.gen_domain_list()
        time_list = self.gen_time_list()
        self.domain_dict += domain_list
        for e in self.ext_list:
            for d in domain_list:
                self.domain_dict.append('{}.{}'.format(d, e))
                # 针对icbc.com.cn
                if '.' not in d and self.level >= 3:
                    # 添加如: icbc-backup字典
                    self.domain_dict.append('{}bak.{}'.format(d, e))
                    self.domain_dict.append('{}-bak.{}'.format(d, e))
                    self.domain_dict.append('{}backup.{}'.format(d, e))
                    self.domain_dict.append('{}-backup.{}'.format(d, e))
                    
                    # 排除www拼接时间,减少数据量
                    if 'www' in d:
                        continue

                    self.domain_dict.append('{}api.{}'.format(d, e))
                    self.domain_dict.append('{}-api.{}'.format(d, e))
                    self.domain_dict.append('api-{}.{}'.format(d, e))
                    for t in time_list:
                        self.domain_dict.append('{}{}.{}'.format(d, t, e))
                        # level >= 4时, 添加如: icbc-2022.tar.gz, icbc-20220202.tar.gz, icbc-2022-02-02.tar.gz
                        if self.level >= 4:
                            self.domain_dict.append('{}-{}.{}'.format(d, t, e))

        return self.domain_dict

    def gen_keywords_dict(self):
        '''
        生成关键词字典及关键词时间拼接字典, 如: 工商银行.rar, 工行2021.zip, 工行20220202.zip
        '''
        keywords_list = self.gen_keywords_list()
        time_list = self.gen_time_list()
        self.keywords_dict += keywords_list
        for e in self.ext_list:
            for k in keywords_list:
                self.keywords_dict.append('{}.{}'.format(k, e))
                if self.level >= 3:
                    self.keywords_dict.append('{}bak.{}'.format(k, e))
                    self.keywords_dict.append('{}-bak.{}'.format(k, e))
                    self.keywords_dict.append('{}backup.{}'.format(k, e))
                    self.keywords_dict.append('{}-backup.{}'.format(k, e))
                    for t in time_list:
                        self.keywords_dict.append('{}{}.{}'.format(k, t, e))
                        if self.level >= 4:
                            self.keywords_dict.append('{}-{}.{}'.format(k, t, e))
        
        return self.keywords_dict

    def gen_path_dict(self):
        '''
        根据站点已知路径和目录及时间生成字典
        '''
        path_list = self.gen_path_list()
        time_list = self.gen_time_list()
        self.path_dict += path_list
        for e in self.ext_list:
            for p in path_list:
                self.path_dict.append('{}.{}'.format(p, e))
                # 排除api拼接时间，减少数据量
                if self.level >= 3 and 'api' not in p:
                    self.path_dict.append('{}bak.{}'.format(p, e))
                    self.path_dict.append('{}-bak.{}'.format(p, e))
                    self.path_dict.append('{}backup.{}'.format(p, e))
                    self.path_dict.append('{}-backup.{}'.format(p, e))
                    for t in time_list:
                        self.path_dict.append('{}{}.{}'.format(p, t, e))
                        if self.level >= 4:
                            self.path_dict.append('{}-{}.{}'.format(p, t, e))
        
        return self.path_dict


def check_domain(host):
    '''检查host是否为域名'''
    pattern = '^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+$'
    result = re.match(pattern, host)
    return result

def save_result(filename, dict):
    '''保存字典'''
    with open(filename, 'wb') as f:
        for d in dict:
            f.write(d.encode() + b'\n')

def parse_url(url):
    '''解析url, 提取出host和path'''
    res = urlparse(url)
    host = res.netloc
    path = res.path
    path_list = path.split('/')

    # hostname为IP地址
    domain = ''
    if check_domain(host):
        domain = host

    # 针对http://www.baidu.com, path为空
    if not path:
        return domain, path
    # path非空, 将其第一个子目录加入字典组合列表
    else:
        return domain, path_list[1]


def handle_file():
    # TODO 处理从文件输入多个url和域名
    pass

def get_args():
    '''获取用户输入参数'''
    parser = argparse.ArgumentParser(description='Generate dictionary of brute force directory', formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--domain', dest='domain', help='Single domain. eg: www.baidu.com or baidu.com')
    group.add_argument('-u', '--url', dest='url', help='Single url. eg: https://www.baidu.com/baidu.php?id=1')
    group.add_argument('-f', '--file', dest='file', help='Domain or url file, one domain or url per line.')
    parser.add_argument('-k', '--keywords', dest='keywords', help='Keywords of target site, separated by commas. eg: baidu,百度')
    parser.add_argument('-p', '--path', dest='path', help='Known path of target site. eg: sysadmin')
    parser.add_argument('-y', '--year', dest='year', choices=range(1, 6), default=2, type=int, help='Latest year range of time dictionary. Default year is 2.')
    parser.add_argument('--dirsearch-path', dest='dirsearch_path', help='Path of dirsearch. eg: c:\\users\\administrator\\dirsearch')
    parser.add_argument('--exclude-url-path-words', dest='exclude_url_path_words', help='Exclude Words in url path, separated by commas. eg: static')
    parser.add_argument('-o', '--output', dest='output', default='dir.txt', help='Filename of dictionary to be generated. eg: baidu.com.txt. Default filename is dir.txt.')
    parser.add_argument('-l', '--level', dest='level', choices=range(1, 6), default=3, type=int, help=textwrap.dedent('''\
        Choose level of dictionory complexity.
        Level 1: Only generate directory dictionary without keywords, path and time.
        Level 2: Generate directory dictionary without time.
        Level 3: Generate directory dictionary with domain, keywords, path and time. eg: baidu20220202.zip
        Level 4: Generate directory dictionary with domain, keywords, path and time. 
        This level add more combination of domain, keywords, path and time. eg: baidu-20220202.zip
        This level add more extension filename to combine. ext: 7z,bak,bz2,gz,log,mdb,rar,sql,tar,tar.bz2,tar.gz,txt,zip,old,tar.gzip
        Level 5: Generate directory dictionary with domain, keywords, path and time. 
        This level adds hour, minute, second and year, month, and day combinations. eg: 20220202020202.zip
        Default level is 3, which is supposed to use. Level 5 is not recommended, because the amount of data is very large and it takes a long time to brute.
        '''))
    args = parser.parse_args()
    return args
    

def main():
    args = get_args()
    domain = args.domain
    url = args.url
    file = args.file
    keywords = args.keywords
    path = args.path
    year = args.year
    output = args.output
    level = args.level
    dirsearch_path = args.dirsearch_path
    exclude_url_path_words = args.exclude_url_path_words

    gen_dir_dict = GenDirDict(url=url, domain=domain, keywords=keywords, path=path, year=1, level=3)

    time_dict = gen_dir_dict.gen_time_dict()
    
    domain_dict = gen_dir_dict.gen_domain_dict()
    
    keywords_dict = gen_dir_dict.gen_keywords_dict()
    
    path_dict = gen_dir_dict.gen_path_dict()
    
    dir_dict = list(set(time_dict + domain_dict + keywords_dict + path_dict))
    save_result(output, dir_dict)


if __name__ == '__main__':
    main()