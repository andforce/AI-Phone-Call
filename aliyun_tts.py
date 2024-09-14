import threading

import nls
from LiveData import LiveData
from nls.token import getToken
import logger
from Config import Config


class Tts:
    def __init__(self, tid):
        self.__id = tid
        self.tts_result_livedata = LiveData()
        self.tts_status_livedata = LiveData()
        self.is_call_stop = False

    def start(self, text):
        self.is_call_stop = False
        self.__text = text
        self.__th = threading.Thread(target=self.__test_run)
        self.__th.start()
        self.tts_status_livedata.value = "start"

    def stop(self):
        self.is_call_stop = True
        try:
            self.tts.shutdown()
        except Exception as e:
            logger.e("tts shutdown error:{}".format(e))

    def test_on_metainfo(self, message, *args):
        logger.e("TTS :on_metainfo message=>{}".format(message))

    def test_on_error(self, message, *args):
        logger.e("TTS :on_error args=>{}".format(args))
        self.tts_status_livedata.value = "error"

    def test_on_close(self, *args):
        logger.e("TTS :on_close: args=>{}".format(args))
        self.tts_status_livedata.value = "close"

    def test_on_data(self, data, *args):
        # logger.i("tts on_data, len:{}".format(len(data)))
        if self.is_call_stop:
            logger.e("TTS :通话已经停止，不需要把TTS的语音发送给设备")
            return
        self.tts_result_livedata.value = data
        self.tts_status_livedata.value = "data"

    def test_on_completed(self, message, *args):
        logger.e("TTS :on_completed:args=>{} message=>{}".format(args, message))
        self.tts_status_livedata.value = "completed"

    def __test_run(self):
        if self.is_call_stop:
            logger.e("TTS :通话已经停止，不需要TTS")
            return

        config = Config.get_instance()
        URL = config.get("service_url")
        APPKEY = config.get("app_key")
        ak_id = config.get("ak_id")
        ak_secret = config.get("ak_secret")

        token = getToken(ak_id, ak_secret)

        logger.i("TTS :获取到的token:{}".format(token))

        logger.i("TTS :thread:{} start..".format(self.__id))
        self.tts = nls.NlsSpeechSynthesizer(
            url=URL,
            token=token,
            appkey=APPKEY,
            long_tts=False,
            on_metainfo=self.test_on_metainfo,
            on_data=self.test_on_data,
            on_completed=self.test_on_completed,
            on_error=self.test_on_error,
            on_close=self.test_on_close,
            callback_args=[self.__id]
        )

        # https://ai.aliyun.com/nls/tts?spm=5176.11801677.help.50.2b523adddCLUlp
        r = self.tts.start(self.__text, sample_rate=8000, voice="zhiyuan", ex={'enable_subtitle': False})
        logger.i("TTS :{}: tts done with result:{}".format(self.__id, r))
