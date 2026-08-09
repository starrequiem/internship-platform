"""
实习通 · 本地开发服务器
启动后访问 http://localhost:8080
"""
import http.server
import os
import sys
import io

# Fix Windows GBK encoding for emoji
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def guess_type(self, path):
        """Override to add charset=utf-8 for text files"""
        base_type = super().guess_type(path)
        if base_type.startswith('text/') or base_type == 'application/javascript':
            return base_type + '; charset=utf-8'
        if path.endswith('.json'):
            return 'application/json; charset=utf-8'
        return base_type

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

print(f"""
╔══════════════════════════════════════╗
║   🚀 实习通 · 本地开发服务器          ║
║   地址：http://localhost:{PORT}        ║
║   按 Ctrl+C 停止服务器                ║
║   不要关闭此窗口                      ║
╚══════════════════════════════════════╝
""")

try:
    http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
except KeyboardInterrupt:
    print('\n服务器已停止')
