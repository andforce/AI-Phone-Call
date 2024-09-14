import threading
import time

import serial
from LiveData import LiveData
import logger


class AudioHelper:
    def __init__(self, audio_ser=None, baud_rate=115200):
        try:
            self.audio_ser = serial.Serial(audio_ser, baud_rate, timeout=1)
        except Exception as e:
            logger.e("初始化音频串口失败：" + str(e))
        self.is_calling = False
        self.call_audio_data_read_thread = None
        self.call_audio_data_livedata = LiveData()

    def __read_audio_data(self):
        while self.is_calling:
            data = self.audio_ser.read(640)
            if data and data != b'':
                self.call_audio_data_livedata.value = data
            time.sleep(0.01)
        logger.i("通话结束，循环读取音频数据已经结束")

    def write_audio_data(self, data):
        self.audio_ser.write(data)

    def start_audio_read_thread(self):
        if self.call_audio_data_read_thread is not None:
            logger.i("音频读取线程已经启动，无需重复启动")
            return
        logger.d("启动音频读取线程，开始读取音频数据")
        self.is_calling = True
        self.call_audio_data_read_thread = threading.Thread(target=self.__read_audio_data)
        self.call_audio_data_read_thread.start()

    def stop_audio_read_thread(self):
        self.is_calling = False
        self.call_audio_data_read_thread = None
        logger.d("停止读取音频的线程")
