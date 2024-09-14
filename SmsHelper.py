import logger
import re
import pdu_decoder
import time

from LiveData import LiveData
import threading


class SmsHelper:
    def __init__(self, at_command_helper):
        self.at_command_helper = at_command_helper
        self.one_sms_livedata = LiveData()
        self.one_sms_read_lock = threading.Lock()
        self.received_sms = {}

    def __read_all_sms(self, content: str):
        logger.i("读取所有短信：" + content)
        # 使用正则分段解析
        pattern = r"\+CMGL: (\d+),(\d+),\"\",(\d+) > [0-9A-F]+ > "
        matches = re.finditer(pattern, content)

        results = []

        udh_dict = {}
        delete_index_list = []
        for match in matches:
            find_result = match.group(0)
            splits = find_result.split(" > ")
            if len(splits) == 3:
                cmgl = splits[0]
                sms_index_matches = re.finditer(r"(?<=\+CMGL: )\d+(?=,\d+,\"\",\d+)", cmgl)
                sms_index = sms_index_matches.__next__().group(0)
                logger.i(f"短信索引：{sms_index}")

                # 记录要删除的短信索引
                delete_index_list.append(int(sms_index))

                dpu = splits[1]
                decode_result = pdu_decoder.decodeSmsPdu(dpu)
                decode_result["read_id"] = sms_index
                if "udh" in decode_result:
                    """ 如果有分割短信，那么把分割的短信放到字典中 """
                    for udh in decode_result["udh"]:
                        decode_result["udh_index"] = udh.number
                        if udh.reference not in udh_dict:
                            udh_dict[udh.reference] = [decode_result]
                        else:
                            udh_dict[udh.reference].append(decode_result)
                else:
                    """ 如果没有分割短信，那么直接放到结果中 """
                    results.append(decode_result)

        """ 把分割的短信合并 """
        for reference, split_messages_list in udh_dict.items():
            sorted_list = sorted(split_messages_list, key=lambda x: x['udh_index'])
            merge_message = None
            for message in sorted_list:
                if merge_message is None:
                    merge_message = message
                else:
                    merge_message['text'] += message['text']

                # logger.i(f"reference:{reference}, {message}\r\n\r\n")
            del merge_message['udh_index']
            del merge_message['udh']
            results.append(merge_message)

        for result in results:
            logger.i(f"短信内容：{result}")
            self.one_sms_livedata.value = result
        threading.Thread(target=self.__delete_all_sms, args=(delete_index_list,)).start()

    def read_all_sms(self, content: str):
        threading.Thread(target=self.__read_all_sms, args=(content,)).start()

    def __cmti(self, index: str):
        """等待10s，让所有的短信都接收完毕，然后再读取短信"""
        time.sleep(2)
        self.send_read_sms_command(int(index))

    def cmti(self, index: str):
        threading.Thread(target=self.__cmti, args=(index,)).start()

    def __read_one_sms(self, content: str):
        splits = content.split(" > ")
        if len(splits) == 4:
            read_id = int(splits[0].split("=")[1])
            dpu = splits[2]
            decoded_sms = pdu_decoder.decodeSmsPdu(dpu)
            decoded_sms["read_id"] = read_id

            udh_info = decoded_sms["udh"][0] if "udh" in decoded_sms else None

            if udh_info is not None:

                decoded_sms["udh_index"] = udh_info.number

                if udh_info.reference not in self.received_sms or len(self.received_sms[udh_info.reference]) == 0:
                    logger.i(
                        f"收到一条长短信，这是开头第一条，reference:{udh_info.reference} 开始读取下一条：{read_id + 1}")
                    self.received_sms[udh_info.reference] = [decoded_sms]
                    self.send_read_sms_command(read_id + 1, delay=2)
                else:
                    logger.i(
                        f"收到一条长短信，这是其中一个片段，reference:{udh_info.reference}")
                    self.received_sms[udh_info.reference].append(decoded_sms)

                    if len(self.received_sms[udh_info.reference]) == udh_info.parts:
                        """ 如果已经收到所有分割短信，那么合并 """
                        sorted_list = sorted(self.received_sms[udh_info.reference], key=lambda x: x['udh_index'])
                        merge_message = None
                        delete_index_list = []
                        for message in sorted_list:
                            delete_index_list.append(message["read_id"])
                            if merge_message is None:
                                merge_message = message
                            else:
                                merge_message['text'] += message['text']
                        del merge_message['udh_index']
                        del merge_message['udh']
                        self.received_sms[udh_info.reference] = []
                        logger.d(f"已经完整读取一条短信，合并完毕： {merge_message}")
                        self.one_sms_livedata.value = merge_message

                        # 开始删除所有分割短信
                        threading.Thread(target=self.__delete_all_sms, args=(delete_index_list,)).start()
                    else:
                        logger.i(f"开始读取下一条：{read_id + 1}")
                        self.send_read_sms_command(read_id + 1)
            else:
                logger.i(f"短信内容：{read_id}, {decoded_sms}")
                """ 没有分割短信，直接显示 """
                self.one_sms_livedata.value = decoded_sms
                self.delete_sms(read_id)

    def read_one_sms(self, content: str):
        threading.Thread(target=self.__read_one_sms, args=(content,)).start()

    def __delete_sms(self, index: int):
        fix_index = index % 5
        logger.e(f"发送AT+CMGD命令，删除短信：{index}，delay: {fix_index}秒")
        self.at_command_helper.send_command_helper.write_at_command(f"AT+CMGD={index}", delay=fix_index)
        time.sleep(2)
        self.at_command_helper.send_command_helper.write_at_command('AT+CMGL=4')

    def delete_sms(self, index: int):
        threading.Thread(target=self.__delete_sms, args=(index,)).start()

    def __delete_all_sms(self, delete_index_list):
        logger.d(f"删除所有短信：{delete_index_list}")
        if len(delete_index_list) == 0:
            return
        for index in delete_index_list:
            self.__delete_sms(index)
            time.sleep(1)
        time.sleep(2)
        self.at_command_helper.send_command_helper.write_at_command('AT+CMGL=4')

    def send_read_sms_command(self, index: int, delay=1):
        with self.one_sms_read_lock:
            want_read_sms_command = "AT+CMGR=" + str(index)
            if self.at_command_helper.current_write_at_command() == want_read_sms_command:
                logger.e(f"正在读取短信中, 无需重复读取1: {want_read_sms_command}")
                return
            else:
                # 检查 one_sms 中是否已经读取到了
                for reference, message_list in self.received_sms.items():
                    for message in message_list:
                        logger.e(f"message: {message}")
                        if message["read_id"] is not None and message["read_id"] == index:
                            logger.e(f"已经读取过了，无需重复读取2: {want_read_sms_command}")
                            return
                self.at_command_helper.send_command_helper.write_at_command("AT+CMGR=" + str(index), delay=delay)

    def handle_sms(self, decode_string):
        if decode_string.startswith("+SMS FULL"):
            logger.e("短信存储区域已满")
            return True
        elif decode_string.startswith("+CMTI: \""):
            # +CMTI: "ME",5
            logger.e("收到新短信通知：" + decode_string)
            # threading.Thread(target=self.__cmti, args=(decode_string.split(",")[1],)).start()
            self.cmti(decode_string.split(",")[1])
            return True
        return False

    def prepare(self):
        # 设置 UTF16 编码，更好兼容中英文和Emoji
        self.at_command_helper.send_command_helper.write_at_command('AT+CSCS="UCS2"')

        '''
        AT+CMGF=0 是 PDU 模式
        AT+CMGF=1 是 TEXT 模式
        '''
        self.at_command_helper.send_command_helper.write_at_command("AT+CMGF=0")

        ''' 查看短信存储情况'''
        self.at_command_helper.send_command_helper.write_at_command('AT+CMGL=?')

        ''' 设置短信存储区域为"ME", 之后读取短信时，才能读取出来 '''
        self.at_command_helper.send_command_helper.write_at_command('AT+CPMS="ME","ME"')

        '''读取所有短信，包括已读和未读'''
        self.at_command_helper.send_command_helper.write_at_command('AT+CMGL=4')

        # """ 删除一条短信 """
        # # self.at_command_helper.send_command_helper.write_at_command('AT+CMGD=1')
        #
        # """ 从第一条开始，删除所有短信 """
        # self.at_command_helper.send_command_helper.write_at_command('AT+CMGD=1,4')

        # '''读取一条短信'''
        # self.at_command_helper.send_command_helper.write_at_command('AT+CMGR=0')
