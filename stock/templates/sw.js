// Service worker ของ Southern Group Stock
//
// หน้าที่:
//   1. ทำให้เว็บผ่านเกณฑ์ "installable PWA" ซึ่งเป็นเงื่อนไขบังคับของ App Badging API
//   2. รับ Web Push แล้วอัปเดต badge บนไอคอน แม้ผู้ใช้จะปิดแอปอยู่
//
// ตั้งใจไม่ทำ cache ใด ๆ เพราะหน้าเว็บทั้งหมดเป็น server-rendered จาก Django
// การ cache จะทำให้ผู้ใช้เห็นข้อมูลเก่า

const VERSION = 'stg-stock-v2';

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

    // ทั้ง iOS และ Chrome บังคับ userVisibleOnly คือ push ทุกครั้งต้องมี
    // notification ให้ผู้ใช้เห็น ถ้าไม่แสดงเอง เบราว์เซอร์จะขึ้นข้อความ
    // "เว็บไซต์นี้อัปเดตในเบื้องหลัง" ให้แทน ซึ่งดูแย่กว่า
    // จึงต้องแสดงเอง และคุมความถี่จากฝั่งเซิร์ฟเวอร์แทน
    event.waitUntil(
        Promise.all([
            self.registration.showNotification(title, {
                body: body,
                icon: '/media/company/android-chrome-192x192.png',
                badge: '/media/company/android-chrome-192x192.png',
                // tag เดิมเสมอ -- แจ้งเตือนใหม่จะแทนที่อันเก่าแทนที่จะกองซ้อนกัน
                tag: 'stg-stock-badge',
                renotify: false,
                data: { url: data.url || '/' }
            }),
            setBadge(count)
        ])
    );
});

function setBadge(count) {
    if (!('setAppBadge' in self.navigator)) return Promise.resolve();
    return (count > 0 ? self.navigator.setAppBadge(count) : self.navigator.clearAppBadge())
        .catch(function (e) { console.warn('SW badge failed:', e); });
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
