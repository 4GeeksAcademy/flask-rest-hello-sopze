from flask import jsonify, url_for
import re

class APIException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

def _get_url_color(url):
    if "admin" in url:
        return "#ffff00"
    if "api" in url:
        return "#66ff00"
    elif "db" in url:
        return "#ff6600"
    elif url == "/":
        return "#A4A4A4"
    return "#aa77ff"

def _get_link(url):
    return [url, _get_url_color(url)]

def _get_method(methods):
    if "DELETE" in methods:
        return [3, "DELETE"]
    elif "POST" in methods:
        return [2, "POST"]
    elif "PUT" in methods:
        return [1, "PUT"]
    return [0, "GET"]

def generate_sitemap(app):
    admin_raw_link= '/admin/'
    endpoint_raw_link= []
    endpoint_raw_span= []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule) and not 'wipe' in rule.endpoint:
            link= _get_method("GET") + _get_link(url_for(rule.endpoint, **(rule.defaults or {})))
            if 'admin' not in link[2]:
                endpoint_raw_link.append(link)
        else:
            str= rule.__str__()
            if not re.search(r'static|export|admin', str):
                result= _get_method(rule.methods) + [rule.__str__()]
                if '<' in result[2]:
                    result[2]= result[2].replace('<','<span class="arg">&lt;').replace('>','&gt;</span>')
                endpoint_raw_span.append(result)

    admin_link= f"<p><a class=\"admin\" href=\"{admin_raw_link}\">Site admin: <span>{admin_raw_link}</span></a></p>"
    endpoint_link = "".join([f"<li><div class=\"ept{y[0]}\">{y[1]}</div><a style=\"color: {y[3]}\" href=\"{y[2]}\">{y[2]}</a></li>" for y in endpoint_raw_link])
    endpoint_span = "".join([f"<li><div class=\"ept{y[0]}\">{y[1]}</div>{y[2]}</li>" for y in endpoint_raw_span])

    html= open("res/index.html",'r').read()
    css= open("res/styles.css",'r').read()

    page= html.replace(
        "{css}",css).replace(
        "{admin_link}",admin_link).replace(
        "{endpoint_link}",endpoint_link).replace(
        "{endpoint_span}",endpoint_span)

    return page