from trisigma.time_utils import to_timestamp

class BadInterval (Exception):
   pass 

def get_step (interval, duration=360):
    duration = 360
    factors = [5, 15, 30, 60, 120, 240]
    mins = to_timestamp(interval) / 60
    if mins >= 86400/60:
        market_days = mins/(86400/60)
        if market_days % 1 != 0:
            raise BadInterval(f"interval: {interval} cannot be divided into days")
        mins = market_days * duration
        factors = [fac for fac in factors if duration % fac == 0]

    coefs = [mins / fac for fac in factors]

    for i, coef in enumerate(reversed(coefs)):
        if coef % 1 == 0:
            return (coef, factors[-(i+1)])
    return -1



while True:
    print(get_step(input("interval: ")))

