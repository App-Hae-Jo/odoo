from odoo import http

class HelloWorld(http.Controller):
    @http.route('/hello', auth='public', website=True)
    def hello(self, **kw):
        return http.request.render('hello_world.hello_template', {})