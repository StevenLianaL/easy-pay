from dataclasses import dataclass

import pendulum
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.domain.AlipayTradeWapPayModel import AlipayTradeWapPayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.request.AlipayTradeWapPayRequest import AlipayTradeWapPayRequest

from easy_pay.settings import time_zone, order_time_expire


@dataclass
class Alipay:
    """集成支付宝支付"""
    is_sandbox: bool = False
    app_id: str = ''
    alipay_public_key: str = ''
    app_private_key: str = ''

    def __post_init__(self):
        self.config = AlipayClientConfig(sandbox_debug=self.is_sandbox)
        self.config.app_id = self.app_id
        self.config.alipay_public_key = self.alipay_public_key
        self.config.app_private_key = self.app_private_key
        self.client = DefaultAlipayClient(alipay_client_config=self.config)

    def pay(self, method: str, subject: str, price: int, trade_no: str, describe: str = '',
            notice_url: str = '', return_url: str = '', quit_url: str = ''
            ) -> str:
        """
        :param method: 支付途径
        :param price: 分
        :param trade_no: 商家订单号
        :param subject: 商品名
        :param describe: 商品描述
        :param notice_url: 订单通知 url
        :param return_url: 订单返回页面 url
        :param quit_url: 用户付款中途退出返回商户网站的地址
        """
        if method == 'page':
            func = self.page_pay
        elif method == 'wap':
            func = self.wap_pay
        else:
            raise ValueError(f'当然不支持:{method}，请使用 page/wap')
        return func(
            subject=subject, price=price, trade_no=trade_no, describe=describe,
            notice_url=notice_url, return_url=return_url, quit_url=quit_url
        )

    def page_pay(self, subject: str, price: int, trade_no: str, describe: str = '',
                 notice_url: str = '', return_url: str = '', **kw
                 ) -> str:
        """Pc page pay, get alipay redirect url."""

        model = AlipayTradePagePayModel()

        model.out_trade_no = trade_no
        model.product_code = "FAST_INSTANT_TRADE_PAY"
        model.total_amount = round(price / 100, 2)
        model.subject = subject
        model.body = describe

        now = pendulum.now(time_zone)
        after_now = now.add(seconds=order_time_expire)
        model.time_expire = after_now.format('YYYY-MM-DD HH:mm:ss')

        request = AlipayTradePagePayRequest(biz_model=model)
        request.notify_url = notice_url
        request.return_url = return_url

        pay_url = self.client.page_execute(request, http_method="GET")
        return pay_url

    def wap_pay(self, subject: str, price: int, trade_no: str, describe: str = '',
                notice_url: str = '', return_url: str = '', quit_url: str = ''
                ) -> str:
        """Phone wap pay, get alipay redirect url."""
        model = AlipayTradeWapPayModel()
        model.out_trade_no = trade_no
        model.product_code = "QUICK_WAP_WAY"
        model.total_amount = round(price / 100, 2)
        model.subject = subject
        model.body = describe
        model.quit_url = quit_url

        now = pendulum.now(time_zone)
        after_now = now.add(seconds=order_time_expire)
        model.time_expire = after_now.format('YYYY-MM-DD HH:mm:ss')

        request = AlipayTradeWapPayRequest(biz_model=model)
        request.notify_url = notice_url
        request.return_url = return_url

        response = self.client.page_execute(request, http_method="GET")
        return response
