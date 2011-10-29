import re
from ordereddict import OrderedDict

class RouteComponent(object):
    def __init__(self, pattern=r'\w+', coerce_func=None):
        self.pattern = pattern
        self.coerce_func = coerce_func

    def coerce(self, val):
        if self.coerce_func:
            return self.coerce_func(val)
        return val

class Router(object):
    """
    Idea stolen from Zed Shaw's Lamson SMTP server.

    No idea how the implementations line up, since
    I haven't peeked under the covers of his router
    code.

    Take a string pattern and interpolate regexes based on
    keyword arguments to the function.  Returns a decorator.

    router = Router()
    route = router.route
    @route("/hello/(first_name)/")
    def hello_world(first_name):
        print "hello %s"

    If you want to be match a route more strictly than just 
    any character, simply include it as a keyword argument
    after the pattern string:

    @route("/happy_birthday/(name)/(age)/", age=r'\d+')
    def happy_birthday(name, age):
        print "happy bday, %s! Can't believe you made it to %s"%(name, age)

    Sometimes it's useful to have a route component that not only
    matches a specific regular expression, but also coerces
    the values to a specific type.  If instead of providing a custom
    regex in the keyword argument's value, you pass in a subclass
    of RouteComponent, we'll do just that.

    class DateComponent(RouteComponent):
        pattern = r'\d{4}-\d{2}-\d{2}'
        def coerce(self, value):
            return datetime.datetime.strptime(value, '%Y-%m-%d')

    @route('/news/(date)/', date=DateComponent)
    def get_news(date):
        next_day = date + datetime.timedelta(1)
        return db.query(table='news', where='date BETWEEN %s AND %s', params=(date, next_day))

    Pretty simple, no?
    """
    def __init__(self, registry=None):
        if registry is None:
            self.registry = OrderedDict()
        else:
            self.registry = registry

    def route(self, pattern, **kwargs):
        components = {}
        for name in set(re.findall(r"\((\w+)\)", pattern)):
            component = kwargs.get(name, RouteComponent())
            if not isinstance(component, RouteComponent):
                component = RouteComponent(component)
            components[name] = component
            pattern = pattern.replace("(%s)"%name, "(?P<%s>%s)"%(name,component.pattern))
        regex = re.compile(pattern)
        def registrar(f):
            print "setting callback %r to answer the following regex: %s"%(f, pattern)
            self.registry[regex] = (f, components)
            return f
        return registrar

    def resolve(self, string):
        for pattern, handler in self.registry.items():
            callback, components = handler
            match = pattern.match(string)
            if match is not None:
                return callback, dict([(k, components[k].coerce(v)) for k,v in match.groupdict().items()])
        return None, {}

