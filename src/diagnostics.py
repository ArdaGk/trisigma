from binance.spot import Spot
from datetime import datetime
import requests

class BinanceDiagnostics ():

    @staticmethod
    def check_exchange(last_exchange_info):
        symbols = [item["symbol"] for item in last_exchange_info["symbols"]]
        new_exchange_info = Spot().exchange_info(symbols=symbols)
        del new_exchange_info["serverTime"]
        if len(last_exchange_info) == 0 and "symbols" in last_exchange_info:
            return new_exchange_info
        diff = get_diff(last_exchange_info, new_exchange_info)
        report = {"result": len(diff) == 0, "details": diff, "new": new_exchange_info}
        return report

    @staticmethod
    def check_patch(last_patch):
        resp = requests.get("https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/CHANGELOG.md")
        cur_patch = resp.text.split("## ")[1:][0]
        report = {"result": last_patch == cur_patch, "details": cur_patch, "new": cur_patch}
        return report

    @staticmethod
    def check_acc_status(api, secret):
        client = Spot(key=api, secret=secret)
        acc_state = client.account_status()['data']
        trading_state = client.api_trading_status()['data']
        result = acc_state == "Normal" and not trading_state['isLocked']
        report = {"result": result, "details": {"acc_state": acc_state, "trading_state": trading_state}}
        return report

    @staticmethod
    def check_weight():
        resp = Spot(show_limit_usage=True).ping()
        weight = float(resp['limit_usage']['x-mbx-used-weight'])
        report = {"result": None, "details": {"weight": weight}}
        return report

    @staticmethod
    def check_connection():
        resp = requests.get("https://api.binance.com/api/v3/time")
        latency = resp.elapsed.total_seconds()*1000
        server_time = resp.json()["serverTime"]
        local_time = datetime.now().timestamp()*1000
        clock_diff = local_time - server_time
        report = {"result": None, "details": {"latency": latency, "clock_diff": clock_diff}}
        return report


def get_diff(d1, d2, path=""):
    output = []
    for k in d1:
        if k in d2:
            if type(d1[k]) is dict:
                diff = get_diff(d1[k],d2[k], "%s -> %s" % (path, k) if path else k)
                if diff:
                    output.extend(diff)
            elif d1[k] != d2[k]:
                result = [ "%s: " % path, " - %s : %s" % (k, d1[k]) , " + %s : %s" % (k, d2[k])]
                output.append("\n".join(result))
        else:
            result ="%s%s as key not in d2\n" % ("%s: " % path if path else "", k)
            output.append(result)
    return output
