==========================
Webull Integration Testing
==========================

Manual Testing
--------------

"remote" is a python file that can be used to trigger actions on the bot. This will only work on this specific ``TestingAlgo`` class defined in the ``algo.py``.

add python block


Steps:
 1. Navigate *test/webull-manual*
 2. ``python3 main.py TESTING``
 3. Wait until the port is displayed: ``listening on port 300*``
 4. Bot can now be contolled using the "remote" file.

Format:
~~~~~~~~~~
**General format**

``./remote <port> <label> <symbol> "<action>"``

**market buy/sell:**

``./remote 3004 TESTING AAPL "market buy 2"``

**market quote buy/sell:**

``./remote 3004 TESTING AAPL "market quote_buy 135.0"``

**limit buy/sell:**

``./remote 3004 TESTING AAPL "limit buy 2 @ 120.0"``

**limit quote buy/sell:**

``./remote 3004 TESTING AAPL "limit quote_buy 135.0 @ 120.0"``

**cancel open order by orderId**

``./remote 3004 TESTING AAPL "cancel 1234567"``

**cancel all open orders of a specific side (buy/sell/all)**

``./remote 3004 TESTING AAPL "cancel_all buy"``



Automated Testing
------------------
The scope of this automated testing is to verify the integration of the software with Webull API's. This includes testing the functionality of the API calls, the accuracy of data retrieval and manipulation, and the overall stability of the integration. Any potential issues or discrepancies found during the testing will be addressed accordingly to ensure the smooth functioning of the software with Webull API's.

Usage
~~~~~
    1. navigate *test/webull-auto*
    2. Edit settings in ``main.py``
    3. ``python3 main.py TESTING``


What is being tested?
---------------------
    * Signals (Market/Limit)
    * Order cancelation
    * Market data accessibility (price and candlesticks)
    * Account portfolio
    * Account's past trades
    * Latency of each response


Detailed Testing Steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    For each given symbol:
        1. Cancel every open order
        2. Get current position, sell all of it
        3. Market buy 1
        4. Check current balance and position
        5. Market sell 2
        6. Get past trades, look for orderIds of the preivous buy and sell
        7. Check current balance and position
        8. Get current price of the asset
        9. Place one limit order 10% below the price
        10. Check account's locked balance to validate the past order
        11. Cancel the limit order using it's orderId
        12. Check open orders and locked balance to validate cancelation
        13. Get past candlestick at given intervals
        14. Repeat steps 9-13 with one limit sell at %10 above the price

Limitations
~~~~~~~~~~~
    * Market Data values aren't validated, testing is based on accessibility and response format.
    * Symbols are tested serially, therefore account will not hold two symbol at once.
