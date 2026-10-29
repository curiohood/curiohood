/* CurioHood · 微信分享卡片
 * 作用：让微信内「发送给朋友 / 分享到朋友圈」显示自定义标题、描述与缩略图。
 * 前提（缺一不可，详见《CurioHood 微信分享卡片配置指南.md》）：
 *   1) 已认证的服务号（订阅号不行）；
 *   2) 公众号后台把 www.curiohoodtravel.com 写入「JS接口安全域名」并放好 MP_verify_xxx.txt；
 *   3) 页面注入 window.CURIOHOOD_WX（appId / timestamp / nonceStr / signature 由服务端算好）。
 * 没有配置时本文件什么都不做，不会报错、不会阻塞页面。
 */
(function () {
  var cfg = window.CURIOHOOD_WX;
  if (!cfg || !cfg.appId || !cfg.signature) return;
  if (!/MicroMessenger/i.test(navigator.userAgent)) return;

  var link = cfg.link || location.href.split('#')[0];

  var s = document.createElement('script');
  s.src = 'https://res.wx.qq.com/open/js/jweixin-1.6.0.js';
  s.onload = function () {
    if (!window.wx) return;
    wx.config({
      debug: false,
      appId: cfg.appId,
      timestamp: cfg.timestamp,
      nonceStr: cfg.nonceStr,
      signature: cfg.signature,
      jsApiList: ['updateAppMessageShareData', 'updateTimelineShareData']
    });
    wx.ready(function () {
      wx.updateAppMessageShareData({
        title: cfg.title,
        desc: cfg.desc,
        link: link,
        imgUrl: cfg.imgUrl
      });
      wx.updateTimelineShareData({
        title: cfg.title,
        link: link,
        imgUrl: cfg.imgUrl
      });
    });
  };
  document.head.appendChild(s);
})();
