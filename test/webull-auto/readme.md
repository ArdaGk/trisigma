# Manual Testing

"remote" is a python file that can be used to trigger actions on the bot. This will only work on this specific ```TestingAlgo``` class defined in the ```algo.py```.

## Steps:
1. Run the bot using ```python3 main.py TESTING``` (label doesn't have to be "TESTING")
2. Wait until the port is displayed: ```listening on port 300*```
3. Bot can now be contolled using the "remote" file.

## Format:
**General format**
```./remote <port> <label> <symbol> <action>```

**market buy/sell:**
```./remote 3004 TESTING AAPL "market buy 2```

**market quote buy/sell:**
```./remote 3004 TESTING AAPL "market quote_buy 135.0```

**limit buy/sell:**
```./remote 3004 TESTING AAPL "limit buy 2 @ 120.0"```

**limit quote buy/sell:**
```./remote 3004 TESTING AAPL "limit quote_buy 135.0 @ 120.0"```

**cancel open order by orderId**
```./remote 3004 TESTING AAPL "cancel 1234567"```

**cancel all open orders of a specific side (buy/sell/all)**
```./remote 3004 TESTING AAPL "cancel_all buy"```





