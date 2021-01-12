import secrets
from pathlib import Path

import pendulum

from easy_pay.settings import time_zone, order_time_expire
from easy_pay.wechat_pay import WechatPay

key = Path('test/apiclient_key.pem').read_text('utf8')
w = WechatPay(
    private_key=key, mch_id='',
    serial_no='',
    app_id='',
    app_secret=""
)

now = pendulum.now(tz=time_zone)


def test_get_cert():
    cert_url = "https://api.mch.weixin.qq.com/v3/certificates"
    r = w.request(method='GET', url=cert_url)
    assert r.status_code == 200


def test_pc_native():
    trade_order = secrets.token_hex(16)

    native_data = {
        "appid": w.app_id,
        "mchid": w.mch_id,
        "description": 'Image',
        "out_trade_no": trade_order,
        "time_expire": f"{now.add(seconds=order_time_expire)}",
        "notify_url": 'https://www.baidu.com',
        "amount": {
            "total": 1,
            "currency": "CNY"
        }
    }
    native_url = "https://api.mch.weixin.qq.com/v3/pay/transactions/native"
    r = w.request(method='POST', url=native_url, data=native_data)
    assert r.status_code == 200
    print(r.json())


def test_generate_qr_code():
    trade_order = secrets.token_hex(16)
    p = Path(f"{now.int_timestamp}.png")
    w.build_native_qr_code(
        description="中文 body", trade_no=trade_order, notice_url='https://www.baidu.com',
        price=1, path=p
    )


def test_get_prepay_id():
    trade_order = secrets.token_hex(16)
    r = w.build_jsapi_prepay(
        description="中文 body", trade_no=trade_order, notice_url='https://www.baidu.com',
        price=1, openid="ovwDJjj_g98G9X9-2KynNznEHmeM"
    )
    print(r)


def test_query_order():
    trade_order = secrets.token_hex(16)
    r = w.query_order(
        transaction_id=trade_order
    )
    print(r)


def test_get_openid():
    code = "081Vzo000hD6ZK1PFI000MISZS1Vzo0S"
    r = w.request_wx_openid(code=code)
    print(r)
