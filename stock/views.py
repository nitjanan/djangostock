from typing import cast
from django import forms
from django import http
from django.core import paginator
from django.db.models.fields import NullBooleanField
from django.db.models.query import QuerySet
from django.http import request, HttpResponseRedirect, HttpResponse ,JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext
from stock.models import BaseSparesType, BaseUnit, BaseUrgency, Category, Distributor, Position, Product, Cart, CartItem, Order, OrderItem, PurchaseOrder, PurchaseRequisition, Receive, ReceiveItem, Requisition, RequisitionItem, CrudUser, BaseApproveStatus, UserProfile,PositionBasePermission, PurchaseOrderItem,ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor, BasePermission
from stock.forms import SignUpForm, RequisitionForm, RequisitionItemForm, PurchaseRequisitionForm, UserProfileForm, PurchaseOrderForm, PurchaseOrderPriceForm, ComparisonPriceForm, CPDModelForm, CPDForm, CPSelectBidderForm, PurchaseOrderFromComparisonPriceForm, ReceiveForm, ReceivePriceForm
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
from .resources import ReceiveItemResource
from tablib import Dataset


# Create your views here.
@login_required(login_url='signIn')
def index(request, category_slug = None):
    products = None
    categories_page = None
    if category_slug != None :
        categories_page = get_object_or_404(Category, slug = category_slug) #เช็ค 404 คือเช็คว่ามีค่ามาไหม
        products = Product.objects.all().filter(category = categories_page, available=True) #ดึงข้อมูล Product จาก db ทั้งหมดโดยที่ available=True
    else :
        products = Product.objects.all().filter(available=True) #ดึงข้อมูล Product จาก db ทั้งหมดโดยที่ available=True
    
    paginator =Paginator(products,2) #หมายถึงให้แสดงสินค้า 4 ต่อ 1 หน้า
    try:
        page = int(request.GET.get('page', '1')) #กำหนดหมายเลขหน้าแรกเปน str แล้วแปลงเปน int
    except:
        page = 1 #กำหนดหมายเลขหน้าเริ่มแรกเปน 1

    #กำหนดจำนวนชิ้นต่อหน้า
    try:
        productperPage = paginator.page(page)
    except (EmptyPage, InvalidPage):
        productperPage = paginator.page(paginator.num_pages)

    return render(request,'index.html', {'products':productperPage , 'category':categories_page})

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
            customer_group = Group.objects.get(name = "Customer")
            customer_group.user_set.add(signUpUser)
            return redirect('signInView')

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
            #ถ้าล็อกอินสำเร็จไปหน้า home else ให้ไปสมัครใหม่
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signUp')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form':form})

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
    data = Requisition.objects.all()

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

def createRequisition(request):
    form = RequisitionForm(request.POST or None)
    if form.is_valid():
        form = RequisitionForm(request.POST or None, request.FILES)
        new_contact = form.save(commit=False)
        new_contact.supplies_approve_user_name_id = request.user.id
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

        product_item = get_object_or_404(Product, id_express=product1)

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

        product_item = get_object_or_404(Product, id_express=product1)

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

def showRequisition(request, requisition_id):
    items = RequisitionItem.objects.filter(requisition_id = requisition_id)
    requisition = Requisition.objects.get(id=requisition_id)
    try:
        pr = PurchaseRequisition.objects.get(id = requisition.purchase_requisition_id)
    except:
        pr = ""
            
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()

    context = {
        'items': items,
        'requisition': requisition,
        'pr': pr,
        'baseUrgency': baseUrgency,
        'baseUnit': baseUnit,
        'requisitions_page':"tab-active",
        'requisitions_show':"show",
    }

    return render(request, "requisition/showRequisition.html", context)


@login_required(login_url='signIn')
def viewPR(request):

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)

    #ถ้าเป็นจัดซื้อให้ดึงมาเฉพาะที่ ผู้ขอซื้อ กับ ผู้อนุมัติ อนุมัติแล้ว
    if isPurchasing:
        data = PurchaseRequisition.objects.filter(purchase_status_id = 2, approver_status_id = 2)

        #เช็คว่าใช้หมดแล้วหรือเปล่า
        for pr in data:
            ri_is_used = RequisitionItem.objects.filter(requisition_id = pr.requisition.id, is_used = True, quantity_pr__gt=0).count()
            ri_all = RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0).count()
            if ri_is_used == ri_all:
                #ให้เอา pr ออกจากใน list
                data = data.exclude(id = pr.id)
    else:
        data = PurchaseRequisition.objects.all()

    #กรองข้อมูล
    myFilter = PurchaseRequisitionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
                'prs':dataPage,
                'filter':myFilter,
                'isPurchasing':isPurchasing,
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
    return user.groups.filter(name='Purchasing').exists()

def createPR(request, requisition_id):
    items= RequisitionItem.objects.filter(requisition_id = requisition_id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=requisition_id)
    baseUrgency = BaseUrgency.objects.all() #ระดับความเร่งด่วน
    baseUnit = BaseUnit.objects.all()
    #หา id express
    baseProduct = Product.objects.all()

    #ถ้า user login เป็นจัดซื้อ
    isPurchasing = is_purchasing(request.user)
        
    #หาจำนวนสินค้าทั้งหมด
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    #form
    form = PurchaseRequisitionForm(request.POST or None)
    if form.is_valid():
        #save PR
        new_contact = form.save()

        #save id express
        saveIdExpressPR(request)

        #save requisition ใน purchase_requisition_id 
        pr = PurchaseRequisition.objects.get(id = new_contact.pk)
        pr.requisition = requisition
        pr.purchase_status_id = 1 #กำหนดค่าเริ่มต้น
        pr.purchase_user_id = requisition.chief_approve_user_name
        pr.approver_status_id = 1 #กำหนดค่าเริ่มต้น
        #พัสดุ
        pr.stockman_user_id = request.user.id
        pr.stockman_update = datetime.datetime.now()
        pr.save()

        #save purchase_requisition_id ใน requisition
        obj = Requisition.objects.get(id = requisition_id)
        obj.purchase_requisition_id = new_contact.pk
        obj.pr_ref_no = pr.ref_no
        obj.save()
        return redirect('viewPR')

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

def createCMorPO(request, pr_id):
    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #หา id express
    baseProduct = Product.objects.all()

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
        )
        cp.save()

        cpd = ComparisonPriceDistributor.objects.create(
            cp_id = cp.id,
            vat_type_id = 1
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
                cp = cp.id
            )
            item.save()
        return redirect('editComparePricePOItemFromPR', cp_id = cp.id , cpd_id = cpd.id)
    if request.method=='POST' and 'btnformPO' in request.POST:
        po = PurchaseOrder.objects.create(
            stockman_user = request.user,
            approver_status_id = 1,
            vat_type_id = 1,
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
                unit_id = ri.unit,
                po_id = po.id
            )
            item.save()
        return redirect('editPOFromPR', po_id = po.id)

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
    baseProduct = Product.objects.all()

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

def showPR(request, pr_id, isAP):
    pr = PurchaseRequisition.objects.get(id=pr_id)

    items= RequisitionItem.objects.filter(requisition_id = pr.requisition.id, quantity_pr__gt=0)
    requisition = Requisition.objects.get(id=pr.requisition.id)
    baseUrgency = BaseUrgency.objects.all()
    baseUnit = BaseUnit.objects.all()
    #หา id express
    baseProduct = Product.objects.all()

    #หาจำนวนสินค้าทั้งหมด
    quantityTotal = 0
    for item in items:
        quantityTotal += item.quantity_pr

    if isAP == 'True':
        context = {
            'items':items,
            'requisition':requisition,
            'quantityTotal': quantityTotal,
            'baseUrgency': baseUrgency,
            'baseUnit': baseUnit,
            'baseProduct':baseProduct,
            'pr': pr,
            'create_mode': False,
            'ap_pr_page': "tab-active",
            'ap_pr_show': "show",
        }
    else:
        context = {
            'items':items,
            'requisition':requisition,
            'quantityTotal': quantityTotal,
            'baseUrgency': baseUrgency,
            'baseUnit': baseUnit,
            'baseProduct':baseProduct,
            'pr': pr,
            'create_mode': False,
            'pr_page': "tab-active",
            'pr_show': "show",
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
                            product_item = get_object_or_404(Product, id_express=val_product)
                            item.product = product_item
                            item.save()
                    else:
                        pass
    except stripe.error.CardError as e:
        return False, e


@login_required(login_url='signIn')
def viewPRApprove(request):

    data = PurchaseRequisition.objects.all()

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

def editPRApprove(request, pr_id):
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
        return redirect('viewPRApprove')

    return render(request, "purchaseRequisitionApprove/editPRApprove.html", context)

@login_required(login_url='signIn')
def viewPO(request):
    data = PurchaseOrder.objects.all()

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
        'po_page': "tab-active",
        'po_show': "show",
    }
    return render(request, "purchaseOrder/viewPO.html", context)

def preparePO(request):
    return render(request, 'purchaseOrder/preparePO.html')

def createPO(request):
    # set ค่าเริ่มต้นของเจ้าหน้าที่พัสดุ และสเตตัสการอนุมัติเป็น รอดำเนินการ
    form = PurchaseOrderForm(request.POST or None)
    if form.is_valid():
        form = PurchaseOrderForm(request.POST or None, request.FILES)
        new_contact = form.save(commit=False)
        new_contact.stockman_user = request.user
        new_contact.approver_status_id = 1
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
    po = PurchaseOrder.objects.get(id=po_id)
    form = PurchaseOrderForm(instance=po)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, request.FILES, instance=po)
        if form.is_valid():
            form.save()
            return redirect('editPOItem', po_id = po_id, isFromPR = 'True')

    context = {
        'form':form,
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
    items.delete()

    #ล้าง po_ref_no ที่ผูกไว้
    try:
        cp = ComparisonPrice.objects.get(po_ref_no = po.ref_no)
        cp.po_ref_no = ""
        cp.save()
    except (ComparisonPriceDistributor.DoesNotExist, AttributeError):
        pass

    #ลบ PurchaseOrder ทีหลัง
    po.delete()
    return redirect('viewPO')

def showPO(request, po_id, isAP):
    po = PurchaseOrder.objects.get(id = po_id)
    items = PurchaseOrderItem.objects.filter(po = po)

    if isAP == 'True':
        context = {
            'po':po,
            'items':items,
            'ap_po_page': "tab-active",
            'ap_po_show': "show",
        }
    else:
        context = {
            'po':po,
            'items':items,
            'po_page': "tab-active",
            'po_show': "show",
        }
    return render(request, 'purchaseOrder/showPO.html',context)

def createPOItem(request, po_id):
    template_name = 'purchaseOrderItem/createPOItem.html'
    heading_message = 'Model Formset Demo'
    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False)

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

def editPOItem(request, po_id, isFromPR):
    template_name = 'purchaseOrderItem/editPOItem.html'
    heading_message = 'Model Formset Demo'
    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False)

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
            price.save()

            form.save()
            # save po item
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()
            return redirect('viewPO')
    else:
        formset = PurchaseOrderItemInlineFormset(instance=po_data)
        price_form = PurchaseOrderPriceForm(instance=po_data)
        form = PurchaseOrderForm(instance=po_data)

    po = PurchaseOrder.objects.get(id = po_id)
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
        'heading': heading_message,
    }
    return render(request, template_name, context)

@login_required(login_url='signIn')
def viewPOApprove(request):

    data = PurchaseOrder.objects.all()

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

def editPOApprove(request, po_id):
    po = PurchaseOrder.objects.get(id = po_id)
    items = PurchaseOrderItem.objects.filter(po = po)

    #get permission with position login
    #get permission with position login
    try:
        user_profile = UserProfile.objects.get(user_id = request.user.id)

        permiss = BasePermission.objects.filter(codename ='CAAPO')
        isPermiss = PositionBasePermission.objects.filter(position_id = user_profile.position_id, base_permission__codename='CAAPO').prefetch_related(Prefetch('base_permission', queryset=permiss))
    except:
        isPermiss  = False

    if request.method == 'POST':
        post_status = request.POST['status'] or None
        status = BaseApproveStatus.objects.get(name = post_status)

        obj = PurchaseOrder.objects.get(id = po_id)
        #ผู้อนุมัติ
        if(isPermiss):
            obj.approver_status = status
            obj.approver_user_id = request.user.id
        obj.save()
        return redirect('viewPOApprove')

    context = {
                'po':po,
                'items':items,
                'isPermiss':isPermiss,
                'ap_po_page': "tab-active",
                'ap_po_show': "show",
    }
    return render(request, 'purchaseOrderApprove/editPOApprove.html',context)

@login_required(login_url='signIn')
def viewComparePricePO(request):
    data = ComparisonPrice.objects.all()

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
        'cp_page': "tab-active",
        'cp_show': "show",
    }

    return render(request, 'comparePricePO/viewComparePricePO.html',context)

def createComparePricePO(request):
    form = ComparisonPriceForm(request.POST or None, initial={'organizer': request.user.id, 'approver_status':1, 'examiner_status':1})
    if form.is_valid():
        new_contact = form.save()
        return HttpResponseRedirect(reverse('createComparePricePOItem', args=(new_contact.pk,)))

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
    return HttpResponseRedirect(reverse('createComparePricePOItem', args=(cp.id,)))

def createComparePricePOItem(request, cp_id):

    cp = ComparisonPrice.objects.get(id=cp_id)

    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False)

    try:
        bidder = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('id').first()
        bidder_oldest = bidder.id
    except (ComparisonPriceDistributor.DoesNotExist, AttributeError):
        bidder_oldest = None

    if request.method == 'GET':
        bookform = CPDModelForm(request.GET or None, initial={'cp': cp_id})
        formset = CPitemFormset(queryset=ComparisonPriceItem.objects.none())
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
            return redirect('createComparePricePOItem', cp_id = cp_id)

    cpd = ComparisonPriceDistributor.objects.filter(cp = cp_id)
    cp_item = ComparisonPriceItem.objects.filter(cp = cp_id)
    
    context = {
        'link_cp_id':cp_id,
        'cpd':cpd,
        'cp_item':cp_item,
        'bidder_oldest':bidder_oldest,
        'itemList': itemList,
        'bookform': bookform,
        'formset': formset,
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePOItem/createComparePricePOItem.html',context)

def editComparePricePOItemFromPR(request, cp_id , cpd_id):
    cp = ComparisonPrice.objects.get(id=cp_id)

    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False)

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
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()
            return redirect('createComparePricePOItem',cp_id = cp_id)    
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
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePOItem/editComparePricePOItemFromPR.html',context)

def editComparePricePOItem(request, cp_id , cpd_id):
    cp = ComparisonPrice.objects.get(id=cp_id)

    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False)

    data = ComparisonPriceDistributor.objects.get(id = cpd_id)
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
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()
            return redirect('createComparePricePOItem',cp_id = cp_id)
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
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePOItem/editComparePricePOItem.html',context)

def removeComparePriceDistributor(request, cp_id, cpd_id):
    cpd = ComparisonPriceDistributor.objects.get(id = cpd_id)
    #ลบ item ใน PurchaseOrder ด้วย
    items = ComparisonPriceItem.objects.filter(bidder = cpd)
    items.delete()
    #ลบ PurchaseOrder ทีหลัง
    cpd.delete()
    return redirect('createComparePricePOItem', cp_id = cp_id)

def printComparePricePO(request, cp_id):
    try:
        bidder_oldest = ComparisonPriceDistributor.objects.filter(cp = cp_id).order_by('id').first()
        items_oldest = ComparisonPriceItem.objects.filter(bidder = bidder_oldest.id)
    except (ComparisonPriceDistributor.DoesNotExist, ComparisonPriceItem.DoesNotExist, AttributeError):
        items_oldest = None

    pr_ref_no = ""
    if items_oldest:
        new_pr_id = dict()
        for obj in items_oldest:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

        for id in new_pr_id:
            pr = PurchaseRequisition.objects.get(id = id)
            pr_ref_no += pr.ref_no + ", "

    cp = ComparisonPrice.objects.get(id=cp_id)
    form = CPSelectBidderForm(instance=cp)
    if request.method == 'POST':
        form = CPSelectBidderForm(request.POST, instance=cp)
        if form.is_valid():
            form.save()
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
        'form':form,
        'baseSparesType' : baseSparesType,
        'cp_page': "tab-active",
        'cp_show': "show",
    }
    return render(request, 'comparePricePO/printComparePricePO.html',context)

def showComparePricePO(request, cp_id, isAP):
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
    if items_oldest:
        new_pr_id = dict()
        for obj in items_oldest:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

        for id in new_pr_id:
            pr = PurchaseRequisition.objects.get(id = id)
            pr_ref_no += pr.ref_no + ", "

    if isAP == 'True':
        context = {
            'cp':cp,
            'bidder' : bidder,
            'items_oldest' : items_oldest,
            'itemName':itemName,
            'baseSparesType':baseSparesType,
            'pr_ref_no': pr_ref_no,
            'ap_cp_page': "tab-active",
            'ap_cp_show': "show",
        }
    else:
        context = {
            'cp':cp,
            'bidder' : bidder,
            'items_oldest' : items_oldest,
            'itemName':itemName,
            'baseSparesType':baseSparesType,
            'pr_ref_no': pr_ref_no,
            'cp_page': "tab-active",
            'cp_show': "show",
        }
    return render(request, 'comparePricePO/showComparePricePO.html',context)

def createPOFromComparisonPrice(request, cp_id):
    #set ค่าเริ่มต้นของเจ้าหน้าที่พัสดุ และสเตตัสการอนุมัติเป็น รอดำเนินการ
    form = PurchaseOrderFromComparisonPriceForm(request.POST or None, initial={'cp': cp_id})
    if form.is_valid():
        new_contact = form.save(commit=False)
        cp = ComparisonPrice.objects.get(id = new_contact.cp.id)
        cpd = ComparisonPriceDistributor.objects.get(cp = new_contact.cp.id, distributor = cp.select_bidder)
        new_contact.distributor = cp.select_bidder
        new_contact.credit = cpd.credit
        new_contact.stockman_user = cp.organizer
        new_contact.vat_type = cpd.vat_type
        new_contact.quotation_pdf = cpd.quotation_pdf
        #ดึงสถานะอนุมัติใบเปรียบเทียบมาใบขอซื้อเลย
        new_contact.approver_user = cp.approver_user
        new_contact.approver_status = cp.approver_status
        new_contact.approver_update = cp.approver_update
        
        new_contact.save()

        cp.po_ref_no = new_contact.ref_no
        cp.save()
        return HttpResponseRedirect(reverse('createPOItemFromComparisonPrice', args=(new_contact.pk,)))

    context = {
        'form':form,
        'po_page': "tab-active",
        'po_show': "show",
    }

    return render(request, "purchaseOrder/createPO.html", context)

def createPOItemFromComparisonPrice(request, po_id):
    template_name = 'purchaseOrderItem/createPOItemFromComparisonPrice.html'
    heading_message = 'Model Formset Demo'
    #ดึง item ที่ทำใบ po แล้ว
    itemList = RequisitionItem.objects.filter(requisit__purchase_requisition_id__isnull = False)

    po_data = PurchaseOrder.objects.get(id=po_id)
    po_items = PurchaseOrderItem.objects.filter(po = po_id)
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
        'heading': heading_message,
    }
    return render(request, template_name, context)

@login_required(login_url='signIn')
def viewCPApprove(request):
    data = ComparisonPrice.objects.all()

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

def printCPApprove(request, cp_id):
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

    try:
        cpd_select = ComparisonPriceDistributor.objects.get(cp = cp, distributor = cp.select_bidder)
    except ComparisonPriceDistributor.DoesNotExist:
        cpd_select = None

    if isPermissAA and cpd_select:
        if pmAA.ap_amount_min <= cpd_select.amount <= pmAA.ap_amount_max:
            isApprover = True

    if isPermissAE and cpd_select:
        if pmAE.ap_amount_min <= cpd_select.amount <= pmAE.ap_amount_max:
            isExaminer = True


    pr_ref_no = ""
    if items_oldest:
        new_pr_id = dict()
        for obj in items_oldest:
            if obj.item.requisit.purchase_requisition_id not in new_pr_id:
                new_pr_id[obj.item.requisit.purchase_requisition_id] = obj

        for id in new_pr_id:
            pr = PurchaseRequisition.objects.get(id = id)
            pr_ref_no += pr.ref_no + ", "

    if request.method == 'POST':
        post_status = request.POST['status'] or None
        status = BaseApproveStatus.objects.get(name = post_status)

        obj = ComparisonPrice.objects.get(id = cp_id)
        #ผู้อนุมัติ

        if(isApprover):
            obj.approver_status = status
            obj.approver_user_id = request.user.id
            obj.approver_update = datetime.datetime.now()
        elif(isExaminer):
            obj.examiner_status = status
            obj.examiner_user_id = request.user.id
            obj.examiner_update = datetime.datetime.now()
        obj.save()
        return redirect('viewCPApprove')

    context = {
        'cp':cp,
        'bidder' : bidder,
        'items_oldest' : items_oldest,
        'itemName':itemName,
        'baseSparesType':baseSparesType,
        'pr_ref_no': pr_ref_no,
        'isApprover': isApprover,
        'isExaminer': isExaminer,
        'ap_cp_page': "tab-active",
        'ap_cp_show': "show",
    }
    return render(request, 'comparePricePOApprove/printCPApprove.html',context)

def searchItemExpress(request):
    strName = ""
    name = request.GET.get('title', None)
    product = Product.objects.filter(name__icontains=name)
    for i in product:
        strName += "<div class='row'><div class='col-2'>"+ i.id_express + "</div><div class='col-5'>" + i.name + "</div><div class='col'>เหลือใน stock&emsp;"+ str(i.stock) + '</div></div>' 
    
    data = {
        'instance': strName,
    }
    return JsonResponse(data)

def viewReceive(request):
    data = Receive.objects.all()

    #กรองข้อมูล
    myFilter = ReceiveFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    dataPage = p.get_page(page)

    context = {
        'rcs':dataPage,
        'filter':myFilter,
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
        pr.purchase_status_id = 1 #กำหนดค่าเริ่มต้น
        pr.purchase_update = None
        pr.approver_status_id = 1 #กำหนดค่าเริ่มต้น
        pr.approver_update = None
        #พัสดุ
        pr.stockman_user_id = request.user.id
        pr.stockman_update = datetime.datetime.now()
        pr.save()

        users = RequisitionItem.objects.filter(requisit = pr.requisition)
        requisition = Requisition.objects.get(id = pr.requisition.id)
            
        baseUrgency = BaseUrgency.objects.all()
        baseUnit = BaseUnit.objects.all()
        baseProduct = Product.objects.all()

        context = {
            'users' : users,
            'requisition' : requisition,
            'pr' : pr,
            'baseUrgency' : baseUrgency,
            'baseUnit' : baseUnit,
            'baseProduct' : baseProduct,
            'ap_pr_page': "tab-active",
            'ap_pr_show': "show",
        }

        return render(request, "purchaseRequisition/reApprovePR.html", context)

def export(request):
    person_resource = ReceiveItemResource()
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
                if data[0] is None and data[1] is None and data[2] is None and data[3] is None:
                    pass
                elif not(data[0] is None):
                    #เช็คว่าเคย save ไปหรือยังถ้าเคยจะไม่ให้ save
                    try:
                        rc_old = Receive.objects.get(ref_no = data[0])
                    except:
                        rc_old = None
                    if not rc_old:
                        po = PurchaseOrder.objects.get(ref_no = data[10])
                        rc = Receive(
                            ref_no = data[0],
                            created = data[1],
                            distributor_id = data[2],
                            tax_invoice = data[3],
                            total_price = data[6],
                            total_after_discount = data[6],
                            vat = data[7],
                            amount = data[8],
                            due_date = data[9],
                            pay = data[11],
                            po_id = po.id,
                            receive_user = request.user,
                            )
                        rc.save()
                elif data[0] is None and data[1] is None and data[2] is None and not(data[3] is None):
                    rc = Receive.objects.get(po__ref_no = data[12])
                    po_item = PurchaseOrderItem.objects.get(po_id = rc.po.id, item__product__id_express = data[4])
                    #เช็คว่าเคย save ไปหรือยังถ้าเคยจะไม่ให้ save
                    try:
                        rc_item_old =  ReceiveItem.objects.get(item_id = po_item.id)
                    except:
                        rc_item_old = None
                    if not rc_item_old:
                        unit = BaseUnit.objects.get(name = data[8])
                        if po_item:
                            rc_item = ReceiveItem(
                                id = data[2],
                                item_id = po_item.id,
                                quantity = data[7],
                                unit_id  = unit.id,
                                unit_price  = data[9],
                                price = data[11],
                                rc_id = rc.id,
                            )
                            rc_item.save()
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
