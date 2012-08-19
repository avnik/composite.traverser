import unittest
from zope.interface import Interface, implementer, directlyProvides
from pyramid.interfaces import IRequest
from pyramid.testing import cleanUp, setUp, get_current_registry, DummyModel
from pyramid.testing import DummyRequest
from composite.traverser.interfaces import IPluggableTraverser

@implementer(IRequest)
class TestRequest(DummyRequest):
    pass

class TestTraverser(unittest.TestCase):
    def tearDown(self):
        cleanUp()

    def setUp(self):
        from pyramid.registry import Registry
        from pyramid.configuration import Configurator
        from pyramid.interfaces import IRootFactory
        c = setUp()
        c.include('pyramid_zcml')
        c.load_zcml('composite.traverser.tests:configure.zcml')
        r = c.registry
        r.registerUtility(lambda x: self.models, IRootFactory)
        r.registerAdapter(CustomTraverser, 
            (ISecond, IRequest), IPluggableTraverser)
        r.registerAdapter(NamedCustomTraverser, 
            (ISecond, IRequest), IPluggableTraverser, name="named")

    def _getTargetClass(self):
        from composite.traverser.traverser import ModelGraphTraverser
        return ModelGraphTraverser

    def _makeOne(self, *arg, **kw):
        klass = self._getTargetClass()
        return klass(*arg, **kw)

    def _getEnviron(self, **kw):
        environ = {}
        environ.update(kw)
        return environ

    def _traverse(self, model, path):
        klass = self._getTargetClass()
        request = TestRequest(environ={'PATH_INFO': path})
        request.registry = get_current_registry()
        tr = klass(self.models)
        D =  tr(request)
        return D

    @property
    def models(self):
        root = DummyModel()
        first = DummyModel()
        second = Second()
        root['first'] = first
        first['second'] = second
        return root

    def test_is_locateable(self):
        from zope.location.interfaces import ILocation
        from zope.location.location import LocationProxy
        from composite.traverser.traverser import is_locateable

        class M(object):
            __name__ = "M"
            __parent__ = None

        self.failIf(is_locateable(object()))
        self.failUnless(is_locateable(M()))
        proxied = LocationProxy(object(), "name", None)
        self.failUnless(is_locateable(proxied))
        

    def test_traverser_is_our_traverser(self):
        from pyramid.interfaces import ITraverser
        from pyramid.testing import get_current_registry
        from composite.traverser.traverser import ModelGraphTraverser
        registry = get_current_registry()
        traverser = registry.queryAdapter(object(), ITraverser)
        self.failUnless(isinstance(traverser, ModelGraphTraverser))

    def test_class_conforms_to_ITraverser(self):
        from zope.interface.verify import verifyClass
        from pyramid.interfaces import ITraverser
        verifyClass(ITraverser, self._getTargetClass())

    def test_instance_conforms_to_ITraverser(self):
        from zope.interface.verify import verifyObject
        from pyramid.interfaces import ITraverser
        context = DummyModel()
        verifyObject(ITraverser, self._makeOne(context))

    def test_plain_path(self):
        D = self._traverse(self.models, "/first/second")
        self.failUnlessEqual(D['context'].__name__, "second")
        self.failUnless(ISecond.providedBy(D['context']))

    def test_path(self):
        D = self._traverse(self.models, "/first/second/third")
        self.failUnlessEqual(D['context'].__name__, "third")

    def test_view(self):
        D = self._traverse(self.models, "/first/second/third/@@named_view")
        self.failUnlessEqual(D['context'].__name__, "third")
        self.failUnlessEqual(D['view_name'], 'named_view')

    def test_namespace(self):
        D = self._traverse(self.models, "/first/second/++named++context")
        self.failUnless(isinstance(D['context'], AnotherContext))
        self.failUnlessEqual(D['context'].value, 'context')

    def test_namespace_view(self):
        D = self._traverse(self.models, 
            "/first/second/++named++context/@@named_view")
        self.failUnless(isinstance(D['context'], AnotherContext))
        self.failUnlessEqual(D['context'].value, 'context')
        self.failUnlessEqual(D['view_name'], 'named_view')

class AnotherContext(object):
    def __init__(self, value):
        self.value = value

    def __getitem__(self, item):
        dummy = DummyModel()
        dummy.__name__ = item
        return dummy

class ISecond(Interface):
    pass

@implementer(ISecond)
class Second(object):
    pass

@implementer(IPluggableTraverser)
class CustomTraverser(object):
    def __init__(self, context, request):
        self.context = context
        self.data = DummyModel()
        self.data['third'] = DummyModel()

    def __getitem__(self, item):
        return self.data[item]

    def __repr__(self):
        return "<CustomTraverser for %r>" % self.context

class NamedCustomTraverser(CustomTraverser):
    def __getitem__(self, item):
        return AnotherContext(item)

def test_suite():
    return unittest.makeSuite(TestTraverser)
