# _*_ coding : UTF-8 _*_
# @Time : 2025/08/04 01:26
# @UpdateTime : 2025/08/04 01:26
# @Author : sonder
# @File : captcha.py
# @Software : PyCharm
# @Comment : 本程序
import base64
import io
import os
import random
import string

from PIL import Image, ImageDraw, ImageFont
from fastapi import Request

from utils.get_redis import RedisKeyConfig


class CaptchaUtil:
    """
    验证码类
    """

    @classmethod
    async def create_captcha(cls, captcha_type: str = "0"):
        """
        生成验证码
        :param captcha_type: 验证码类型，0为算术题验证码，1为字母数字混合验证码
        :return: 验证码图片和验证码答案（[base64图片字符串, 答案]）
        """
        # 创建空白图像
        image = Image.new('RGB', (120, 40), color='#EAEAEA')
        draw = ImageDraw.Draw(image)

        # 设置字体
        font_path = os.path.join(os.path.abspath(os.getcwd()), 'assets', 'font', 'MiSans-Medium.ttf')
        font = ImageFont.truetype(font_path, size=25)

        if captcha_type == '0':
            # 算术题验证码：生成两个0-9之间的随机整数
            num1 = random.randint(0, 9)
            num2 = random.randint(0, 9)
            # 从运算符列表中随机选择一个
            operational_character_list = ['+', '-', '*']
            operational_character = random.choice(operational_character_list)
            # 根据选择的运算符进行计算
            if operational_character == '+':
                result = str(num1 + num2)
            elif operational_character == '-':
                result = str(num1 - num2)
            else:
                result = str(num1 * num2)
            # 生成算术题文本
            text = f'{num1} {operational_character} {num2} = ?'
            # 计算文本宽度以居中显示
            text_width = draw.textlength(text, font=font)
            x = (120 - text_width) / 2
            draw.text((x, 5), text, fill='blue', font=font)
        else:
            # 字母数字混合验证码：生成随机字母和数字组合（4位）
            result = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
            # 绘制每个字符，并添加随机旋转和倾斜
            x = 10
            for char in result:
                # 创建单个字符的图像
                char_image = Image.new('RGBA', (25, 40), color=(234, 234, 234, 0))
                char_draw = ImageDraw.Draw(char_image)
                char_draw.text((0, 0), char, font=font, fill=(0, 0, 255))
                # 随机旋转字符
                char_image = char_image.rotate(random.randint(-40, 40), expand=1)
                # 随机倾斜字符
                char_image = char_image.transform(char_image.size, Image.AFFINE,
                                                  (1, random.uniform(-0.3, 0.3), 0, 0, 1, 0))
                # 将字符粘贴到主图像上
                image.paste(char_image, (x, 0), char_image)
                x += 25
        # 添加干扰元素
        cls._add_noise(image)
        cls._add_lines(image)

        # 将图像数据保存到内存中
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')

        # 将图像数据转换为base64字符串
        base64_string = base64.b64encode(buffer.getvalue()).decode()

        return [base64_string, result]

    @staticmethod
    def _add_noise(image):
        """
        添加噪点干扰
        """
        draw = ImageDraw.Draw(image)
        for _ in range(100):  # 添加100个噪点
            x = random.randint(0, 120)
            y = random.randint(0, 40)
            draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    @staticmethod
    def _add_lines(image):
        """
        添加干扰线
        """
        draw = ImageDraw.Draw(image)
        for _ in range(5):  # 添加5条干扰线
            x1 = random.randint(0, 120)
            y1 = random.randint(0, 40)
            x2 = random.randint(0, 120)
            y2 = random.randint(0, 40)
            draw.line((x1, y1, x2, y2),
                      fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
                      width=1)

    @classmethod
    async def verify_code(cls, request: Request, code: str, session_id: str) -> dict:
        """
        验证验证码
        :param request
        :param code: 验证码（用户输入）
        :param session_id: 会话ID
        """
        redis_code = await request.app.state.redis.get(f"{RedisKeyConfig.CAPTCHA_CODES.key}:{session_id}")
        if redis_code is None:
            return {
                "status": False,
                "msg": "验证码已过期"
            }
        
        # 统一转换为字符串进行比较（支持算术题和字母数字两种类型）
        redis_code_str = str(redis_code).strip()
        code_str = str(code).strip()
        
        # 不区分大小写比较
        if redis_code_str.lower() == code_str.lower():
            await request.app.state.redis.delete(f"{RedisKeyConfig.CAPTCHA_CODES.key}:{session_id}")
            return {
                "status": True,
                "msg": "验证码正确"
            }
        return {
            "status": False,
            "msg": "验证码错误"
        }
