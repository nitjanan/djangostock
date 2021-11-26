from stock.models import BasePermission, BaseVisible, Category, Cart, CartItem, ComparisonPrice, PurchaseOrder, PurchaseRequisition, UserProfile, PositionBasePermission, ComparisonPriceDistributor, RequisitionItem
from stock.views import _cart_id, is_purchasing
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.db import connection

def userVisibleTab(request):
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        visible_tab = BaseVisible.objects.filter(userprofile = user_profile)
    except:
        visible_tab = None

    return dict(visible_tab = visible_tab)

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

#ใบขอซื้อ
#หาจำนวนสถานะรอดำเนินการในการอนุมัติของผู้มีสิทธิอนุมัติ
def approvePendingCounter(request):
    pending_count = 0
    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPR')
        isPermiss = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPR').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss  = False

    #ถ้าเป็นผู้อนุมัติ

    if(isPermiss):
        try:
            #ดึงข้อมูล PurchaseRequisition
            pr_item = PurchaseRequisition.objects.all().filter(purchase_status = 2, approver_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
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

#หาจำนวนสถานะรอดำเนินการในการอนุมัติของผู้มีสั่งซื้อ
def approvePOCounter(request):
    po_count = 0
    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPO')
        isPermiss = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPO').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss  = False

    #ถ้าเป็นผู้อนุมัติ
    if(isPermiss):
        try:
            #ดึงข้อมูล PurchaseOrder
            po_item = PurchaseOrder.objects.all().filter(approver_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
            #หาความยาวของ index PurchaseOrder ที่มี สถานะรอดำเนินการของผู้อนุมัติ
            po_count = len(po_item)
        except PurchaseOrder.DoesNotExist:
            po_count = 0

    return po_count

#รวมการรออนุมัติใบสั่งซื้อ
def allApprovePOCounter(request):
    all_po_ap = approvePOCounter(request)

    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า

    return dict(all_po_ap = all_po_ap)

#รวมการรอนุมัติใบขอซื้อ
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

    #ผู้ตรวจสอบ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        permiss = BasePermission.objects.filter(codename__in= ['CAECP1','CAECP2','CAECP3'])
        isPermissAE = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename__in= ['CAECP1','CAECP2','CAECP3']).prefetch_related(Prefetch('base_permission', queryset=permiss)).values('base_permission')
    except:
        isPermissAE = None

    if(isPermissAE):
        for i in isPermissAE:
            pmAE = BasePermission.objects.get(id = i['base_permission'])

    #ผู้อนุมัติ
    try:
        permiss = BasePermission.objects.filter(codename__in= ['CAACP1','CAACP2','CAACP3'])
        isPermissAA = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename__in= ['CAACP1','CAACP2','CAACP3']).prefetch_related(Prefetch('base_permission', queryset=permiss)).values('base_permission')
    except:
        isPermissAA = None

    if(isPermissAA):
        for i in isPermissAA:
            pmAA = BasePermission.objects.get(id = i['base_permission'])

    #ถ้าเป็นผู้ตรวจสอบ
    if(isPermissAE):
        try:
            #ดึงข้อมูล PurchaseOrder
            ecm_count = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__select_bidder_id__isnull = False, amount__range=(pmAE.ap_amount_min, pmAE.ap_amount_max)).values("cp").distinct().count()
        except ComparisonPriceDistributor.DoesNotExist:
            ecm_count = 0
    #ถ้าเป็นผู้อนุมัติ
    if(isPermissAA):
        try:
        #ดึงข้อมูล PurchaseOrder
            acm_count = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__select_bidder_id__isnull = False, amount__range=(pmAA.ap_amount_min, pmAA.ap_amount_max)).values("cp").distinct().count()
        except ComparisonPriceDistributor.DoesNotExist:
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

def isPurchasingPRCounter(request):
    pr_count = 0
    #ถ้าเป็นเจ้าหน้าที่จัดซื้อ
    if(request.user.groups.filter(name='Purchasing').exists()):
        try:
            data =  PurchaseRequisition.objects.filter(purchase_status_id = 2, approver_status_id = 2)
            #เช็คว่าใช้หมดแล้วหรือเปล่า
            for pr in data:
                ri_is_used = RequisitionItem.objects.filter(requisition_id = pr.requisition.id, is_used = True, quantity_pr__gt=0).count()
                ri_all = RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0).count()
                if ri_is_used == ri_all:
                    #ให้เอา pr ออกจากใน list
                    data = data.exclude(id = pr.id)
            pr_count = len(data)
        except PurchaseOrder.DoesNotExist:
            pr_count = 0
    return pr_count

def isPurchasingPR(request):
    is_purchasing_pr = isPurchasingPRCounter(request)

    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า

    return dict(is_purchasing_pr = is_purchasing_pr)

def addPOCounter(request):
    cp_count = 0
    if(request.user.groups.filter(name='Purchasing').exists()):
        try:
            cp_count = ComparisonPrice.objects.filter(select_bidder__isnull = False, po_ref_no = "", examiner_status_id = 2, approver_status_id = 2).count()
        except ComparisonPrice.DoesNotExist:
            pass
    return cp_count

def addPOAll(request):
    add_po_all = addPOCounter(request)

    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า

    return dict(add_po_all = add_po_all)

def purchasingAllConter(request):
    add_po = addPOCounter(request)
    pr_count = isPurchasingPRCounter(request)
    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า
    else:
        pc_all = add_po + pr_count
    return dict(pc_all = pc_all)

        

