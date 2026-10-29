// Cloudflare Pages Function · 微信 JS-SDK 签名
// 路由：GET /api/wx-sign?url=<encodeURIComponent(当前页面URL，去掉#)>
// 环境变量（在 Cloudflare Pages 项目 Settings → Environment variables 里加，WX_SECRET 设为 Secret）：
//   WX_APPID   认证服务号的 AppID（wx 开头）
//   WX_SECRET  服务号的 AppSecret
// 说明：jsapi_ticket 有 7200s 有效期，这里用 Edge Cache 缓存 7000s，避免每次请求都打微信接口。

const TOKEN = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential';
const TICKET = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?type=jsapi&access_token=';

async function getTicket(env) {
  const cache = caches.default;
  const key = new Request('https://wx-ticket.internal/jsapi-ticket');
  const hit = await cache.match(key);
  if (hit) return hit.text();

  const tkRes = await fetch(`${TOKEN}&appid=${env.WX_APPID}&secret=${env.WX_SECRET}`);
  const tk = await tkRes.json();
  if (!tk.access_token) throw new Error('token: ' + JSON.stringify(tk));

  const jsRes = await fetch(TICKET + tk.access_token);
  const js = await jsRes.json();
  if (!js.ticket) throw new Error('ticket: ' + JSON.stringify(js));

  await cache.put(key, new Response(js.ticket, {
    headers: { 'Cache-Control': 'max-age=7000' }
  }));
  return js.ticket;
}

async function sha1Hex(str) {
  const buf = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(str));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function onRequestGet({ request, env }) {
  const target = new URL(request.url).searchParams.get('url');
  if (!target) return Response.json({ error: 'missing url' }, { status: 400 });
  if (!env.WX_APPID || !env.WX_SECRET) {
    return Response.json({ error: 'WX_APPID / WX_SECRET not configured' }, { status: 500 });
  }

  try {
    const ticket = await getTicket(env);
    const nonceStr = Math.random().toString(36).slice(2, 18);
    const timestamp = Math.floor(Date.now() / 1000);
    // 参与签名的 url 必须与 wx.config 时的 location.href 完全一致（不含 #hash），且未被再次转义
    const signature = await sha1Hex(
      `jsapi_ticket=${ticket}&noncestr=${nonceStr}&timestamp=${timestamp}&url=${target}`
    );
    return Response.json(
      { appId: env.WX_APPID, timestamp, nonceStr, signature },
      { headers: { 'Cache-Control': 'no-store' } }
    );
  } catch (e) {
    // 常见：40164 = 调用方 IP 不在公众号「IP 白名单」里
    return Response.json({ error: String(e.message || e) }, { status: 502 });
  }
}
