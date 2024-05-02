from flask import jsonify, url_for
import os, re, tools

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
        return "admin"
    if "api" in url:
        return "api"
    elif "db" in url:
        return "db"
    elif url == "/":
        return "root"
    return "other"

def _get_link(url):
    return [url, _get_url_color(url)]

def _get_method(methods):
    if "DELETE" in methods:
        return "DELETE"
    elif "POST" in methods:
        return "POST"
    elif "PUT" in methods:
        return "PUT"
    return "GET"

def generate_sitemap(app, entitytypes=None):
    admin_raw_link= '/admin/'
    endpoint_raw_link= []
    endpoint_raw_span= []

    method_get= [_get_method("GET")]

    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule) and not re.search(r'wipe|execute', rule.endpoint):
            link= _get_link(url_for(rule.endpoint, **(rule.defaults or {})))
            if 'admin' not in link[0]:
                endpoint_raw_link.append(method_get + link)
        else:
            str= rule.__str__()
            if not re.search(r'static|export|admin', str):
                rulestr= rule.__str__()
                if '<' in rulestr:
                    rulestr= rulestr.replace('<','<span class="arg">&lt;').replace('>','&gt;</span>')
                endpoint_raw_span.append([_get_method(rule.methods), rulestr])

    admin_link= f"<p><a class=\"admin\" href=\"{admin_raw_link}\">Site admin: <span>{admin_raw_link}</span></a></p>"
    endpoint_link = "".join([f"<li><div class=\"method method-{y[0].lower()}\">{y[0]}</div><a class=\"apilink-{y[2]}\" href=\"{y[1]}\">{y[1]}</a></li>" for y in endpoint_raw_link])
    endpoint_span = "".join([f"<li><div class=\"method method-{y[0].lower()}\">{y[0]}</div>{y[1]}</li>" for y in endpoint_raw_span])
    tool_list = "".join([f"<li>{t}</li>" for t in tools.generate_html_links()])

    if entitytypes:
        endpoint_link+= "".join([f"<li><div class=\"method method-get\">GET</div><a class=\"apilink-api\" href=\"{l}\">{l}</a></li>" for l in entitytypes])

    html= open("res/index.html",'r').read()
    css= open("res/styles.css",'r').read()

    page= html.replace(
        "%SWATCH%", os.environ.get('BOOTSTRAP_THEME', 'slate')).replace(
        "%CSS%",css).replace(
        "%ADMIN_LINK%",admin_link).replace(
        "%ENDPOINT_LINK%",endpoint_link).replace(
        "%ENDPOINT_SPAN%",endpoint_span).replace(
        "%TOOL_LIST%",tool_list)

    return page