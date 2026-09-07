'use strict';
/*
 * PositionBasePermission admin:
 * เมื่อผู้ดูแลเลือก "ผู้ใช้" ให้ดึงตำแหน่งงานจาก UserProfile.position (ผ่าน AJAX)
 * แล้วตั้งค่าฟิลด์ "ตำแหน่งงาน" ให้อัตโนมัติ โดยไม่ต้องรีโหลดหน้า
 * ใช้ได้ทั้งหน้า add และ change
 * หมายเหตุ: การตรวจสอบจริงอยู่ฝั่งเซิร์ฟเวอร์ (form.clean()) สคริปต์นี้เป็นเพียง UX
 */
(function () {
    function init() {
        var $ = (window.django && window.django.jQuery) || window.jQuery;
        if (!$) { return; }

        var $user = $('#id_user');
        var $position = $('#id_position');
        if (!$user.length || !$position.length) { return; }

        // /admin/<...>/stock/positionbasepermission/{add|<id>/change}/  ->  .../user-position/
        var parts = window.location.pathname.split('/positionbasepermission/');
        if (parts.length < 2) { return; }
        var endpoint = parts[0] + '/positionbasepermission/user-position/';

        function showMessage(msg) {
            var $holder = $('#position_base_permission_msg');
            if (!$holder.length) {
                $holder = $('<p id="position_base_permission_msg" class="help" style="color:#ba2121;margin-top:4px;"></p>');
                var $row = $position.closest('.form-row, .field-position');
                ($row.length ? $row : $position.parent()).append($holder);
            }
            $holder.text(msg || '');
        }

        function setPosition(id, text) {
            id = String(id);
            if ($position.find('option[value="' + id + '"]').length === 0) {
                $position.append(new Option(text, id, true, true));
            }
            $position.val(id).trigger('change');
        }

        function clearPosition() {
            $position.val(null).trigger('change');
        }

        $user.on('change', function () {
            var userId = $user.val();
            showMessage('');
            if (!userId) { clearPosition(); return; }

            $.ajax({ url: endpoint, data: { user_id: userId }, dataType: 'json' })
                .done(function (data) {
                    if (data && data.ok) {
                        setPosition(data.position_id, data.position_name);
                    } else {
                        clearPosition();
                        showMessage((data && data.message) || 'ไม่พบตำแหน่งงานของผู้ใช้ที่เลือก');
                    }
                })
                .fail(function () {
                    clearPosition();
                    showMessage('เกิดข้อผิดพลาดในการดึงข้อมูลตำแหน่งงาน');
                });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
