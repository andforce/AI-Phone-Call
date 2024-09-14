from LiveData import LiveData
from VoiceCall import VoiceCall
import threading
import time
import logger
from audio_resource import say_hello_pcm_file


class CallHelper:
    def __init__(self, at_serial_helper, audio_helper):
        self.at_serial_helper = at_serial_helper
        self.pickup_lock = threading.Lock()
        self.call_status = LiveData()
        self.is_pickup = False
        self.ring_count = 0
        self.say_hello_pcm_file = say_hello_pcm_file()
        self.audio_helper = audio_helper

    def __call_no_carrier(self):
        with self.pickup_lock:
            if self.is_pickup:
                self.is_pickup = False
                self.call_status.value = VoiceCall(VoiceCall.VOICE_CALL_NO_CARRIER)
                self.at_serial_helper.send_command_helper.write_at_command("AT+CPCMREG=0", delay=1.5)

    def __call_start(self):
        time.sleep(0.1)  # 等ATA命令返回OK，以保证Log打印的时间顺序看起来是对的
        self.call_status.value = VoiceCall(VoiceCall.VOICE_CALL_BEGIN)
        self.is_pickup = True

    def __call_end(self):
        with self.pickup_lock:
            if self.is_pickup:
                self.is_pickup = False
                self.call_status.value = VoiceCall(VoiceCall.VOICE_CALL_END)
                self.at_serial_helper.send_command_helper.write_at_command("AT+CPCMREG=0", delay=1.5)

    def __call_missed(self):
        self.is_pickup = False
        self.call_status.value = VoiceCall(VoiceCall.VOICE_CALL_MISSED)

    def __pick_up_inner(self):
        self.is_pickup = True
        self.ring_count = 0
        # 等待0.5秒，等待音频串口准备好, 否则串口可能返回ERROR
        self.at_serial_helper.send_command_helper.write_at_command("AT+CPCMREG=1", delay=0.5)
        time.sleep(0.6)
        # 去读取音频数据， 每次读取640字节
        with open(self.say_hello_pcm_file, "rb") as f:
            while self.is_pickup:
                data = f.read(640)
                if not data:
                    break
                self.audio_helper.write_audio_data(data)
                time.sleep(0.01)
        time.sleep(0.5)
        self.call_status.value = VoiceCall(VoiceCall.VOICE_CALL_SAY_HELLO_DONE)

    def pick_up(self, say_hello_pcm_file):
        logger.d("发送 ATA 命令，接听电话")
        self.at_serial_helper.send_command_helper.write_at_command("ATA", delay=0)
        threading.Thread(target=self.__pick_up_inner).start()

    def hang_up(self):
        logger.d("发送 ATH 命令，挂断电话")
        self.is_pickup = False
        self.at_serial_helper.send_command_helper.write_at_command("ATH", delay=0)
        # self.call_status.value = VoiceCall(VoiceCall.VOICE_CALL_END)

    def is_in_voice_calling(self):
        return self.is_pickup

    def handle_call(self, decode_string):
        # logger.e("AT串口返回：" + decode_string)
        if (decode_string.find("RING") != -1) and (not self.is_pickup):
            self.call_status.value = VoiceCall(VoiceCall.VOICE_CALL_RING)
            # logger.i("收到1 ： " + decode_string)
            return True
        # 判断字符串是不是以 +CLIP: 开头
        elif decode_string.startswith("+CLIP: \"") and (not self.is_pickup):  # +CLIP: "13200000000",161,,,,0
            # logger.i("收到2 ： " + decode_string)
            """
            Calling Line Identification Presentation
            允许在接收电话呼叫时，接收方可以看到呼叫方的电话号码。
            """
            self.ring_count += 1
            if decode_string.find('"') != -1:
                split_strings = decode_string.split('"')
                if len(split_strings) >= 2:
                    phone_number = split_strings[1]
                    self.call_status.value = VoiceCall(status=VoiceCall.VOICE_CALL_CLIP,
                                                       phone_number=phone_number, ring_count=self.ring_count)
                    return True
            self.call_status.value = VoiceCall(status=VoiceCall.VOICE_CALL_CLIP, phone_number="UNKNOWN",
                                               ring_count=self.ring_count)
            return True
        elif decode_string.find("VOICE CALL: BEGIN") != -1:
            # logger.i("收到3 ： " + decode_string)
            threading.Thread(target=self.__call_start).start()
            return True
        elif decode_string.find("VOICE CALL: END:") != -1:
            # logger.i("收到4 ： " + decode_string)
            threading.Thread(target=self.__call_end).start()
            return True
        elif decode_string.find("MISSED_CALL:") != -1:
            # logger.i("收到5 ： " + decode_string)
            threading.Thread(target=self.__call_missed).start()
            return True
        elif decode_string.find("NO CARRIER") != -1:
            # logger.i("收到6 ： " + decode_string)
            threading.Thread(target=self.__call_no_carrier).start()
            return True
        else:
            return False

    def prepare(self):
        # 启动线程
        self.at_serial_helper.send_command_helper.write_at_command("AT+CLIP=?")

        self.at_serial_helper.send_command_helper.write_at_command("AT+CLIP=1")
        # write_at_command("AT+CPCMFRM=1") 设置采样率为16k，默认为8k https://techship.com/support/faq/voice-calls-and-usb-audio/

        self.at_serial_helper.send_command_helper.write_at_command("AT+CNMP=?")
        self.at_serial_helper.send_command_helper.write_at_command("AT+CNMP=2")

        self.at_serial_helper.send_command_helper.write_at_command("AT+CPCMREG=?")

        # 主要改善TDD noise效果
        self.at_serial_helper.send_command_helper.write_at_command("AT^PWRCTL=0,1,3")
        # 重置状态
        self.at_serial_helper.send_command_helper.write_at_command("AT+CPCMREG=0")
