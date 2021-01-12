import pendulum

ALIPAY_APP_ID = ""
ALIPAY_PUBLIC_KEY = ''
ALIPAY_APP_PRIVATE_KEY = ''
ALIPAY_APP_PUBLIC_KEY = ''

from easy_pay.ali_pay import Alipay

alipay = Alipay(
    is_sandbox=False,
    app_id=ALIPAY_APP_ID,
    alipay_public_key=ALIPAY_PUBLIC_KEY,
    app_private_key=ALIPAY_APP_PRIVATE_KEY
)
now = pendulum.now()


def test_page_pay():
    r = alipay.page_pay(
        subject='糖果',
        price=1,
        trade_no=f"{now}",
        return_url='https://www.baidu.com',
        # notice_url='https://www.baidu.com',
        describe='好吃的糖果',
    )
    print(r)


def test_wap_pay():
    r = alipay.wap_pay(
        subject='糖果',
        price=1,
        trade_no=f"{now}",
        return_url='https://www.baidu.com',
        # notice_url='https://www.baidu.com',
        describe='好吃的糖果',
        quit_url='https://www.baidu.com'
    )
    print(r)


def test_pay():
    for m in ('page', 'wap'):
        r = alipay.pay(
            method=m,
            subject='糖果',
            price=1,
            trade_no=f"{now}",
            return_url='https://www.baidu.com',
            # notice_url='https://www.baidu.com',
            describe='好吃的糖果',
            quit_url='https://ydassess.com'
        )
        print(r)
