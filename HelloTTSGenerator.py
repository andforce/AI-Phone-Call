import threading

import nls
from nls.token import getToken
from Config import Config

config = Config.get_instance()
TEST_ACCESS_APPKEY = config.get("app_key")  # 使用Config获取app_key

TEXT = '围，您好，我是王先生的私人秘书，您找他有什么事情吗？'


class HelloTTSGenerator:
    def __init__(self, tid, test_file):
        self.__th = threading.Thread(target=self.__test_run)
        self.__id = tid
        self.__test_file = test_file

    def start(self, text):
        self.__text = text
        self.__f = open(self.__test_file, "wb")
        self.__th.start()

    def test_on_metainfo(self, message, *args):
        print("on_metainfo message=>{}".format(message))

    def test_on_error(self, message, *args):
        print("on_error args=>{}".format(args))

    def test_on_close(self, *args):
        print("on_close: args=>{}".format(args))
        try:
            self.__f.close()
        except Exception as e:
            print("close file failed since:", e)

    def test_on_data(self, data, *args):
        try:
            self.__f.write(data)
        except Exception as e:
            print("write data failed:", e)

    def test_on_completed(self, message, *args):
        print("on_completed:args=>{} message=>{}".format(args, message))

    def __test_run(self):
        ak_id = config.get("ak_id")
        ak_secret = config.get("ak_secret")
        info = getToken(ak_id, ak_secret)
        print(info)

        print("thread:{} start..".format(self.__id))
        tts = nls.NlsSpeechSynthesizer(
            token=info,
            appkey=TEST_ACCESS_APPKEY,
            long_tts=False,
            on_metainfo=self.test_on_metainfo,
            on_data=self.test_on_data,
            on_completed=self.test_on_completed,
            on_error=self.test_on_error,
            on_close=self.test_on_close,
            callback_args=[self.__id]
        )

        print("{}: session start".format(self.__id))
        r = tts.start(self.__text, sample_rate=8000, voice="zhiyuan", ex={'enable_subtitle': False})
        print("{}: tts done with result:{}".format(self.__id, r))


if __name__ == '__main__':
    nls.enableTrace(True)
    t = HelloTTSGenerator("thread1", "say_hello.pcm")
    t.start(TEXT)
