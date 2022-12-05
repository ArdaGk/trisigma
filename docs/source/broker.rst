=================
Broker Interface
=================

This is the object that should used to access market data and send signals. This object will be constructed by the Base class (Strategy) and can be accessed via ``self.broker``.


The method signatures does not contain any parameter for the symbol and trading platform. This is because each symbol is treated as an individual Strategy object, In other words, A new Broker object is automatically constructed for each symbol, in the specified trading platform, therefore those values are already stored as an attribute.

.. autoclass:: src.broker.Broker
   :members:
   :special-members: __call__
   :member-order: bysource
