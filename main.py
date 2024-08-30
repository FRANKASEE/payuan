import urllib.request
from urllib.parse import urlparse
import re  # 正则
import os
from datetime import datetime

# 执行开始时间
timestart = datetime.now()
# 报时
print(f"time: {datetime.now().strftime('%Y%m%d_%H_%M_%S')}")

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

# read BlackList 2024-06-17 15:02
def read_blacklist_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    BlackList = [line.split(',')[1].strip() for line in lines if ',' in line]
    return BlackList

blacklist_auto = read_blacklist_from_txt('blacklist/blacklist_auto.txt')
blacklist_manual = read_blacklist_from_txt('blacklist/blacklist_manual.txt')
combined_blacklist = set(blacklist_auto + blacklist_manual)

# 定义多个对象用于存储不同内容的行文本
sh_lines = []
ys_lines = []  # CCTV
ws_lines = []  # 卫视频道
ty_lines = []  # 体育频道
dy_lines = []
dsj_lines = []
gat_lines = []  # 港澳台
gj_lines = []  # 国际台
jlp_lines = []  # 纪录片
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
    path = parsed_url.path
    extension = os.path.splitext(path)[1]
    return extension

def convert_m3u_to_txt(m3u_content):
    lines = m3u_content.split('\n')
    txt_lines = []
    channel_name = ""

    for line in lines:
        if line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF"):
            channel_name = line.split(',')[-1].strip()
        elif line.startswith("http") or line.startswith("rtmp") or line.startswith("p3p"):
            txt_lines.append(f"{channel_name},{line.strip()}")

    return '\n'.join(txt_lines)

def check_url_existence(data_list, url):
    urls = [item.split(',')[1] for item in data_list]
    return url not in urls

def clean_url(url):
    last_dollar_index = url.rfind('$')
    if last_dollar_index != -1:
        return url[:last_dollar_index]
    return url

def process_channel_line(line):
    if "#genre#" not in line and "," in line and "://" in line:
        channel_name = line.split(',')[0].strip()
        channel_address = clean_url(line.split(',')[1].strip())
        line = channel_name + "," + channel_address

        if channel_address not in combined_blacklist:
            if "CCTV" in channel_name and check_url_existence(ys_lines, channel_address):
                ys_lines.append(process_name_string(line.strip()))
            elif channel_name in ws_lines and check_url_existence(ws_lines, channel_address):
                ws_lines.append(process_name_string(line.strip()))
            elif channel_name in ty_lines and check_url_existence(ty_lines, channel_address):
                ty_lines.append(process_name_string(line.strip()))
            elif channel_name in dy_lines and check_url_existence(dy_lines, channel_address):
                dy_lines.append(process_name_string(line.strip()))
            elif channel_name in dsj_lines and check_url_existence(dsj_lines, channel_address):
                dsj_lines.append(process_name_string(line.strip()))
            elif channel_name in sh_lines and check_url_existence(sh_lines, channel_address):
                sh_lines.append(process_name_string(line.strip()))
            elif channel_name in gat_lines and check_url_existence(gat_lines, channel_address):
                gat_lines.append(process_name_string(line.strip()))
            elif channel_name in gj_lines and check_url_existence(gj_lines, channel_address):
                gj_lines.append(process_name_string(line.strip()))
            elif channel_name in jlp_lines and check_url_existence(jlp_lines, channel_address):
                jlp_lines.append(process_name_string(line.strip()))
            else:
                other_lines.append(line.strip())

def process_url(url):
    try:
        other_lines.append("◆◆◆　" + url)
        with urllib.request.urlopen(url) as response:
            data = response.read()
            text = data.decode('utf-8')

            if get_url_file_extension(url) == ".m3u" or get_url_file_extension(url) == ".m3u8":
                text = convert_m3u_to_txt(text)

            lines = text.split('\n')
            print(f"行数: {len(lines)}")
            for line in lines:
                if "#genre#" not in line and "," in line and "://" in line:
                    channel_name, channel_address = line.split(',', 1)
                    if "#" not in channel_address:
                        process_channel_line(line)
                    else:
                        url_list = channel_address.split('#')
                        for channel_url in url_list:
                            newline = f'{channel_name},{channel_url}'
                            process_channel_line(newline)

            other_lines.append('\n')

    except Exception as e:
        print(f"处理URL时发生错误：{e}")

current_directory = os.getcwd()

# 读取文本
ys_dictionary = read_txt_to_array('主频道/CCTV.txt')
sh_dictionary = read_txt_to_array('主频道/shanghai.txt')
ws_dictionary = read_txt_to_array('主频道/卫视频道.txt')
ty_dictionary = read_txt_to_array('主频道/体育频道.txt')
dy_dictionary = read_txt_to_array('主频道/电影.txt')
dsj_dictionary = read_txt_to_array('主频道/电视剧.txt')
gat_dictionary = read_txt_to_array('主频道/港澳台.txt')
gj_dictionary = read_txt_to_array('主频道/国际台.txt')
jlp_dictionary = read_txt_to_array('主频道/纪录片.txt')

# 定义
urls = read_txt_to_array('assets/urls-daily.txt')

# 读取纠错频道名称方法
def load_corrections_name(filename):
    corrections = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            correct_name = parts[0]
            for name in parts[1:]:
                corrections[name] = correct_name
    return corrections

# 读取纠错文件
corrections_name = load_corrections_name('assets/corrections_name.txt')

# 纠错频道名称
def correct_name_data(corrections, data):
    corrected_data = []
    for line in data:
        name, url = line.split(',', 1)
        if name in corrections and name != corrections[name]:
            name = corrections[name]
        corrected_data.append(f"{name},{url}")
    return corrected_data

def sort_data(order, data):
    order_dict = {name: i for i, name in enumerate(order)}
    
    def sort_key(line):
        name = line.split(',')[0]
        return order_dict.get(name, len(order))
    
    sorted_data = sorted(data, key=sort_key)
    return sorted_data

# 处理
for url in urls:
    print(f"处理URL: {url}")
    process_url(url)

# 合并所有对象中的行文本（去重，排序后拼接）
version = datetime.now().strftime("%Y%m%d-%H-%M-%S") + ",url"
all_lines = ["更新时间,#genre#"] + [version] + ['\n'] + \
            ["🆕专享源1️⃣,#genre#"] + read_txt_to_array('主频道/♪专享源①.txt') + ['\n'] + \
            ["🆕专享源2️⃣,#genre#"] + read_txt_to_array('主频道/♪专享源②.txt') + ['\n'] + \
            ["🆕专享央视,#genre#"] + read_txt_to_array('主频道/♪优质央视.txt') + ['\n'] + \
            ["🆕优质源,#genre#"] + read_txt_to_array('主频道/♪优质源.txt') + ['\n'] + \
            ["🌐央视频道,#genre#"] + sorted(set(ys_lines)) + ['\n'] + \
            ["📡卫视频道,#genre#"] + sorted(set(ws_lines)) + ['\n'] + \
            ["上海频道,#genre#"] + sorted(set(sh_lines)) + ['\n'] + \
            ["体育频道,#genre#"] + sorted(set(ty_lines)) + ['\n'] + \
            ["电影频道,#genre#"] + sorted(set(dy_lines)) + ['\n'] + \
            ["电视剧频道,#genre#"] + sorted(set(dsj_lines)) + ['\n'] + \
            ["港澳台,#genre#"] + sorted(set(gat_lines)) + ['\n'] + \
            ["国际台,#genre#"] + sorted(set(gj_lines)) + ['\n'] + \
            ["纪录片,#genre#"] + sorted(set(jlp_lines)) + ['\n'] + \
            ["直播中国,#genre#"] + sorted(set(other_lines)) + ['\n']

# 将合并后的文本写入文件
output_file = "merged_output.txt"
others_file = "others_output.txt"
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in all_lines:
            f.write(line + '\n')
    print(f"合并后的文本已保存到文件: {output_file}")

    with open(others_file, 'w', encoding='utf-8') as f:
        for line in other_lines:
            f.write(line + '\n')
    print(f"Others已保存到文件: {others_file}")

except Exception as e:
    print(f"保存文件时发生错误：{e}")

# 执行结束时间
timeend = datetime.now()

# 计算时间差
elapsed_time = timeend - timestart
total_seconds = elapsed_time.total_seconds()

# 转换为分钟和秒
minutes = int(total_seconds // 60)
seconds = int(total_seconds % 60)
# 格式化开始和结束时间
timestart_str = timestart.strftime("%Y%m%d_%H_%M_%S")
timeend_str = timeend.strftime("%Y%m%d_%H_%M_%S")

print(f"开始时间: {timestart_str}")
print(f"结束时间: {timeend_str}")
print(f"执行时间: {minutes} 分 {seconds} 秒")

combined_blacklist_hj = len(combined_blacklist)
all_lines_hj = len(all_lines)
other_lines_hj = len(other_lines)
print(f"blacklist行数: {combined_blacklist_hj} ")
print(f"merged_output.txt行数: {all_lines_hj} ")
print(f"others_output.txt行数: {other_lines_hj} ")
