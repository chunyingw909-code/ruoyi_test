import re


_ocr = None


def recognize_captcha(image_bytes):
    """识别若依算术或字符验证码，算术题返回计算结果。"""
    text = _engine().classification(image_bytes)
    return captcha_code(text)


def captcha_code(text):
    """把识别文本收成登录接口要的 code。

    算术验证码图片上是算式，Redis 里存的是结果。
    """
    cleaned = (
        str(text)
        .strip()
        .replace(' ', '')
        .replace('？', '')
        .replace('?', '')
        .replace('＝', '')
        .replace('=', '')
        .replace('×', '*')
        .replace('x', '*')
        .replace('X', '*')
        .replace('÷', '/')
    )
    match = re.fullmatch(r'(\d+)([+\-*/])(\d+)', cleaned)
    if match:
        left, operator, right = match.groups()
        first, second = int(left), int(right)
        if operator == '+':
            return str(first + second)
        if operator == '-':
            return str(first - second)
        if operator == '*':
            return str(first * second)
        if second:
            return str(first // second)
    return re.sub(r'[^0-9A-Za-z]', '', str(text))


def _engine():
    global _ocr
    if _ocr is None:
        try:
            import ddddocr
        except ImportError as exc:
            raise RuntimeError(
                '验证码已开启，需要安装 ddddocr 才能登录。'
                '也可以在系统参数里关闭 sys.account.captchaEnabled。'
            ) from exc
        try:
            _ocr = ddddocr.DdddOcr(show_ad=False)
        except TypeError:
            _ocr = ddddocr.DdddOcr()
    return _ocr
