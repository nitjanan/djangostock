from dis import dis
from multiprocessing import context
import numbers
from pickletools import decimalnl_short
import re
from turtle import numinput, title
from typing import cast
from unicodedata import decimal, numeric
from urllib import response
from django import forms
from django import http
from django.core import paginator
from django.db.models.fields import NullBooleanField
from django.db.models.query import QuerySet
from django.http import request, HttpResponseRedirect, HttpResponse ,JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext
from stock.models import BaseBranchCompany, BaseDepartment, BaseSparesType, BaseUnit, BaseUrgency, Category, Distributor, Position, Product, Cart, CartItem, Order, OrderItem, PurchaseOrder, PurchaseRequisition, Receive, ReceiveItem, Requisition, RequisitionItem, CrudUser, BaseApproveStatus, UserProfile,PositionBasePermission, PurchaseOrderItem,ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor, BasePermission, BaseVisible
from stock.forms import SignUpForm, RequisitionForm, RequisitionItemForm, PurchaseRequisitionForm, UserProfileForm, PurchaseOrderForm, PurchaseOrderPriceForm, ComparisonPriceForm, CPDModelForm, CPDForm, CPSelectBidderForm, PurchaseOrderFromComparisonPriceForm, ReceiveForm, ReceivePriceForm, PurchaseOrderReceiptForm, RequisitionMemorandumForm
from django.contrib.auth.models import Group,User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.auth.decorators import login_required, permission_required 
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.views.generic import ListView, View, TemplateView, DeleteView
from django.template.loader import render_to_string
from django.urls import reverse
from .filters import ComparisonPriceFilter, RequisitionFilter, PurchaseRequisitionFilter, PurchaseOrderFilter,ComparisonPriceFilter, ReceiveFilter
from .forms import PurchaseOrderItemFormset, PurchaseOrderItemModelFormset, PurchaseOrderItemInlineFormset, CPitemFormset, CPitemInlineFormset, ReceiveItemForm, RequisitionItemModelFormset, ReceiveItemInlineFormset
from django.forms import inlineformset_factory
import stripe, logging, datetime
from django.db.models import Prefetch
from .resources import ReceiveItemResource, DistributorResource
from tablib import Dataset
from django.db.models import Q
from django.core.cache import cache
import json
from django.core.serializers import serialize
from django.db.models import Count
import xlwt
from django.db.models import F, Func, Value, CharField
from django.db.models import Sum
from django.views.decorators.cache import cache_control

# Create your views here.
@login_required(login_url='signIn')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request, category_slug = None):
    '''
    catalogy show สินค้า
    '''

    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    products = None
    categories_page = None
    if category_slug != None :
        categories_page = get_object_or_404(Category, slug = category_slug) #เช็ค 404 คือเช็คว่ามีค่ามาไหม
        #products = Product.objects.all().filter(category = categories_page, available=True, affiliated =  company.affiliated) #ดึงข้อมูล Product จาก db ทั้งหมดโดยที่ available=True
        products = Product.objects.all().filter(category = categories_page, available=True)
    else :
        #products = Product.objects.all().filter(available=True, affiliated =  company.affiliated) #ดึงข้อมูล Product จาก db ทั้งหมดโดยที่ available=True
        products = Product.objects.all().filter(available=True)
    
    paginator = Paginator(products,20) #หมายถึงให้แสดงสินค้า 4 ต่อ 1 หน้า
    try:
        page = int(request.GET.get('page', '1')) #กำหนดหมายเลขหน้าแรกเปน str แล้วแปลงเปน int
    except:
        page = 1 #กำหนดหมายเลขหน้าเริ่มแรกเปน 1

    #กำหนดจำนวนชิ้นต่อหน้า
    try:
        productperPage = paginator.page(page)
    except (EmptyPage, InvalidPage):
        productperPage = paginator.page(paginator.num_pages)    
    
    '''
    #สร้าง page
    p = Paginator(products, 10)
    page = request.GET.get('page')
    productperPage = p.get_page(page)    
    '''


    '''
    first page
    '''
    #ใบขอซื้อ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPR')
        isPermiss_pr = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPR').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss_pr  = False

    #ถ้าเป็นผู้อนุมัติ

    pr_item_ap = None
    if(isPermiss_pr):
        try:
            #ดึงข้อมูล PurchaseRequisition
            pr_item_ap = PurchaseRequisition.objects.filter(purchase_status = 2, approver_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
            #หาความยาวของ index PurchaseRequisition ที่มี สถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseRequisition.DoesNotExist:
            pass

    new_pr = dict()
    if pr_item_ap:
        for obj in pr_item_ap:
            if obj not in new_pr:
                new_pr[obj] = obj

    try:
        #ดึงข้อมูล PurchaseRequisition
        pr_item_pc = PurchaseRequisition.objects.filter(purchase_user = request.user.id, purchase_status = 1) #หาสถานะรอดำเนินการของผู้อนุมัติ
    except PurchaseRequisition.DoesNotExist:
        pr_item_pc = None

    if pr_item_pc:
        for obj in pr_item_pc:
            if obj not in new_pr:
                new_pr[obj] = obj

    #ใบสั่งซื้อ
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPO')
        isPermiss_po = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPO').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss_po  = False

    po_item = None
    #ถ้าเป็นผู้อนุมัติที่มีสิทธิ
    if isPermiss_po:
        try:
            #ดึงข้อมูล PurchaseOrder
            po_item = PurchaseOrder.objects.all().filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user__isnull = True) #หาสถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseOrder.DoesNotExist:
            pass

    new_po = dict()
    if po_item:
        for obj in po_item:
            if obj not in new_po:
                new_po[obj] = obj

    cm_po_item = None
    #เคสที่ดึงมาจากใบเปรียบเทียบมีชื่อคนอนุมัติอยู่แล้ว
    if request.user.is_authenticated:
        try:
            #ดึงข้อมูล PurchaseOrder
            cm_po_item = PurchaseOrder.objects.all().filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user = request.user) #หาสถานะรอดำเนินการของผู้อนุมัติ
        except PurchaseOrder.DoesNotExist:
            cm_po_item = None
    
    if cm_po_item:
        for obj in cm_po_item:
            if obj not in new_po:
                new_po[obj] = obj

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
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__cm_type = 1, cp__select_bidder_id__isnull = False).values("cp")
                elif ae.codename == 'CAECPA':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__cm_type = 2, cp__select_bidder_id__isnull = False).values("cp")
                else:
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 1, cp__select_bidder_id__isnull = False, is_select = True, amount__range=(ae.ap_amount_min, ae.ap_amount_max), cp__cm_type_id__isnull = True).values("cp")
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
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__cm_type = 1, cp__select_bidder_id__isnull = False).values("cp")
                elif aa.codename == 'CAACPA':
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__cm_type = 2, cp__select_bidder_id__isnull = False).values("cp")
                else:
                    obj = ComparisonPriceDistributor.objects.filter( cp__examiner_status = 2,cp__approver_status = 1, cp__select_bidder_id__isnull = False, is_select = True, amount__range=(aa.ap_amount_min, aa.ap_amount_max), cp__cm_type_id__isnull = True).values("cp")
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


    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        visible_tab = BaseVisible.objects.filter(userprofile = user_profile)
    except:
        visible_tab = None
    
    isHaveTab = False
    for tab in visible_tab:
        if 'Category' in tab.name:
            isHaveTab = True
            break

    if isHaveTab:
        return render(request,'index.html', {'products':productperPage , 'category':categories_page})
    else:
        return render(request,'firstPage.html', {'prs':new_pr,'pos':new_po,'cms':new_cm})


def productPage(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug = category_slug, slug = product_slug)
    except Exception as e:
        raise e
    return render(request,'product.html', {'product':product})

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


@login_required(login_url='signIn') #ถ้า addCart แล้วยังไม่ได้ login ก็ให้ไปหน้า signIn
def addCart(request, product_id):
    #ส่งรหัสสินค้ามา
    #ดึงสินค้าตามรหัสที่ส่งมา
    product = Product.objects.get(id=product_id) #หา Product จาก id ที่ส่งมา
    #สร้างตะกร้าสินค้า
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) #หาตะกร้าสินค้า
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request)) #ถ้าไม่มีตะกร้าสินค้าให้สร้างใหม่
        cart.save()

    #ซื้อสินค้าอันนี้คือกดเพิ่มสินค้า
    try:
        #ซื้อรายการสินค้าซ้ำ
        cart_item = CartItem.objects.get(product=product,cart=cart) #หาว่ามี cart_item หรือยัง
        if cart_item.quantity < cart_item.product.stock :
            #เพิ่มจำนวนสินค้า
            cart_item.quantity += 1
            #บันทึกลงฐานข้อมูล
            cart_item.save()
    except CartItem.DoesNotExist :
        #หา CartItem คือสั่งรายการครั้งแรก
        #สร้าง CartItem และ บันทึกลงฐานข้อมูล
        cart_item = CartItem.objects.create(
            product = product,
            cart = cart,
            quantity = 1,
        )
        cart_item.save()
    return redirect('cartdetail')


def cartdetail(request):
    total = 0 #ผลรวมสินค้าทั้งหมดในตะกร้า
    counter = 0 #จำนวนสินค้าทั้งหมด
    cart_items = None 

    try:
        cart = Cart.objects.get(cart_id = _cart_id(request)) #ดึงตะกร้า
        cart_items = CartItem.objects.filter(cart = cart, active = True) #ดึงข้อมูลสินค้าในตะกร้า
        for item in cart_items:
            total+=(item.product.price*item.quantity) #ผลรวมของสินค้าทุกชิ้น
            counter+=item.quantity #ผลรวมของจำนวนสินค้าทุกชิ้น
    except Exception as e:
        pass #ไม่ต้องทำไร

    stripe.api_key = settings.SECRET_KEY
    strip_total = int(total*100) #เช่น 800 strip มองเป็น 8 เลยต้อง  *100
    description = "Payment Online"
    data_key = settings.PUBLIC_KEY

    if request.method == "POST":
        try:
            #ชื่อจากใน POST เอามาจากปริ้นคำสั่ง print(request.POST) แล้ว link ฟิลด์กับ order ที่หน้า admin
            token = request.POST['stripeToken']
            email = request.POST['stripeEmail']
            name = request.POST['stripeBillingName']
            address = request.POST['stripeBillingAddressLine1']
            city = request.POST['stripeBillingAddressCity']
            postcode = request.POST['stripeShippingAddressZip']

            # print(request.POST)

            customer = stripe.Customer.create(
                email = email,
                source = token,
            )

            charge = stripe.Charge.create(
                amount = strip_total,
                currency = "thb",
                description = description,
                customer = customer.id
            )

            #บันทึกข้อมูลใบสั่งซื้อ (ดึงข้อมูลจาก request.POST ไป save ใน db order)
            order = Order.objects.create(
                name = name,
                address = address,
                city = city,
                postcode = postcode,
                total = total,
                email = email,
                token = token,
            )
            order.save()

            #บันทึกรายการสั่งซื้อ
            #ใน cart_items มีสินค้าเช่น รองเท้า, กระเป๋า เลยต้องวนลูปทุกตัว
            for item in cart_items:
                order_item = OrderItem.objects.create(
                    product = item.product.name,
                    quantity = item.quantity,
                    price = item.product.price,
                    order = order,
                )
                order_item.save()

                #ลดจำนวน stock หลังจากที่จ่ายเงินแล้ว
                product = Product.objects.get(id = item.product.id) #หา product จาก product id
                product.stock = int(item.product.stock - item.quantity) #จำนวนสินค้าในสต็อก = ในสต็อก - ที่ซื้อ
                product.save() #บันทึก

                item.delete() #ล้างตะกร้าสินค้า
            return redirect('thankyou')

        except stripe.error.CardError as e:
            return False, e

    return render(request,'cartdetail.html',
    dict(cart_items=cart_items, total = total, counter = counter,
    data_key = data_key, strip_total = strip_total, description = description))

def removeCart(request, product_id):
    #หา cart ที่เลือกอยู๋ A
    cart = Cart.objects.get(cart_id = _cart_id(request))
    #หาสินค้าที่เลือกจะลบ 2
    product = get_object_or_404(Product,id = product_id)

    #ลบรายการที่มี product และ cart ตรงกับที่เลือกอยู๋
    cartItem = CartItem.objects.get(product = product, cart = cart)
    #ลบรายการสินค้า 2 ที่อยู่ในตะกร้า A
    cartItem.delete()
    return redirect('cartdetail')

def signUpView(request):
    #ถ้าส่งข้อมูลจาก form signup มา
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            #บันทึกข้อมูล User
            user = form.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            profile.save()
            #บันทึก Group Customer
            #ดึง username จากฟอร์มมาใช้
            username = form.cleaned_data.get('username')
            #ดึง user จาก db มาใช้
            signUpUser = User.objects.get(username = username)
            #จัด Group
            #customer_group = Group.objects.get(name = "Customer")
            #customer_group.user_set.add(signUpUser)
            return redirect('signIn')

    else:
        form = SignUpForm()
        profile_form = UserProfileForm()
    context = {'form':form, 'profile_form':profile_form}
    return render(request, "signup.html", context)

def signInView(request):
    companys = BaseBranchCompany.objects.all()
    if request.method == 'POST':
        form = AuthenticationForm(data = request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            company = request.POST['company']
            user = authenticate(username=username,password=password)
            #ถ้าล็อกอินสำเร็จไปหน้า home else ให้ไปสมัครใหม่
            if user is not None:
                #เซลชั่น
                request.session['company_code'] = company.split("-",1)[0]
                request.session['company'] = company.split("-",1)[1]
                login(request, user)
                return redirect('home')
            else:
                return redirect('signUp')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form':form,'companys':companys })

def signOutView(request):
    logout(request)
    return redirect('signIn')

def search(request):
    name = request.GET['title']
    products = Product.objects.filter(name__icontains=name)
    return render(request,'index.html', {'products':products})

def orderHistory(request):
    #ดึง order ทั้งหมดของ user คนนี้
    if request.user.is_authenticated:
        email = str(request.user.email) #หา order จาก email เพราะ  email ไม่มีทางซ้ำกันอยู่แล้ว
        orders = Order.objects.filter(email=email)#ดึง order ทั้งหมด
    return render(request, 'orders.html', {'orders':orders})

def viewOrder(request, order_id):
    #ดึง order ที่เลือกของ user คนนี้
    if request.user.is_authenticated:
        email = str(request.user.email) #หา order จาก email เพราะ  email ไม่มีทางซ้ำกันอยู่แล้ว
        order = Order.objects.get(email=email, id=order_id) #ดึง order ที่เลือก
        order_items = OrderItem.objects.filter(order= order) #หา OrderItem
    return render(request, 'viewOrder.html', {'order':order, 'order_items': order_items})

def thankyou(request):
    return render(request, 'thankyou.html')

def requisitionPageMode(mode):
    if mode == 1:
        return 'requisitions_page'
    elif mode == 2:
        return 'ap_pr_page'
    elif mode == 4:
        return 'h_requisitions_page'
    elif mode == 5:
        return 'h_i_pr_page'

def requisitionShowMode(mode):
    if mode == 1:
        return 'requisitions_show'
    elif mode == 2:
        return 'ap_pr_show'
    elif mode == 4:
        return 'h_requisitions_show'
    elif mode == 5:
        return 'h_i_pr_show'

def PRPageMode(mode):
    if mode == 1:
        return 'pr_page'
    elif mode == 2:
        return 'ap_pr_page'
    elif mode == 3:
        return 'rc_page'
    elif mode == 4:
        return 'h_pr_page'
    elif mode == 5:
        return 'h_i_pr_page'

def PRShowMode(mode):
    if mode == 1:
        return 'pr_show'
    elif mode == 2:
        return 'ap_pr_show'
    elif mode == 3:
        return 'rc_show'
    elif mode == 4:
        return 'h_pr_show'
    elif mode == 5:
        return 'h_i_pr_show'

def CPPageMode(mode):
    if mode == 1:
        return 'cp_page'
    elif mode == 2:
        return 'ap_cp_page'
    elif mode == 3:
        return 'rc_page'
    elif mode == 4:
        return 'h_cp_page'
    elif mode == 5:
        return 'h_i_cp_page'

def CPShowMode(mode):
    if mode == 1:
        return 'cp_show'
    elif mode == 2:
        return 'ap_cp_show'
    elif mode == 3:
        return 'rc_show'
    elif mode == 4:
        return 'h_cp_show'
    elif mode == 5:
        return 'h_i_cp_show'

def POPageMode(mode):
    if mode == 1:
        return 'po_page'
    elif mode == 2:
        return 'ap_po_page'
    elif mode == 3:
        return 'rc_page'
    elif mode == 4:
        return 'h_po_page'
    elif mode == 5:
        return 'h_i_po_page'

def POShowMode(mode):
    if mode == 1:
        return 'po_show'
    elif mode == 2:
        return 'ap_po_show'
    elif mode == 3:
        return 'rc_show'
    elif mode == 4:
        return 'h_po_show'
    elif mode == 5:
        return 'h_i_po_show'

@login_required(login_url='signIn')
@permission_required('auth.view_user', login_url='requisition')
def requisitionAll(request):
    data = Requisition.objects.all()
    myFilter = RequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs
    return render(request,'requisitionAll.html',{'requisitions':data, 'filter':myFilter})

def requisitionItemAll(request, requisition_id):
    #ดึงใบเบิกของ
    data = Requisition.objects.get(id = requisition_id)
    #ดึงสินค้าในใบเบิกของ
    items = RequisitionItem.objects.filter(requisition_id=requisition_id)

    # form สินค้าในใบเบิกของ
    form = RequisitionItemForm(request.POST or None, initial={'requisition_id': requisition_id})
    if form.is_valid():
        form.save()
        return redirect('createRequisitionItem', requisition_id = requisition_id)

def findStatusApprove(request, id, status):
    try:
        user = User.objects.get(id = id)
        if(status != 'รออนุมัติ'):
            approve_name = user.first_name + " " + user.last_name
        else:
            approve_name = ""
    except:
        approve_name = ""
    return approve_name

#ใช้ได้เหมือนกันกับ  CrudView 
def crudRequisitionItemView(request, requisition_id):
    users = RequisitionItem.objects.filter(requisition_id = requisition_id)
    requisition = Requisition.objects.get(id = requisition_id)

    user_login = User.objects.get(id = request.user.id)

    #หาชื่อหัวหน้างาน
    chief_approve_name = findStatusApprove(request, requisition.chief_approve_user_id, requisition.chief_approve_status)
    #หาชื่อเจ้าหน้าที่พัสดุ
    supplies_approve_name = findStatusApprove(request, requisition.supplies_approve_user_id, requisition.supplies_approve_status)
    
    context = {
        'users': users,
        'requisition': requisition,
        'chief_approve_name': chief_approve_name,
        'supplies_approve_name': supplies_approve_name,
    }
    if request.method == 'POST':
        status = request.POST['status'] or None
        obj = Requisition.objects.get(id = requisition_id)
        if(user_login.has_perm('auth.change_user')):
            obj.chief_approve_status = status
            obj.chief_approve_user_id = request.user.id
        if(user_login.has_perm('auth.add_user')):
            obj.supplies_approve_status = status
            obj.supplies_approve_user_id = request.user.id
        obj.save()
        return redirect('crudRequisitionItemView', requisition_id = requisition_id)
    
    return render(request, "requisitionItemDetail.html", context)
    
@login_required(login_url='signIn')
def requisition(request):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    '''
    data = Requisition.objects.filter(Q(created__year__gte = year,
                              created__month__gte= month,
                              created__year__lte = year,
                              created__month__lte = month) | Q(purchase_requisition_id__isnull = True))   
    '''
    data = Requisition.objects.filter(purchase_requisition_id__isnull = True)

    #กรองข้อมูล
    myFilter = RequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
            'requisitions':dataPage,
            'filter':myFilter,
            'requisitions_page': "tab-active",
            'requisitions_show': "show",
    }

    return render(request,'requisition/viewRequisition.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def createRequisition(request):
    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    form = RequisitionForm(request.POST or None)
    if form.is_valid():
        form = RequisitionForm(request.POST or None, request.FILES)
        new_contact = form.save(commit=False)
        new_contact.supplies_approve_user_name_id = request.user.id
        new_contact.branch_company = company

        try:
            userProfile = UserProfile.objects.get(user = new_contact.name)
            new_contact.section = userProfile.department
        except UserProfile.DoesNotExist:
            pass
        new_contact.save()
        return HttpResponseRedirect(reverse('crud_ajax', args=(new_contact.pk,)))

    context = {
        'form':form,
        'requisitions_page': "tab-active",
        'requisitions_show': "show",
    }
    return render(request, "requisition/createRequisition.html", context)

def removeRequisition(request, id):
    requisition = Requisition.objects.get(id = id)
    #ลบ item ใน Requisition ด้วย
    items = RequisitionItem.objects.filter(requisition_id = id)
    items.delete()
    #ลบ Requisition ทีหลัง
    requisition.delete()
    return redirect('requisition')

def editRequisition(request, id):
    requisition = Requisition.objects.get(id=id)
    form = RequisitionForm(instance=requisition)

    if request.method == 'POST':
        form = RequisitionForm(request.POST, request.FILES, instance=requisition)
        if form.is_valid():
            new_contact = form.save()
            try :
                obj = PurchaseRequisition.objects.get(requisition = new_contact.pk)
                obj.purchase_user_id = requisition.chief_approve_user_name
                obj.save()
            except PurchaseRequisition.DoesNotExist :
                pass
            return redirect('requisition')

    context = {
        'form':form,
        'requisitions_page': "tab-active",
        'requisitions_show': "show",
    }
    return render(request, "requisition/createRequisition.html", context)

def createRequisitionItem(request, requisition_id):
    template_name = 'requisitionItem/createRequisitionItem.html'
    heading_message = 'Model Formset Demo'

    requisition = Requisition.objects.get(id=requisition_id)

    formset = RequisitionItemModelFormset(request.POST or None, queryset=RequisitionItem.objects.none())
    if request.method == 'POST':
        formset = RequisitionItemModelFormset(request.POST or None)
        if formset.is_valid():
            # save po item
            for form in formset:
                # only save if name is present
                if form.cleaned_data.get('product_name'):
                    obj = form.save(commit=False)
                    obj.requisition_id = requisition.id
                    obj.requisit = requisition
                    obj.quantity_pr = int(obj.quantity) - int(obj.quantity_take)
                    obj.save()
            #redirect นอก loop
            return redirect('viewPO')

    context = {
        'requisition':requisition,
        'po_page': "tab-active",
        'po_show': "show",
        'formset': formset,
        'heading': heading_message,
    }
    return render(request, template_name, context)

def removeRequisitionItem(request, item_id):
    item = RequisitionItem.objects.get(id = item_id)
    requisition = Requisition.objects.get(id = item.requisition_id)
    item.delete()
    return redirect('createRequisitionItem', requisition_id = requisition.id)

def editRequisitionItem(request, item_id):
    item = get_object_or_404(RequisitionItem, id = item_id)
    requisit = Requisition.objects.get(id = item.requisition_id)
    item_all = RequisitionItem.objects.filter(requisition_id = item.requisition_id)
    form = RequisitionItemForm(instance=item )

    if request.method == 'POST':
        form = RequisitionItemForm(request.POST, instance=item )
        return redirect('createRequisitionItem', requisition_id = requisit.id)
    else:
        form = RequisitionItemForm(instance=item)
        return redirect('createRequisitionItem', requisition_id = requisit.id)


# class CrudView(PermissionRequiredMixin, TemplateView):
#    raise_exception = True 
#    permission_required = 'stock.cruduser.change_cruduser'

class CrudView(TemplateView):
    template_name = 'requisition/crud.html'
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args,**kwargs)
        context['users'] = RequisitionItem.objects.filter(requisition_id = self.kwargs['requisition_id'])
        requisition = Requisition.objects.get(id=self.kwargs['requisition_id'])
        context['requisition'] = requisition
        try:
            pr = PurchaseRequisition.objects.get(id = requisition.purchase_requisition_id)
        except:
            pr = ""
            
        context['pr'] = pr
        context['baseUrgency'] = BaseUrgency.objects.all()
        context['baseUnit'] = BaseUnit.objects.all()
        context['requisitions_page'] = "tab-active"
        context['requisitions_show'] = "show"
        
        return context

class CreateCrudUser(View):

    def  get(self, request, *args, **kwargs):
        name1 = request.GET.get('name', None)
        description1 = request.GET.get('description', None)
        quantity1 = request.GET.get('quantity', None)
        quantityTake1 = request.GET.get('quantity_take', None)
        machine1 = request.GET.get('machine', None)
        desireddate1 = request.GET.get('desired_date', None) or None
        unit1 = request.GET.get('unit', None)
        urgency1 = request.GET.get('urgency', None)
        product1 = request.GET.get('product', None)
        
        try:
            product_item = get_object_or_404(Product, id=product1)
        except:
            product_item = None

        try:
            if(not quantityTake1):
                quantityTake1 = 0
            quantityPQ  = int(quantity1) - int(quantityTake1)
        except:
            quantityPQ = 0

        rqs = Requisition.objects.get(id=kwargs['requisition_id'])

        obj = RequisitionItem.objects.create(
            requisition_id = kwargs['requisition_id'],
            product_name = name1,
            description = description1,
            quantity = quantity1,
            quantity_take = 0,
            quantity_pr = quantityPQ,
            machine = machine1,
            desired_date = desireddate1,
            unit = unit1,
            urgency = urgency1,
            requisit = rqs,
            product = product_item,
        )

        user = {'id':obj.id,'name':obj.product_name,'description':obj.description,
        'quantity':obj.quantity,'quantity_take':obj.quantity_take,'machine':obj.machine,'desired_date':obj.desired_date,
        'unit':obj.unit, 'urgency': obj.urgency}

        data = {
            'user': user
        }
        return JsonResponse(data)

class UpdateCrudUser(View):

    def  get(self, request, *args, **kwargs):
        id1 = request.GET.get('id', None)
        name1 = request.GET.get('name', None)
        description1 = request.GET.get('description', None)
        quantity1 = request.GET.get('quantity', None)
        quantityTake1 = request.GET.get('quantity_take', None)
        machine1 = request.GET.get('machine', None)
        desireddate1 = request.GET.get('desired_date', None)
        unit1 = request.GET.get('unit', None)
        urgency1 = request.GET.get('urgency', None)
        product1 = request.GET.get('product', None)

        try:
            product_item = get_object_or_404(Product, id=product1)
        except:
            product_item = None

        try:
            quantityPQ  = int(quantity1) - int(quantityTake1)
        except:
            quantityPQ = 0

        obj = RequisitionItem.objects.get(id=id1)
        obj.requisition_id = kwargs['requisition_id']
        obj.product_name = name1
        obj.description = description1
        obj.quantity = quantity1
        obj.quantity_take = quantityTake1
        obj.quantity_pr = quantityPQ
        obj.machine = machine1
        obj.desired_date = desireddate1
        obj.unit = unit1
        obj.urgency = urgency1
        obj.product = product_item
        obj.save()


        user = {'id':obj.id,'name':obj.product_name,'description':obj.description,
        'quantity':obj.quantity,'quantity_take':obj.quantity_take,'machine':obj.machine,'desired_date':obj.desired_date,
        'unit':obj.unit, 'urgency':obj.urgency}

        data = {
            'user': user
        }
        return JsonResponse(data)

class DeleteCrudUser(View):
    def  get(self, request):
        id1 = request.GET.get('id', None)
        RequisitionItem.objects.get(id=id1).delete()
        data = {
            'deleted': True
        }
        return JsonResponse(data)

def editAllRequisition(request, requisition_id):
    users = RequisitionItem.objects.filter(requisition_id = requisition_id)
    requisition = Requisition.objects.get(id=requisition_id)
    try:
        pr = PurchaseRequisition.objects.get(id = requisition.purchase_requisition_id)
    except:
        pr = ""
            
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()

    #form save
    form = RequisitionForm(instance=requisition)

    if request.method == 'POST':
        form = RequisitionForm(request.POST, request.FILES , instance=requisition)
        if form.is_valid():
            new_contact =  form.save()
            try :
                obj = PurchaseRequisition.objects.get(requisition = new_contact.pk)
                obj.purchase_user_id = requisition.chief_approve_user_name
                obj.save()
            except PurchaseRequisition.DoesNotExist :
                pass
            return redirect('editAllRequisition', requisition_id = requisition.id)

    context = {
        'form':form,
        'users': users,
        'requisition': requisition,
        'pr': pr,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        'requisitions_page':"tab-active",
        'requisitions_show':"show",
    }

    return render(request, "requisition/editAllRequisition.html", context)

def showRequisition(request, requisition_id, mode):
    items = RequisitionItem.objects.filter(requisition_id = requisition_id)
    requisition = Requisition.objects.get(id=requisition_id)
    try:
        pr = PurchaseRequisition.objects.get(id = requisition.purchase_requisition_id)
    except:
        pr = ""
            
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()

    page = requisitionPageMode(mode)
    show = requisitionShowMode(mode)

    context = {
        'items': items,
        'requisition': requisition,
        'pr': pr,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        page:"tab-active",
        show:"show",
    }

    return render(request, "requisition/showRequisition.html", context)


@login_required(login_url='signIn')
def viewPR(request):

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)

    ri_not_used = RequisitionItem.objects.filter(is_used = False, quantity_pr__gt=0)
    #ถ้าเป็นจัดซื้อให้ดึงมาเฉพาะที่ ผู้ขอซื้อ กับ ผู้อนุมัติ อนุมัติแล้ว
    if isPurchasing:
        data = PurchaseRequisition.objects.filter(purchase_status_id = 2, approver_status_id = 2, organizer = request.user)

        #เช็คว่าใช้หมดแล้วหรือเปล่า
        for pr in data:
            ri_is_used = RequisitionItem.objects.filter(requisition_id = pr.requisition.id, is_used = True, quantity_pr__gt=0).count()
            ri_all = RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0).count()
            if ri_is_used == ri_all:
                #ให้เอา pr ออกจากใน list
                data = data.exclude(id = pr.id)
    else:
        data = PurchaseRequisition.objects.filter(Q(purchase_status_id = 1) | Q(approver_status_id = 1) & ~Q(purchase_status_id = 3))

    #กรองข้อมูล
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)

    baseUrgency = BaseUrgency.objects.all()
    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
                'prs':dataPage,
                'filter':myFilter,
                'isPurchasing':isPurchasing,
                'ri_not_used':ri_not_used,
                'baseUrgency':baseUrgency,
                'pr_page': "tab-active",
                'pr_show': "show",
              }

    return render(request,'purchaseRequisition/viewPR.html',context)

def preparePR(request):

    requisitions = Requisition.objects.filter(purchase_requisition_id__isnull = True)

    #สร้าง page
    paginator = Paginator(requisitions,10) #หมายถึงให้แสดงสินค้า 4 ต่อ 1 หน้า
    try:
        page = int(request.GET.get('page', '1')) #กำหนดหมายเลขหน้าแรกเปน str แล้วแปลงเปน int
    except:
        page = 1 #กำหนดหมายเลขหน้าเริ่มแรกเปน 1

    #กำหนดจำนวนชิ้นต่อหน้า
    try:
        dataPage = paginator.page(page)
    except (EmptyPage, InvalidPage):
        dataPage = paginator.page(paginator.num_pages)

    items = RequisitionItem.objects.filter(quantity_pr__gt=0)
    context = {
        'requisitions':dataPage,
        'items':items,
        'pr_page': "tab-active",
        'pr_show': "show",
    }
    return render(request,'purchaseRequisition/preparePR.html', context)

def is_purchasing(user):
    return user.groups.filter(name='จัดซื้อ').exists()

def is_supplies(user):
    return user.groups.filter(name='พัสดุ').exists()

def is_edit_po_id(user):
    return user.groups.filter(name='แก้ไขรหัสใบสั่งซื้อ').exists()

def get_bool(str):
    if str == 'True':
        bol  = True
    elif str == 'False':
        bol =  False
    return bol

def createPR(request, requisition_id):
    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    items= RequisitionItem.objects.filter(requisition_id = requisition_id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=requisition_id)
    baseUrgency = BaseUrgency.objects.all() #ระดับความเร่งด่วน
    baseUnit = BaseUnit.objects.all()
    #หา id express
    baseProduct = Product.objects.all().values('id', 'name')

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)
        
    #หาจำนวนสินค้าทั้งหมด
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    first_items = RequisitionItem.objects.filter(requisition_id = requisition_id, quantity_pr__gt=0).first()
    #form
    form = PurchaseRequisitionForm(request.POST or None, initial={'note': first_items.description})
    if form.is_valid():
        #save id express
        bool = saveIdExpressPR(request)
        if bool is None:
            #save PR
            new_contact = form.save()
            new_contact.branch_company = company
            #save requisition ใน purchase_requisition_id
            pr = PurchaseRequisition.objects.get(id = new_contact.pk)
            pr.requisition = requisition
            pr.purchase_status_id = 1 #กำหนดค่าเริ่มต้น
            pr.purchase_user_id = requisition.chief_approve_user_name
            # set ให้ผู้ขอซื้ออนุมัติมาเลย
            pr.purchase_status_id = 2
            pr.purchase_update = datetime.datetime.now()

            pr.approver_status_id = 1 #กำหนดค่าเริ่มต้น
            #พัสดุ
            pr.stockman_user_id = request.user.id
            pr.stockman_update = datetime.datetime.now()
            #เจ้าหน้าที่จัดซื้อ
            pr.organizer = requisition.organizer

            pr.save()

            #save purchase_requisition_id ใน requisition
            obj = Requisition.objects.get(id = requisition_id)
            obj.purchase_requisition_id = new_contact.pk
            obj.pr_ref_no = pr.ref_no
            obj.save()
            return HttpResponseRedirect(reverse('viewPR'))

    #context
    context = {
        'items':items,
        'requisition':requisition,
        'quantityTotal': quantityTotal,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        'form':form,
        'baseProduct':baseProduct,
        'isPurchasing':isPurchasing,
        'pr_page': "tab-active",
        'create_mode': True,
        'pr_show': "show",
    }
    return render(request,'purchaseRequisition/createPR.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def createCMorPO(request, pr_id):
    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #หา id express
    baseProduct = Product.objects.all().values('id', 'name')

    #หาจำนวนสินค้าทั้งหมด
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr
    
    listItem = request.POST.getlist('choices')

    if request.method=='POST' and 'btnformCM' in request.POST:
        cp = ComparisonPrice.objects.create(
            organizer = request.user,
            approver_status_id = 1,
            examiner_status_id = 1,
            branch_company = company,
            note = pr.note,
        )
        cp.save()

        cpd = ComparisonPriceDistributor.objects.create(
            cp_id = cp.id,
            vat_type_id = 0
        )
        cpd.save()
        for i in listItem:
            #บอกสถานะว่าใช้ไปใน CM หรือ PR แล้ว
            ri = RequisitionItem.objects.get(id = i)
            ri.is_used = True
            ri.save()

            item = ComparisonPriceItem.objects.create(
                item_id = i,
                bidder_id = cpd.id,
                cp = cp.id,
                quantity = ri.quantity_pr,
                unit = ri.product.unit
            )
            item.save()
        return HttpResponseRedirect(reverse('editComparePricePOItemFromPR', args=(cp.id, cpd.id)))
    if request.method=='POST' and 'btnformPO' in request.POST:
        po = PurchaseOrder.objects.create(
            stockman_user = request.user,
            approver_status_id = 1,
            vat_type_id = 0,
            pr = pr,
            branch_company = company,
        )
        po.save()

        for i in listItem:
            #บอกสถานะว่าใช้ไปใน CM หรือ PR แล้ว
            ri = RequisitionItem.objects.get(id = i)
            ri.is_used = True
            ri.save()

            item = PurchaseOrderItem.objects.create(
                item_id = i,
                quantity = ri.quantity_pr,
                po_id = po.id,
                unit = ri.product.unit
            )
            item.save()
        return HttpResponseRedirect(reverse('editPOFromPR', args=(po.id,)))

    context = {
        'items':items,
        'requisition':requisition,
        'quantityTotal': quantityTotal,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        'baseProduct':baseProduct,        
        'pr': pr,
        'pr_page': "tab-active",
        'pr_show': "show",
    }
    return render(request,'purchaseRequisition/createCMorPO.html',context)

def removePR(request, pr_id):
    pr = PurchaseRequisition.objects.get(id = pr_id)
    requisition = Requisition.objects.get(purchase_requisition_id = pr_id)
    requisition.purchase_requisition_id = None
    requisition.pr_ref_no = None
    requisition.save()
    pr.delete()
    return redirect('viewPR')

def editPR(request, pr_id):
    pr = PurchaseRequisition.objects.get(id=pr_id)
    form = PurchaseRequisitionForm(instance=pr)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #หา id express
    baseProduct = Product.objects.all().values('id', 'name')

    #หาจำนวนสินค้าทั้งหมด
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    if request.method == 'POST':
        form = PurchaseRequisitionForm(request.POST, instance=pr)
        if form.is_valid():
            new_contact = form.save()
            #save id express
            saveIdExpressPR(request)
            
            return redirect('viewPR')

    context = {
        'items':items,
        'requisition':requisition,
        'quantityTotal': quantityTotal,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        'form':form,
        'baseProduct':baseProduct,
        'pr': pr,
        'create_mode': False,
        'pr_page': "tab-active",
        'pr_show': "show",
    }
    return render(request, "purchaseRequisition/createPR.html", context)

def showPR(request, pr_id, mode):
    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #หา id express
    baseProduct = Product.objects.all().values('id', 'name')

    #หาจำนวนสินค้าทั้งหมด
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    page = PRPageMode(mode)
    show = PRShowMode(mode)

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)
    #ถ้า user login เป็นจัดซื้อ
    isSupplies = is_supplies(request.user)

    # re approver แสดงเฉพาะหน้า history complete และ history incomplete เท่านั้น
    isReApprove = False
    if (mode == 4 or mode == 5) and (isPurchasing or isSupplies):
        isReApprove = True

    form = RequisitionMemorandumForm(instance=requisition)
    if request.method == 'POST':
        form = RequisitionMemorandumForm(request.POST, request.FILES, instance=requisition)
        if form.is_valid():
            form.save()
            return redirect('viewPRHistory')

    context = {
            'items':items,
            'requisition':requisition,
            'quantityTotal': quantityTotal,
            'baseUrgency': baseUrgency,
            'baseUnit': baseUnit,
            'baseProduct':baseProduct,
            'pr': pr,
            'create_mode': False,
            page: "tab-active",
            show: "show",
            'form':form,
            'isReApprove': isReApprove
    }

    return render(request, "purchaseRequisition/showPR.html", context)

@require_http_methods(["POST"])
def saveIdExpressPR(request):
    try:
        list_id = request.POST.getlist('id') or None
        if list_id:
            list_id = list(map(int, list_id))
            list_product = request.POST.getlist('product') or None
            try:
                list_product = list(map(int, list_product))
            except ValueError:
                pass
            for i, val_id in enumerate(list_id):
                for j, val_product in enumerate(list_product):
                    if i == j:
                        item = get_object_or_404(RequisitionItem, id=val_id)
                        if val_product != "":
                            try:
                                product_item = get_object_or_404(Product, id=val_product)
                                item.product = product_item
                            except:
                                return False
                            item.save()
                    else:
                        pass
    except stripe.error.CardError as e:
        return False, e


@login_required(login_url='signIn')
def viewPRApprove(request):
    data = PurchaseRequisition.objects.filter(Q(purchase_status_id = 1)| Q(approver_status_id = 1) & ~Q(purchase_status_id = 3))

    #กรองข้อมูล
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
                'prs':dataPage,
                'filter':myFilter,
                'ap_pr_page': "tab-active",
                'ap_pr_show': "show",
              }

    return render(request,'purchaseRequisitionApprove/viewPRApprove.html',context)

def editPRApprove(request, pr_id, isFromHome):
    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()

    #หาจำนวนสินค้าทั้งหมด
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPR')
        isPermiss = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPR').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss  = False

    context = {
        'items':items,
        'requisition':requisition,
        'quantityTotal': quantityTotal,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        'pr':pr,
        'isPermiss':isPermiss,
        'isFromHome':isFromHome,
        'ap_pr_page': "tab-active",
        'ap_pr_show': "show",
    }

    if request.method == 'POST':
        post_status = request.POST['status'] or None
        status = BaseApproveStatus.objects.get(name = post_status)

        obj = PurchaseRequisition.objects.get(id = pr_id)
        #ผู้ขอซื้อ
        if(obj.purchase_user_id == request.user.id):
            obj.purchase_status = status
            obj.purchase_update = datetime.datetime.now()
        #ผู้อนุมัติ
        if(isPermiss):
            obj.approver_status = status
            obj.approver_user_id = request.user.id
            obj.approver_update = datetime.datetime.now()
        #หากอนุมัติแล้วแก้ใบขอเบิกไม่ได้
        if obj.purchase_status_id != 1 or obj.approver_status_id != 1:
            r = Requisition.objects.get(purchase_requisition_id = obj.id)
            r.is_edit = False
            r.save()
        obj.save()
        return redirect('editPRApprove', pr_id = pr_id, isFromHome = isFromHome)

    return render(request, "purchaseRequisitionApprove/editPRApprove.html", context)

@login_required(login_url='signIn')
def viewPO(request):
    data = PurchaseOrder.objects.filter(Q(approver_status_id = 1) | Q(is_receive = False) & ~Q(approver_status_id = 3))

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = PurchaseOrderItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','po')

    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs': prs,
        'po_page': "tab-active",
        'po_show': "show",
    }
    return render(request, "purchaseOrder/viewPO.html", context)

def preparePO(request):
    return render(request, 'purchaseOrder/preparePO.html')

def createPO(request):
    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    # set ค่าเริ่มต้นของเจ้าหน้าที่พัสดุ และสเตตัสการอนุมัติเป็น รอดำเนินการ
    form = PurchaseOrderForm(request.POST or None)
    if form.is_valid():
        form = PurchaseOrderForm(request.POST or None, request.FILES)
        new_contact = form.save(commit=False)
        new_contact.stockman_user = request.user
        new_contact.approver_status_id = 1
        new_contact.branch_company = company
        new_contact.save()
        return HttpResponseRedirect(reverse('createPOItem', args=(new_contact.pk,)))

    context = {
        'form':form,
        'po_page': "tab-active",
        'po_show': "show",
    }

    return render(request, "purchaseOrder/createPO.html", context)

def editPO(request, po_id):
    po = PurchaseOrder.objects.get(id=po_id)
    form = PurchaseOrderForm(instance=po)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        if form.is_valid():
            form.save()
            return redirect('viewPO')

    context = {
        'form':form,
        'po_page': "tab-active",
        'po_show': "show",
    }

    return render(request, "purchaseOrder/createPO.html", context)

def editPOFromPR(request, po_id):
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    po = PurchaseOrder.objects.get(id=po_id)
    form = PurchaseOrderForm(instance=po, initial={'tax': 1})
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, request.FILES, instance=po, initial={'tax': 1})
        if form.is_valid():
            form.save()
            return redirect('editPOItem', po_id = po_id, isFromPR = 'True', isReApprove = 'False')

    context = {
        'form':form,
        'distributorList': distributorList,
        'po_page': "tab-active",
        'po_show': "show",
    }

    return render(request, "purchaseOrder/createPO.html", context)

def editPOFromComparison(request, po_id):
    po = PurchaseOrder.objects.get(id=po_id)
    form = PurchaseOrderFromComparisonPriceForm(instance=po)
    if request.method == 'POST':
        form = PurchaseOrderFromComparisonPriceForm(request.POST, instance=po)
        if form.is_valid():
            form.save()
            return redirect('viewPO')

    context = {
        'form':form,
        'po_page': "tab-active",
        'po_show': "show",
    }

    return render(request, "purchaseOrder/createPO.html", context)

def removePO(request, po_id):
    po = PurchaseOrder.objects.get(id = po_id)
    #ลบ item ใน PurchaseOrder ด้วย
    items = PurchaseOrderItem.objects.filter(po = po)
    for obj in items:
        try:
            d_item = RequisitionItem.objects.get(id = obj.item.id)
            d_item.is_used = False
            d_item.save()
        except RequisitionItem.DoesNotExist:
            pass

    items.delete()

    #ล้าง po_ref_no ที่ผูกไว้
    try:
        cp = ComparisonPrice.objects.get(po_ref_no = po.ref_no)
        cp.po_ref_no = ""
        cp.save()
    except (ComparisonPrice.DoesNotExist, AttributeError):
        pass

    #ลบ PurchaseOrder ทีหลัง
    po.delete()
    return redirect('viewPO')

def showPO(request, po_id, mode):
    po = PurchaseOrder.objects.get(id = po_id)
    items = PurchaseOrderItem.objects.filter(po = po)

    new_pr_id = dict()
    if items:
        for obj in items:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

    new_pr = dict()
    for id in new_pr_id:
        try:
            pr = PurchaseRequisition.objects.get(id = id)
            new_pr[pr] = pr
        except PurchaseRequisition.DoesNotExist:
            pass
    
    page = POPageMode(mode)
    show = POShowMode(mode)

    form = PurchaseOrderReceiptForm(instance=po)
    if request.method == 'POST':
        form = PurchaseOrderReceiptForm(request.POST, request.FILES, instance=po)
        if form.is_valid():
            form.save()
            return redirect('viewPOHistory')

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)
    #ถ้า user login เป็นจัดซื้อ
    isSupplies = is_supplies(request.user)
    isUploadeReceipt = False
    if isPurchasing or isSupplies:
        isUploadeReceipt = True

    context = {
            'po':po,
            'items':items,
            'new_pr':new_pr,
            'form': form,
            'isUploadeReceipt':isUploadeReceipt,
            'isPurchasing':isPurchasing,
            'mode': mode,
            page: "tab-active",
            show: "show",
    }
    return render(request, 'purchaseOrder/showPO.html',context)

def createPOItem(request, po_id):
    template_name = 'purchaseOrderItem/createPOItem.html'
    heading_message = 'Model Formset Demo'
    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)

    po_data = PurchaseOrder.objects.get(id=po_id)
    if request.method == 'GET':
        formset = PurchaseOrderItemModelFormset(queryset=PurchaseOrderItem.objects.none())
        price_form = PurchaseOrderPriceForm()
    elif request.method == 'POST':
        formset = PurchaseOrderItemModelFormset(request.POST)
        price_form = PurchaseOrderPriceForm(request.POST, instance=po_data)
        if formset.is_valid() and price_form.is_valid():
            # save ราคาใบ po
            price = price_form.save(commit=False)
            if not price.discount:
                price.discount = 0.00
            if not price.freight:
                price.freight = 0.00
            price.save()

            # save po item
            for form in formset:
                # only save if name is present
                if form.cleaned_data.get('item'):
                    obj = form.save(commit=False)
                    obj.po = po_data
                    obj.save()
            #redirect นอก loop
            return redirect('viewPO')

    po = PurchaseOrder.objects.get(id = po_id)
    context = {
        'po':po,
        'po_page': "tab-active",
        'po_show': "show",
        'formset': formset,
        'price_form': price_form,
        'itemList':itemList,
        'heading': heading_message,
    }
    return render(request, template_name, context)

def editPOItem(request, po_id, isFromPR, isReApprove):
    template_name = 'purchaseOrderItem/editPOItem.html'
    heading_message = 'Model Formset Demo'

    #ถ้า user login แก้ไขรหัสใบสั่งซื้อได้
    isEditPO = is_edit_po_id(request.user)

    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    po_data = PurchaseOrder.objects.get(id = po_id)
    po_items = PurchaseOrderItem.objects.filter(po = po_id)
    form = PurchaseOrderForm(instance=po_data)
    if request.method == "POST":
        formset = PurchaseOrderItemInlineFormset(request.POST, request.FILES, instance=po_data)
        price_form = PurchaseOrderPriceForm(request.POST, instance=po_data)
        form = PurchaseOrderForm(request.POST, request.FILES, instance=po_data)
        if formset.is_valid() and price_form.is_valid() and form.is_valid():
            # save ราคาใบ po
            price = price_form.save(commit=False)
            if not price.discount:
                price.discount = 0.00
            if not price.freight:
                price.freight = 0.00

            're approve po'
            price.is_re_approve = get_bool(isReApprove)
            if get_bool(isReApprove) == True:
                price.approver_status_id = 1
                price.approver_update = None
            price.save()

            po_form = form.save()
            #แก้เลขที่ผูก cp po_ref_no
            try:
                cp = ComparisonPrice.objects.get(id = po_form.cp_id)
                cp.po_ref_no = po_form.ref_no
                cp.save()
            except ComparisonPrice.DoesNotExist:
                pass    

            # save po item
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
                try:
                    r_item = RequisitionItem.objects.get(id = instance.item.id)
                    r_item.is_used = True
                    r_item.save()
                except RequisitionItem.DoesNotExist:
                    pass
            for obj in formset.deleted_objects:
                try:
                    d_item = RequisitionItem.objects.get(id = obj.item.id)
                    d_item.is_used = False
                    d_item.save()
                except RequisitionItem.DoesNotExist:
                    pass
                obj.delete()
            formset.save_m2m()
            return redirect('viewPO')
    else:
        formset = PurchaseOrderItemInlineFormset(instance=po_data)
        price_form = PurchaseOrderPriceForm(instance=po_data)
        form = PurchaseOrderForm(instance=po_data)

    po = PurchaseOrder.objects.get(id = po_id)
    items = PurchaseOrderItem.objects.filter(po = po_id)

    new_pr_id = dict()
    if items:
        for obj in items:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

    new_pr = dict()
    for id in new_pr_id:
        try:
            pr = PurchaseRequisition.objects.get(id = id)
            new_pr[pr] = pr
        except PurchaseRequisition.DoesNotExist:
            pass

    context = {
        'po':po,
        'po_items':po_items,
        'po_page': "tab-active",
        'po_show': "show",
        'formset': formset,
        'price_form':price_form,
        'form': form,
        'isFromPR':isFromPR,
        'itemList':itemList,
        'new_pr':new_pr,
        'isEditPO':isEditPO,
        'distributorList': distributorList,
        'heading': heading_message,
    }
    return render(request, template_name, context)

@login_required(login_url='signIn')
def viewPOApprove(request):

    data = PurchaseOrder.objects.filter(approver_status_id = 1, amount__isnull = False, amount__gt = 0)

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
                'pos':dataPage,
                'filter':myFilter,
                'ap_po_page': "tab-active",
                'ap_po_show': "show",
              }

    return render(request,'purchaseOrderApprove/viewPOApprove.html',context)

def editPOApprove(request, po_id, isFromHome):
    po = PurchaseOrder.objects.get(id = po_id)
    items = PurchaseOrderItem.objects.filter(po = po)
    new_pr_id = dict()
    if items:
        for obj in items:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

    new_pr = dict()
    for id in new_pr_id:
        try:
            pr = PurchaseRequisition.objects.get(id = id)
            new_pr[pr] = pr
        except PurchaseRequisition.DoesNotExist:
            pass

    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPO')
        isPermiss = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPO').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss  = False

    if isPermiss and not po.approver_user:
        isPermiss  = True
    elif po.approver_user == request.user:
        isPermiss  = True

    if request.method == 'POST':
        post_status = request.POST['status'] or None
        status = BaseApproveStatus.objects.get(name = post_status)

        obj = PurchaseOrder.objects.get(id = po_id)
        #ผู้อนุมัติ
        if(isPermiss):
            obj.approver_status = status
            obj.approver_user_id = request.user.id
            obj.approver_update = datetime.datetime.now()
        obj.save()
        return redirect('editPOApprove', po_id = po_id, isFromHome = isFromHome)

    context = {
                'po':po,
                'items':items,
                'isPermiss':isPermiss,
                'isFromHome':isFromHome,
                'new_pr':new_pr,
                'ap_po_page': "tab-active",
                'ap_po_show': "show",
    }
    return render(request, 'purchaseOrderApprove/editPOApprove.html',context)

@login_required(login_url='signIn')
def viewComparePricePO(request):
    #data = ComparisonPrice.objects.filter(Q(examiner_status_id = 1) | Q(approver_status_id = 1))
    data = ComparisonPrice.objects.filter(Q(po_ref_no = "") & ~Q(examiner_status_id = 3) & ~Q(approver_status_id = 3))

    prs = ComparisonPriceItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','cp').annotate(Count('item')).order_by().filter(item__count__gt=0)

    #กรองข้อมูล
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.all()
    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    context = {
        'cps':dataPage,
        'prs': prs,
        'filter':myFilter,
        'bidder':bidder,
        'cp_page': "tab-active",
        'cp_show': "show",
    }

    return render(request, 'comparePricePO/viewComparePricePO.html',context)

def createComparePricePO(request):
    form = ComparisonPriceForm(request.POST or None, initial={'organizer': request.user.id, 'approver_status':1, 'examiner_status':1})
    if form.is_valid():
        new_contact = form.save()
        return HttpResponseRedirect(reverse('createComparePricePOItem', args=(new_contact.pk, 'False')))

    context = {
        'form':form,
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePO/createComparePricePO.html', context)

def editComparePricePO(request, cp_id):
    cp = ComparisonPrice.objects.get(id=cp_id)
    form = ComparisonPriceForm(instance=cp)
    if request.method == 'POST':
        form = ComparisonPriceForm(request.POST, instance=cp)
        if form.is_valid():
            form.save()
            return redirect('viewComparePricePO')

    context = {
        'form':form,
        'cp_page': "tab-active",
        'cp_show': "show",
    }

    return render(request, 'comparePricePO/createComparePricePO.html', context)

def removeComparePricePO(request, cp_id):
    cp = ComparisonPrice.objects.get(id = cp_id)

    bidder = ComparisonPriceDistributor.objects.filter(cp = cp_id)

    #ลบ item ใน ComparisonPriceItem ด้วย
    items = ComparisonPriceItem.objects.filter(cp = cp_id)
    for obj in items:
        try:
            d_item = RequisitionItem.objects.get(id = obj.item.id)
            d_item.is_used = False
            d_item.save()
        except RequisitionItem.DoesNotExist:
            pass
    items.delete()

    #ลบผู้จำหน่าย
    bidder.delete()

    #ลบใบเปรียบเทียบทีหลัง
    cp.delete()
    return redirect('viewComparePricePO')

def prepareComparePricePO(request):
    cp = ComparisonPrice.objects.create(
        organizer = request.user,
        approver_status_id = 1,
        examiner_status_id = 1,
    )
    cp.save()
    return HttpResponseRedirect(reverse('createComparePricePOItem', args=(cp.id, 'False')))

def createComparePricePOItem(request, cp_id, isReApprove):

    cp = ComparisonPrice.objects.get(id=cp_id)

    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    #ร้านแรก
    try:
        bidder = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('id').first()
        bidder_oldest = bidder.id
    except (ComparisonPriceDistributor.DoesNotExist, AttributeError):
        bidder_oldest = None

    #ร้านทั้งหมดในใบเปรียบเทียบ
    try:
        bidder_have = ComparisonPriceDistributor.objects.filter(cp = cp_id)
    except (ComparisonPriceDistributor.DoesNotExist, AttributeError):
        bidder_have = None

    if request.method == 'GET':
        bookform = CPDModelForm(request.GET or None, initial={'cp': cp_id})
        formset = CPitemFormset(queryset=ComparisonPriceItem.objects.none())
        're approve cp'
        cp.is_re_approve = get_bool(isReApprove)
        if get_bool(isReApprove) == True:
            cp.approver_user = None
            cp.approver_status_id = 1
            cp.approver_update = None
            cp.examiner_user= None
            cp.examiner_status_id = 1
            cp.examiner_update= None
            cp.save()

    elif request.method == 'POST':
        bookform = CPDModelForm(request.POST or None, request.FILES, initial={'cp': cp_id})
        formset = CPitemFormset(request.POST)
        if bookform.is_valid() and formset.is_valid():
            # first save this book, as its reference will be used in `Author`
            book = bookform.save(commit=False)
            if not book.discount:
                book.discount = 0.00
            if not book.freight:
                book.freight = 0.00
            book.save()

            for form in formset:
                # so that `book` instance can be attached.
                if form.cleaned_data.get('item'):
                    cpi = form.save(commit=False)
                    cpi.bidder = book 
                    cpi.cp = cp_id
                    cpi.save()
                    #ตัดสินค้าหน้า PR
                    try:
                        r_item = RequisitionItem.objects.get(id = cpi.item.id)
                        r_item.is_used = True
                        r_item.save()
                    except RequisitionItem.DoesNotExist:
                        pass
            return redirect('createComparePricePOItem', cp_id = cp_id, isReApprove = 'False')

    cpd = ComparisonPriceDistributor.objects.filter(cp = cp_id)
    cp_item = ComparisonPriceItem.objects.filter(cp = cp_id)
    
    context = {
        'link_cp_id':cp_id,
        'cpd':cpd,
        'cp_item':cp_item,
        'bidder_oldest':bidder_oldest,
        'bidder_have': bidder_have,
        'itemList': itemList,
        'bookform': bookform,
        'formset': formset,
        'distributorList': distributorList,
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePOItem/createComparePricePOItem.html',context)

def autocompalteDistributor(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        qs = Distributor.objects.filter(Q(id__icontains = term) | Q(name__icontains = term))[:10]
        titles = list()
        for obj in qs:
            titles.append(obj.id +"-"+ obj.name)
    return JsonResponse(titles, safe=False)

def editComparePricePOItemFromPR(request, cp_id , cpd_id):
    cp = ComparisonPrice.objects.get(id=cp_id)

    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    data = ComparisonPriceDistributor.objects.get(id = cpd_id)
    if request.method == "POST":
        formset = CPitemInlineFormset(request.POST, request.FILES, instance=data)
        bookform = CPDModelForm(request.POST, request.FILES, instance=data)

        if formset.is_valid() and bookform.is_valid():
            # save ราคาใบ po
            book = bookform.save(commit=False)
            if not book.discount:
                book.discount = 0.00
            if not book.freight:
                book.freight = 0.00
            book.save()

            # save po item
            instances = formset.save(commit=False)
            for instance in instances:
                instance.bidder = book
                instance.cp = cp_id
                instance.save()
                #ตัดสินค้าหน้า PR
                try:
                    r_item = RequisitionItem.objects.get(id = instance.item.id)
                    r_item.is_used = True
                    r_item.save()
                except RequisitionItem.DoesNotExist:
                    pass
            for obj in formset.deleted_objects:
                try:
                    d_item = RequisitionItem.objects.get(id = obj.item.id)
                    d_item.is_used = False
                    d_item.save()
                except RequisitionItem.DoesNotExist:
                    pass
                obj.delete()
            formset.save_m2m()
            return redirect('createComparePricePOItem', cp_id = cp_id, isReApprove = 'False')    
    else:
        bookform = CPDModelForm(instance=data)
        formset = CPitemInlineFormset(instance=data)

    cpd = ComparisonPriceDistributor.objects.filter(cp = cp_id)
    cp_item = ComparisonPriceItem.objects.filter(cp = cp_id)

    context = {
        'link_cp_id' : cp_id,
        'link_cpd_id' : cpd_id,
        'cpd':cpd,
        'cp_item':cp_item,
        'itemList':itemList,
        'bookform': bookform,
        'formset': formset,
        'distributorList': distributorList,
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePOItem/editComparePricePOItemFromPR.html',context)

def editComparePricePOItem(request, cp_id , cpd_id):
    cp = ComparisonPrice.objects.get(id=cp_id)

    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    data = ComparisonPriceDistributor.objects.get(id = cpd_id)
    numDistributor = ComparisonPriceDistributor.objects.filter(cp = cp_id).count()
    if request.method == "POST":
        formset = CPitemInlineFormset(request.POST, request.FILES, instance=data)
        bookform = CPDModelForm(request.POST, request.FILES, instance=data)

        if formset.is_valid() and bookform.is_valid():
            # save ราคาใบ po
            book = bookform.save(commit=False)
            if not book.discount:
                book.discount = 0.00
            book.save()

            # save po item
            instances = formset.save(commit=False)
            for instance in instances:
                instance.bidder = book 
                instance.cp = cp_id
                instance.save()
                #ตัดสินค้าหน้า PR
                try:
                    r_item = RequisitionItem.objects.get(id = instance.item.id)
                    r_item.is_used = True
                    r_item.save()
                except RequisitionItem.DoesNotExist:
                    pass
            for obj in formset.deleted_objects:
                if numDistributor == 1:
                    try:
                        d_item = RequisitionItem.objects.get(id = obj.item.id)
                        d_item.is_used = False
                        d_item.save()
                    except RequisitionItem.DoesNotExist:
                        pass   
                obj.delete()
            formset.save_m2m()
            return redirect('createComparePricePOItem',cp_id = cp_id, isReApprove = 'False')
    else:
        bookform = CPDModelForm(instance=data)
        formset = CPitemInlineFormset(instance=data)

    cpd = ComparisonPriceDistributor.objects.filter(cp = cp_id)
    cp_item = ComparisonPriceItem.objects.filter(cp = cp_id)

    context = {
        'link_cp_id' : cp_id,
        'link_cpd_id' : cpd_id,
        'cpd':cpd,
        'cp_item':cp_item,
        'itemList':itemList,
        'bookform': bookform,
        'formset': formset,
        'distributorList': distributorList,
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePOItem/editComparePricePOItem.html',context)

def removeComparePriceDistributor(request, cp_id, cpd_id):
    numDistributor = ComparisonPriceDistributor.objects.filter(cp = cp_id).count()
    cpd = ComparisonPriceDistributor.objects.get(id = cpd_id)
    #ลบ item ใน PurchaseOrder ด้วย
    items = ComparisonPriceItem.objects.filter(bidder = cpd)
    if numDistributor == 1:
        for obj in items:
            try:
                d_item = RequisitionItem.objects.get(id = obj.item.id)
                d_item.is_used = False
                d_item.save()
            except RequisitionItem.DoesNotExist:
                pass  
    items.delete()
    #ลบ PurchaseOrder ทีหลัง
    cpd.delete()
    return redirect('createComparePricePOItem', cp_id = cp_id, isReApprove = 'False')

def printComparePricePO(request, cp_id):
    try:
        bidder_oldest = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('id').first()
        items_oldest = ComparisonPriceItem.objects.filter(bidder = bidder_oldest.id)
    except (ComparisonPriceDistributor.DoesNotExist, ComparisonPriceItem.DoesNotExist, AttributeError):
        items_oldest = None

    pr_ref_no = ""
    new_pr_id = dict()
    if items_oldest:
        for obj in items_oldest:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

    new_pr = dict()
    for id in new_pr_id:
        try:
            pr = PurchaseRequisition.objects.get(id = id)
            pr_ref_no += pr.ref_no + ", "
            new_pr[pr] = pr
        except PurchaseRequisition.DoesNotExist:
            pass 

    cp = ComparisonPrice.objects.get(id=cp_id)
    form = CPSelectBidderForm(instance=cp)
    if request.method == 'POST':
        form = CPSelectBidderForm(request.POST, instance=cp)
        if form.is_valid():
            f_cp = form.save()
            select_bidder = ComparisonPriceDistributor.objects.get(cp = f_cp, distributor = f_cp.select_bidder)
            select_bidder.is_select = True
            if f_cp.select_bidder:
                f_cp.select_bidder_update = datetime.datetime.now()
            select_bidder.save()
            f_cp.save()
            return redirect('viewComparePricePO')

    bidder = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('amount')
    itemName = ComparisonPriceItem.objects.filter(cp = cp_id).order_by('bidder__amount')
    baseSparesType = BaseSparesType.objects.all()
    context = {
        'cp':cp,
        'bidder' : bidder,
        'items_oldest' : items_oldest,
        'itemName':itemName,
        'pr_ref_no': pr_ref_no,
        'new_pr': new_pr,
        'form':form,
        'baseSparesType' : baseSparesType,
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePO/printComparePricePO.html',context)

def showComparePricePO(request, cp_id, mode):
    try:
        bidder_oldest = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('id').first()
        items_oldest = ComparisonPriceItem.objects.filter(bidder = bidder_oldest.id)
    except (ComparisonPriceDistributor.DoesNotExist, ComparisonPriceItem.DoesNotExist, AttributeError):
        items_oldest = None

    cp = ComparisonPrice.objects.get(id=cp_id)
    baseSparesType = BaseSparesType.objects.all()

    bidder = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('amount')
    itemName = ComparisonPriceItem.objects.filter(cp = cp_id).order_by('bidder__amount')

    pr_ref_no = ""
    new_pr_id = dict()
    if items_oldest:
        for obj in items_oldest:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj
    
    new_pr = dict()
    for id in new_pr_id:
        try:
            pr = PurchaseRequisition.objects.get(id = id)
            pr_ref_no += pr.ref_no + ", "
            new_pr[pr] = pr
        except PurchaseRequisition.DoesNotExist:
            pass

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)

    page = CPPageMode(mode)
    show = CPShowMode(mode)
    context = {
            'cp':cp,
            'bidder' : bidder,
            'items_oldest' : items_oldest,
            'itemName':itemName,
            'baseSparesType':baseSparesType,
            'pr_ref_no': pr_ref_no,
            'new_pr': new_pr,
            'isPurchasing':isPurchasing,
            page: "tab-active",
            show: "show",
    }
    return render(request, 'comparePricePO/showComparePricePO.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def createPOFromComparisonPrice(request, cp_id):
    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    #ถ้า user login แก้ไขรหัสใบสั่งซื้อได้
    isEditPO = is_edit_po_id(request.user)

    #set ค่าเริ่มต้นของเจ้าหน้าที่พัสดุ และสเตตัสการอนุมัติเป็น รอดำเนินการ
    form = PurchaseOrderFromComparisonPriceForm(request.POST or None, initial={'cp': cp_id, 'tax': 1})
    if form.is_valid():
        try:
            new_contact = form.save(commit=False)
            cp = ComparisonPrice.objects.get(id = new_contact.cp.id)
            cpd = ComparisonPriceDistributor.objects.get(cp = new_contact.cp.id, distributor = cp.select_bidder)
            new_contact.distributor = cp.select_bidder
            new_contact.credit = cpd.credit
            new_contact.stockman_user = cp.organizer
            new_contact.vat_type = cpd.vat_type
            new_contact.quotation_pdf = cpd.quotation_pdf
            new_contact.approver_status_id = 1
            new_contact.approver_user = cp.approver_user
            new_contact.branch_company = company
        except:
            return HttpResponseRedirect(reverse('createPOFromComparisonPrice', args=(cp_id,)))
        else:
            new_contact.save()

            cp.po_ref_no = new_contact.ref_no
            cp.save()
            return HttpResponseRedirect(reverse('createPOItemFromComparisonPrice', args=(new_contact.pk,)))

    context = {
        'form':form,
        'isEditPO':isEditPO,
        'po_page': "tab-active",
        'po_show': "show",
    }

    return render(request, "purchaseOrder/createPO.html", context)

def createPOItemFromComparisonPrice(request, po_id):
    template_name = 'purchaseOrderItem/createPOItemFromComparisonPrice.html'
    heading_message = 'Model Formset Demo'
    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)

    po_data = PurchaseOrder.objects.get(id=po_id)
    po_items = PurchaseOrderItem.objects.filter(po = po_id)
    cp = ComparisonPrice.objects.get(id = po_data.cp.id)
    cp_item = ComparisonPriceItem.objects.filter(cp = po_data.cp.id, bidder__distributor = po_data.cp.select_bidder)
    cpd_price = ComparisonPriceDistributor.objects.get(cp = po_data.cp.id, distributor = po_data.cp.select_bidder)
    if request.method == 'GET':
        formset = PurchaseOrderItemModelFormset(queryset=PurchaseOrderItem.objects.none())
        price_form = PurchaseOrderPriceForm()
    elif request.method == 'POST':
        formset = PurchaseOrderItemModelFormset(request.POST)
        price_form = PurchaseOrderPriceForm(request.POST, instance=po_data)
        if formset.is_valid() and price_form.is_valid():

            # save ราคาใบ po
            price_form.save()
            # save po item
            for form in formset:
                # only save if name is present
                if form.cleaned_data.get('item'):
                    obj = form.save(commit=False)
                    obj.po = po_data
                    obj.save()
            #redirect นอก loop
            return redirect('viewPO')

    po = PurchaseOrder.objects.get(id = po_id)
    items = PurchaseOrderItem.objects.filter(po = po_id)
    new_pr_id = dict()
    if items:
        for obj in items:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

    new_pr = dict()
    for id in new_pr_id:
        try:
            pr = PurchaseRequisition.objects.get(id = id)
            new_pr[pr] = pr
        except PurchaseRequisition.DoesNotExist:
            pass

    context = {
        'po':po,
        'po_items':po_items,
        'cp_item':cp_item,
        'cpd_price':cpd_price,
        'po_page': "tab-active",
        'po_show': "show",
        'formset': formset,
        'price_form': price_form,
        'itemList':itemList,
        'new_pr':new_pr,
        'heading': heading_message,
    }
    return render(request, template_name, context)

@login_required(login_url='signIn')
def viewCPApprove(request):
    data = ComparisonPrice.objects.filter(Q(examiner_status_id = 1) | Q(approver_status_id = 1) & ~Q(examiner_status_id = 3), select_bidder_id__isnull = False)

    #กรองข้อมูล
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.all()
    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    context = {
        'cps':dataPage,
        'filter':myFilter,
        'bidder':bidder,
        'ap_cp_page': "tab-active",
        'ap_cp_show': "show",
    }
    return render(request, "comparePricePOApprove/viewCPApprove.html",context)

def printCPApprove(request, cp_id, isFromHome):
    try:
        bidder_oldest = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('id').first()
        items_oldest = ComparisonPriceItem.objects.filter(bidder = bidder_oldest.id)
    except (ComparisonPriceDistributor.DoesNotExist, ComparisonPriceItem.DoesNotExist, AttributeError):
        items_oldest = None

    cp = ComparisonPrice.objects.get(id=cp_id)
    baseSparesType = BaseSparesType.objects.all()

    bidder = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('amount')
    itemName = ComparisonPriceItem.objects.filter(cp = cp_id).order_by('bidder__amount')

    isApprover = False
    isExaminer = False

    #get permission with position login
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

    try:
        cpd_select = ComparisonPriceDistributor.objects.get(cp = cp, distributor = cp.select_bidder)
    except ComparisonPriceDistributor.DoesNotExist:
        cpd_select = None

    if isPermissAA and cpd_select:
        for aa in pmAA:
            if aa.codename == 'CAACPD' or aa.codename == 'CAACPA':
                try:
                    if aa.codename == 'CAACPD' and cp.cm_type.id == '1':
                        isApprover = True
                    if aa.codename == 'CAACPA' and cp.cm_type.id == '2':
                        isApprover = True
                except:
                    pass
            else:
                if aa.ap_amount_min <= cpd_select.amount <= aa.ap_amount_max and cpd_select.cp.cm_type is None:
                    isApprover = True


    if isPermissAE and cpd_select:
        for ae in pmAE:
            if ae.codename == 'CAECPD' or ae.codename == 'CAECPA':
                try:
                    if ae.codename == 'CAECPD' and cp.cm_type.id == '1':
                        isExaminer = True
                    if ae.codename == 'CAECPA' and cp.cm_type.id == '2':
                        isExaminer = True
                except:
                    pass
            else:
                if ae.ap_amount_min <= cpd_select.amount <= ae.ap_amount_max and cpd_select.cp.cm_type is None:
                    isExaminer = True


    pr_ref_no = ""
    new_pr_id = dict()
    if items_oldest:
        for obj in items_oldest:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

    new_pr = dict()
    for id in new_pr_id:
        try:
            pr = PurchaseRequisition.objects.get(id = id)
            pr_ref_no += pr.ref_no + ", "
            new_pr[pr] = pr
        except PurchaseRequisition.DoesNotExist:
            pass

    if request.method == 'POST':
        post_status = request.POST['status'] or None
        status = BaseApproveStatus.objects.get(name = post_status)

        obj = ComparisonPrice.objects.get(id = cp_id)
        #ผู้อนุมัติ
        if(isApprover and isExaminer):
            obj.examiner_status = status
            obj.examiner_user_id = request.user.id
            obj.examiner_update = datetime.datetime.now()

            obj.approver_status = status
            obj.approver_user_id = request.user.id
            obj.approver_update = datetime.datetime.now()
        elif(isApprover):
            obj.approver_status = status
            obj.approver_user_id = request.user.id
            obj.approver_update = datetime.datetime.now()
        elif(isExaminer):
            obj.examiner_status = status
            obj.examiner_user_id = request.user.id
            obj.examiner_update = datetime.datetime.now()
        obj.save()
        return redirect('printCPApprove', cp_id = cp_id, isFromHome = isFromHome)

    context = {
        'cp':cp,
        'bidder' : bidder,
        'items_oldest' : items_oldest,
        'itemName':itemName,
        'baseSparesType':baseSparesType,
        'new_pr': new_pr,
        'pr_ref_no': pr_ref_no,
        'isApprover': isApprover,
        'isExaminer': isExaminer,
        'isFromHome': isFromHome,
        'ap_cp_page': "tab-active",
        'ap_cp_show': "show",
    }
    return render(request, 'comparePricePOApprove/printCPApprove.html',context)

def searchItemExpress(request):
    strName = "<ul class='list-group list-group-flush'>"
    name = request.GET.get('title', None)
    product = Product.objects.filter(name__icontains=name)
    index = 1
    for i in product:
        strName += "<li class='list-group-item'>"+ str(index) + ")  " + i.id + "  " + i.name + "</li>"
        index += 1
    strName += "</ul>"

    data = {
        'instance': strName,
    }
    return JsonResponse(data)

def viewReceive(request):
    data = PurchaseOrder.objects.filter(approver_status_id = 2, is_receive = False)

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = PurchaseOrderItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','po')
    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs':prs,
        'rc_page': "tab-active",
        'rc_show': "show",
    }
    return render(request, 'receive/viewReceive.html',context)

def removeReceive(request, rc_id):
    rc = Receive.objects.get(id = rc_id)
    #ลบ item ใน PurchaseOrder ด้วย
    items = ReceiveItem.objects.filter(rc = rc)
    items.delete()
    #ลบ PurchaseOrder ทีหลัง
    rc.delete()
    return redirect('viewReceive')

def createReceive(request):
    #set ค่าเริ่มต้นของผู้รับสินค้า
    form = ReceiveForm(request.POST or None, initial={'receive_user': request.user})
    if form.is_valid():
        new_contact = form.save(commit=False)
        po = PurchaseOrder.objects.get(id = new_contact.po_id)
        new_contact.total_price = po.total_price
        new_contact.discount = po.discount
        new_contact.total_after_discount = po.total_after_discount
        new_contact.vat = po.vat
        new_contact.amount = po.amount
        new_contact.freight = po.freight
        new_contact.save()

        #create receive item
        items = PurchaseOrderItem.objects.filter(po = new_contact.po)
        if items:
            for item in items:
                rc_item = ReceiveItem.objects.create(
                    item = item.item,
                    quantity = item.quantity,
                    unit = item.unit,
                    unit_price = item.unit_price,
                    price = item.price,
                    rc = new_contact,
                )
                rc_item.save()

        return HttpResponseRedirect(reverse('editReceiveItem', args=(new_contact.pk,)))
    context = {
        'form' : form,
        'rc_page': "tab-active",
        'rc_show': "show",
    }
    return render(request, 'receive/createReceive.html',context)

def editReceiveItem(request, rc_id):
    rc = Receive.objects.get(id = rc_id)
    items = PurchaseOrderItem.objects.filter(po = rc.po)

    if request.method == "POST":
        formset = ReceiveItemInlineFormset(request.POST, request.FILES, instance=rc)
        receive_form = ReceivePriceForm(request.POST, instance=rc)
        if formset.is_valid() and receive_form.is_valid():
            # save ราคาใบ po
            receive_form.save()
            # save po item
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
            formset.save_m2m()
            return redirect('viewReceive')
    else:
        formset = ReceiveItemInlineFormset(instance=rc)
        receive_form = ReceivePriceForm(instance=rc)

    context = {
        'rc': rc,
        'items': items,
        'receive_form': receive_form,
        'formset': formset,
        'rc_page': "tab-active",
        'rc_show': "show",
    }
    return render(request, 'receiveItem/editReceiveItem.html',context)

def reApprovePR(request, pr_id):
        pr = PurchaseRequisition.objects.get(id = pr_id)

        pr.approver_status_id = 1 #กำหนดค่าเริ่มต้น
        pr.approver_update = None
        pr.approver_user = None
        #พัสดุ
        #pr.stockman_user_id = request.user.id
        pr.stockman_update = datetime.datetime.now()
        pr.save()

        items = RequisitionItem.objects.filter(requisit = pr.requisition)
        for item in items:
            item.is_used = False
            item.save()

        requisition = Requisition.objects.get(id = pr.requisition.id)
            
        baseUrgency = BaseUrgency.objects.all()
        baseUnit = BaseUnit.objects.all()
        baseProduct = Product.objects.all().values('id', 'name')

        context = {
            'users' : items,
            'requisition' : requisition,
            'pr' : pr,
            'baseUrgency' : baseUrgency,
            'baseUnit' : baseUnit,
            'baseProduct' : baseProduct,
            'pr_page': "tab-active",
            'pr_show': "show",
        }

        return render(request, "purchaseRequisition/reApprovePR.html", context)

def export(request):
    person_resource = DistributorResource()
    dataset = person_resource.export()
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="persons.xls"'
    return response

def uploadReceive(request):
    if request.method == 'POST':
        dataset = Dataset()
        new_persons = request.FILES.get('myfile', False)

        if new_persons:
            imported_data = dataset.load(new_persons.read(),format='xlsx')
            for data in imported_data:
                if not(data[1] is None) and not(data[10] is None):
                    strRefNo = data[10]
                    try:
                        refNo = strRefNo.split(' ')[0]
                    except:
                        refNo = strRefNo

                    try:
                        po = PurchaseOrder.objects.get(ref_no = refNo)
                        po.is_receive = True
                        po.receive_update = data[1]
                        po.save()
                        #เปลี่ยนเป็นแบบนี้
                        try:
                            po_item = PurchaseOrderItem.objects.filter(po__ref_no = refNo)
                            for i in po_item: 
                                i.is_receive = True
                                i.save()
                                try:
                                    item = RequisitionItem.objects.get(id = i.item_id)
                                    item.is_receive = True
                                    item.save()
                                except RequisitionItem.DoesNotExist:
                                    pass
                        except PurchaseOrderItem.DoesNotExist or PurchaseOrderItem.MultipleObjectsReturned:
                            pass
                        #เปลี่ยนเป็นแบบนี้
                    except PurchaseOrder.DoesNotExist:
                        pass
                '''
                elif data[1] is None and data[2] is None and not(data[3] is None):
                    #เช็คว่ามี po item หรือเปล่าถ้ามีถึงจะเอาไป save
                    strRefNo = data[12]
                    try:
                        refNo = strRefNo.split(' ')[0]
                        try:
                            po_item = PurchaseOrderItem.objects.filter(po__ref_no = refNo, item__product__id = data[4])
                            for i in po_item: 
                                i.is_receive = True
                                i.save()
                                try:
                                    item = RequisitionItem.objects.get(id = i.item_id)
                                    item.is_receive = True
                                    item.save()
                                except RequisitionItem.DoesNotExist:
                                    pass
                        except PurchaseOrderItem.DoesNotExist or PurchaseOrderItem.MultipleObjectsReturned:
                            pass
                    except:
                        pass                
                '''

            return redirect('viewReceive')
    context = {
        'rc_page': "tab-active",
        'rc_show': "show",
    }
    return render(request, 'receive/uploadReceive.html',context)

def showReceive(request, rc_id):
    rc = Receive.objects.get(id = rc_id)
    items = ReceiveItem.objects.filter(rc = rc)

    context = {
        'rc':rc,
        'items':items,
        'rc_page': "tab-active",
        'rc_show': "show",
    }
    return render(request, 'receive/showReceive.html',context)

def viewRequisitionHistory(request):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    #data = Requisition.objects.filter(created__year__lte = year,created__month__lt = month, purchase_requisition_id__isnull = False)
    data = Requisition.objects.filter(purchase_requisition_id__isnull = False)

    #กรองข้อมูล
    myFilter = RequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
            'requisitions':dataPage,
            'filter':myFilter,
            'h_requisitions_page': "tab-active",
            'h_requisitions_show': "show",
    }

    return render(request,'history/viewRequisition.html', context)

def viewPRHistory(request):
    data = PurchaseRequisition.objects.filter(Q(purchase_status_id = 2, approver_status_id = 2) | Q(Q(purchase_status_id = 3) | Q(approver_status_id = 3)))

    #กรองข้อมูล
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    ri_not_used = RequisitionItem.objects.filter(quantity_pr__gt=0)
    context = {
                'prs':dataPage,
                'filter':myFilter,
                'ri_not_used': ri_not_used,
                'h_pr_page': "tab-active",
                'h_pr_show': "show",
              }

    return render(request,'history/viewPR.html',context)

def viewPOHistory(request):
    data = PurchaseOrder.objects.filter(Q(~Q(approver_status_id = 1), is_receive = True) | Q(approver_status_id = 3))

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = PurchaseOrderItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','item__product__name','po')
    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs': prs,
        'h_po_page': "tab-active",
        'h_po_show': "show",
    }
    return render(request, "history/viewPO.html", context)

def viewComparePricePOHistory(request):
    data = ComparisonPrice.objects.filter(Q(examiner_status_id = 2, approver_status_id = 2) | Q(examiner_status_id = 3) | Q(approver_status_id = 3))

    #กรองข้อมูล
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.all()
    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = ComparisonPriceItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','cp').annotate(Count('item')).order_by().filter(item__count__gt=0)
    context = {
        'cps':dataPage,
        'filter':myFilter,
        'bidder':bidder,
        'prs': prs,
        'h_cp_page': "tab-active",
        'h_cp_show': "show",
    }

    return render(request, 'history/viewComparePricePO.html',context)

#Incomplate
def viewRequisitionHistoryIncomplete(request):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    #data = Requisition.objects.filter(created__year__lte = year,created__month__lt = month, purchase_requisition_id__isnull = False)
    data = Requisition.objects.filter(purchase_requisition_id__isnull = False)

    #กรองข้อมูล
    myFilter = RequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
            'requisitions':dataPage,
            'filter':myFilter,
            'h_i_requisitions_page': "tab-active",
            'h_i_requisitions_show': "show",
    }

    return render(request,'historyIncomplete/viewRequisition.html', context)

def viewPRHistoryIncomplete(request):
    data = PurchaseRequisition.objects.filter(Q(purchase_status_id = 3) | Q(approver_status_id = 3))

    #กรองข้อมูล
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
                'prs':dataPage,
                'filter':myFilter,
                'h_i_pr_page': "tab-active",
                'h_i_pr_show': "show",
              }

    return render(request,'historyIncomplete/viewPR.html',context)

def viewPOHistoryIncomplete(request):
    data = PurchaseOrder.objects.filter(approver_status_id = 3)

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
        'pos':dataPage,
        'filter':myFilter,
        'h_i_po_page': "tab-active",
        'h_i_po_show': "show",
    }
    return render(request, "historyIncomplete/viewPO.html", context)

def viewComparePricePOHistoryIncomplete(request):
    data = ComparisonPrice.objects.filter(Q(examiner_status_id = 3) | Q(approver_status_id = 3))

    #กรองข้อมูล
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.all()
    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    context = {
        'cps':dataPage,
        'filter':myFilter,
        'bidder':bidder,
        'h_i_cp_page': "tab-active",
        'h_i_cp_show': "show",
    }

    return render(request, 'historyIncomplete/viewComparePricePO.html',context)

def viewPOReport(request):
    data = PurchaseOrder.objects.filter(approver_status = 2)

    #กรองข้อมูล
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    prs = PurchaseOrderItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','po')

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs':prs,
        'rp_po_page': "tab-active",
        'rp_po_show': "show",
    }
    return render(request, "report/viewPO.html", context)

def exportExcelPO(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="PO_Report.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('รายงานใบสั่งสินค้า', cell_overwrite_ok=True) # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['เลขที่', 'วันที่', 'รหัสผู้จำหน่าย', 'ผู้จำหน่าย', 'รับของวันที่', 'เครดิต', 'V', 'ส่วนลด', 'มูลค่าสินค้า','VAT.', 'รวมทั้งสิ้น', 'ผู้สั่งสินค้า', 'เลขที่ใบขอซื้อ']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column 

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    date_style = xlwt.easyxf(num_format_str='DD/MM/YYYY')
    decimal_style = xlwt.easyxf(num_format_str='#,##0.00')

    stockman_user = request.GET.get('stockman_user') or None
    ref_no = request.GET.get('ref_no') or None
    distributor = request.GET.get('distributor') or None
    amount_min = request.GET.get('amount_min') or None
    amount_max = request.GET.get('amount_max') or None
    start_created = request.GET.get('start_created') or None
    end_created = request.GET.get('end_created') or None

    my_q = Q()
    if stockman_user is not None:
        my_q = Q(stockman_user = stockman_user)
    if ref_no is not None:
        my_q &= Q(ref_no__icontains = ref_no)
    if distributor is not None:
        my_q &= Q(distributor__name__startswith = distributor)
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    if amount_min is not None:
        my_q &= Q(amount__gte = amount_min)
    if amount_max is not None :
        my_q &=Q(amount__lte = amount_max)

    my_q &=Q(approver_status = 2)


    rows = PurchaseOrder.objects.filter(
        my_q
    ).values_list('ref_no', 'created', 'distributor', 'distributor__name', 'receive_update', 'credit__name', 'vat_type__id','discount','total_after_discount','vat' ,'amount','stockman_user__first_name', 'pr__ref_no').order_by('amount')

    total_price = PurchaseOrder.objects.filter(my_q).values_list('total_after_discount', flat=True)
    sum_total_price = sum(total_price)

    vat = PurchaseOrder.objects.filter(my_q).values_list('vat', flat=True)
    sum_vat = sum(vat)

    amount = PurchaseOrder.objects.filter(my_q).values_list('amount', flat=True)
    sum_amount = sum(amount)

    count = PurchaseOrder.objects.filter(my_q).count()
    
    prs = PurchaseOrderItem.objects.all()
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            if isinstance(row[col_num], datetime.date):
                ws.write(row_num, col_num, row[col_num], date_style)
            elif col_num == 8 or col_num == 9 or col_num == 10:
                ws.write(row_num, col_num, row[col_num], decimal_style)
            else:
                ws.write(row_num, col_num, row[col_num], font_style)
            
            if col_num == 12:
                strPr = ""
                prev_obj = None
                for pr in prs:
                    if row[0] == pr.po.ref_no:
                        if prev_obj is not None and pr.item.requisit.pr_ref_no == prev_obj:
                            pass
                        else:
                            strPr += str(pr.item.requisit.pr_ref_no) + ", "
                        prev_obj = pr.item.requisit.pr_ref_no

                ws.write(row_num, col_num, strPr, font_style)
    ws.write(row_num+1, 0, "รวมทั้งสิ้น", font_style)
    ws.write(row_num+1, 1, count, font_style)
    ws.write(row_num+1, 2, "ใบ", font_style)
    ws.write(row_num+1, 8, sum_total_price, decimal_style)
    ws.write(row_num+1, 9, sum_vat, decimal_style)
    ws.write(row_num+1, 10, sum_amount, decimal_style)
                        
    wb.save(response)

    return response