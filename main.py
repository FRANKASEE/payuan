import urllib.request
from urllib.parse import urlparse
import re
import os
from datetime import datetime

# 执行开始时间
timestart = datetime.now()

# 读取文本方法
def read_txt_to_array(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
            return lines
    except FileNotFoundError:
        print(f"File '{file_name}' not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# 读取黑名单
def read_blacklist_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    BlackList = [line.split(',')[1].strip() for line in lines if ',' in line]
    return BlackList

blacklist_auto = read_blacklist_from_txt('blacklist/blacklist_auto.txt')
blacklist_manual = read_blacklist_from_txt('blacklist/blacklist_manual.txt')
combined_blacklist = set(blacklist_auto + blacklist_manual)

# 定义多个对象用于存储不同内容的行文本
ys_lines = [] # CCTV
ws_lines = [] # 卫视频道
ty_lines = [] # 体育频道
dy_lines = []
gat_lines = [] # 港澳台
gj_lines = [] # 国际台
jlp_lines = [] # 记录片

# 保留湖南频道
hn_lines = [] # 湖南频道

Olympics_2024_Paris_lines = [] # Paris_2024_Olympics

other_lines = []

def process_name_string(input_str):
    parts = input_str.split(',')
    processed_parts = []
    for part in parts:
        processed_part = process_part(part)
        processed_parts.append(processed_part)
    result_str = ','.join(processed_parts)
    return result_str

def process_part(part_str):
    if "CCTV" in part_str and "://" not in part_str:
        part_str = part_str.replace("IPV6", "")  # 先剔除IPV6字样
        part_str = part_str.replace("PLUS", "+")  # 替换PLUS
        part_str = part_str.replace("1080", "")  # 替换1080
        filtered_str = ''.join(char for char in part_str if char.isdigit() or char == 'K' or char == '+')
        if not filtered_str.strip():  # 处理特殊情况，如果发现没有找到频道数字返回原名称
            filtered_str = part_str.replace("CCTV", "")

        if len(filtered_str) > 2 and re.search(r'4K|8K', filtered_str):  # 特殊处理CCTV中部分4K和8K名称
            filtered_str = re.sub(r'(4K|8K).*', r'\1', filtered_str)
            if len(filtered_str) > 2:
                filtered_str = re.sub(r'(4K|8K)', r'(\1)', filtered_str)

        return "CCTV" + filtered_str

    elif "卫视" in part_str:
        pattern = r'卫视「.*」'
        result_str = re.sub(pattern, '卫视', part_str)
        return result_str

    return part_str

# 准备支持m3u格式
def get_url_file_extension(url):
    parsed_url = urlparse(url)
    return os.path.splitext(parsed_url.path)[1]

# 代码结束时间
timeend = datetime.now()
print(f"Execution time: {timeend - timestart}")
