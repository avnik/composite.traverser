import re
from zope.interface import implementer
from zope.interface import provider

from zope.location.location import LocationProxy

from pyramid.interfaces import VH_ROOT_KEY
from pyramid.interfaces import ILocation, ITraverser, ITraverserFactory

from pyramid.traversal import traversal_path

from composite.traverser.interfaces import ISecurityProxyFactory
from composite.traverser.interfaces import IPluggableTraverser

_marker = object()
namespace_pattern = re.compile('[+][+]([a-zA-Z0-9_]+)[+][+]')

class DefaultPyramidTraverser(object):
    """Simulate default pyramid traverser"""
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __getitem__(self, segment):
        try:
            getter = getattr(self.context, '__getitem__')
        except AttributeError:
            raise KeyError(segment)

        return getter(segment)

def is_locateable(ob):
    if ILocation.providedBy(ob):
        return True
    if hasattr(ob, '__name__') and hasattr(ob, '__parent__'):
        return True

@implementer(ITraverser)
@provider(ITraverserFactory)
class ModelGraphTraverser(object):
    """ A pluggable model graph traverser:
        * when object does not provides ILocation, object will be wrapped
          with LocationProxy
        * if ISecurityProxyFactory registered, it used fot additional
          proxying traver
    when no object in the graph supplies either a ``__name__`` or a
    ``__parent__`` attribute (ie. no object 'provides the ILocation
    interface') ."""

    VIEW_SELECTOR = "@@"
    NAMESPACE_SELECTOR = "++"

    def __init__(self, root):
        self.root = root

    def __call__(self, request):
        environ = request.environ
        registry = request.registry

        if 'bfg.routes.matchdict' in environ:
            matchdict = environ['bfg.routes.matchdict']
            path = matchdict.get('traverse', '/')
            subpath = matchdict.get('subpath', '')
            subpath = tuple(filter(None, subpath.split('/')))
        else:
            # this request did not match a Routes route
            subpath = ()
            try:
                path = environ['PATH_INFO'] or '/'
            except KeyError:
                path = '/'

        try:
            vroot_path = environ[VH_ROOT_KEY]
        except KeyError:
            vroot_tuple = ()
            vpath = path
            vroot_idx = -1
        else:
            vroot_tuple = traversal_path(vroot_path)
            vpath = vroot_path + path
            vroot_idx = len(vroot_tuple) -1


        ob = self.root

        proxy = registry.queryUtility(ISecurityProxyFactory, default=None)
        if proxy:
            ob = proxy(ob)
        vroot = root = ob

        if vpath == '/' or (not vpath):
            # prevent a call to traversal_path if we know it's going
            # to return the empty tuple
            vpath_tuple = ()
        else:
            # we do dead reckoning here via tuple slicing instead of
            # pushing and popping temporary lists for speed purposes
            # and this hurts readability; apologies
            i = 0
            vpath_tuple = traversal_path(vpath)
            marker = object()
            for segment in vpath_tuple:

                if segment[:2] == self.VIEW_SELECTOR:
                    return dict(context=ob, view_name=segment[2:],
                                subpath=vpath_tuple[i+1:],
                                traversed=vpath_tuple[:vroot_idx+i+1],
                                virtual_root=vroot,
                                virtual_root_path=vroot_tuple,
                                root=self.root)

                ns_match =  namespace_pattern.match(segment)
                namespace = u""
                if ns_match:
                    prefix, namespace = ns_match.group(0, 1)
                    segment = segment[len(prefix):]

                adapter = registry.getMultiAdapter((ob, request),
                    IPluggableTraverser,
                    name=namespace)

                try:
                    next = adapter[segment]
                except KeyError:
                    return dict(context=ob, view_name=segment,
                                subpath=vpath_tuple[i+1:],
                                traversed=vpath_tuple[:vroot_idx+i+1],
                                virtual_root=vroot,
                                virtual_root_path=vroot_tuple,
                                root=self.root)

                if not is_locateable(next):
                    next = LocationProxy(next, ob, segment)

                if proxy:
                    next = proxy(next)

                if i == vroot_idx: 
                    vroot = next
                ob = next
                i += 1

        return dict(context=ob, view_name=u'', subpath=subpath,
                    traversed=vpath_tuple, virtual_root=vroot,
                    virtual_root_path=vroot_tuple, root=self.root)
