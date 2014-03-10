import webapp2, jinja2, os
import json
import datetime

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'])


def export_timestamp(timestamp):
  if not timestamp:
    return None
  return timestamp.strftime("%Y-%m-%d %H:%M:%S")


class StaticHandler(webapp2.RequestHandler):
  def render_template(self, name):
    if name == "":
      name = "index"

    values = {
      "name": name
    }
    self.response.write(JINJA_ENVIRONMENT.get_template("templates/" + name + '.html').render(values))
  
  def get(self, _):
    name = self.request.path.split("/")[1]
    try:
      self.render_template(name)
    except IOError, e:
      self.render_template("error")


class JsonAPIHandler(webapp2.RequestHandler):
  def post(self):
    self.get()

  def get(self):
    resp = self.handle()
    self.response.headers['Content-Type'] = "application/json"
    dthandler = lambda obj: export_timestamp(obj) if isinstance(obj, datetime.datetime) else None
    self.response.write(json.dumps(resp, default=dthandler))


