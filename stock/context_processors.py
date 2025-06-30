from stock.models import BasePermission, BaseVisible, Category, Cart, CartItem, ComparisonPrice, PurchaseOrder, PurchaseRequisition, UserProfile, PositionBasePermission, ComparisonPriceDistributor, RequisitionItem, BaseBranchCompany, Document
from stock.views import _cart_id, is_purchasing
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from django.db import connection
from collections import Counter
from django.contrib.auth.decorators import login_required

def findCompanyIn(request):
    active = request.session['company_code']
    #หาหน้าต่างการมองเห็นบริษัททั้งหมดของ user
    try:
        user_profile = UserProfile.objects.get(user = request.user.id)
        company_all = BaseBranchCompany.objects.filter(userprofile = user_profile).values('code')
    except:
        company_all = ""

    if active == "ALL":
        company_in = company_all
    else:
        company_in = BaseBranchCompany.objects.filter(code = active).values('code')
    return company_in


def userVisibleTab(request):
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        visible_tab = BaseVisible.objects.filter(userprofile = user_profile)
    except:
        visible_tab = None

    return dict(visible_tab = visible_tab)

def companyVisibleTab(request):
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        company_tab = BaseBranchCompany.objects.filter(userprofile = user_profile)
        company_code = BaseBranchCompany.objects.filter(userprofile = user_profile).values('code')

        #ถ้าเป็นจัดซื้อ
        if is_purchasing(request.user):
                for i in company_tab:
                    setAlertPurchasingCompanyTab(request, i.code)
        elif is_approve(request.user):
            for i in company_tab:
                setAlertApproveCompanyTab(request, i.code, company_code)
        
    except:
        company_tab = None

    return dict(company_tab = company_tab)

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
    try:
        active = request.session['company_code']
    except:
        active = ""
    
    pending_count = 0
    #หาหน้าต่างการมองเห็นบริษัททั้งหมดของ user
    try:
        company_in = findCompanyIn(request)
    except:
        company_in = BaseBranchCompany.objects.filter(code = active).values('code')

    #ใบขอซื้อ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPR')
        isPermiss_pr = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPR', branch_company__code__in = company_in).values('branch_company__code')
    except:
        isPermiss_pr  = False

    try:
        in_company = BaseBranchCompany.objects.filter(userprofile = user_profile, code__in = isPermiss_pr).exists()
    except:
        pass


    #ถ้าเป็นผู้อนุมัติ
    pr_item_ap = None
    if(isPermiss_pr and in_company):
        try:
            #ดึงข้อมูล PurchaseRequisition
            pr_item_ap = PurchaseRequisition.objects.filter(purchase_status = 2, approver_status = 1, approver_user = request.user, branch_company__code__in = isPermiss_pr) #หาสถานะรอดำเนินการของผู้อนุมัติ
            #หาความยาวของ index PurchaseRequisition ที่มี สถานะรอดำเนินการของผู้อนุมัติ
            pending_count = pr_item_ap.count()
        except PurchaseRequisition.DoesNotExist:
            pass
        
    return pending_count

#เปลี่ยน flow ผู้มีสิทธิขอซื้อไม่ต้องกดอนุมัติ
#หาจำนวนสถานะรอดำเนินการในการอนุมัติของผู้มีสิทธิขอซื้อ
def approvePRCounter(request):
    try:
        active = request.session['company_code']
    except:
        active = ""

    try:
        company_in = findCompanyIn(request)
    except:
        company_in = ""

    pr_count = 0
    try:
        #ดึงข้อมูล PurchaseRequisition
        pr_item = PurchaseRequisition.objects.all().filter(purchase_user = request.user.id, purchase_status = 1, branch_company__code__in = company_in) #หาสถานะรอดำเนินการของผู้อนุมัติ
        #หาความยาวของ index PurchaseRequisition ที่มี สถานะรอดำเนินการของผู้อนุมัติ
        pr_count = pr_item.count()
    except PurchaseRequisition.DoesNotExist:
        pr_count = 0

    return pr_count

#หาจำนวนสถานะรอดำเนินการในการอนุมัติของผู้มีสั่งซื้อ
def approvePOCounter(request):
    try:
        active = request.session['company_code']
    except:
        active = ""
    
    try:
        company_in = findCompanyIn(request)
    except:
        company_in = BaseBranchCompany.objects.filter(code = active).values('code')

    po_count = 0
    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPO')
        isPermiss = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPO', branch_company__code__in = company_in).values('branch_company__code')
    except:
        isPermiss  = False

    try:
        in_company = BaseBranchCompany.objects.filter(userprofile = user_profile, code__in = isPermiss).exists()
    except:
        pass
    po_item = None
    #ถ้าเป็นผู้อนุมัติที่มีสิทธิ
    if isPermiss and in_company:
        try:
            #ดึงข้อมูล PurchaseOrder
            po_item = PurchaseOrder.objects.all().filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user__isnull = True, cp__isnull = True, branch_company__code__in = isPermiss) #หาสถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseOrder.DoesNotExist:
            po_item = None

    new_po = dict()
    if po_item:
        for obj in po_item:
            if obj not in new_po:
                new_po[obj] = obj

    #เคสที่ดึงมาจากใบเปรียบเทียบมีชื่อคนอนุมัติอยู่แล้ว
    cm_po_item = None
    if request.user.is_authenticated:
        try:
            #ดึงข้อมูล PurchaseOrder
            cm_po_item = PurchaseOrder.objects.all().filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user = request.user, branch_company__code__in = company_in) #หาสถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseOrder.DoesNotExist:
            cm_po_item = None
    
    if cm_po_item:
        for obj in cm_po_item:
            if obj not in new_po:
                new_po[obj] = obj
                
    po_count  =  len(new_po)
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
    pr_count = 0 #approvePRCounter(request)

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
    try:
        active = request.session['company_code']
    except:
        active = ""

    try:
        company_in = findCompanyIn(request)
    except:
        company_in = BaseBranchCompany.objects.filter(code = active).values('code')


    ''' สิทธิใบเปรียบเทียบแบบเก่าเปลี่ยนเป็นแบบ fix ชื่อ
    #ผู้ตรวจสอบ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        permiss = BasePermission.objects.filter(codename__in= ['CAECP1','CAECP2','CAECP3','CAECP4','CAECPD','CAECPA'])
        isPermissAE = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename__in= ['CAECP1','CAECP2','CAECP3','CAECP4','CAECPD','CAECPA']).prefetch_related(Prefetch('base_permission', queryset=permiss)).values('base_permission')
    except:
        isPermissAE = None

    try:
        in_company = BaseBranchCompany.objects.filter(userprofile = user_profile, code = active).exists()
    except:
        pass

    pmAE = []
    if(isPermissAE and in_company):
        for i in isPermissAE:
            obj = BasePermission.objects.get(id = i['base_permission'])
            pmAE.append(obj)

    #ผู้อนุมัติ
    try:
        permiss = BasePermission.objects.filter(codename__in= ['CAACP1','CAACP2','CAACP3','CAACP4','CAACPD','CAACPA'])
        isPermissAA = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename__in= ['CAACP1','CAACP2','CAACP3','CAACP4','CAACPD','CAACPA']).prefetch_related(Prefetch('base_permission', queryset=permiss)).values('base_permission')
    except:
        isPermissAA = None

    pmAA = []
    if(isPermissAA and in_company):
        for i in isPermissAA:
            obj = BasePermission.objects.get(id = i['base_permission'])
            pmAA.append(obj)

    ecm_item = []
    #ถ้าเป็นผู้ตรวจสอบ
    if(isPermissAE and in_company):
        try:
            for ae in pmAE:
                if ae.codename == 'CAECPD':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__cm_type = 1, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = company_in).values("cp")
                elif ae.codename == 'CAECPA':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__cm_type = 2, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = company_in).values("cp")
                else:
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__select_bidder_id__isnull = False, is_select = True, amount__range=(ae.ap_amount_min, ae.ap_amount_max), cp__cm_type_id__isnull = True, cp__branch_company__code__in = company_in).values("cp")
                ecm_item.append(obj)
        except ComparisonPriceDistributor.DoesNotExist:
            ecm_item = None

    ecp = []
    new_cm = dict()
    try:
        for item in ecm_item:
            ecp = ComparisonPrice.objects.filter(pk__in = item).distinct()
            if ecp:
                for obj in ecp:
                    if obj not in new_cm:
                        new_cm[obj] = obj
    except:
        pass


    acm_item = []
    #ถ้าเป็นผู้อนุมัติ
    if(isPermissAA and in_company):
        try:
            for aa in pmAA:
                if aa.codename == 'CAACPD':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__cm_type = 1, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = company_in).values("cp")
                elif aa.codename == 'CAACPA':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__cm_type = 2, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = company_in).values("cp")
                else:
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__select_bidder_id__isnull = False, is_select = True, amount__range=(aa.ap_amount_min, aa.ap_amount_max), cp__cm_type_id__isnull = True, cp__branch_company__code__in = company_in).values("cp")
                acm_item.append(obj)
        except ComparisonPriceDistributor.DoesNotExist:
            acm_item = None

    acp = []
    try:
        for item in acm_item:
            acp = ComparisonPrice.objects.filter(pk__in = item).distinct()
            if acp:
                for obj in acp:
                    if obj not in new_cm:
                        new_cm[obj] = obj
    except:
        pass
    '''
    
    cm_count = 0
    new_cm = dict()

    #ถ้าเป็นผู้ตรวจสอบ ใบเปรียบเทียบ
    ecm_item = []
    try:
        ecm_item = ComparisonPrice.objects.filter(examiner_status = 1, examiner_user = request.user, branch_company__code__in = company_in)
    except :
        ecm_item = None


    try:
        for obj in ecm_item:
            if obj not in new_cm:
                new_cm[obj] = obj
    except:
        pass


    #ถ้าเป็นผู้ตรวจสอบ ใบเปรียบเทียบ
    acm_item = []
    try:
        acm_item = ComparisonPrice.objects.filter(examiner_status = 2, approver_status = 1, approver_user = request.user, branch_company__code__in = company_in)
    except :
        acm_item = None
        
    try:
        for obj in acm_item:
            if obj not in new_cm:
                new_cm[obj] = obj
    except:
        pass

    #ถ้าเป็นผู้อนุมัติพิเศษ ใบเปรียบเทียบ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CASCP')
        isPermiss_scp = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CASCP', branch_company__code__in = company_in).values('branch_company__code', 'base_permission')
    except:
        isPermiss_scp  = None

    pmAA = []
    if(isPermiss_scp):
        for i in isPermiss_scp:
            obj = BasePermission.objects.get(id = i['base_permission'])
            pmAA.append(obj)


    cpd_item = []
    #ถ้าเป็นผู้อนุมัติที่มีสิทธิ
    if isPermiss_scp:
        for aa in isPermiss_scp:
            for pm in pmAA:
                try:
                    #ดึงข้อมูล PurchaseOrder
                    obj = ComparisonPriceDistributor.objects.filter(cp__examiner_status = 2,cp__approver_status = 2, cp__special_approver_status = 1, is_select = True, amount__range=(pm.ap_amount_min, pm.ap_amount_max), cp__cm_type_id__isnull = True, cp__branch_company__code = aa['branch_company__code']).values("cp")
                    cpd_item.append(obj)
                except ComparisonPriceDistributor.DoesNotExist:
                    pass
    
    scp = []
    try:
        for item in cpd_item:
            scp = ComparisonPrice.objects.filter(pk__in = item).distinct()
            if scp:
                for obj in scp:
                    if obj not in new_cm:
                        new_cm[obj] = obj
    except:
        pass
    

    cm_count =  len(new_cm)
    return cm_count


#รวมการรออนุมัติทุกใบ
def approveAllCounter(request):
    ap_all = 0
    pd_count = approvePendingCounter(request)
    pr_count = 0 #approvePRCounter(request)
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
    try:
        active = request.session['company_code']
    except:
        active = ""

    pr_count = 0
    #ถ้าเป็นเจ้าหน้าที่จัดซื้อ
    if(is_purchasing(request.user)):
        try:
            pr_count =  PurchaseRequisition.objects.filter(purchase_status_id = 2, approver_status_id = 2, organizer = request.user, is_complete = 0, branch_company__code = active).count()
        except PurchaseOrder.DoesNotExist:
            pr_count = 0
    return pr_count

def isPurchasingPR(request):
    is_purchasing_pr = isPurchasingPRCounter(request)

    if 'admin' in request.path:
        return {} #รีเทริ์นค่าเปล่า

    return dict(is_purchasing_pr = is_purchasing_pr)

def is_purchasing(user):
    return user.groups.filter(name='จัดซื้อ').exists()

def is_approve(user):
    return user.groups.filter(name='ผู้อนุมัติ').exists()

def addPOCounter(request):
    try:
        active = request.session['company_code']
    except:
        active = ""

    cp_count = 0
    if(is_purchasing(request.user)):
        try:
            cp_count = ComparisonPrice.objects.filter(Q(special_approver_status_id = 2) | Q(special_approver_status_id = 4), examiner_status_id = 2, approver_status_id = 2 , select_bidder__isnull = False, po_ref_no = "", branch_company__code = active, organizer = request.user ).count()
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


def receiveCounter(request):
    try:
        active = request.session['company_code']
    except:
        active = ""

    rc_count = 0
    if(is_purchasing(request.user)):
        try:
            rc_count = PurchaseOrder.objects.filter(approver_status_id = 2, is_receive = False, branch_company__code = active).count()
        except PurchaseOrder.DoesNotExist:
            pass
    return dict(rc_count = rc_count)

def setAlertPurchasingCompanyTab(request, tab):
    if tab == "S1":
        request.session['NUM_S1'] = findAllPurchasingAlert(request, tab)
    elif tab == "D1":
        request.session['NUM_D1'] = findAllPurchasingAlert(request, tab)
    elif tab == "I1":
        request.session['NUM_I1'] = findAllPurchasingAlert(request, tab)
    elif tab == "U1":
        request.session['NUM_U1'] = findAllPurchasingAlert(request, tab)
    elif tab == "G1":
        request.session['NUM_G1'] = findAllPurchasingAlert(request, tab)
    elif tab == "R1":
        request.session['NUM_R1'] = findAllPurchasingAlert(request, tab)
    elif tab == "Y1":
        request.session['NUM_Y1'] = findAllPurchasingAlert(request, tab)
    elif tab == "P1":
        request.session['NUM_P1'] = findAllPurchasingAlert(request, tab)
    elif tab == "B1":
        request.session['NUM_B1'] = findAllPurchasingAlert(request, tab)
    elif tab == "J1":
        request.session['NUM_J1'] = findAllPurchasingAlert(request, tab)
    elif tab == "P2":
        request.session['NUM_P2'] = findAllPurchasingAlert(request, tab)
    elif tab == "Y2":
        request.session['NUM_Y2'] = findAllPurchasingAlert(request, tab)
    elif tab == "Y4":
        request.session['NUM_Y4'] = findAllPurchasingAlert(request, tab)
    elif tab == "Y5":
        request.session['NUM_Y5'] = findAllPurchasingAlert(request, tab)
    return

def findAllPurchasingAlert(request, tab):
    try:
        cp_count = ComparisonPrice.objects.filter(Q(special_approver_status_id = 2) | Q(special_approver_status_id = 4), examiner_status_id = 2, approver_status_id = 2 , select_bidder__isnull = False, po_ref_no = "", branch_company__code = tab, organizer = request.user).count()
    except ComparisonPrice.DoesNotExist:
        cp_count = 0

    try:
        pr_count =  PurchaseRequisition.objects.filter(purchase_status_id = 2, approver_status_id = 2, organizer = request.user, is_complete = 0, branch_company__code = tab).count()
    except PurchaseOrder.DoesNotExist:
        pr_count = 0
    return cp_count + pr_count


def setAlertApproveCompanyTab(request, tab, company_code):
    code = BaseBranchCompany.objects.filter(code = tab).values('code')
    if tab == "S1":
        request.session['NUM_S1'] = findAllApproveAlert(request, code)
    elif tab == "D1":
        request.session['NUM_D1'] = findAllApproveAlert(request, code)
    elif tab == "I1":
        request.session['NUM_I1'] = findAllApproveAlert(request, code)
    elif tab == "U1":
        request.session['NUM_U1'] = findAllApproveAlert(request, code)
    elif tab == "G1":
        request.session['NUM_G1'] = findAllApproveAlert(request, code)
    elif tab == "R1":
        request.session['NUM_R1'] = findAllApproveAlert(request, code)
    elif tab == "Y1":
        request.session['NUM_Y1'] = findAllApproveAlert(request, code)
    elif tab == "P1":
        request.session['NUM_P1'] = findAllApproveAlert(request, code)
    elif tab == "B1":
        request.session['NUM_B1'] = findAllApproveAlert(request, code)
    elif tab == "J1":
        request.session['NUM_J1'] = findAllApproveAlert(request, code)
    elif tab == "P2":
        request.session['NUM_P2'] = findAllApproveAlert(request, code)
    elif tab == "Y2":
        request.session['NUM_Y2'] = findAllApproveAlert(request, code)
    elif tab == "Y4":
        request.session['NUM_Y4'] = findAllApproveAlert(request, code)
    elif tab == "Y5":
        request.session['NUM_Y5'] = findAllApproveAlert(request, code)
    elif tab == "ALL":
        request.session['NUM_ALL'] = findAllApproveAlert(request, company_code)
    return 

def findAllApproveAlert(request, tab):
    pending_count = 0
    pr_count = 0
    po_count = 0
    cm_count = 0

    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPR')
        isPermiss = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPR', branch_company__code__in = tab).values('branch_company__code')
    except:
        isPermiss  = False

    try:
        in_company = BaseBranchCompany.objects.filter(userprofile = user_profile, code__in = isPermiss).exists()
    except:
        pass

    if(isPermiss and in_company):
        try:
            #ดึงข้อมูล PurchaseRequisition
            pending_count = PurchaseRequisition.objects.filter(purchase_status = 2, approver_status = 1, approver_user = request.user, branch_company__code__in = isPermiss).count() #หาสถานะรอดำเนินการของผู้อนุมัติ
            #หาความยาวของ index PurchaseRequisition ที่มี สถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseRequisition.DoesNotExist:
            pending_count = 0

	#เปลี่ยน flow ผู้มีสิทธิขอซื้อไม่ต้องกดอนุมัติ
    '''
        try:
            #ดึงข้อมูล PurchaseRequisition
            pr_count = PurchaseRequisition.objects.filter(purchase_user = request.user.id, purchase_status = 1, branch_company__code__in = isPermiss).count() #หาสถานะรอดำเนินการของผู้อนุมัติ
            #หาความยาวของ index PurchaseRequisition ที่มี สถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseRequisition.DoesNotExist:
            pr_count = 0    
    '''

	#################################

	#get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPO')
        isPermiss_po = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPO', branch_company__code__in = tab).values('branch_company__code')
    except:
        isPermiss_po  = False

    po_item = None
    #ถ้าเป็นผู้อนุมัติที่มีสิทธิ
    if isPermiss_po:
        try:
            #ดึงข้อมูล PurchaseOrder
            po_item = PurchaseOrder.objects.filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user__isnull = True, cp__isnull = True, branch_company__code__in = isPermiss_po) #หาสถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseOrder.DoesNotExist:
            po_item = None

    new_po = dict()
    if po_item:
        for obj in po_item:
            if obj not in new_po:
                new_po[obj] = obj

    #เคสที่ดึงมาจากใบเปรียบเทียบมีชื่อคนอนุมัติอยู่แล้ว
    cm_po_item = None
    if request.user.is_authenticated:
        try:
            #ดึงข้อมูล PurchaseOrder
            cm_po_item = PurchaseOrder.objects.filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user = request.user, branch_company__code__in = tab) #หาสถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseOrder.DoesNotExist:
            cm_po_item = None
    
    if cm_po_item:
        for obj in cm_po_item:
            if obj not in new_po:
                new_po[obj] = obj
                
    po_count  =  len(new_po)
	

    ''' สิทธิการอนุมัติใบเปรียบเทียบเก่าเปลี่ยนเป็นแบบ fix ชื่อ
	########################################
	#ผู้ตรวจสอบ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        permiss = BasePermission.objects.filter(codename__in= ['CAECP1','CAECP2','CAECP3','CAECP4','CAECPD','CAECPA'])
        isPermissAE = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename__in= ['CAECP1','CAECP2','CAECP3','CAECP4','CAECPD','CAECPA']).prefetch_related(Prefetch('base_permission', queryset=permiss)).values('base_permission')
    except:
        isPermissAE = None

    pmAE = []
    if(isPermissAE):
        for i in isPermissAE:
            obj = BasePermission.objects.get(id = i['base_permission'])
            pmAE.append(obj)

    #ผู้อนุมัติ
    try:
        permiss = BasePermission.objects.filter(codename__in= ['CAACP1','CAACP2','CAACP3','CAACP4','CAACPD','CAACPA'])
        isPermissAA = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename__in= ['CAACP1','CAACP2','CAACP3','CAACP4','CAACPD','CAACPA']).prefetch_related(Prefetch('base_permission', queryset=permiss)).values('base_permission')
    except:
        isPermissAA = None

    pmAA = []
    if(isPermissAA):
        for i in isPermissAA:
            obj = BasePermission.objects.get(id = i['base_permission'])
            pmAA.append(obj)

    ecm_item = []
    #ถ้าเป็นผู้ตรวจสอบ
    if(isPermissAE):
        try:
            for ae in pmAE:
                if ae.codename == 'CAECPD':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__cm_type = 1, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = tab).values("cp")
                elif ae.codename == 'CAECPA':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__cm_type = 2, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = tab).values("cp")
                else:
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__select_bidder_id__isnull = False, is_select = True, amount__range=(ae.ap_amount_min, ae.ap_amount_max), cp__cm_type_id__isnull = True, cp__branch_company__code__in = tab).values("cp")
                ecm_item.append(obj)
        except ComparisonPriceDistributor.DoesNotExist:
            ecm_item = None

    ecp = []
    new_cm = dict()
    try:
        for item in ecm_item:
            ecp = ComparisonPrice.objects.filter(pk__in = item).distinct()
            if ecp:
                for obj in ecp:
                    if obj not in new_cm:
                        new_cm[obj] = obj
    except:
        pass


    acm_item = []
    #ถ้าเป็นผู้อนุมัติ
    if(isPermissAA):
        try:
            for aa in pmAA:
                if aa.codename == 'CAACPD':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__cm_type = 1, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = tab).values("cp")
                elif aa.codename == 'CAACPA':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__cm_type = 2, cp__select_bidder_id__isnull = False, cp__branch_company__code__in = tab).values("cp")
                else:
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__select_bidder_id__isnull = False, is_select = True, amount__range=(aa.ap_amount_min, aa.ap_amount_max), cp__cm_type_id__isnull = True, cp__branch_company__code__in = tab).values("cp")
                acm_item.append(obj)
        except ComparisonPriceDistributor.DoesNotExist:
            acm_item = None

    acp = []
    try:
        for item in acm_item:
            acp = ComparisonPrice.objects.filter(pk__in = item).distinct()
            if acp:
                for obj in acp:
                    if obj not in new_cm:
                        new_cm[obj] = obj
    except:
        pass
    '''

    new_cm = dict()
    #ถ้าเป็นผู้ตรวจสอบ ใบเปรียบเทียบ
    ecm_item = []
    try:
        ecm_item = ComparisonPrice.objects.filter(examiner_status = 1, examiner_user = request.user, branch_company__code__in = tab)
    except ComparisonPrice.DoesNotExist:
        ecm_item = None

    try:
        for obj in ecm_item:
            if obj not in new_cm:
                new_cm[obj] = obj
    except:
        pass


    #ถ้าเป็นผู้ตรวจสอบ ใบเปรียบเทียบ
    acm_item = []
    try:
        acm_item = ComparisonPrice.objects.filter(examiner_status = 2, approver_status = 1, approver_user = request.user, branch_company__code__in = tab)
    except ComparisonPrice.DoesNotExist:
        acm_item = None
        
    try:
        for obj in acm_item:
            if obj not in new_cm:
                new_cm[obj] = obj
    except:
        pass

    #ถ้าเป็นผู้อนุมัติพิเศษ ใบเปรียบเทียบ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CASCP')
        isPermiss_scp = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CASCP', branch_company__code__in = tab).values('branch_company__code', 'base_permission')
    except:
        isPermiss_scp  = None

    pmAA = []
    if(isPermiss_scp):
        for i in isPermiss_scp:
            obj = BasePermission.objects.get(id = i['base_permission'])
            pmAA.append(obj)


    cpd_item = []
    #ถ้าเป็นผู้อนุมัติที่มีสิทธิ
    if isPermiss_scp:
        for aa in isPermiss_scp:
            for pm in pmAA:
                try:
                    #ดึงข้อมูล PurchaseOrder
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 2, cp__special_approver_status = 1, is_select = True, amount__range=(pm.ap_amount_min, pm.ap_amount_max), cp__cm_type_id__isnull = True, cp__branch_company__code = aa['branch_company__code']).values("cp")
                    cpd_item.append(obj)
                except ComparisonPriceDistributor.DoesNotExist:
                    pass
    
    scp = []
    try:
        for item in cpd_item:
            scp = ComparisonPrice.objects.filter(pk__in = item).distinct()
            if scp:
                for obj in scp:
                    if obj not in new_cm:
                        new_cm[obj] = obj
    except:
        pass

    cm_count =  len(new_cm)

    return pending_count + pr_count + po_count + cm_count

def document(request):
    try:
        document = Document.objects.filter().order_by('-id')[0]
    except:
        document = None

    return dict(document = document)