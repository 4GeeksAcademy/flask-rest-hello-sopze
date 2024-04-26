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

def generate_sitemap(app):
    links = ['/admin/']
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            if "/admin/" not in url:
                links.append(url)

    links_html = "".join(["<li><a href='" + y + "'>" + y + "</a></li>" for y in links])
    return f"""
    <html style="background: #111">
        <head>
            <style>
                :root {{ color: #eee; }}
                .title {{ padding:0; margin:4px; & .old {{ color: #444; text-decoration: line-through solid #aa3333 4px; }} & .new {{ color: #e20; }} }}
                .subtitle {{ padding:0; margin:0; font-size:12px; color: #777 }}
                .doomguy {{
                    width: 256px; height: auto;
                    image-rendering: pixelated;
                    filter: drop-shadow(0 0 32px #000);
                }}
                ul {{ margin-left: 5%; text-align: left; list-style-type: none }}
                li {{ padding: .1em; }}
                li a {{ font-size: 14px; color: #66ff00; text-decoration: none; font-weight: 700 }}
            </style>
        </head>
        <body>
            <div style="text-align: center; font-family: sans-serif; padding-top: 16px;">
                <img class="doomguy" src="https://i.imgur.com/O1w94Wp.png" />
                <h2 class="title"><span class="old">Rigo</span> <span class="new">Doomguy</span> welcomes you to your API!!</h2>
                <p class="subtitle">(he finally killed rigo baby)</p>
                <p><script>document.write('<input style="padding: 5px; width: 500px" type="text" value="'+window.location.href+'" />');</script></p>
                <ul>
                    {links_html}
                </ul>
            </div>
        </body>
    </html>
    """

def clear_database_records(db):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()