from odoo import http

class ILoadController(http.Controller):

    @http.route('/iload', auth='public', website=True)
    def iload_home(self, **kw):
        return http.request.render('iload.iload_dashboard_content', {})

    @http.route('/iload/upload', type='http', auth='public', csrf=False, methods=['POST'])
    def upload_file(self, **post):
        file = http.request.httprequest.files.get('file')
        if not file:
            return "파일이 업로드되지 않았습니다."
        
        image_data = file.read()
        # 이후 AI 서버로 전송 등 처리
        return f"<h2>파일 {file.filename} 업로드 완료</h2>"
    
    @http.route('/test_static', auth='public')
    def test_static(self):
        import os
        path = os.path.abspath(os.path.join(
            http.addons_module.get_module_path('iload'),
            'static/src/img/iload_logo.svg'
        ))
        return f"<h1>Expected path:</h1><p>{path}</p>"
