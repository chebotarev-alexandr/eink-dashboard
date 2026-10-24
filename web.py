"""Веб-морда: отдаёт красивую HTML-страницу + JSON со всеми данными.

Без внешних зависимостей (stdlib http.server). Страница сама опрашивает
/api/data раз в 5 секунд и перерисовывает карточки.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Панель</title>
<style>
:root{
  --bg:#070b14; --bg2:#0d1322; --surface:rgba(148,163,184,.07);
  --border:rgba(148,163,184,.14); --text:#e6ebf4; --muted:#94a3b8; --faint:#64748b;
  --accent:#6366f1; --accent2:#8b5cf6; --green:#34d399; --red:#f87171; --amber:#fbbf24;
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  background:var(--bg); color:var(--text); min-height:100vh; padding:2rem 1.5rem;
  background-image:
    radial-gradient(60rem 40rem at 85% -10%, color-mix(in srgb,var(--accent) 16%, transparent), transparent 60%),
    radial-gradient(50rem 36rem at -10% 30%, color-mix(in srgb,var(--accent2) 12%, transparent), transparent 60%);
}
.wrap{max-width:72rem;margin:0 auto}
header{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:1.75rem;flex-wrap:wrap;gap:.5rem}
header h1{font-size:1.4rem;font-weight:800;letter-spacing:-.02em}
.meta{color:var(--muted);font-variant-numeric:tabular-nums;font-size:.9rem;display:flex;gap:1rem}
.meta b{color:var(--text);font-weight:700}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem}
.card{
  background:var(--surface); border:1px solid var(--border); border-radius:1rem;
  padding:1.25rem 1.35rem; backdrop-filter:blur(12px);
  transition:border-color .2s ease, transform .2s ease;
}
.card:hover{border-color:color-mix(in srgb,var(--accent) 45%, transparent)}
.card h2{
  font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);
  font-weight:600;margin-bottom:1rem;
}
.muted{color:var(--faint);font-size:.9rem}
/* погода */
.w-main{display:flex;align-items:baseline;gap:.75rem}
.w-temp{font-size:3rem;font-weight:800;letter-spacing:-.03em;line-height:1}
.w-desc{font-size:1rem;color:var(--text);font-weight:600}
.w-details{display:grid;grid-template-columns:1fr 1fr;gap:.5rem 1rem;margin-top:1rem;color:var(--muted);font-size:.9rem}
/* строки списков */
.row{display:flex;align-items:center;gap:.6rem;padding:.45rem 0;border-bottom:1px solid var(--border);font-size:.92rem}
.row:last-child{border-bottom:none}
.dot{width:.55rem;height:.55rem;border-radius:50%;flex-shrink:0}
.dot.ok{background:var(--green);box-shadow:0 0 8px color-mix(in srgb,var(--green) 60%, transparent)}
.dot.fail{background:var(--red);box-shadow:0 0 8px color-mix(in srgb,var(--red) 60%, transparent)}
.name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.time{font-variant-numeric:tabular-nums;color:var(--accent);font-weight:600;flex-shrink:0}
.val{color:var(--muted);font-variant-numeric:tabular-nums;flex-shrink:0}
footer{margin-top:1.75rem;color:var(--faint);font-size:.8rem;text-align:center}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Панель · Хабаровск</h1>
    <div class="meta"><span id="clock"></span><span id="ip"></span></div>
  </header>
  <main>
    <section class="card"><h2>Погода</h2><div id="weather"></div></section>
    <section class="card"><h2>Серверы</h2><div id="servers"></div></section>
    <section class="card"><h2>Сегодня</h2><div id="planner"></div></section>
    <section class="card"><h2>Спутники</h2><div id="satellites"></div></section>
  </main>
  <footer>обновляется автоматически</footer>
</div>
<script>
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const none = el => el.innerHTML = '<span class="muted">нет данных</span>';

function weather(d){
  const el = document.getElementById('weather');
  if(!d || d.error || !d.weather) return none(el);
  const w = d.weather;
  el.innerHTML = `
    <div class="w-main"><span class="w-temp">${w.temp}°</span><span class="w-desc">${esc(w.weather)}</span></div>
    <div class="w-details">
      <span>Ощущается ${w.feels_like}°</span><span>Ветер ${w.wind} м/с</span>
      <span>Влажность ${w.humidity}%</span><span>Макс ${w.high}° / мин ${w.low}°</span>
    </div>`;
}
function servers(d){
  const el = document.getElementById('servers');
  if(!d || d.error || !d.servers) return none(el);
  el.innerHTML = d.servers.map(s => `
    <div class="row">
      <span class="dot ${s.ok?'ok':'fail'}"></span>
      <span class="name">${esc(s.name)}</span>
      <span class="val">${s.ok ? (s.latency_ms ?? '—')+' мс' : 'недоступен'}</span>
    </div>`).join('');
}
function planner(d){
  const el = document.getElementById('planner');
  if(!d || d.error) return none(el);
  if(!d.events || !d.events.length) return el.innerHTML = '<span class="muted">На сегодня пусто</span>';
  el.innerHTML = d.events.map(e => `
    <div class="row"><span class="time">${esc(e.time)}</span><span class="name">${esc(e.text)}</span></div>`).join('');
}
function satellites(d){
  const el = document.getElementById('satellites');
  if(!d || d.error) return none(el);
  if(!d.passes || !d.passes.length) return el.innerHTML = '<span class="muted">Нет ближайших пролётов</span>';
  el.innerHTML = d.passes.map(p => `
    <div class="row">
      <span class="name">${esc(p.name)}</span>
      <span class="time">${esc(p.time)}</span>
      <span class="val">↑${p.max_elevation}° · ${p.duration_min} мин</span>
    </div>`).join('');
}
async function refresh(){
  try{
    const d = await (await fetch('/api/data')).json();
    weather(d.clock_weather);
    servers(d.servers);
    planner(d.planner);
    satellites(d.satellites);
    if(d.clock_weather && d.clock_weather.ip)
      document.getElementById('ip').innerHTML = '<b>IP</b> '+esc(d.clock_weather.ip);
  }catch(e){}
}
setInterval(()=>{document.getElementById('clock').textContent=new Date().toLocaleTimeString('ru-RU');},1000);
setInterval(refresh,5000);
refresh();
</script>
</body>
</html>
"""


_DATA_GETTER = None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/data":
            data = _DATA_GETTER() if _DATA_GETTER else {}
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def start_web_server(data_getter, host="0.0.0.0", port=8080):
    global _DATA_GETTER
    _DATA_GETTER = data_getter
    server = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
