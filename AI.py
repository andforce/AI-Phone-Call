from Config import Config
import json
from http import HTTPStatus
import dashscope
import logger

# Proxyman Code Generator (1.0.0): Python + Request
# GET https://chatai.mixerbox.com/api/chat

class AI:
    def __init__(self):
        config = Config.get_instance()
        self.system_prompt = config.get("system_prompt")
        self.say_hello = config.get("say_hello")

        self.system_prompt = [
            {'role': 'system',
             'content': self.system_prompt
             }
        ]

        self.say_hello_prompt = [
            {"role": "assistant",
             "content": self.say_hello
             }
        ]

        self.qa_history = []

    def ai(self, q: str, callback=None):
        self.send_request_aliyun(self.qa_history, q, callback)

    def read_all_call_history(self):
        all_history = self.say_hello_prompt + self.qa_history
        result = ""
        for i in all_history:
            role = i['role']
            if role == "assistant":
                result += "+助理：" + i["content"] + "\n"
            else:
                result += "*对方：" + i["content"] + "\n"
        return result

    def clear_call_history(self):
        self.qa_history = []

    def send_request_aliyun(self, history: list, question: str, callback=None):
        config = Config.get_instance()
        dashscope.api_key = config.get("api_key")  # 修改这里

        q = {"role": "user", "content": question}
        # 从 qa_history 取元素，最多取最后 5 个
        fixed_history = history[-15:]
        prompt = self.system_prompt + self.say_hello_prompt + fixed_history
        prompt.append(q)

        logger.d(f"prompt: {prompt}")

        response = dashscope.Generation.call(
            dashscope.Generation.Models.qwen_plus,
            messages=prompt,
            result_format='message',  # 将返回结果格式设置为 message
        )
        if response.status_code == HTTPStatus.OK:
            logger.e("-----------------------------------1")
            # dict 转 json
            json_str = json.dumps(response, indent=4, ensure_ascii=False)
            logger.i(json_str)

            # 把 response.content 解码成Str
            # 把 response_str 转换成 JSON 对象
            logger.e("-----------------------------------2")
            response_json = json.loads(json_str)
            logger.e("----------------------------------3")
            # logger.d(response_json)
            logger.e("-----------------------------------4")
            # 把 response_json 中的 "output" 字段取出来
            response_output = response_json["output"]
            # 把 response_output 中的 "choices" 字段取出来
            response_choices = response_output["choices"]
            # 把 response_choices 中的第一个元素取出来
            response_choice = response_choices[0]
            # 把 response_choice 中的 "message" 字段取出来
            response_message = response_choice["message"]
            # 把 response_message 中的 "content" 字段取出来
            response_content = response_message["content"]
            # 打印 response_content
            logger.i(response_content)
            self.qa_history.append(q)
            self.qa_history.append(response_message)
            if callback is not None:
                callback(response_content)
        else:
            logger.e('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                response.request_id, response.status_code,
                response.code, response.message
            ))


if __name__ == '__main__':
    ai = AI()
    ai.ai("你好")
