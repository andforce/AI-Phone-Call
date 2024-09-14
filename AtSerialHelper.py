import os
import threading
import time

import serial

import logger
from CallHelper import CallHelper
from SmsHelper import SmsHelper
from SendCommandHelper import SendCommandHelper


class AtSerialHelper:
    def __init__(self, at_ser=None, baud_rate=115200, audio_helper=None):
        try:
            self.at_ser = serial.Serial(at_ser, baud_rate, timeout=2)
        except Exception as e:
            self.at_ser = None
            logger.e("初始化AT串口失败：" + str(e))

        self.is_need_read_at_command_data = False
        self.at_command_read_thread = None

        self.sms_helper = SmsHelper(self)
        self.call_helper = CallHelper(self, audio_helper)

        self.send_command_helper = SendCommandHelper(self.at_ser, self.sms_helper, self.call_helper)

    def read_at_command_data(self):
        if self.at_ser is None:
            logger.e("AT串口未初始化")
            return

        while self.is_need_read_at_command_data:
            try:
                data: bytes = self.at_ser.readline()
                if data is None or data == b'':
                    time.sleep(0.01)
                    continue

                if data == b'\r\n':
                    continue

                data_string = data.decode().strip()
                if data_string == "":
                    continue

                # 开始处理串口数据
                if self.call_helper.handle_call(data_string):
                    continue
                elif self.sms_helper.handle_sms(data_string):
                    continue
                elif self.send_command_helper.handle_command_result(data_string):
                    continue
                else:
                    logger.e("串口读取到数据:" + data_string)
            except Exception as e:
                # 执行lsof，查看串口是否被占用
                logger.e("读取串口数据异常：" + str(e))
                f = os.popen("lsof | grep /dev/ttyUSB2")
                logger.e(f.read())

    def current_write_at_command(self):
        return self.send_command_helper.wait_result_at_command

    def start_read_serial_thread(self):
        if self.at_command_read_thread is not None:
            logger.d("串口读取线程已经启动，无需重复启动")
            return
        self.is_need_read_at_command_data = True
        self.at_command_read_thread = threading.Thread(target=self.read_at_command_data)
        self.at_command_read_thread.start()

    def prepare(self, debug=False):
        self.call_helper.prepare()
        self.sms_helper.prepare()
        # 开启等待接听电话
        if debug:
            try:
                while True:
                    user_input = input("输入命令：\n")
                    if user_input == "\n" or user_input == "":
                        continue
                    self.send_command_helper.write_at_command(user_input)
                    time.sleep(1)
            except KeyboardInterrupt as e:
                logger.e("用户终止程序")
        else:
            self.at_command_read_thread.join()
