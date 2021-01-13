import hashlib
import json
import secrets
import time
from base64 import b64encode
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pendulum
import qrcode
import requests
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from easy_pay.settings import wechat_domain, time_zone, order_time_expire


@dataclass
class WechatBase:
    """接入 v3 微信支付"""
    app_id: str
    app_secret: str
    private_key: str
    mch_id: str
    serial_no: str  # 商户 api 证书

    nonce_str: str = ''
    timestamp: str = ''

    def request(self, method: str, url: str, data: Optional[dict] = None, params: Optional[dict] = None):
        url_path = url.replace(wechat_domain, '')
        if data:
            json_body = json.dumps(data)
        else:
            json_body = ''
        headers = {
            "Authorization": self.gen_authorization(method=method, url=url_path, body=json_body),
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36",
            "Content-Type": "application/json",
            'Accept': 'application/json',
            "char-set": 'utf8'
        }
        res = requests.request(method=method, url=url, data=json_body, headers=headers, params=params)
        return res

    def gen_authorization(self, method: str, url: str, body: str):
        """"""
        sign = self.sign(method=method, url=url, body=body)
        authorization = f'WECHATPAY2-SHA256-RSA2048 ' \
                        f'mchid="{self.mch_id}",' \
                        f'signature="{sign}",' \
                        f'nonce_str="{self.nonce_str}",' \
                        f'timestamp="{self.timestamp}",' \
                        f'serial_no="{self.serial_no}"'
        return authorization

    def sign(self, method: str, url: str, body: str):
        sign_str = self.gen_sign_str(url=url, method=method, body=body)
        rsa_key = RSA.importKey(self.private_key)
        signer = pkcs1_15.new(rsa_key)
        digest = SHA256.new(sign_str.encode('utf8'))
        sign = b64encode(signer.sign(digest)).decode('utf8')
        return sign

    def gen_sign_str(self, url: str, method: str, body: Optional[str] = '') -> str:
        """
        :param url: 绝对 url 去除域名：v3/certificates
        :param method: 请求方法
        :param body: object
        """
        current = pendulum.now('utc').int_timestamp
        self.nonce_str = secrets.token_hex(10)
        self.timestamp = str(current)
        sign_list = [method, url, self.timestamp, self.nonce_str, body]
        return '\n'.join(sign_list) + '\n'

    def __hash__(self):
        return hash(time.time())

    def get_cert(self):
        """平台证书序列号"""
        url = "https://api.mch.weixin.qq.com/v3/certificates"
        cert = self.request('GET', url)
        return cert.json()['data'][0]['serial_no']

    def validate_sign(self, serial_no: str):
        """
        :param serial_no: Wechatpay-Serial 商户平台证书序列号
        """
        local_cert = self.get_cert()
        return True if local_cert == serial_no else False


@dataclass
class WechatPublic(WechatBase):
    """公众号平台工具"""

    @staticmethod
    def generate_wx_sign(d: dict, key: str) -> str:
        """
        @param d: all request params without sign
        @param key: wechat key
        @return: sign
        """
        raw_sign = '&'.join(sorted([f"{k}={v}" for k, v in d.items()])) + f'&key={key}'
        m = hashlib.md5()
        m.update(raw_sign.encode(encoding='utf8'))
        sign = m.hexdigest().upper()
        return sign

    def request_wx_openid(self, code: str):
        base = "https://api.weixin.qq.com/sns/oauth2/access_token"
        data = (f"appid={self.app_id}", f"secret={self.app_secret}",
                f"code={code}", "grant_type=authorization_code")
        suffix = '&'.join(data)
        url = f"{base}?{suffix}"
        res = requests.get(url)
        res_data = res.json()
        open_id = res_data.get('openid')
        return open_id

    def build_jsapi_invoke_data(self, nonce_str: str, prepay_id: str):
        """Build the front-end to call up jsapi payment request data."""
        now = pendulum.now(tz=time_zone)
        base_data = {
            "appId": self.app_id,
            "timeStamp": str(now.int_timestamp()),
            "nonceStr": nonce_str,
            "package": f"prepay_id={prepay_id}",
            "signType": "RSA",
        }
        pay_sign = self.generate_wx_sign(base_data, self.app_secret)
        base_data['paySign'] = pay_sign
        return base_data


@dataclass
class WechatPay(WechatPublic):
    """支付平台工具"""

    def build_native_qr_code(
            self, description: str, trade_no: str, notice_url: str, price: int, path: Path
    ):
        """Generate and save the QR code of Native Payment."""
        now = pendulum.now(tz=time_zone)
        native_data = {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": description,
            "out_trade_no": trade_no,
            "time_expire": f"{now.add(seconds=order_time_expire)}",
            "notify_url": notice_url,
            "amount": {
                "total": price,
                "currency": "CNY"
            }
        }
        # get wechat pay qr_code url
        native_url = "https://api.mch.weixin.qq.com/v3/pay/transactions/native"
        r = self.request(method='POST', url=native_url, data=native_data)
        pay_code = r.json()['code_url']

        # build qr_code image
        img = qrcode.make(pay_code)
        with path.open(mode='wb') as w:
            img.save(w)

    def build_jsapi_prepay(
            self, price: int, description: str, notice_url: str, openid: str,
            trade_no: str,
    ):
        """Generate prepay id."""
        now = pendulum.now(tz=time_zone)
        jsapi_url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"
        jsapi_data = {
            "time_expire": f"{now.add(seconds=order_time_expire)}",
            "amount": {
                "total": price,
                "currency": "CNY"
            },
            "mchid": self.mch_id,
            "description": description,
            "notify_url": notice_url,
            "payer": {
                "openid": openid
            },
            "out_trade_no": trade_no,
            "appid": self.app_id,
        }

        r = self.request(method='POST', url=jsapi_url, data=jsapi_data)
        prepay_id = r.json()['prepay_id']
        return prepay_id

    def call_jsapi_sign(self):
        """"""

    def query_order(self, transaction_id: str):
        url = f"https://api.mch.weixin.qq.com/v3/pay/transactions/id/{transaction_id}?mchid={self.mch_id}"
        r = self.request(method='GET', url=url)
        return r.json()
