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
from django.http import request, HttpResponseRedirect, HttpResponse ,JsonResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext
from stock.models import BaseBranchCompany, BaseDepartment, BaseSparesType, BaseUnit, BaseUrgency, Category, Distributor, Position, Product, Cart, CartItem, Order, OrderItem, PurchaseOrder, PurchaseRequisition, Receive, ReceiveItem, Requisition, RequisitionItem, CrudUser, BaseApproveStatus, UserProfile,PositionBasePermission, PurchaseOrderItem,ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor, BasePermission, BaseVisible, BranchCompanyBaseAdress
from stock.forms import SignUpForm, RequisitionForm, RequisitionItemForm, PurchaseRequisitionForm, UserProfileForm, PurchaseOrderForm, PurchaseOrderPriceForm, ComparisonPriceForm, CPDModelForm, CPDForm, CPSelectBidderForm, PurchaseOrderFromComparisonPriceForm, ReceiveForm, ReceivePriceForm, PurchaseOrderReceiptForm, RequisitionMemorandumForm, PurchaseRequisitionAddressCompanyForm, ComparisonPriceAddressCompanyForm, PurchaseOrderAddressCompanyForm
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

def findCompanyIn(request):
    code = request.session['company_code']

    #???????????????????????????????????????????????????????????????????????????????????????????????????????????? user
    user_profile = UserProfile.objects.get(user = request.user.id)
    company_all = BaseBranchCompany.objects.filter(userprofile = user_profile).values('code')

    if code == "ALL":
        company_in = company_all
    else:
        company_in = BaseBranchCompany.objects.filter(code = code).values('code')
    return company_in

# Create your views here.
@login_required(login_url='signIn')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request, category_slug = None):
    try:
        active = request.session['company_code']
    except:
        user_profile = UserProfile.objects.get(user = request.user.id)
        company = BaseBranchCompany.objects.filter(userprofile = user_profile).first()
        active = company.code
        request.session['company'] = company.affiliated.name_sh
        request.session['company_code'] = company.code
    '''
    catalogy show ??????????????????
    '''

    products = None
    categories_page = None
    if category_slug != None :
        categories_page = get_object_or_404(Category, slug = category_slug) #???????????? 404 ????????????????????????????????????????????????????????????
        #products = Product.objects.all().filter(category = categories_page, available=True, affiliated =  company.affiliated) #??????????????????????????? Product ????????? db ??????????????????????????????????????? available=True
        products = Product.objects.all().filter(category = categories_page, available=True)
    else :
        #products = Product.objects.all().filter(available=True, affiliated =  company.affiliated) #??????????????????????????? Product ????????? db ??????????????????????????????????????? available=True
        products = Product.objects.all().filter(available=True)
    
    paginator = Paginator(products,20) #???????????????????????????????????????????????????????????? 4 ????????? 1 ????????????
    try:
        page = int(request.GET.get('page', '1')) #?????????????????????????????????????????????????????????????????? str ????????????????????????????????? int
    except:
        page = 1 #????????????????????????????????????????????????????????????????????????????????? 1

    #???????????????????????????????????????????????????????????????
    try:
        productperPage = paginator.page(page)
    except (EmptyPage, InvalidPage):
        productperPage = paginator.page(paginator.num_pages)    
    
    '''
    #??????????????? page
    p = Paginator(products, 10)
    page = request.GET.get('page')
    productperPage = p.get_page(page)
    '''


    '''
    first page
    '''

    #???????????????????????????????????????????????????????????????????????????????????????????????????????????? user
    try:
        company_in = findCompanyIn(request)
    except:
        company_in = BaseBranchCompany.objects.filter(code = active).values('code')
    
    #????????????????????????
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPR')
        isPermiss_pr = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPR').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss_pr  = False

    try:
        in_company = BaseBranchCompany.objects.filter(userprofile = user_profile, code = active).exists()
    except:
        pass

    #???????????????????????????????????????????????????
    pr_item_ap = None
    if(isPermiss_pr and in_company):
        try:
            #??????????????????????????? PurchaseRequisition
            pr_item_ap = PurchaseRequisition.objects.filter(purchase_status = 2, approver_status = 1, branch_company__code__in = company_in) #?????????????????????????????????????????????????????????????????????????????????????????????
            #???????????????????????????????????? index PurchaseRequisition ??????????????? ???????????????????????????????????????????????????????????????????????????????????????
        except PurchaseRequisition.DoesNotExist:
            pass

    new_pr = dict()
    if pr_item_ap:
        for obj in pr_item_ap:
            if obj not in new_pr:
                new_pr[obj] = obj

    try:
        #??????????????????????????? PurchaseRequisition
        pr_item_pc = PurchaseRequisition.objects.filter(purchase_user = request.user.id, purchase_status = 1, branch_company__code__in = company_in) #?????????????????????????????????????????????????????????????????????????????????????????????
    except PurchaseRequisition.DoesNotExist:
        pr_item_pc = None

    if pr_item_pc:
        for obj in pr_item_pc:
            if obj not in new_pr:
                new_pr[obj] = obj

    #??????????????????????????????
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPO')
        isPermiss_po = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPO').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss_po  = False

    po_item = None
    #?????????????????????????????????????????????????????????????????????????????????
    if isPermiss_po:
        try:
            #??????????????????????????? PurchaseOrder
            po_item = PurchaseOrder.objects.all().filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user__isnull = True, branch_company__code__in = company_in) #?????????????????????????????????????????????????????????????????????????????????????????????
        except PurchaseOrder.DoesNotExist:
            pass

    new_po = dict()
    if po_item:
        for obj in po_item:
            if obj not in new_po:
                new_po[obj] = obj

    cm_po_item = None
    #??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    if request.user.is_authenticated:
        try:
            #??????????????????????????? PurchaseOrder
            cm_po_item = PurchaseOrder.objects.all().filter(approver_status = 1, amount__isnull = False, amount__gt = 0, approver_user = request.user, branch_company__code__in = company_in) #?????????????????????????????????????????????????????????????????????????????????????????????
        except PurchaseOrder.DoesNotExist:
            cm_po_item = None
    
    if cm_po_item:
        for obj in cm_po_item:
            if obj not in new_po:
                new_po[obj] = obj

    #??????????????????????????????
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)
        permiss = BasePermission.objects.filter(codename__in= ['CAECP1','CAECP2','CAECP3','CAECP4','CAECPD','CAECPA'])
        isPermissAE = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename__in= ['CAECP1','CAECP2','CAECP3','CAECP4','CAECPD','CAECPA']).prefetch_related(Prefetch('base_permission', queryset=permiss)).values('base_permission')
    except:
        isPermissAE = None

    pmAE = []
    if(isPermissAE and in_company):
        for i in isPermissAE:
            obj = BasePermission.objects.get(id = i['base_permission'])
            pmAE.append(obj)

    #??????????????????????????????
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
    #???????????????????????????????????????????????????
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
    #???????????????????????????????????????????????????
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
        return render(request,'index.html', {'products':productperPage , 'category':categories_page, active :"active show", "colorNav":"enableNav"})
    else:
        return render(request,'firstPage.html', {'prs':new_pr,'pos':new_po,'cms':new_cm, active :"active show", "colorNav":"enableNav"})


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


@login_required(login_url='signIn') #????????? addCart ??????????????????????????????????????? login ????????????????????????????????? signIn
def addCart(request, product_id):
    #?????????????????????????????????????????????
    #????????????????????????????????????????????????????????????????????????
    product = Product.objects.get(id=product_id) #?????? Product ????????? id ????????????????????????
    #???????????????????????????????????????????????????
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) #??????????????????????????????????????????
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request)) #????????????????????????????????????????????????????????????????????????????????????????????????
        cart.save()

    #????????????????????????????????????????????????????????????????????????????????????????????????
    try:
        #?????????????????????????????????????????????????????????
        cart_item = CartItem.objects.get(product=product,cart=cart) #????????????????????? cart_item ?????????????????????
        if cart_item.quantity < cart_item.product.stock :
            #????????????????????????????????????????????????
            cart_item.quantity += 1
            #???????????????????????????????????????????????????
            cart_item.save()
    except CartItem.DoesNotExist :
        #?????? CartItem ???????????????????????????????????????????????????????????????
        #??????????????? CartItem ????????? ???????????????????????????????????????????????????
        cart_item = CartItem.objects.create(
            product = product,
            cart = cart,
            quantity = 1,
        )
        cart_item.save()
    return redirect('cartdetail')


def cartdetail(request):
    total = 0 #??????????????????????????????????????????????????????????????????????????????
    counter = 0 #??????????????????????????????????????????????????????
    cart_items = None 

    try:
        cart = Cart.objects.get(cart_id = _cart_id(request)) #???????????????????????????
        cart_items = CartItem.objects.filter(cart = cart, active = True) #?????????????????????????????????????????????????????????????????????
        for item in cart_items:
            total+=(item.product.price*item.quantity) #???????????????????????????????????????????????????????????????
            counter+=item.quantity #??????????????????????????????????????????????????????????????????????????????
    except Exception as e:
        pass #?????????????????????????????????

    stripe.api_key = settings.SECRET_KEY
    strip_total = int(total*100) #???????????? 800 strip ????????????????????? 8 ?????????????????????  *100
    description = "Payment Online"
    data_key = settings.PUBLIC_KEY

    if request.method == "POST":
        try:
            #??????????????????????????? POST ????????????????????????????????????????????????????????? print(request.POST) ???????????? link ???????????????????????? order ????????????????????? admin
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

            #?????????????????????????????????????????????????????????????????? (???????????????????????????????????? request.POST ?????? save ?????? db order)
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

            #????????????????????????????????????????????????????????????
            #?????? cart_items ???????????????????????????????????? ?????????????????????, ????????????????????? ??????????????????????????????????????????????????????
            for item in cart_items:
                order_item = OrderItem.objects.create(
                    product = item.product.name,
                    quantity = item.quantity,
                    price = item.product.price,
                    order = order,
                )
                order_item.save()

                #????????????????????? stock ??????????????????????????????????????????????????????????????????
                product = Product.objects.get(id = item.product.id) #?????? product ????????? product id
                product.stock = int(item.product.stock - item.quantity) #?????????????????????????????????????????????????????? = ????????????????????? - ?????????????????????
                product.save() #??????????????????

                item.delete() #????????????????????????????????????????????????
            return redirect('thankyou')

        except stripe.error.CardError as e:
            return False, e

    return render(request,'cartdetail.html',
    dict(cart_items=cart_items, total = total, counter = counter,
    data_key = data_key, strip_total = strip_total, description = description))

def removeCart(request, product_id):
    #?????? cart ???????????????????????????????????? A
    cart = Cart.objects.get(cart_id = _cart_id(request))
    #???????????????????????????????????????????????????????????? 2
    product = get_object_or_404(Product,id = product_id)

    #??????????????????????????????????????? product ????????? cart ??????????????????????????????????????????????????????
    cartItem = CartItem.objects.get(product = product, cart = cart)
    #?????????????????????????????????????????? 2 ????????????????????????????????????????????? A
    cartItem.delete()
    return redirect('cartdetail')

def signUpView(request):
    #????????????????????????????????????????????? form signup ??????
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            #???????????????????????????????????? User
            user = form.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            profile.save()
            #?????????????????? Group Customer
            #????????? username ???????????????????????????????????????
            username = form.cleaned_data.get('username')
            #????????? user ????????? db ???????????????
            signUpUser = User.objects.get(username = username)
            #????????? Group
            #customer_group = Group.objects.get(name = "Customer")
            #customer_group.user_set.add(signUpUser)
            return redirect('signIn')

    else:
        form = SignUpForm()
        profile_form = UserProfileForm()
    context = {'form':form, 'profile_form':profile_form}
    return render(request, "signup.html", context)

def signInView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data = request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username,password=password)
            #?????????????????????????????????????????????????????????????????? home else ??????????????????????????????????????????
            if user is not None:
                login(request, user)
                try:
                    user_profile = UserProfile.objects.get(user = request.user.id)
                    company = BaseBranchCompany.objects.filter(userprofile = user_profile).first()
                except:
                    company = None
                request.session['company_code'] = company.code
                request.session['company'] = company.name
                return redirect('home')
            else:
                return redirect('signUp')
    else:
        form = AuthenticationForm()
        company = BaseBranchCompany.objects.first()
        request.session['company_code'] = company.code
        request.session['company'] = company.name

    return render(request, 'signin.html', {'form':form,})

def signOutView(request):
    logout(request)
    return redirect('signIn')

def search(request):
    name = request.GET['title']
    products = Product.objects.filter(name__icontains=name)
    return render(request,'index.html', {'products':products})

def orderHistory(request):
    #????????? order ?????????????????????????????? user ???????????????
    if request.user.is_authenticated:
        email = str(request.user.email) #?????? order ????????? email ???????????????  email ??????????????????????????????????????????????????????????????????
        orders = Order.objects.filter(email=email)#????????? order ?????????????????????
    return render(request, 'orders.html', {'orders':orders})

def viewOrder(request, order_id):
    #????????? order ????????????????????????????????? user ???????????????
    if request.user.is_authenticated:
        email = str(request.user.email) #?????? order ????????? email ???????????????  email ??????????????????????????????????????????????????????????????????
        order = Order.objects.get(email=email, id=order_id) #????????? order ????????????????????????
        order_items = OrderItem.objects.filter(order= order) #?????? OrderItem
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
    #????????????????????????????????????
    data = Requisition.objects.get(id = requisition_id)
    #????????????????????????????????????????????????????????????
    items = RequisitionItem.objects.filter(requisition_id=requisition_id)

    # form ???????????????????????????????????????????????????
    form = RequisitionItemForm(request.POST or None, initial={'requisition_id': requisition_id})
    if form.is_valid():
        form.save()
        return redirect('createRequisitionItem', requisition_id = requisition_id)

def findStatusApprove(request, id, status):
    try:
        user = User.objects.get(id = id)
        if(status != '???????????????????????????'):
            approve_name = user.first_name + " " + user.last_name
        else:
            approve_name = ""
    except:
        approve_name = ""
    return approve_name

#??????????????????????????????????????????????????????  CrudView 
def crudRequisitionItemView(request, requisition_id):
    users = RequisitionItem.objects.filter(requisition_id = requisition_id)
    requisition = Requisition.objects.get(id = requisition_id)

    user_login = User.objects.get(id = request.user.id)

    #????????????????????????????????????????????????
    chief_approve_name = findStatusApprove(request, requisition.chief_approve_user_id, requisition.chief_approve_status)
    #??????????????????????????????????????????????????????????????????
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
    active = request.session['company_code']

    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    '''
    data = Requisition.objects.filter(Q(created__year__gte = year,
                              created__month__gte= month,
                              created__year__lte = year,
                              created__month__lte = month) | Q(purchase_requisition_id__isnull = True))   
    '''
    data = Requisition.objects.filter(purchase_requisition_id__isnull = True, branch_company__code = active)

    #??????????????????????????????
    myFilter = RequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
            'requisitions':dataPage,
            'filter':myFilter,
            'requisitions_page': "tab-active",
            'requisitions_show': "show",
            active :"active show",
            "colorNav":"enableNav"
    }

    return render(request,'requisition/viewRequisition.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def createRequisition(request):
    active = request.session['company_code']
    company = BaseBranchCompany.objects.get(code = active)
    requestName = User.objects.all()
    
    form = RequisitionForm(request, request.POST or None, initial={'branch_company': company})
    if form.is_valid():
        form = RequisitionForm(request, request.POST or None, request.FILES)
        new_contact = form.save(commit=False)
        new_contact.supplies_approve_user_name_id = request.user.id

        try:
            userProfile = UserProfile.objects.get(user = new_contact.name)
            new_contact.section = userProfile.department
        except UserProfile.DoesNotExist:
            pass
        new_contact.save()
        return HttpResponseRedirect(reverse('crud_ajax', args=(new_contact.pk,)))

    context = {
        'form':form,
        'requestName':requestName,
        'requisitions_page': "tab-active",
        'requisitions_show': "show",
        active :"active show",
        "disableTab":"disableTab",
        "colorNav":"disableNav"
    }
    return render(request, "requisition/createRequisition.html", context)

def removeRequisition(request, id):
    requisition = Requisition.objects.get(id = id)
    #?????? item ?????? Requisition ????????????
    items = RequisitionItem.objects.filter(requisition_id = id)
    items.delete()
    #?????? Requisition ??????????????????
    requisition.delete()
    return redirect('requisition')

def editRequisition(request, id):
    requisition = Requisition.objects.get(id=id)
    form = RequisitionForm(request, instance=requisition)

    if request.method == 'POST':
        form = RequisitionForm(request, request.POST, request.FILES, instance=requisition)
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
            #redirect ????????? loop
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
        active = self.request.session['company_code']
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
        context[active] = "active show"
        context['disableTab'] = "disableTab"
        context['colorNav'] = "disableNav"

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
            quantityPQ  = float(quantity1) - float(quantityTake1)
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
            quantityPQ  = float(quantity1) - float(quantityTake1)
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
    active = request.session['company_code']
    users = RequisitionItem.objects.filter(requisition_id = requisition_id)
    requisition = Requisition.objects.get(id=requisition_id)
    try:
        pr = PurchaseRequisition.objects.get(id = requisition.purchase_requisition_id)
    except:
        pr = ""
            
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()

    requestName = User.objects.all()
    #form save
    form = RequisitionForm(request, instance=requisition)

    if request.method == 'POST':
        form = RequisitionForm(request, request.POST, request.FILES , instance=requisition)
        if form.is_valid():
            new_contact =  form.save()
            try :
                obj = PurchaseRequisition.objects.get(requisition = new_contact.pk)
                obj.purchase_user_id = requisition.chief_approve_user_name
                obj.save()
            except PurchaseRequisition.DoesNotExist :
                pass
            return redirect('requisition')

    context = {
        'form':form,
        'users': users,
        'requisition': requisition,
        'pr': pr,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        'requestName':requestName,
        'requisitions_page':"tab-active",
        'requisitions_show':"show",
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }

    return render(request, "requisition/editAllRequisition.html", context)

def showRequisition(request, requisition_id, mode):
    active = request.session['company_code']
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }

    return render(request, "requisition/showRequisition.html", context)


@login_required(login_url='signIn')
def viewPR(request):
    active = request.session['company_code']

    #????????? user login ?????????????????????????????????
    isPurchasing = is_purchasing(request.user)

    #?????????????????????????????????????????????????????????????????????????????????????????? ??????????????????????????? ????????? ?????????????????????????????? ?????????????????????????????????
    if isPurchasing:
        data = PurchaseRequisition.objects.filter(purchase_status_id = 2, approver_status_id = 2, organizer = request.user , is_complete = 0, branch_company__code = active)
        requisit = PurchaseRequisition.objects.filter(purchase_status_id = 2, approver_status_id = 2, organizer = request.user, is_complete = 0).values("requisition")
        ri_not_used = RequisitionItem.objects.filter(is_used = False, quantity_pr__gt=0, requisit__in = requisit).defer('requisition_id', 'product_name', 'urgency')
    else:
        data = PurchaseRequisition.objects.filter(Q(purchase_status_id = 1) | Q(approver_status_id = 1) & ~Q(purchase_status_id = 3), is_complete = 0 , branch_company__code = active)
        requisit = PurchaseRequisition.objects.filter(Q(purchase_status_id = 1) | Q(approver_status_id = 1) & ~Q(purchase_status_id = 3), is_complete = 0).values("requisition")
        ri_not_used = RequisitionItem.objects.filter(is_used = False, quantity_pr__gt=0, requisit__in = requisit).defer('requisition_id', 'product_name', 'urgency')

    #??????????????????????????????
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    baseUrgency = BaseUrgency.objects.all()
    #??????????????? page
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
                active :"active show",
                "colorNav":"enableNav"
              }

    return render(request,'purchaseRequisition/viewPR.html',context)

def preparePR(request):
    active = request.session['company_code']
    requisitions = Requisition.objects.filter(purchase_requisition_id__isnull = True, branch_company__code = active)

    #??????????????? page
    paginator = Paginator(requisitions,10) #???????????????????????????????????????????????????????????? 4 ????????? 1 ????????????
    try:
        page = int(request.GET.get('page', '1')) #?????????????????????????????????????????????????????????????????? str ????????????????????????????????? int
    except:
        page = 1 #????????????????????????????????????????????????????????????????????????????????? 1

    #???????????????????????????????????????????????????????????????
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
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request,'purchaseRequisition/preparePR.html', context)

def is_purchasing(user):
    return user.groups.filter(name='?????????????????????').exists()

def is_supplies(user):
    return user.groups.filter(name='???????????????').exists()

def is_edit_po_id(user):
    return user.groups.filter(name='?????????????????????????????????????????????????????????').exists()

def get_bool(str):
    if str == 'True':
        bol  = True
    elif str == 'False':
        bol =  False
    return bol

def createPR(request, requisition_id):
    active = request.session['company_code']
    company = BaseBranchCompany.objects.get(code = active)

    items= RequisitionItem.objects.filter(requisition_id = requisition_id, quantity_pr__gt=0)
    try:
        requisition = Requisition.objects.get(id=requisition_id, purchase_requisition_id__isnull = True)
    except:
        return redirect('preparePR')

    baseUrgency = BaseUrgency.objects.all() #???????????????????????????????????????????????????
    baseUnit = BaseUnit.objects.all()
    #?????? id express
    baseProduct = Product.objects.all().values('id', 'name')

    #????????? user login ?????????????????????????????????
    isPurchasing = is_purchasing(request.user)
        
    #????????????????????????????????????????????????????????????
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    try:
        first_items = RequisitionItem.objects.filter(requisition_id = requisition_id, quantity_pr__gt=0).first()
        description = first_items.description
    except:
        description = ""
        
    #form
    form = PurchaseRequisitionForm(request.POST or None, initial={'note': description, 'branch_company': company})
    if form.is_valid():
        #save id express
        bool = saveIdExpressPR(request)
        if bool is None:
            #save PR
            new_contact = form.save()

            #save requisition ?????? purchase_requisition_id
            new_contact.requisition = requisition
            new_contact.purchase_status_id = 1 #????????????????????????????????????????????????
            new_contact.purchase_user_id = requisition.chief_approve_user_name
            # set ????????????????????????????????????????????????????????????????????????
            new_contact.purchase_status_id = 2
            new_contact.purchase_update = datetime.datetime.now()

            new_contact.approver_status_id = 1 #????????????????????????????????????????????????
            #???????????????
            new_contact.stockman_user_id = request.user.id
            new_contact.stockman_update = datetime.datetime.now()
            #??????????????????????????????????????????????????????
            new_contact.organizer = requisition.organizer

            new_contact.save()

            #save purchase_requisition_id ?????? requisition
            obj = Requisition.objects.get(id = requisition_id)
            obj.purchase_requisition_id = new_contact.pk
            obj.pr_ref_no = new_contact.ref_no
            obj.save()
            return HttpResponseRedirect(reverse('viewPR'))
        else:
            return HttpResponseRedirect(reverse('createPR', args=(requisition_id,)))

    #?????????????????????????????????????????????????????????
    company = BranchCompanyBaseAdress.objects.filter(branch_company__code = active ).first()

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
        'company':company,
        'pr_page': "tab-active",
        'create_mode': True,
        'pr_show': "show",
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request,'purchaseRequisition/createPR.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def createCMorPO(request, pr_id):
    active = request.session['company_code']
    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #?????? id express
    baseProduct = Product.objects.all().values('id', 'name')

    #????????????????????????????????????????????????????????????
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
            #?????????????????????????????????????????????????????? CM ???????????? PR ????????????
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
            #?????????????????????????????????????????????????????? CM ???????????? PR ????????????
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
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
    active = request.session['company_code']
    pr = PurchaseRequisition.objects.get(id=pr_id)
    form = PurchaseRequisitionForm(instance=pr)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #?????? id express
    baseProduct = Product.objects.all().values('id', 'name')

    #????????????????????????????????????????????????????????????
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request, "purchaseRequisition/createPR.html", context)

def showPR(request, pr_id, mode):
    active = request.session['company_code']
    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #?????? id express
    baseProduct = Product.objects.all().values('id', 'name')

    #????????????????????????????????????????????????????????????
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    page = PRPageMode(mode)
    show = PRShowMode(mode)

    #????????? user login ?????????????????????????????????
    isPurchasing = is_purchasing(request.user)
    #????????? user login ?????????????????????????????????
    isSupplies = is_supplies(request.user)

    # re approver ??????????????????????????????????????? history complete ????????? history incomplete ????????????????????????
    isReApprove = False
    if (mode == 4 or mode == 5) and (isPurchasing or isSupplies):
        isReApprove = True

    #?????????????????????????????????????????????????????????
    company = BranchCompanyBaseAdress.objects.filter(branch_company__code = active).first()
    form = RequisitionMemorandumForm(instance=requisition)
    pr_form = PurchaseRequisitionAddressCompanyForm(instance=pr)

    if request.method == 'POST' and 'btnformR' in request.POST:
        form = RequisitionMemorandumForm(request.POST, request.FILES, instance=requisition)
        if form.is_valid():
            form.save()
            return redirect('viewPRHistory')

    if request.method == 'POST' and 'btnformPR' in request.POST:
        pr_form = PurchaseRequisitionAddressCompanyForm(request.POST, request.FILES, instance=pr)
        if pr_form.is_valid():
            pr_form.save()
            return redirect('showPR', pr_id = pr.id , mode = mode)

    context = {
            'items':items,
            'requisition':requisition,
            'quantityTotal': quantityTotal,
            'baseUrgency': baseUrgency,
            'baseUnit': baseUnit,
            'baseProduct':baseProduct,
            'pr': pr,
            'isPurchasing': isPurchasing,
            'isSupplies': isSupplies,
            'create_mode': False,
            page: "tab-active",
            show: "show",
            'form':form,
            'pr_form': pr_form,
            'isReApprove': isReApprove,
            active :"active show",
			"disableTab":"disableTab",
			"colorNav":"disableNav"
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
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = PurchaseRequisition.objects.filter(Q(purchase_status_id = 1)| Q(approver_status_id = 1) & ~Q(purchase_status_id = 3), branch_company__code__in = company_in)

    #??????????????????????????????
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
                'prs':dataPage,
                'filter':myFilter,
                'ap_pr_page': "tab-active",
                'ap_pr_show': "show",
                active :"active show",
                "colorNav":"enableNav"
              }

    return render(request,'purchaseRequisitionApprove/viewPRApprove.html',context)

def editPRApprove(request, pr_id, isFromHome):
    active = request.session['company_code']
    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()

    #????????????????????????????????????????????????????????????
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }

    if request.method == 'POST':
        post_status = request.POST['status'] or None
        status = BaseApproveStatus.objects.get(name = post_status)

        obj = PurchaseRequisition.objects.get(id = pr_id)
        #???????????????????????????
        if(obj.purchase_user_id == request.user.id):
            obj.purchase_status = status
            obj.purchase_update = datetime.datetime.now()
        #??????????????????????????????
        if(isPermiss):
            obj.approver_status = status
            obj.approver_user_id = request.user.id
            obj.approver_update = datetime.datetime.now()
        #?????????????????????????????????????????????????????????????????????????????????????????????
        if obj.purchase_status_id != 1 or obj.approver_status_id != 1:
            r = Requisition.objects.get(purchase_requisition_id = obj.id)
            r.is_edit = False
            r.save()
        obj.save()
        return redirect('editPRApprove', pr_id = pr_id, isFromHome = isFromHome)

    return render(request, "purchaseRequisitionApprove/editPRApprove.html", context)

@login_required(login_url='signIn')
def viewPO(request):
    active = request.session['company_code']
    data = PurchaseOrder.objects.filter(Q(approver_status_id = 1) | Q(is_receive = False) & ~Q(approver_status_id = 3), branch_company__code = active)

    #??????????????????????????????
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = PurchaseOrderItem.objects.filter(po__in=data).values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','po')

    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs': prs,
        'po_page': "tab-active",
        'po_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "purchaseOrder/viewPO.html", context)

def preparePO(request):
    return render(request, 'purchaseOrder/preparePO.html')

def createPO(request):
    try:
        company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    except:
        return redirect('signOut')

    # set ?????????????????????????????????????????????????????????????????????????????????????????? ????????????????????????????????????????????????????????????????????? ?????????????????????????????????
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
    active = request.session['company_code']
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    #distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    po = PurchaseOrder.objects.get(id=po_id)
    form = PurchaseOrderForm(instance=po)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, request.FILES, instance=po)
        if form.is_valid():
            form.save()
            return redirect('editPOItem', po_id = po_id, isFromPR = 'True', isReApprove = 'False')
        
    #'distributorList': distributorList,
    context = {
        'form':form,
        'po_page': "tab-active",
        'po_show': "show",
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
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
    #?????? item ?????? PurchaseOrder ????????????
    items = PurchaseOrderItem.objects.filter(po = po)
    for obj in items:
        try:
            d_item = RequisitionItem.objects.get(id = obj.item.id)
            d_item.is_used = False
            d_item.save()
            #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
            check_item = RequisitionItem.objects.filter(requisit = d_item.requisit, is_used = False).distinct()
            if check_item:
                try:
                    pr = PurchaseRequisition.objects.get(requisition = d_item.requisit)
                    pr.is_complete = False
                    pr.save()
                except:
                    pass
        except RequisitionItem.DoesNotExist:
            pass

    items.delete()

    #???????????? po_ref_no ???????????????????????????
    try:
        cp = ComparisonPrice.objects.get(po_ref_no = po.ref_no)
        cp.po_ref_no = ""
        cp.save()
    except (ComparisonPrice.DoesNotExist, AttributeError):
        pass

    #?????? PurchaseOrder ??????????????????
    po.delete()
    return redirect('viewPO')

def showPO(request, po_id, mode):
    active = request.session['company_code']
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
    if request.method == 'POST' and 'btnformPOr' in request.POST:
        form = PurchaseOrderReceiptForm(request.POST, request.FILES, instance=po)
        if form.is_valid():
            form.save()
            return redirect('viewPOHistory')

    poa_form = PurchaseOrderAddressCompanyForm(instance=po)
    if request.method == 'POST' and 'btnformPOa' in request.POST:
        poa_form = PurchaseOrderAddressCompanyForm(request.POST, request.FILES, instance=po)
        if poa_form.is_valid():
            poa_form.save()
            return redirect('showPO', po_id = po_id , mode = mode)

    #????????? user login ?????????????????????????????????
    isPurchasing = is_purchasing(request.user)
    #????????? user login ?????????????????????????????????
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
            'poa_form':poa_form,
            page: "tab-active",
            show: "show",
            active :"active show",
			"disableTab":"disableTab",
			"colorNav":"disableNav"
    }
    return render(request, 'purchaseOrder/showPO.html',context)

def createPOItem(request, po_id):
    template_name = 'purchaseOrderItem/createPOItem.html'
    heading_message = 'Model Formset Demo'
    #????????? item ????????????????????? po ????????????
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)

    po_data = PurchaseOrder.objects.get(id=po_id)
    if request.method == 'GET':
        formset = PurchaseOrderItemModelFormset(queryset=PurchaseOrderItem.objects.none())
        price_form = PurchaseOrderPriceForm()
    elif request.method == 'POST':
        formset = PurchaseOrderItemModelFormset(request.POST)
        price_form = PurchaseOrderPriceForm(request.POST, instance=po_data)
        if formset.is_valid() and price_form.is_valid():
            # save ?????????????????? po
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
            #redirect ????????? loop
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
    active = request.session['company_code']
    template_name = 'purchaseOrderItem/editPOItem.html'
    heading_message = 'Model Formset Demo'

    #????????? user login ??????????????????????????????????????????????????????????????????
    isEditPO = is_edit_po_id(request.user)

    #????????? item ????????????????????? po ????????????
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    #distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    po_data = PurchaseOrder.objects.get(id = po_id)
    po_items = PurchaseOrderItem.objects.filter(po = po_id)
    form = PurchaseOrderForm(instance=po_data)
    if request.method == "POST":
        formset = PurchaseOrderItemInlineFormset(request.POST, request.FILES, instance=po_data)
        price_form = PurchaseOrderPriceForm(request.POST, instance=po_data)
        form = PurchaseOrderForm(request.POST, request.FILES, instance=po_data)
        if formset.is_valid() and price_form.is_valid() and form.is_valid():
            # save ?????????????????? po
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
            #???????????????????????????????????? cp po_ref_no
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
                    #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                    check_item = RequisitionItem.objects.filter(requisit = r_item.requisit, is_used = False).distinct()
                    if not check_item:
                        try:
                            pr = PurchaseRequisition.objects.get(requisition = r_item.requisit)
                            pr.is_complete = True
                            pr.save()
                        except:
                            pass
                except RequisitionItem.DoesNotExist:
                    pass
            for obj in formset.deleted_objects:
                try:
                    d_item = RequisitionItem.objects.get(id = obj.item.id)
                    d_item.is_used = False
                    d_item.save()
                    #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                    check_item = RequisitionItem.objects.filter(requisit = d_item.requisit, is_used = False).distinct()
                    if check_item:
                        try:
                            pr = PurchaseRequisition.objects.get(requisition = d_item.requisit)
                            pr.is_complete = False
                            pr.save()
                        except:
                            pass
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

    #'distributorList': distributorList,
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
        'heading': heading_message,
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request, template_name, context)

@login_required(login_url='signIn')
def viewPOApprove(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = PurchaseOrder.objects.filter(approver_status_id = 1, amount__isnull = False, amount__gt = 0, branch_company__code__in = company_in)

    #??????????????????????????????
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
                'pos':dataPage,
                'filter':myFilter,
                'ap_po_page': "tab-active",
                'ap_po_show': "show",
                active :"active show",
                "colorNav":"enableNav"
              }

    return render(request,'purchaseOrderApprove/viewPOApprove.html',context)

def editPOApprove(request, po_id, isFromHome):
    active = request.session['company_code']
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
        #??????????????????????????????
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
                active :"active show",
			    "disableTab":"disableTab",
			    "colorNav":"disableNav"
    }
    return render(request, 'purchaseOrderApprove/editPOApprove.html',context)

@login_required(login_url='signIn')
def viewComparePricePO(request):
    active = request.session['company_code']

    #data = ComparisonPrice.objects.filter(Q(examiner_status_id = 1) | Q(approver_status_id = 1))
    data = ComparisonPrice.objects.filter(Q(po_ref_no = "") & ~Q(examiner_status_id = 3) & ~Q(approver_status_id = 3) , branch_company__code = active)

    prs = ComparisonPriceItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','cp').annotate(Count('item')).order_by().filter(item__count__gt=0, cp__in=data)

    #??????????????????????????????
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.values('cp_id','distributor__name','distributor__id','amount').filter(cp__in=data)
    #??????????????? page
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
        active :"active show",
        "colorNav":"enableNav",
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

    #?????? item ?????? ComparisonPriceItem ????????????
    items = ComparisonPriceItem.objects.filter(cp = cp_id)
    for obj in items:
        try:
            d_item = RequisitionItem.objects.get(id = obj.item.id)
            d_item.is_used = False
            d_item.save()
            #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
            check_item = RequisitionItem.objects.filter(requisit = d_item.requisit, is_used = False).distinct()
            if check_item:
                try:
                    pr = PurchaseRequisition.objects.get(requisition = d_item.requisit)
                    pr.is_complete = False
                    pr.save()
                except:
                    pass
        except RequisitionItem.DoesNotExist:
            pass
    items.delete()

    #????????????????????????????????????
    bidder.delete()

    #???????????????????????????????????????????????????????????????
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
    active = request.session['company_code']
    cp = ComparisonPrice.objects.get(id=cp_id)

    #????????? item ????????????????????? po ????????????
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    #distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    #?????????????????????
    try:
        bidder = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('id').first()
        bidder_oldest = bidder.id
    except (ComparisonPriceDistributor.DoesNotExist, AttributeError):
        bidder_oldest = None

    #??????????????????????????????????????????????????????????????????????????????
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
                    #??????????????????????????????????????? PR
                    try:
                        r_item = RequisitionItem.objects.get(id = cpi.item.id)
                        r_item.is_used = True
                        r_item.save()
                        #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                        check_item = RequisitionItem.objects.filter(requisit = r_item.requisit, is_used = False).distinct()
                        if not check_item:
                            try:
                                pr = PurchaseRequisition.objects.get(requisition = r_item.requisit)
                                pr.is_complete = True
                                pr.save()
                            except:
                                pass
                    except RequisitionItem.DoesNotExist:
                        pass
            return redirect('createComparePricePOItem', cp_id = cp_id, isReApprove = 'False')

    cpd = ComparisonPriceDistributor.objects.filter(cp = cp_id)
    cp_item = ComparisonPriceItem.objects.filter(cp = cp_id)
    
    #'distributorList': distributorList,
    context = {
        'link_cp_id':cp_id,
        'cpd':cpd,
        'cp_item':cp_item,
        'bidder_oldest':bidder_oldest,
        'bidder_have': bidder_have,
        'itemList': itemList,
        'bookform': bookform,
        'formset': formset,
        'cp_page': "tab-active",
        'cp_show': "show",
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request, 'comparePricePOItem/createComparePricePOItem.html',context)

def autocompalteDistributor(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        qs = Distributor.objects.filter(Q(id__icontains = term) | Q(name__icontains = term))[:15]
        titles = list()
        for obj in qs:
            titles.append(obj.id +"-"+ obj.name)
    return JsonResponse(titles, safe=False)

def searchDataDistributor(request):
    if 'id_distributor' in request.GET:
        id = request.GET.get('id_distributor')
        qs = Distributor.objects.get(id = id)

    data = {
        'credit': qs.credit.id,
        'vat_type': qs.vat_type.id,
    }
    return JsonResponse(data)

def setDataDistributor(request):
    if 'id_distributor' in request.GET:
        id = request.GET.get('id_distributor')
        qs = Distributor.objects.get(id = id)
        val = qs.id + "-" + qs.name
    data = {
        'val': val,
    }
    return JsonResponse(data)

def editComparePricePOItemFromPR(request, cp_id , cpd_id):
    active = request.session['company_code']

    #????????? item ????????????????????? po ????????????
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    
    #company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    #distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    data = ComparisonPriceDistributor.objects.get(id = cpd_id)
    if request.method == "POST":
        formset = CPitemInlineFormset(request.POST, request.FILES, instance=data)
        bookform = CPDModelForm(request.POST, request.FILES, instance=data)

        if formset.is_valid() and bookform.is_valid():
            # save ?????????????????? po
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
                #??????????????????????????????????????? PR
                try:
                    r_item = RequisitionItem.objects.get(id = instance.item.id)
                    r_item.is_used = True
                    r_item.save()
                    #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                    check_item = RequisitionItem.objects.filter(requisit = r_item.requisit, is_used = False).distinct()
                    if not check_item:
                        try:
                            pr = PurchaseRequisition.objects.get(requisition = r_item.requisit)
                            pr.is_complete = True
                            pr.save()
                        except:
                            pass
                except RequisitionItem.DoesNotExist:
                    pass
            for obj in formset.deleted_objects:
                try:
                    d_item = RequisitionItem.objects.get(id = obj.item.id)
                    d_item.is_used = False
                    d_item.save()
                    #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                    check_item = RequisitionItem.objects.filter(requisit = d_item.requisit, is_used = False).distinct()
                    if check_item:
                        try:
                            pr = PurchaseRequisition.objects.get(requisition = d_item.requisit)
                            pr.is_complete = False
                            pr.save()
                        except:
                            pass
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

    #'distributorList': distributorList,
    context = {
        'link_cp_id' : cp_id,
        'link_cpd_id' : cpd_id,
        'cpd':cpd,
        'cp_item':cp_item,
        'itemList':itemList,
        'bookform': bookform,
        'formset': formset,
        'cp_page': "tab-active",
        'cp_show': "show",
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request, 'comparePricePOItem/editComparePricePOItemFromPR.html',context)

def editComparePricePOItem(request, cp_id , cpd_id):
    active = request.session['company_code']
    cp = ComparisonPrice.objects.get(id=cp_id)

    #????????? item ????????????????????? po ????????????
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False, is_receive = False, product__isnull = False)
    #
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    #distributorList = Distributor.objects.filter(affiliated = company.affiliated)
    #distributorList = Distributor.objects.all().values('id','name','credit__id','vat_type__id')

    data = ComparisonPriceDistributor.objects.get(id = cpd_id)
    numDistributor = ComparisonPriceDistributor.objects.filter(cp = cp_id).count()
    if request.method == "POST":
        formset = CPitemInlineFormset(request.POST, request.FILES, instance=data)
        bookform = CPDModelForm(request.POST, request.FILES, instance=data)

        if formset.is_valid() and bookform.is_valid():
            # save ?????????????????? po
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
                #??????????????????????????????????????? PR
                try:
                    r_item = RequisitionItem.objects.get(id = instance.item.id)
                    r_item.is_used = True
                    r_item.save()
                    #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                    check_item = RequisitionItem.objects.filter(requisit = r_item.requisit, is_used = False).distinct()
                    if not check_item:
                        try:
                            pr = PurchaseRequisition.objects.get(requisition = r_item.requisit)
                            pr.is_complete = True
                            pr.save()
                        except:
                            pass
                except RequisitionItem.DoesNotExist:
                    pass
            for obj in formset.deleted_objects:
                if numDistributor == 1:
                    try:
                        d_item = RequisitionItem.objects.get(id = obj.item.id)
                        d_item.is_used = False
                        d_item.save()
                        #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                        check_item = RequisitionItem.objects.filter(requisit = d_item.requisit, is_used = False).distinct()
                        if check_item:
                            try:
                                pr = PurchaseRequisition.objects.get(requisition = d_item.requisit)
                                pr.is_complete = False
                                pr.save()
                            except:
                                pass
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

    #'distributorList': distributorList,
    context = {
        'link_cp_id' : cp_id,
        'link_cpd_id' : cpd_id,
        'cpd':cpd,
        'cp_item':cp_item,
        'itemList':itemList,
        'bookform': bookform,
        'formset': formset,
        'cp_page': "tab-active",
        'cp_show': "show",
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request, 'comparePricePOItem/editComparePricePOItem.html',context)

def removeComparePriceDistributor(request, cp_id, cpd_id):
    numDistributor = ComparisonPriceDistributor.objects.filter(cp = cp_id).count()
    cpd = ComparisonPriceDistributor.objects.get(id = cpd_id)
    #?????? item ?????? PurchaseOrder ????????????
    items = ComparisonPriceItem.objects.filter(bidder = cpd)
    if numDistributor == 1:
        for obj in items:
            try:
                d_item = RequisitionItem.objects.get(id = obj.item.id)
                d_item.is_used = False
                d_item.save()
                #???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
                check_item = RequisitionItem.objects.filter(requisit = d_item.requisit, is_used = False).distinct()
                if check_item:
                    try:
                        pr = PurchaseRequisition.objects.get(requisition = d_item.requisit)
                        pr.is_complete = False
                        pr.save()
                    except:
                        pass
            except RequisitionItem.DoesNotExist:
                pass  
    items.delete()
    #?????? PurchaseOrder ??????????????????
    cpd.delete()
    return redirect('createComparePricePOItem', cp_id = cp_id, isReApprove = 'False')

def printComparePricePO(request, cp_id):
    active = request.session['company_code']
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
            
            #????????????????????????????????????????????????????????????????????????????????????????????????
            all_bidder = ComparisonPriceDistributor.objects.filter(cp = f_cp)
            for bd in all_bidder:
                bd.is_select = False
                bd.save()

            #set ?????????????????????????????????????????????
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request, 'comparePricePO/printComparePricePO.html',context)

def showComparePricePO(request, cp_id, mode):
    active = request.session['company_code']
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

    #????????? user login ?????????????????????????????????
    isPurchasing = is_purchasing(request.user)

    form = ComparisonPriceAddressCompanyForm(instance=cp)
    if request.method == 'POST':
        form = ComparisonPriceAddressCompanyForm(request.POST, request.FILES, instance=cp)
        if form.is_valid():
            form.save()
            return redirect('showComparePricePO', cp_id = cp_id , mode = mode)

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
            'form':form,
            page: "tab-active",
            show: "show",
            active :"active show",
			"disableTab":"disableTab",
			"colorNav":"disableNav"
    }
    return render(request, 'comparePricePO/showComparePricePO.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def createPOFromComparisonPrice(request, cp_id):
    active = request.session['company_code']
    company = BaseBranchCompany.objects.get(code = active)


    #????????? user login ??????????????????????????????????????????????????????????????????
    isEditPO = is_edit_po_id(request.user)

    bc = ComparisonPrice.objects.get(id = cp_id)
    #set ?????????????????????????????????????????????????????????????????????????????????????????? ????????????????????????????????????????????????????????????????????? ?????????????????????????????????
    form = PurchaseOrderFromComparisonPriceForm(request, request.POST or None, initial={'cp': cp_id , 'address_company': bc.address_company , 'approver_user' : bc.approver_user})
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
            #new_contact.approver_user = cp.approver_user
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }

    return render(request, "purchaseOrder/createPO.html", context)

def createPOItemFromComparisonPrice(request, po_id):
    active = request.session['company_code']

    template_name = 'purchaseOrderItem/createPOItemFromComparisonPrice.html'
    heading_message = 'Model Formset Demo'
    #????????? item ????????????????????? po ????????????
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

            # save ?????????????????? po
            price_form.save()
            # save po item
            for form in formset:
                # only save if name is present
                if form.cleaned_data.get('item'):
                    obj = form.save(commit=False)
                    obj.po = po_data
                    obj.save()
            #redirect ????????? loop
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
    }
    return render(request, template_name, context)

@login_required(login_url='signIn')
def viewCPApprove(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = ComparisonPrice.objects.filter(Q(examiner_status_id = 1) | Q(approver_status_id = 1) & ~Q(examiner_status_id = 3), select_bidder_id__isnull = False, branch_company__code__in = company_in)

    #??????????????????????????????
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.filter(cp__in=data)
    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)
    context = {
        'cps':dataPage,
        'filter':myFilter,
        'bidder':bidder,
        'ap_cp_page': "tab-active",
        'ap_cp_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "comparePricePOApprove/viewCPApprove.html",context)

def printCPApprove(request, cp_id, isFromHome):
    active = request.session['company_code']
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
    #??????????????????????????????
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

    #??????????????????????????????
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
        #??????????????????????????????
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
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
    active = request.session['company_code']
    data = PurchaseOrder.objects.filter(approver_status_id = 2, is_receive = False, branch_company__code = active)

    #??????????????????????????????
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = PurchaseOrderItem.objects.filter(po__in=data).values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','po')
    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs':prs,
        'rc_page': "tab-active",
        'rc_show': "show",
        active :"active show",
        "colorNav":"enableNav",
    }
    return render(request, 'receive/viewReceive.html',context)

def removeReceive(request, rc_id):
    rc = Receive.objects.get(id = rc_id)
    #?????? item ?????? PurchaseOrder ????????????
    items = ReceiveItem.objects.filter(rc = rc)
    items.delete()
    #?????? PurchaseOrder ??????????????????
    rc.delete()
    return redirect('viewReceive')

def createReceive(request):
    #set ??????????????????????????????????????????????????????????????????????????????
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
            # save ?????????????????? po
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

        pr.approver_status_id = 1 #????????????????????????????????????????????????
        pr.approver_update = None
        pr.approver_user = None
        #???????????????
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

def closePR(request, pr_id):
    pr = PurchaseRequisition.objects.get(id = pr_id)
    requisition = Requisition.objects.get(purchase_requisition_id = pr_id)
    r_items = RequisitionItem.objects.filter(requisit = requisition.id)
    #set pr ??????????????????????????????????????????
    pr.is_complete = True
    pr.save()
    #set ???????????????????????????????????? ?????????????????????????????????
    for i in r_items:
        i.is_used = True
        i.save()
    return redirect('viewPR')

def export(request):
    person_resource = DistributorResource()
    dataset = person_resource.export()
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="persons.xls"'
    return response

def uploadReceive(request):
    active = request.session['company_code']
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
                        #???????????????????????????????????????????????????
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
                        #???????????????????????????????????????????????????
                    except PurchaseOrder.DoesNotExist:
                        pass
                '''
                elif data[1] is None and data[2] is None and not(data[3] is None):
                    #??????????????????????????? po item ???????????????????????????????????????????????????????????????????????? save
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
        active :"active show",
		"disableTab":"disableTab",
		"colorNav":"disableNav"
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
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    #data = Requisition.objects.filter(created__year__lte = year,created__month__lt = month, purchase_requisition_id__isnull = False)
    data = Requisition.objects.filter(purchase_requisition_id__isnull = False, branch_company__code__in = company_in)

    #??????????????????????????????
    myFilter = RequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
            'requisitions':dataPage,
            'filter':myFilter,
            'h_requisitions_page': "tab-active",
            'h_requisitions_show': "show",
            active :"active show",
            "colorNav":"enableNav"
    }

    return render(request,'history/viewRequisition.html', context)

def viewPRHistory(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    
    data = PurchaseRequisition.objects.filter(Q(purchase_status_id = 2, approver_status_id = 2) | Q(Q(purchase_status_id = 3) | Q(approver_status_id = 3)), branch_company__code__in = company_in)
    requisit = PurchaseRequisition.objects.filter(Q(purchase_status_id = 2, approver_status_id = 2) | Q(Q(purchase_status_id = 3) | Q(approver_status_id = 3))).values("requisition")

    #??????????????????????????????
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    ri = RequisitionItem.objects.filter(quantity_pr__gt=0, requisit__in = requisit)
    context = {
                'prs':dataPage,
                'filter':myFilter,
                'ri': ri,
                'h_pr_page': "tab-active",
                'h_pr_show': "show",
                active :"active show",
                "colorNav":"enableNav"
              }

    return render(request,'history/viewPR.html',context)

def viewPOHistory(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    data = PurchaseOrder.objects.filter(Q(~Q(approver_status_id = 1), is_receive = True) | Q(approver_status_id = 3), branch_company__code__in = company_in)

    #??????????????????????????????
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = PurchaseOrderItem.objects.filter(po__in=data).values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','item__product__name','po')
    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs': prs,
        'h_po_page': "tab-active",
        'h_po_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "history/viewPO.html", context)

def viewComparePricePOHistory(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    data = ComparisonPrice.objects.filter(Q(examiner_status_id = 2, approver_status_id = 2) | Q(examiner_status_id = 3) | Q(approver_status_id = 3), branch_company__code__in = company_in)

    #??????????????????????????????
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.values('cp_id','distributor__name','distributor__id','amount').filter(cp__in=data)
    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    prs = ComparisonPriceItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','cp').annotate(Count('item')).order_by().filter(item__count__gt=0, cp__in=data)
    context = {
        'cps':dataPage,
        'filter':myFilter,
        'bidder':bidder,
        'prs': prs,
        'h_cp_page': "tab-active",
        'h_cp_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }

    return render(request, 'history/viewComparePricePO.html',context)

#Incomplate
def viewRequisitionHistoryIncomplete(request):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    #data = Requisition.objects.filter(created__year__lte = year,created__month__lt = month, purchase_requisition_id__isnull = False)
    data = Requisition.objects.filter(purchase_requisition_id__isnull = False)

    #??????????????????????????????
    myFilter = RequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
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

    #??????????????????????????????
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
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

    #??????????????????????????????
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    #??????????????? page
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

    #??????????????????????????????
    myFilter = ComparisonPriceFilter(request.GET, queryset = data)
    data = myFilter.qs

    bidder = ComparisonPriceDistributor.objects.all()
    #??????????????? page
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
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    data = PurchaseOrder.objects.filter(approver_status = 2, branch_company__code__in = company_in)

    #??????????????????????????????
    myFilter = PurchaseOrderFilter(request.GET, queryset = data)
    data = myFilter.qs

    prs = PurchaseOrderItem.objects.values('item__requisit__pr_ref_no','item__requisit__purchase_requisition_id','po')

    #??????????????? page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
        'pos':dataPage,
        'filter':myFilter,
        'prs':prs,
        'rp_po_page': "tab-active",
        'rp_po_show': "show",
        active :"active show",
        "colorNav":"enableNav"
    }
    return render(request, "report/viewPO.html", context)

def exportExcelPO(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="PO_Report_"'+active+'".xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('??????????????????????????????????????????????????????', cell_overwrite_ok=True) # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['??????????????????', '??????????????????', '??????????????????????????????????????????', '??????????????????????????????', '????????????????????????????????????', '??????????????????', 'V', '??????????????????', '????????????????????????????????????','VAT.', '?????????????????????????????????', '???????????????????????????????????????', '??????????????????????????????????????????','????????????????????????????????????','????????????????????????????????????','???????????????????????????????????????', '???????????????????????????????????????????????????']

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
    my_q &=Q(branch_company__code__in = company_in)

    rows = PurchaseOrder.objects.filter(
        my_q
    ).values_list('ref_no', 'created', 'distributor', 'distributor__name', 'receive_update', 'credit__name', 'vat_type__id','discount','total_after_discount','vat' ,'amount','stockman_user__first_name', 'pr__ref_no', 'note', 'note', 'note', 'note').order_by('amount')

    total_price = PurchaseOrder.objects.filter(my_q).values_list('total_after_discount', flat=True)
    sum_total_price = sum(total_price)

    vat = PurchaseOrder.objects.filter(my_q).values_list('vat', flat=True)
    sum_vat = sum(vat)

    amount = PurchaseOrder.objects.filter(my_q).values_list('amount', flat=True)
    sum_amount = sum(amount)

    count = PurchaseOrder.objects.filter(my_q).count()
    
    po = PurchaseOrder.objects.filter(my_q)
    prs = PurchaseOrderItem.objects.filter(po__in = po)
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
            
            strPrItem = ""
            strPrMachine = ""
            strPrDesired = ""
            strPrUrgency = ""
            for pr in prs:
                if row[0] == pr.po.ref_no:
                    strPrItem += str(pr.item.product.name) + ", "
                    strPrMachine += str(pr.item.machine) + ", "
                    strPrDesired += str(pr.item.desired_date) + ", "
                    try:
                        ug = BaseUrgency.objects.get(id = pr.item.urgency)
                        strPrUrgency += str(ug.name) + ", "
                    except:
                        pass
            ws.write(row_num, 13, strPrItem, font_style)
            ws.write(row_num, 14, strPrMachine, font_style)
            ws.write(row_num, 15, strPrDesired, date_style)
            ws.write(row_num, 16, strPrUrgency, font_style)

    ws.write(row_num+1, 0, "?????????????????????????????????", font_style)
    ws.write(row_num+1, 1, count, font_style)
    ws.write(row_num+1, 2, "??????", font_style)
    ws.write(row_num+1, 8, sum_total_price, decimal_style)
    ws.write(row_num+1, 9, sum_vat, decimal_style)
    ws.write(row_num+1, 10, sum_amount, decimal_style)
                        
    wb.save(response)

    return response

def setSessionCompany(request):
    name = request.GET.get('title', None)
    request.session['company_code'] = name
    company = BaseBranchCompany.objects.get(code = request.session['company_code'])
    request.session['company'] = company.affiliated.name_sh
    data = {
        'instance': request.session['company_code'],
    }
    return JsonResponse(data)