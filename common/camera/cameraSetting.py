#! /usr/bin/env python


SETTINGS = [
    "cv.CAP_PROP_POS_MSEC",             # 通常用于视频文件的读取，摄像头不适用，表示当前视频帧的毫秒数
    "cv.CAP_PROP_POS_FRAMES",           # 从0开始的即将被获取和解码的帧序号
    "cv.CAP_PROP_POS_AVI_RATIO",        # 视频文件的相对位置：0=视频开始， 1=视频末尾
    "cv.CAP_PROP_FRAME_WIDTH",          # 帧的宽度
    "cv.CAP_PROP_FRAME_HEIGHT",         # 帧的高度
    "cv.CAP_PROP_FPS",                  # 帧率
    "cv.CAP_PROP_FOURCC",               # 4个字符的编码格式
    "cv.CAP_PROP_FRAME_COUNT",          # 视频文件中的帧的数量
    "cv.CAP_PROP_FORMAT",               # MAT对象的格式，设置为-1来获取未解码的RAW视频流
    "cv.CAP_PROP_MODE",                 # 后端指定值，表示当前的捕获模式
    "cv.CAP_PROP_BRIGHTNESS",           # 帧亮度，仅适用于摄像头
    "cv.CAP_PROP_CONTRAST",             # 帧对比度，仅适用于摄像头
    "cv.CAP_PROP_SATURATION",           # 帧饱和度，仅适用于摄像头
    "cv.CAP_PROP_HUE",                  # 帧色调，仅适用于摄像头
    "cv.CAP_PROP_GAIN",                 # 帧增益，仅适用于摄像头
    "cv.CAP_PROP_EXPOSURE",             # 曝光，仅适用于摄像头
    "cv.CAP_PROP_CONVERT_RGB",          # bool类型，表示图像是否需要转换为RGB
    "cv.CAP_PROP_WHITE_BALANCE_BLUE_U", # 不支持
    "cv.CAP_PROP_WHITE_BALANCE_RED_V",  #
    "cv.CAP_PROP_RECTIFICATION",        #
    "cv.CAP_PROP_MONOCHROME",           #
    "cv.CAP_PROP_SHARPNESS",            #
    "cv.CAP_PROP_AUTO_EXPOSURE",        # 自动曝光
    "cv.CAP_PROP_GAMMA",                #
    "cv.CAP_PROP_TEMPERATURE",          #
    "cv.CAP_PROP_TRIGGER",              #
    "cv.CAP_PROP_TRIGGER_DELAY",        #
    "cv.CAP_PROP_ZOOM",                 # 放大倍数，默认值为100
    "cv.CAP_PROP_FOCUS",                # 聚焦
    "cv.CAP_PROP_GUID",                 # 设备GUID
    "cv.CAP_PROP_ISO_SPEED",            # ISO
    "cv.CAP_PROP_BACKLIGHT",            #
    "cv.CAP_PROP_PAN",                  #
    "cv.CAP_PROP_TILT",                 #
    "cv.CAP_PROP_ROLL",                 #
    "cv.CAP_PROP_IRIS",                 #
    "cv.CAP_PROP_SETTINGS",             #
    "cv.CAP_PROP_BUFFERSIZE",           # opencv缓存的帧的数量，可能不支持设置
    "cv.CAP_PROP_AUTOFOCUS",            # 自动对焦
    "cv.CAP_PROP_SAR_NUM",              #
    "cv.CAP_PROP_SAR_DEN",              #
    "cv.CAP_PROP_BACKEND",              #
    "cv.CAP_PROP_CHANNEL",              #
    "cv.CAP_PROP_AUTO_WB",              # 打开或关闭自动白平衡
    "cv.CAP_PROP_WB_TEMPERATURE",       # 白平衡色温
    "cv.CAP_PROP_CODEC_PIXEL_FORMAT",   #
    "cv.CAP_PROP_BITRATE"               # 视频比特率，kbits/s
]
