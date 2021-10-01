from stock.models import Category, Cart, CartItem, ComparisonPrice, PurchaseOrder, PurchaseRequisition, UserProfile, PositionBasePermission
from stock.views import _cart_id
from django.contrib.auth.models import User

#หมวดหมู่สินค้าที่ navbar
def menu_link(request):
    links = Category.objects.all() #เก็บ Category ทั้งหมด
    return dict(links=links)

def counter(request):
    item_count = 0

    #ถ้าเป็น admin
    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า
    else:
        # try เพื่อหาว่าได้สร้าง cart มาแล้วยัง
        try:
            #ดึงข้อมูล cart และ cartitem
            cart = Cart.objects.filter(cart_id = _cart_id(request)) #_cart_id(request) ดึงมาจาก session
            cart_item = CartItem.objects.all().filter(cart = cart[:1]) # cart[:1] คือ คอลัมภ์แรกของ cart ใน db คือดึง id ที่เหมือนกันกับตะกร้าสินค้าที่เราดึงมาบรรทัดก่อน

            #ลูปทุกรายการใน cart_item เพื่อรวมจำนวนชิ้นของ cart_item แต่ละอัน
            for item in cart_item:
                item_count += item.quantity
        except Cart.DoesNotExist:
            item_count = 0
        
    return dict(item_count = item_count)

#หาจำนวนสถานะรอดำเนินการในการอนุมัติของผู้มีสิทธิอนุมัติ
def approvePendingCounter(request):
    pending_count = 0
    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        permission = PositionBasePermission.objects.filter(position_id = user_profile.position_id )
    except:
        permission = None

    #ถ้าเป็นผู้อนุมัติ
    if permission:
        for permiss in permission:
            if(permiss.base_permission.codename == 'CAAPR'):
                try:
                    #ดึงข้อมูล PurchaseRequisition
                    pr_item = PurchaseRequisition.objects.all().filter(approver_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
                    #หาความยาวของ index PurchaseRequisition ที่มี สถานะรอดำเนินการของผู้อนุมัติ
                    pending_count = len(pr_item)
                except PurchaseRequisition.DoesNotExist:
                    pending_count = 0
        
    return pending_count

#หาจำนวนสถานะรอดำเนินการในการอนุมัติของผู้มีขอซื้อ
def approvePRCounter(request):
    pr_count = 0
    try:
        #ดึงข้อมูล PurchaseRequisition
        pr_item = PurchaseRequisition.objects.all().filter(purchase_user = request.user.id, purchase_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
        #หาความยาวของ index PurchaseRequisition ที่มี สถานะรอดำเนินการของผู้อนุมัติ
        pr_count = len(pr_item)
    except PurchaseRequisition.DoesNotExist:
        pr_count = 0

    return pr_count

#หาจำนวนสถานะรอดำเนินการในการอนุมัติของผู้มีขอซื้อ
def approvePOCounter(request):
    po_count = 0
    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        permission = PositionBasePermission.objects.filter(position_id = user_profile.position_id )
    except:
        permission = None

    #ถ้าเป็นผู้อนุมัติ
    if permission:
        for permiss in permission:
            if(permiss.base_permission.codename == 'CAAPO'):
                try:
                    #ดึงข้อมูล PurchaseOrder
                    po_item = PurchaseOrder.objects.all().filter(approver_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
                    #หาความยาวของ index PurchaseOrder ที่มี สถานะรอดำเนินการของผู้อนุมัติ
                    po_count = len(po_item)
                except PurchaseOrder.DoesNotExist:
                    po_count = 0

    return po_count

#รวมการรออนุมัติใบขอซื้อ
def allApprovePOCounter(request):
    all_po_ap = approvePOCounter(request)

    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า

    return dict(all_po_ap = all_po_ap)

#รวมการรออนุมัติใบสั่งซื้อ
def allApprovePRCounter(request):
    all_pr_ap = 0
    pd_count = approvePendingCounter(request)
    pr_count = approvePRCounter(request)

    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า
    else:
        all_pr_ap = pd_count + pr_count
    return dict(all_pr_ap = all_pr_ap)

def allApproveCPCounter(request):
    all_cp_ap = 0
    all_cp_ap = approveCPAllCounter(request)
    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า

    return dict(all_cp_ap = all_cp_ap)

#หาจำนวนสถานะรอดำเนินการในใบเปรียบเทียบราคาของผู้อนุมัติและผู้ตรวจสอบ
def approveCPAllCounter(request):
    cm_count = 0
    ecm_count = 0
    acm_count = 0
    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        permission = PositionBasePermission.objects.filter(position_id = user_profile.position_id )
    except:
        permission = None

    #ถ้าเป็นผู้อนุมัติ
    if permission:
        for permiss in permission:
            if(permiss.base_permission.codename == 'CAECP'):
                try:
                    #ดึงข้อมูล PurchaseOrder
                    e_item = ComparisonPrice.objects.all().filter(examiner_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
                    #หาความยาวของ index PurchaseOrder ที่มี สถานะรอดำเนินการของผู้อนุมัติ
                    ecm_count = len(e_item)
                except PurchaseOrder.DoesNotExist:
                    ecm_count = 0
            if(permiss.base_permission.codename == 'CAACP'):
                try:
                    #ดึงข้อมูล PurchaseOrder
                    a_item = ComparisonPrice.objects.all().filter(approver_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
                    #หาความยาวของ index PurchaseOrder ที่มี สถานะรอดำเนินการของผู้อนุมัติ
                    acm_count = len(a_item)
                except PurchaseOrder.DoesNotExist:
                    acm_count = 0
    cm_count = ecm_count + acm_count
    return cm_count


#รวมการรออนุมัติทุกใบ
def approveAllCounter(request):
    ap_all = 0
    pd_count = approvePendingCounter(request)
    pr_count = approvePRCounter(request)
    po_count = approvePOCounter(request)
    cm_count = approveCPAllCounter(request)

    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า
    else:
        ap_all = pd_count + pr_count + po_count + cm_count
    return dict(ap_all = ap_all)


def findBaseUrgency(request, id):
    if(id == 1):
        base_urgen = 'A'
    else:
        base_urgen = 'B'
    return dict(base_urgen = base_urgen)
