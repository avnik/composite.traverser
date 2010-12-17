from zope.interface import Interface

class IPluggableTraverser(Interface):
    def __getitem__(name):
        """Traverse single name"""

class ISecurityProxyFactory(Interface):
    def __call__(obj):
        """Wrap obj into security (or another) proxy"""
