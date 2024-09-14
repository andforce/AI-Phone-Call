import os

import logger
import notify_to_master
from AtSerialHelper import AtSerialHelper
from AudioHelper import AudioHelper
from VoiceCall import VoiceCall
from aliyun_asr import Asr
from aliyun_tts import Tts
import json
from AI import AI
from audio_resource import say_hello_pcm_file


class Main:
    def __init__(self):
        self.tts: Tts
        self.asr: Asr
        self.ai = AI()
        self.at_serial_helper = None
        self.audio_helper = None
        self.is_wait_tts_back = False
        self.is_ai_speaking = False
        self.call_from_number = None

    def handle_call_status(self, voice_call: VoiceCall):
        call_status = voice_call.status
        if call_status == VoiceCall.VOICE_CALL_RING:
            logger.i("正在播放来电铃声...")
        elif call_status == VoiceCall.VOICE_CALL_CLIP:
            self.call_from_number = "来电号码: " + voice_call.phone_number
            logger.i(self.call_from_number + ", " + "铃声次数: " + str(voice_call.ring_count))
            self.audio_helper.start_audio_read_thread()

            if voice_call.ring_count == 2 and not self.at_serial_helper.call_helper.is_in_voice_calling():
                self.asr.start()  # 开启语音识别线程
                self.at_serial_helper.call_helper.pick_up(say_hello_pcm_file=say_hello_pcm_file())
                self.is_ai_speaking = True
        elif call_status == VoiceCall.VOICE_CALL_BEGIN:
            logger.i("通话开始")
        elif call_status == VoiceCall.VOICE_CALL_SAY_HELLO_DONE:
            logger.i("播放喂，您好完成")
            self.is_ai_speaking = False
        elif (call_status == VoiceCall.VOICE_CALL_END
              or call_status == VoiceCall.VOICE_CALL_MISSED
              or call_status == VoiceCall.VOICE_CALL_NO_CARRIER):

            logger.i("通话结束: " + call_status)
            self.tts.stop()
            self.asr.stop()
            self.audio_helper.stop_audio_read_thread()

            # 去读通话记录，推送给微信
            all_history = self.ai.read_all_call_history()
            notify_to_master.notify(self.call_from_number + "\n" + all_history)
            self.ai.clear_call_history()
        elif call_status == VoiceCall.VOICE_CALL_MISSED:
            logger.i("通话结束: " + call_status)
            self.tts.stop()
            self.asr.stop()
            self.audio_helper.stop_audio_read_thread()

            # 去读通话记录，推送给微信
            notify_to_master.notify("漏接电话：" + self.call_from_number)
        else:
            logger.d("其他状态：" + call_status)

    def handle_call_audio(self, voice_pcm_data):
        if self.at_serial_helper.call_helper.is_in_voice_calling():
            if not self.is_wait_tts_back:
                if not self.is_ai_speaking:
                    self.asr.send_audio(voice_pcm_data)
                else:
                    logger.e("从 USB 串口读取到音频数据，正在AI正在讲话，不用发送给阿里云ASR")
            else:
                logger.e("从 USB 串口读取到音频数据，但正在等待TTS返回，不用发送给阿里云ASR")
        else:
            logger.e("从 USB 串口读取到音频数据，不在通话中，不需要发送音频数据给阿里云ASR")

    def hand_sms_received(self, new_value):
        phone_number = new_value['number']
        time = new_value['time'].strftime('%Y-%m-%d %H:%M:%S')
        text = new_value['text']
        format_sms = phone_number + "\n" + time + "\n------ ------ ------\n" + text

        logger.i(f"开始推送给微信：{format_sms}")
        notify_to_master.notify(format_sms)

    def handle_ai_answer(self, new_value):
        self.text_to_voice(new_value)

    def observe_aliyun_asr_result(self, new_value):
        """
        阿里云语音识别结果
        """
        json_data = json.loads(new_value)
        to_tts_text = json_data['payload']['result']
        if to_tts_text == "嗯。":
            logger.e("只是一个嗯，不需要回答")
        else:
            # 发送给AI，让AI回答
            logger.d("开始发送数据给AI，等待AI回复：" + to_tts_text)
            self.ai.ai(to_tts_text, callback=self.handle_ai_answer)

    def text_to_voice(self, text):
        self.is_wait_tts_back = True
        self.tts.start(text)

    def observe_aliyun_tts_result(self, voice_data):
        self.is_ai_speaking = True
        if self.at_serial_helper.call_helper.is_in_voice_calling():
            self.audio_helper.write_audio_data(voice_data)
        else:
            logger.e("不在通话中，不需要发送TTS音频数据给USB串口")

    def observe_aliyun_tts_status(self, new_value):
        # logger.d("阿里云TTS状态：" + new_value)
        if new_value == "completed" or new_value == "error" or new_value == "close":
            self.is_wait_tts_back = False
            self.is_ai_speaking = False

    def observe_aliyun_asr_status(self, asr_status):
        # logger.d("阿里云ASR状态：" + asr_status)
        pass

    def start_ai_call(self):
        self.asr = Asr("thread_asr")
        self.asr.asr_result_livedata.observe(self.observe_aliyun_asr_result)
        self.asr.asr_status_livedata.observe(self.observe_aliyun_asr_status)

        self.tts = Tts("thread_tts")
        self.tts.tts_result_livedata.observe(self.observe_aliyun_tts_result)
        self.tts.tts_status_livedata.observe(self.observe_aliyun_tts_status)

        # 查看是否存在 /dev/ttyUSB* 设备，判断文件是否存在
        if not os.path.exists('/dev/ttyUSB4') or not os.path.exists('/dev/ttyUSB2'):
            logger.e("串口设备不存在")
            exit(1)
        # os.system("ls -l /dev/ttyUSB*")

        # 执行shell命令，chmod 777 /dev/ttyUSB*，给予USB串口读写权限
        # os.system("sudo chmod 777 /dev/ttyUSB*")

        self.audio_helper = AudioHelper('/dev/ttyUSB4', 115200)
        self.audio_helper.call_audio_data_livedata.observe(self.handle_call_audio)

        self.at_serial_helper = AtSerialHelper('/dev/ttyUSB2', 115200, self.audio_helper)
        self.at_serial_helper.call_helper.call_status.observe(self.handle_call_status)
        self.at_serial_helper.sms_helper.one_sms_livedata.observe(self.hand_sms_received)

        self.at_serial_helper.start_read_serial_thread()
        logger.d("prepare")

    def loop_for_call_in(self):
        self.at_serial_helper.prepare(debug=False)


if __name__ == '__main__':
    main = Main()
    main.start_ai_call()
    main.loop_for_call_in()
