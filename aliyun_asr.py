import time
import threading

from nls.token import getToken
import logger
import nls

from LiveData import LiveData
from Config import Config


class Asr:
    def __init__(self, tid):
        self.__th = None
        self.read_buffer = None
        self.__id = tid

        config = Config.get_instance()
        URL = config.get("service_url")
        APPKEY = config.get("app_key")
        ak_id = config.get("ak_id")
        ak_secret = config.get("ak_secret")

        TOKEN = getToken(ak_id, ak_secret)
        logger.i("ASR :获取到的token:{}".format(TOKEN))

        self.sr = nls.NlsSpeechTranscriber(
            url=URL,
            token=TOKEN,
            appkey=APPKEY,
            on_sentence_begin=self.test_on_sentence_begin,
            on_sentence_end=self.test_on_sentence_end,
            on_start=self.test_on_start,
            on_result_changed=self.test_on_result_chg,
            on_completed=self.test_on_completed,
            on_error=self.test_on_error,
            on_close=self.test_on_close,
            callback_args=[self.__id]
        )
        self.data_buffer = []
        self.thread_start = False
        self.data_buffer_lock = threading.Lock()
        self.asr_result_livedata = LiveData()
        self.asr_status_livedata = LiveData()

    def start(self):
        self.thread_start = True
        self.__th = threading.Thread(target=self.__test_run)
        self.__th.start()
        self.read_buffer = threading.Thread(target=self.__read_buffer)
        self.read_buffer.start()
        self.asr_status_livedata.value = "start"

    def __read_buffer(self):
        while self.thread_start:
            if len(self.data_buffer) >= 640:
                with self.data_buffer_lock:
                    data = self.data_buffer[:640]
                    del self.data_buffer[:640]
                    # logger.i("send audio data length:{}".format(len(data)))
                    # logger.i(
                    #     "从音频Buffer中开始读取PCM数据，发送给阿里云实时转文字： length:{}".format(len(self.data_buffer)))
                    self.sr.send_audio(data)
                time.sleep(0.01)
            else:
                time.sleep(0.01)

    def send_audio(self, data: bytes):
        # 把data 中的数据放到data_buffer中
        with self.data_buffer_lock:
            self.data_buffer.extend(data)

    def stop(self):
        # self.sr.ctrl(ex={"test": "tttt"})
        try:
            if self.thread_start:
                self.thread_start = False
                r = self.sr.stop()
                logger.e("ASR :{}: sr stopped:{}".format(self.__id, r))
                time.sleep(1)
        except Exception as e:
            logger.e("ASR :sr stop error:{}".format(e))
        self.__th = None
        self.read_buffer = None

    def test_on_sentence_begin(self, message, *args):
        logger.i("ASR :test_on_sentence_begin:{}".format(message))
        self.asr_status_livedata.value = "begin"

    def test_on_sentence_end(self, message, *args):
        """
        一句话识别完毕
        """
        logger.i("ASR :test_on_sentence_end:{}".format(message))
        self.asr_result_livedata.value = message
        self.asr_status_livedata.value = "end"

    def test_on_start(self, message, *args):
        logger.i("ASR :test_on_start:{}".format(message))
        self.asr_status_livedata.value = "start"

    def test_on_error(self, message, *args):
        logger.e("ASR :on_error args=>{}".format(args))
        self.asr_status_livedata.value = "error"

    def test_on_close(self, *args):
        logger.i("ASR :on_close: args=>{}".format(args))

    def test_on_result_chg(self, message, *args):
        logger.i("ASR :test_on_chg:{}".format(message))

    def test_on_completed(self, message, *args):
        logger.i("ASR :on_completed:args=>{} message=>{}".format(args, message))

    def __test_run(self):
        logger.d("ASR :thread:{} start..".format(self.__id))

        self.sr.start(aformat="pcm",
                      sample_rate=16000 / 2,
                      enable_intermediate_result=True,
                      enable_punctuation_prediction=True,
                      enable_inverse_text_normalization=True)


if __name__ == "__main__":
    nls.enableTrace(False)
    t = Asr("thread_1")
    t.start()
