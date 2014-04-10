import webapp2, jinja2, os
import json
import datetime

from webapp2_extras import i18n
from webapp2_extras.i18n import gettext as gettext
from translation import get_client_side_translations, get_preferred_locale

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape','jinja2.ext.i18n'])
JINJA_ENVIRONMENT.install_gettext_translations(i18n)

def export_timestamp(timestamp):
  if not timestamp:
    return None
  return timestamp.strftime("%Y-%m-%d %H:%M:%S")


class StaticHandler(webapp2.RequestHandler):
  def render_template(self, name):
    # determine preferred language
    preferred_locale = get_preferred_locale(self.request)
    i18n.get_i18n().set_locale(preferred_locale)
    client_side_translations = get_client_side_translations()

    if name == "":
      name = "index"

    values = {
      "name": name,
      "preferred_locale": preferred_locale,
      "client_side_translations": json.dumps(client_side_translations)
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


