import logger
import time


class SendCommandHelper:
    def __init__(self, at_ser, sms_helper, call_helper):
        self.at_ser = at_ser
        self.wait_result_at_command = None
        self.wait_result_at_command_result = None
        self.sms_helper = sms_helper
        self.call_helper = call_helper

    def write_at_command(self, command, delay=0.1):
        if self.at_ser is None:
            logger.e("AT串口未初始化")
            return
        # delay 不等于0时，等待delay秒
        if delay != 0:
            time.sleep(delay)
        self.wait_result_at_command = command
        logger.i("|>> " + command)
        self.at_ser.write((command + "\r").encode())
        self.at_ser.flush()

    def handle_command_result(self, response):
        if self.wait_result_at_command is not None:
            if self.wait_result_at_command_result is None:
                # logger.i("decode_string:" + decode_string + " wait_result_at_command:" + self.wait_result_at_command)
                if response == self.wait_result_at_command or self.wait_result_at_command == "ATA":
                    # ATA 命令比较特殊，成功返回OK，没有命令名称
                    # 读到这只一行结果，等于发出的AT指令，说明后续的这一行肯定是根这个指令相关
                    self.wait_result_at_command_result = response
                    return True
                else:
                    # 如果不等于，那大概率是由于SIM状态发生变化而主动通知的，不是我们发出的指令的结果
                    # __other_result += decode_string + " > "
                    # logger.e("未知的AT指令结果1：" + decode_string + " ")
                    return False
            else:
                if response == "OK" or response == "ERROR":
                    self.wait_result_at_command_result += " > " + response
                    logger.d("<<| " + self.wait_result_at_command_result + "\n")

                    if self.wait_result_at_command_result.startswith("AT+CMGL=4"):
                        ''' 读取所有短信 '''
                        self.sms_helper.read_all_sms(self.wait_result_at_command_result)
                    elif self.wait_result_at_command_result.startswith("AT+CMGR="):
                        ''' 读取一条短信 '''
                        self.sms_helper.read_one_sms(self.wait_result_at_command_result)

                    # 打印完毕，清空，等待下次AT指令
                    self.wait_result_at_command_result = None
                    self.wait_result_at_command = None
                else:
                    self.wait_result_at_command_result += " > " + response
                return True
        else:
            return False
