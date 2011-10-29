import redis
import router
from gevent.wsgi import WSGIServer
from settings import config

r = router.Router()

@r.route('/')
def index():
    return "Hello World"

@r.route('/count/(metric)/')
def count(metric):


if __name__ == "__main__":
    app = AnyStater()
    server = WSGIServer((config.HOST, config.PORT), app)
    server.serve_forever()
