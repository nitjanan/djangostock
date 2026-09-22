// Service worker ของ Southern Group Stock
//
// หน้าที่:
//   1. ทำให้เว็บผ่านเกณฑ์ "installable PWA" ซึ่งเป็นเงื่อนไขบังคับของ App Badging API
//   2. รับ Web Push แล้วอัปเดต badge บนไอคอน แม้ผู้ใช้จะปิดแอปอยู่
//
// ตั้งใจไม่ทำ cache ใด ๆ เพราะหน้าเว็บทั้งหมดเป็น server-rendered จาก Django
// การ cache จะทำให้ผู้ใช้เห็นข้อมูลเก่า

const VERSION = 'stg-stock-v3';

self.addEventListener('install', function (event) {
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(self.clients.claim());
});

// ต้องมี fetch handler เพื่อให้ Chrome ถือว่าติดตั้งได้ แต่ส่งต่อไปยังเครือข่ายตรง ๆ
self.addEventListener('fetch', function (event) {
    return;
});

// ---------------------------------------------------------------
// Web Push
// ---------------------------------------------------------------
self.addEventListener('push', function (event) {
    let data = {};
    try {
        data = event.data ? event.data.json() : {};
    } catch (e) {
        data = {};
    }

    const count = typeof data.count === 'number' ? data.count : 0;
    const title = data.title || 'Southern Group Stock';
    const body = data.body || 'มีรายการรอดำเนินการ';
    // เซิร์ฟเวอร์ตัดสินว่ารอบนี้ควรให้ผู้ใช้เห็นแบนเนอร์หรือไม่
    const notify = data.notify !== false;
    const silentMode = data.silent_mode || 'none';

    event.waitUntil(Promise.all([
        setBadge(count),
        handleNotification(title, body, data, notify, silentMode)
    ]));
});

function setBadge(count) {
    if (!('setAppBadge' in self.navigator)) return Promise.resolve();
    return (count > 0 ? self.navigator.setAppBadge(count) : self.navigator.clearAppBadge())
        .catch(function (e) { console.warn('SW badge failed:', e); });
}

function handleNotification(title, body, data, notify, silentMode) {
    // รอบเงียบโหมด 'none': ไม่แสดงอะไรเลย badge อัปเดตไปแล้วจาก setBadge()
    //
    // ผิดกติกา userVisibleOnly ซึ่งบังคับให้ push ทุกครั้งต้องมี notification
    // ผลข้างเคียงที่อาจเกิด: เบราว์เซอร์ขึ้นข้อความของตัวเองแทน
    // ("เว็บไซต์นี้อัปเดตในเบื้องหลัง") หรือเพิกถอนสิทธิ์ push ของเว็บนี้
    // แลกมากับโอกาสที่จะอัปเดต badge ได้เงียบจริง ๆ บน iOS
    //
    // โหมด 'show-close' คือแสดงแล้วปิดทันที -- ทดสอบบน iOS แล้วแบนเนอร์ยังโผล่
    // เก็บไว้ให้สลับกลับได้ถ้าโหมด 'none' มีปัญหา
    if (!notify && silentMode === 'none') {
        return Promise.resolve();
    }

    const tag = notify ? 'stg-stock-badge' : 'stg-stock-quiet';

    return self.registration.showNotification(title, {
        body: body,
        icon: '/media/company/android-chrome-192x192.png',
        badge: '/media/company/android-chrome-192x192.png',
        // tag เดิมเสมอ -- แจ้งเตือนใหม่แทนที่อันเก่าแทนที่จะกองซ้อนกัน
        tag: tag,
        renotify: false,
        silent: !notify,
        data: { url: data.url || '/' }
    }).then(function () {
        if (notify) return;
        return self.registration.getNotifications({ tag: tag }).then(function (list) {
            list.forEach(function (n) { n.close(); });
        });
    }).catch(function (e) {
        console.warn('SW showNotification failed:', e);
    });
}

// กดที่แจ้งเตือน -- โฟกัสแท็บที่เปิดอยู่ถ้ามี ไม่งั้นเปิดใหม่
self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    const target = (event.notification.data && event.notification.data.url) || '/';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
            for (const client of list) {
                if ('focus' in client) return client.focus();
            }
            if (self.clients.openWindow) return self.clients.openWindow(target);
        })
    );
});
