# coding=utf-8
#
# Copyright 2020  Yang Liu, Junjie Wang @ Lenovo Research
#
import sys
import time
import datetime
import requests
import urllib3
import json
import os
import argparse
import yaml
from enum import Enum

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.adapters.DEFAULT_RETRIES = 5       # 增加重连次数
requests.session().keep_alive = False       # 关闭多余连接

PRINT_DEBUG_INFO = False
WRITE_DEBUG_INFO = False

APP_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_PATH, 'config.yml')
LENOVO_KEY = 'Please visit https://voice.lenovomm.com to get key'
SECRET_KEY = 'Please visit https://voice.lenovomm.com to get key'

TOTAL_LINE_NUM = 0


class FILETYPE(Enum):
    SRT = 0
    LRC = 1
    TXT = 2


OUTPUT_FILETYPE = FILETYPE.TXT


def recoginse(session, ixid, pidx, over, voice_data):
    files = {'voice-data': voice_data}
    data = {
        # 长语音long  短语音short  不传默认short
        # 'scene': 'short',
        'scene': 'long',
        # 语言  英文识别english 不传或其它值默认中文
        # 'language': 'english',
        # 通道 八通道值为8 不传或其他值默认单通道
        'sample': 1,
        # 语音格式:
        # pcm_16000_16bit_sample  16k 16bit 单声道  pcm
        # pcm_8000_16bit_sample   8k 16bit 单声道  pcm
        # alaw_8000_16bit_sample  8k 16bit 单声道  alaw
        # ulaw_8000_16bit_sample  8k 16bit 单声道  ulaw
        'audioFormat': 'pcm_16000_16bit_sample',
        # 会话id 数字类型，建议使用系统时间戳
        'sessionid': str(ixid),
        # 包id   数字类型  每个会话数字从1开始迭代
        'packageid': pidx,
        # 结束标识 0未结束 1结束
        'over': over
    }
    header = {
        'lenovokey': LENOVO_KEY,
        'secretkey': SECRET_KEY,
        'channel': 'cloudasr'
    }

    try:
        start_time = datetime.datetime.now()
        response = session.post(ASR_URL, headers=header, data=data,
                                files=files, verify=False, timeout=60)
        res = json.loads(response.text)
        end_time = datetime.datetime.now()
        info_text = ("%s [%d]" %
                     (response.text,
                      (end_time - start_time).microseconds / 1000))
        if PRINT_DEBUG_INFO:
            print(info_text)
        if res['status'] != 'success':
            if PRINT_DEBUG_INFO:
                print(response.text)
            return response.text
        return response.text
    except Exception as e:
        if PRINT_DEBUG_INFO:
            print(e)
        return ''


def save_file(file_size, proc_size, buffer_size, start_time,
              raw_text, raw_time, output_file):
    global TOTAL_LINE_NUM

    end_time = datetime.datetime.now()
    info_text = ("Process %.2f%% %.2f minutes speech in %.2f minutes, "
                 "package size %d" %
                 (proc_size * 100.0 / file_size,
                  proc_size / (2 * 16000 * 60),
                  (end_time - start_time).seconds / 60,
                  buffer_size))
    print(info_text)
    if PRINT_DEBUG_INFO:
        print(raw_text)

    # Process SRT information
    temp_text = raw_text.replace('，', '。')
    temp_text = temp_text.replace('！', '。')
    temp_text = temp_text.replace('？', '。')
    raw_lines = temp_text.split('。')
    content_num = 0
    sent_start = 0.0
    if len(raw_time) > 0:
        raw_time_cnt = len(raw_time)
        content_num = int(raw_time[0][0]['NUM'])
        sent_start = float(raw_time[0][0]['SENTENCE-START'])
    start_pos = 0
    raw_time_idx = 0
    for line in raw_lines:
        if len(line) == 0:
            break
        ori_line = ''
        cat_line = ''
        for ch in line:
            if not ch.isdigit() and ch != ' ':
                ori_line += ch
        line_st = ''
        line_ed = ''
        for idx in range(start_pos, content_num):
            words = raw_time[raw_time_idx][idx + 1]['content']
            st_time = raw_time[raw_time_idx][idx + 1]['startTime']
            ed_time = raw_time[raw_time_idx][idx + 1]['endTime']
            if len(line_st) == 0:
                line_st = st_time
            line_ed = ed_time
            if get_digits(words) < 0:
                cat_line += words
            if ori_line[(-1 * len(words)):] == words or \
               len(cat_line) > len(ori_line):
                start_pos = idx + 1
                break

        if len(line_st) == 0 or len(line_ed) == 0:
            continue

        if OUTPUT_FILETYPE == FILETYPE.LRC:
            line_st = datetime.datetime.utcfromtimestamp(
                float(line_st) + sent_start)
            line_st = line_st.strftime('%M:%S.%f')
            line_st = line_st[:(len(line_st)-4)]
            output_file.write('[%s]%s\n' % (line_st, line))

        if OUTPUT_FILETYPE == FILETYPE.SRT:
            line_st = datetime.datetime.utcfromtimestamp(
               float(line_st) + sent_start)
            line_st = line_st.strftime('%H:%M:%S,%f')
            line_st = line_st[:(len(line_st)-3)]
            line_ed = datetime.datetime.utcfromtimestamp(
               float(line_ed) + sent_start)
            line_ed = line_ed.strftime('%H:%M:%S,%f')
            line_ed = line_ed[:(len(line_ed)-3)]

            output_file.write('%d\n' % TOTAL_LINE_NUM)
            output_file.write('%s --> %s\n' % (line_st, line_ed))
            output_file.write(line + '\n')
            output_file.write('\n')

        print('%d' % TOTAL_LINE_NUM)
        print('%s --> %s' % (line_st, line_ed))
        print(line)
        print('\n')
        TOTAL_LINE_NUM += 1

        if start_pos < content_num:
            continue
        if raw_time_idx + 1 >= raw_time_cnt:
            break
        start_pos = 0
        raw_time_idx = raw_time_idx + 1
        content_num = int(raw_time[raw_time_idx][0]['NUM'])
        sent_start = float(raw_time[raw_time_idx][0]['SENTENCE-START'])

    if OUTPUT_FILETYPE == FILETYPE.TXT:
        output_file.write(raw_text)
    if WRITE_DEBUG_INFO:
        output_file.write('\n')
        output_file.write(info_text + '\n')
    output_file.flush()


def get_digits(str):
    zhong = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
             '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    danwei = {'十': 10, '百': 100, '千': 1000, '万': 10000, '亿': 100000000}
    num = 0
    if len(str) == 0:
        return num
    temp = 0
    if str[0] == '十':
        num = 10
    not_digit = False
    for i in str:
        not_hit = False
        if i == '零':
            temp = zhong[i]
        elif i == '一':
            temp = zhong[i]
        elif i == '二':
            temp = zhong[i]
        elif i == '三':
            temp = zhong[i]
        elif i == '四':
            temp = zhong[i]
        elif i == '五':
            temp = zhong[i]
        elif i == '六':
            temp = zhong[i]
        elif i == '七':
            temp = zhong[i]
        elif i == '八':
            temp = zhong[i]
        elif i == '九':
            temp = zhong[i]
        else:
            not_hit = True

        if i == '十':
            temp = temp * danwei[i]
            num += temp
        elif i == '百':
            temp = temp * danwei[i]
            num += temp
        elif i == '千':
            temp = temp * danwei[i]
            num += temp
        elif i == '万':
            temp = temp * danwei[i]
            num += temp
        elif i == '亿':
            temp = temp * danwei[i]
            num += temp
        else:
            if not_hit:
                not_digit = True
    if str[len(str)-1] != '十' and str[len(str)-1] != '百' and \
       str[len(str)-1] != '千' and str[len(str)-1] != '万' and \
       str[len(str)-1] != '亿':
        num += temp
    if not_digit:
        num = -1
    return num


if __name__ == '__main__':

    print("*******************************************************")
    print("*                                                     *")
    print("*                  OFFLINE ASR TOOLS                  *")
    print("*                                                     *")
    print("*     (c)2020 Voice Tech, AI Lab, Lenovo Research     *")
    print("*                                                     *")
    print("*******************************************************")

    parser = argparse.ArgumentParser(
        description='Welcome to use ASR tools of Lenovo voice technology.')
    parser.add_argument('--srt', action='store_true',
                        help='Save recognized results in srt format')
    parser.add_argument('--lrc', action='store_true',
                        help='Save recognized results in lrc format')
    parser.add_argument('--debug', action='store_true',
                        help='Write debug information into output file')
    parser.add_argument('input_filename', type=str,
                        help='Input audio file name')
    parser.add_argument('output_filename', type=str,
                        help='Output audio file name')
    args = parser.parse_args()

    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
            LENOVO_KEY = config['lenovokey']
            SECRET_KEY = config['secretkey']
    except OSError:
        print("Can't open config file:", CONFIG_FILE)
        sys.exit(0)

    AUDIO_FILE = args.input_filename
    OUTPUT_FILE = args.output_filename
    PRINT_DEBUG_INFO = args.debug
    WRITE_DEBUG_INFO = args.debug
    if args.srt:
        OUTPUT_FILETYPE = FILETYPE.SRT
    if args.lrc:
        OUTPUT_FILETYPE = FILETYPE.LRC
    ASR_URL = 'https://voice.lenovomm.com/lasf/cloudasr'
    speech_data = []

    buffer_size = 16 * 2 * 500      # 每毫秒16个short数值

    try:
        file_size = os.path.getsize(AUDIO_FILE)
    except Exception as e:
        print(e)
        sys.exit(0)
    ixid = int(time.time() * 208)
    pidx = 1
    proc_size = 0
    run_time = datetime.datetime.now()
    start_time = datetime.datetime.now()
    session = requests.session()

    with open(AUDIO_FILE, 'rb') as speech_file, \
            open(OUTPUT_FILE, 'w') as output_file:
        speech_data = speech_file.read(buffer_size)
        if WRITE_DEBUG_INFO:
            output_file.write(time.strftime('Start at %H:%M:%S\n',
                              time.localtime(time.time())))
        while speech_data != b'':
            proc_size = proc_size + len(speech_data)
            http_ret = recoginse(session, ixid, pidx, 0, speech_data)
            if len(http_ret) > 0:
                raw_text = http_ret
                try:
                    res = json.loads(http_ret)
                    raw_text = res['rawText']
                    raw_type = res['rawType']
                    status = res['status']
                    desc = res['desc']
                    if status == 'failed' or status == 'faild':
                        print('Exit(%d): ixid %d, pidx %d %s' %
                              (sys._getframe().f_lineno, ixid, pidx, desc))
                        print(http_ret)
                        if WRITE_DEBUG_INFO:
                            output_file.write(time.strftime(
                                              'Exit at %H:%M:%S\n',
                                              time.localtime(time.time())))
                        sys.exit(0)
                    if raw_type == 'final' and len(raw_text) > 0:
                        if PRINT_DEBUG_INFO:
                            print(http_ret)
                        save_file(file_size, proc_size, buffer_size,
                                  start_time, raw_text,
                                  res['rawTime'], output_file)
                    pidx += 1
                    speech_data = speech_file.read(buffer_size)
                except Exception as e:
                    if PRINT_DEBUG_INFO:
                        print(e)
                    save_file(file_size, proc_size, buffer_size, start_time,
                              raw_text, '', output_file)
                    info_text = ('Exit when ixid %d pidx %d' % (ixid, pidx))
                    if WRITE_DEBUG_INFO:
                        output_file.write(info_text + '\n')
                    output_file.flush()
                    print('Exit(%d): %s\n%s' %
                          (sys._getframe().f_lineno, info_text, str(e)))
                    if WRITE_DEBUG_INFO:
                        output_file.write(time.strftime('Exit at %H:%M:%S\n',
                                          time.localtime(time.time())))
                    sys.exit(0)
            else:
                if WRITE_DEBUG_INFO:
                    save_file(file_size, proc_size, buffer_size,
                              start_time, 'INTERNET CONNECTION ERROR!',
                              '', output_file)
                info_text = ("Timeout when ixid %d pidx %d" % (ixid, pidx))
                if WRITE_DEBUG_INFO:
                    output_file.write(info_text + '\n')
                output_file.flush()
                proc_size = proc_size - len(speech_data)

    if PRINT_DEBUG_INFO:
        print('Process last http post request.')
    http_ret = recoginse(session, ixid, pidx, 1, b'0')
    if len(http_ret) == 0:
        if PRINT_DEBUG_INFO:
            print('Retry last http post request.')
        http_ret = recoginse(session, ixid, pidx, 1, b'0')
    if len(http_ret) > 0:
        if PRINT_DEBUG_INFO:
            print(http_ret)
        res = json.loads(http_ret)
        raw_text = res['rawText']
        raw_type = res['rawType']

        with open(OUTPUT_FILE, 'a+') as output_file:
            if len(raw_text) > 0:
                save_file(file_size, proc_size, buffer_size,
                          start_time, raw_text, res['rawTime'], output_file)

    with open(OUTPUT_FILE, 'a+') as output_file:
        secs = (datetime.datetime.now() - run_time).seconds
        info_text = ('Total run %.2f minutes, RTF %.2f.' %
                     (secs / 60, secs / (file_size / (2 * 16000))))
        print(info_text)
        if WRITE_DEBUG_INFO:
            output_file.write(info_text + '\n')
            output_file.write(time.strftime('End at %H:%M:%S\n',
                              time.localtime(time.time())))
        output_file.flush()

    session.close()
