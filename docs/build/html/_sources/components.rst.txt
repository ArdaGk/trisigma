==========
Components
==========

trisigma.toolkit
----------------
.. autoclass:: src.toolkit.Alarm
   :members: static
   :inherited-members:
   :exclude-members: __weakref__
   :special-members: __init__, __call__
|
.. autoclass:: src.toolkit.Trail
   :members: reset, is_active, set_peak, lock, unlock, activate, deactivate
   :inherited-members:
   :exclude-members: __weakref__
   :special-members: __init__, __call__
|
.. autoclass:: src.toolkit.Traces
   :members: set_traces, get_traces, here_since, get_region, is_inside
   :inherited-members:
   :exclude-members: __weakref__
   :special-members: __init__, __call__
|
.. autoclass:: src.toolkit.Sock
   :members: add, send
   :inherited-members:
   :exclude-members: __weakref__
   :special-members: __init__, __call__


trisigma.time_utils
------------------
.. automodule:: src.time_utils
   :members:

trisigma.scraper
--------------
.. autoclass:: src.scraper.Binance
   :members: get_price, get_klines
   :inherited-members:
   :exclude-members: __weakref__
   :special-members:
|
.. autoclass:: src.scraper.Webull
   :members: get_price, get_klines_min
   :inherited-members:
   :exclude-members: __weakref__
   :special-members:

trisigma.slack
-------------
.. autoclass:: src.slack.Slack
   :members: send
   :inherited-members:
   :exclude-members: __weakref__
   :special-members: __init__


trisigma.filemanager
-------------------
.. autoclass:: src.filemanager.FileManager
   :members: save, load, log 
   :inherited-members:
   :exclude-members:
   :special-members: __init__


