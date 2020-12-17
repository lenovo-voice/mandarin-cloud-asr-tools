# 联想语音技术平台工具包

## 概述

联想语音技术平台在联想集团内部被广泛地应用于多种业务，包括联想手机、平板、个人电脑等。

## 官网地址
因安全策略，请复制至浏览器地址栏访问

https://voice.lenovomm.com/voicePlatform/welcome/index.html

## 1. 开发者账号申请
第一步需要在官网注册账号，并在开发者账号页面获取联想密钥AK和安全密钥SK。

## 2. Python 客户端
使用前需要先申请开发者账号，并确认config.yml文件填入了有效的AK和SK。
### 用途
转写录音文件、为视频生成字幕等。
### 命令行参数
usage: offline-asr.py [-h] [--srt] [--lrc] [--debug]
                      input_filename output_filename

必选参数:
参数 | 描述
---|---
input_filename | 输入语音文件
output_filename | 输出文本文件

可选参数:
参数 | 描述
---|---
-h, --help | 显示帮助信息并退出
--srt | 使用SRT格式保存识别结果
--lrc | 使用LRC格式保存识别结果
--debug | 在输出文本文件里保存调试信息

## 3. 平台参数说明
Python客户端源码内已设置。

### 首部(header):<br>

   编码 |  名称  | 描述
   ---: | :----- | :-----
   channel | 来源标识 | 用于标识外部来源的用户，值暂固定cloudasr<br/>
   lenovokey | 账号公钥 | 需从我们的官网注册账号后，即可得到<br/>
   secretkey | 账号私钥 | 需从我们的官网注册账号后，即可得到<br/>

### 请求参数(body):<br/>

   编码 |  名称  | 描述
   ---: | :----- | :-----
   scene |  语音场景 | 长语音是long，短语音是short，默认短语音
   language | 音频语言 | 目前只支持中英文，英文english，中文chinese，默认中文
   sample | 语音通道数 | 目前只对外开放单通道，值为1
   audioFormat | 语音格式 | pcm_16000_16bit_sample 为 16000，16bit，单声道的pcm格式语音 <br> pcm_8000_16bit_sample 为 8000，16bit，单声道的pcm格式语音 <br> alaw_8000_16bit_sample 为 8000，16bit，单声道的alaw格式语音 <br> ulaw_8000_16bit_sample 为 8000，16bit，单声道的ulaw格式语音

有任何问题，请在官网或GITHUB留言。