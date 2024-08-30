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
ys_lines = []  # CCTV
ws_lines = []  # 卫视频道
ty_lines = []  # 体育频道
dy_lines = []
gat_lines = []  # 港澳台
gj_lines = []  # 国际台
jlp_lines = []  # 纪录片
hn_lines = []  # 地方台-湖南频道
Olympics_2024_Paris_lines = []  # Paris_2024_Olympics
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
        part_str = part_str.replace("IPV6", "").replace("PLUS", "+").replace("1080", "")
        filtered_str = ''.join(char for char in part_str if char.isdigit() or char == 'K' or char == '+')
        if not filtered_str.strip():
            filtered_str = part_str.replace("CCTV", "")

        if len(filtered_str) > 2 and re.search(r'4K|8K', filtered_str):
            filtered_str = re.sub(r'(4K|8K).*', r'\1', filtered_str)
            if len(filtered_str) > 2:
                filtered_str = re.sub(r'(4K|8K)', r'(\1)', filtered_str)

        return "CCTV" + filtered_str

    elif "卫视" in part_str:
        pattern = r'卫视「.*」'
        result_str = re.sub(pattern, '卫视', part_str)
        return result_str
    
    return part_str

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
            elif channel_name in Olympics_2024_Paris_dictionary and check_url_existence(Olympics_2024_Paris_lines, channel_address):
                Olympics_2024_Paris_lines.append(process_name_string(line.strip()))
            elif channel_name in ws_dictionary and check_url_existence(ws_lines, channel_address):
                ws_lines.append(process_name_string(line.strip()))
            elif channel_name in ty_dictionary and check_url_existence(ty_lines, channel_address):
                ty_lines.append(process_name_string(line.strip()))
            elif channel_name in dy_dictionary and check_url_existence(dy_lines, channel_address):
                dy_lines.append(process_name_string(line.strip()))
            elif channel_name in gat_dictionary and check_url_existence(gat_lines, channel_address):
                gat_lines.append(process_name_string(line.strip()))
            elif channel_name in gj_dictionary and check_url_existence(gj_lines, channel_address):
                gj_lines.append(process_name_string(line.strip()))
            elif channel_name in jlp_dictionary and check_url_existence(jlp_lines, channel_address):
                jlp_lines.append(process_name_string(line.strip()))
            elif channel_name in hn_dictionary and check_url_existence(hn_lines, channel_address):
                hn_lines.append(process_name_string(line.strip()))
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

ys_dictionary = read_txt_to_array('主频道/CCTV.txt')
ws_dictionary = read_txt_to_array('主频道/卫视频道.txt')
ty_dictionary = read_txt_to_array('主频道/体育频道.txt')
dy_dictionary = read_txt_to_array('主频道/电影.txt')
gat_dictionary = read_txt_to_array('主频道/港澳台.txt')
gj_dictionary = read_txt_to_array('主频道/国际台.txt')
jlp_dictionary = read_txt_to_array('主频道/纪录片.txt')
hn_dictionary = read_txt_to_array('地方台/湖南频道.txt')

def load_corrections_name(filename):
    corrections = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            correct_name = parts[0]
            for name in parts[1:]:
                corrections[name] = correct_name
    return corrections

corrections_name = load_corrections_name('assets/corrections_name.txt')

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

urls = read_txt_to_array('assets/urls-daily.txt')
for url in urls:
    print(f"处理URL: {url}")
    process_url(url)

def extract_number(s):
    num_str = s.split(',')[0].split('-')[1]
    numbers = re.findall(r'\d+', num_str)
    return int(numbers[-1]) if numbers else 999

def custom_sort(s):
    if "CCTV-4K" in s:
        return 2
    elif "CCTV-8K" in s:
        return 3
    elif "(4K)" in s:
        return 1
    else:
        return 0

print(f"ADD whitelist_auto.txt")
whitelist_auto_lines = read_txt_to_array('blacklist/whitelist_auto.txt')
for whitelist_line in whitelist_auto_lines:
    if "#genre#" not in whitelist_line and "," in whitelist_line and "://" in whitelist_line:
        whitelist_parts = whitelist_line.split(",")
        try:
            response_time = float(whitelist_parts[0].replace("s", ""))
            if response_time < 1.6:
                other_lines.append(whitelist_line)
        except ValueError:
            other_lines.append(whitelist_line)

ys_lines = correct_name_data(corrections_name, ys_lines)
ys_lines = sort_data(ys_dictionary, ys_lines)
ys_lines = sorted(ys_lines, key=lambda x: (extract_number(x), custom_sort(x)))

def write_to_txt_file(data, directory, filename):
    if not data:
        return

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        for line in data:
            file.write(line + '\n')

# 保存每个列表的内容到对应的文件中
write_to_txt_file(ys_lines, '主频道', 'CCTV.txt')
write_to_txt_file(ws_lines, '主频道', '卫视频道.txt')
write_to_txt_file(ty_lines, '主频道', '体育频道.txt')
write_to_txt_file(dy_lines, '主频道', '电影.txt')
write_to_txt_file(gat_lines, '主频道', '港澳台.txt')
write_to_txt_file(gj_lines, '主频道', '国际台.txt')
write_to_txt_file(jlp_lines, '主频道', '纪录片.txt')
write_to_txt_file(hn_lines, '地方台', '湖南频道.txt')
write_to_txt_file(Olympics_2024_Paris_lines, '主频道', 'Olympics_2024_Paris.txt')
write_to_txt_file(other_lines, '', f"总表_{datetime.now().strftime('%Y%m%d_%H_%M_%S')}.txt")

print(f"脚本完成, 执行时间: {datetime.now() - timestart}")
