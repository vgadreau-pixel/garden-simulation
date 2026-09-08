#!/usr/bin/env python3
# Vérification CDP du rendu de l'app (client websocket minimal, stdlib only).
import json, time, os, socket, base64, struct, sys
import urllib.request

class WS:
    def __init__(self, url):
        host, path = url.replace('ws://', '').split('/', 1)
        parts = host.split(':')
        self.host = parts[0]
        self.port = int(parts[1]) if len(parts) > 1 else 80
        self.path = '/' + path
        self.sock = socket.create_connection((self.host, self.port), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET {self.path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(req.encode())
        resp = b''
        while b'\r\n\r\n' not in resp:
            resp += self.sock.recv(4096)
        assert b'101' in resp.split(b'\r\n')[0], resp[:200]
        self.buf = b''
        self.id = 0

    def _send(self, obj):
        data = json.dumps(obj).encode()
        hdr = bytearray([0x81])
        n = len(data)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack('>H', n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack('>Q', n)
        mask = os.urandom(4)
        hdr += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(bytes(hdr) + masked)

    def _recv_frame(self):
        while True:
            if self.buf:
                b1, b2 = self.buf[0], self.buf[1]
                op = b1 & 0xF
                ln = b2 & 0x7F
                off = 2
                if ln == 126:
                    ln = struct.unpack('>H', self.buf[2:4])[0]; off = 4
                elif ln == 127:
                    ln = struct.unpack('>Q', self.buf[2:10])[0]; off = 10
                if len(self.buf) >= off + ln:
                    payload = self.buf[off:off + ln]
                    self.buf = self.buf[off + ln:]
                    if op == 1:
                        return json.loads(payload)
                    continue
            self.buf += self.sock.recv(65536)

    def drain(self, seconds=0.3):
        self.sock.settimeout(seconds)
        out = []
        try:
            while True:
                out.append(self._recv_frame())
        except (socket.timeout, TimeoutError):
            pass
        finally:
            self.sock.settimeout(30)
        return out

    def call(self, method, **params):
        self.id += 1
        mid = self.id
        self._send({'id': mid, 'method': method, 'params': params})
        while True:
            m = self._recv_frame()
            if m.get('id') == mid:
                if 'error' in m:
                    raise RuntimeError(m['error'])
                return m['result']


def main():
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'))
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = WS(page['webSocketDebuggerUrl'])
    ws.call('Page.enable')
    ws.call('Runtime.enable')
    ws.call('Page.navigate', url='http://localhost:4173/')
    time.sleep(4)
    events = ws.drain(0.5)
    console_errors = [
        e for e in events
        if e.get('method') == 'Runtime.consoleAPICalled' and e['params'].get('type') in ('error', 'warning')
    ]
    exceptions = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
    print('console_errors:', len(console_errors), 'exceptions:', len(exceptions))
    for e in (console_errors + exceptions)[:5]:
        print('  ', json.dumps(e.get('params', {}))[:300])

    def eval_js(expr):
        r = ws.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return ('EXC', str(r['exceptionDetails'])[:300])
        return r['result'].get('value')

    print('state:', eval_js('JSON.stringify({vis: document.visibilityState, fps: document.getElementById("fps").textContent})'))
    print('raf_fps:', eval_js('new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++; if(performance.now()-t0<1000) requestAnimationFrame(f); else res(Math.round(n*1000/(performance.now()-t0)))};requestAnimationFrame(f)})'))

    # Lecture du HUD FPS après 2s de plus
    time.sleep(2)
    print('hud_fps:', eval_js('document.getElementById("fps").textContent'))

    # Screenshot initial
    shot = ws.call('Page.captureScreenshot', format='png')
    open('/tmp/jardin_initial.png', 'wb').write(base64.b64decode(shot['data']))
    print('shot_initial: ok')

    # --- Test zoom (molette) ---
    def canvas_hash():
        return eval_js('(()=>{const c=document.getElementById("app");const g=c.getContext("webgl2")||c.getContext("webgl");const p=new Uint8Array(4*g.drawingBufferWidth*g.drawingBufferHeight);g.readPixels(0,0,g.drawingBufferWidth,g.drawingBufferHeight,g.RGBA,g.UNSIGNED_BYTE,p);let h=0;for(let i=0;i<p.length;i+=37)h=((h*31)+p[i])>>>0;return h})()')

    h0 = canvas_hash()
    ws.call('Input.dispatchMouseEvent', type='mouseWheel', x=700, y=450, deltaX=0, deltaY=-400, deltaMode=0)
    time.sleep(0.5)
    h1 = canvas_hash()
    print('zoom: hash_before=%s hash_after=%s changed=%s' % (h0, h1, h0 != h1))
    shot = ws.call('Page.captureScreenshot', format='png')
    open('/tmp/jardin_zoom.png', 'wb').write(base64.b64decode(shot['data']))

    # Zoom arrière (retour arrière)
    ws.call('Input.dispatchMouseEvent', type='mouseWheel', x=700, y=450, deltaX=0, deltaY=400, deltaMode=0)
    time.sleep(0.4)
    h2 = canvas_hash()
    print('unzoom: hash=%s (retour proche initial: %s)' % (h2, abs(h2 - h0) < 50 if isinstance(h0, int) and isinstance(h2, int) else '?'))

    # --- Test pan (drag) ---
    ws.call('Input.dispatchMouseEvent', type='mousePressed', x=700, y=450, button='left', clickCount=1)
    for i in range(1, 11):
        ws.call('Input.dispatchMouseEvent', type='mouseMoved', x=700 - 20 * i, y=450 + 12 * i, button='left', buttons=1)
        time.sleep(0.02)
    ws.call('Input.dispatchMouseEvent', type='mouseReleased', x=500, y=570, button='left', clickCount=1)
    time.sleep(0.5)
    h3 = canvas_hash()
    print('pan: hash_after_drag=%s changed=%s' % (h3, h1 != h3 and h2 != h3))
    shot = ws.call('Page.captureScreenshot', format='png')
    open('/tmp/jardin_pan.png', 'wb').write(base64.b64decode(shot['data']))
    print('done')


if __name__ == '__main__':
    main()
