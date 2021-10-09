from django.db.models.deletion import CASCADE
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import Group, User
import stock
from django.db import models
from django.urls import reverse
from django.core.validators import MaxLengthValidator
import datetime
from datetime import date

def requisition_ref_number():   
    today = datetime.datetime.now()
    year = str(today.strftime('%y'))
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'R-'+ YM

    try:
        last_no = Requisition.objects.all().filter(ref_no__contains=format).order_by('id').last()
    except:
        last_no = None

    if not last_no:
        return format + '001'

    ref_no = last_no.ref_no
    oldDate =  ref_no[2:-3]
    if YM == oldDate:
        no_int = int(ref_no.split(format)[-1])
    elif YM != oldDate:
        no_int = 000
    
    width = 3
    new_no_int = no_int + 1
    formatted = (width - len(str(new_no_int))) * "0" + str(new_no_int)
    new_no = format + str(formatted)
    return new_no

def purchaseRequisition_ref_number():
    today = datetime.datetime.now()
    year = str(today.strftime('%y'))
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'PR-'+ YM

    try:
        last_no = PurchaseRequisition.objects.all().filter(ref_no__contains=format).order_by('id').last()
    except:
        last_no = None

    if not last_no:
        return format + '001'

    ref_no = last_no.ref_no
    oldDate =  ref_no[3:-3]
    if YM == oldDate:
        no_int = int(ref_no.split(format)[-1])
    elif YM != oldDate:
        no_int = 000
    
    width = 3
    new_no_int = no_int + 1
    formatted = (width - len(str(new_no_int))) * "0" + str(new_no_int)
    new_no = format + str(formatted)
    return new_no

def comparisonPrice_ref_number():
    
    today = datetime.datetime.now()
    year = str(today.strftime('%y'))
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'CM-'+ YM

    try:
        last_no = ComparisonPrice.objects.all().filter(ref_no__contains=format).order_by('id').last()
    except:
        last_no = None

    if not last_no:
        return format + '001'

    ref_no = last_no.ref_no
    oldDate =  ref_no[3:-3]
    if YM == oldDate:
        no_int = int(ref_no.split(format)[-1])
    elif YM != oldDate:
        no_int = 000
    
    width = 3
    new_no_int = no_int + 1
    formatted = (width - len(str(new_no_int))) * "0" + str(new_no_int)
    new_no = format + str(formatted)
    return new_no

def purchaseOrder_ref_number():
    today = datetime.datetime.now()
    year = str(today.strftime('%y'))
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'PO-'+ YM

    try:
        last_no = PurchaseOrder.objects.all().filter(ref_no__contains=format).order_by('id').last()
    except:
        last_no = None

    if not last_no:
        return format + '001'

    ref_no = last_no.ref_no
    oldDate =  ref_no[3:-3]
    if YM == oldDate:
        no_int = int(ref_no.split(format)[-1])
    elif YM != oldDate:
        no_int = 000
    
    width = 3
    new_no_int = no_int + 1
    formatted = (width - len(str(new_no_int))) * "0" + str(new_no_int)
    new_no = format + str(formatted)
    return new_no

# Create your models here.
def get_first_name(self):
    return self.first_name + " " + self.last_name
User.add_to_class("__str__", get_first_name)

class Category(models.Model):
    name = models.CharField(max_length=255,unique=True) #ชื่อโหมดที่ไม่ซ้ำกัน
    slug = models.SlugField(max_length=255,unique=True) #เก็บ url ไว้ผูกข้อมูล Category

    def __str__(self):
        return self.name
        
    class Meta :
        ordering = ('name',)
        verbose_name = 'หมวดหมู่สินค้า'
        verbose_name_plural = 'ข้อมูลประเภทสินค้า'
    
    def get_url(self):
        return reverse('product_by_category', args=[self.slug])

class Product(models.Model):
    name = models.CharField(max_length=255,unique=True) #ชื่อโหมดที่ไม่ซ้ำกัน
    slug = models.SlugField(max_length=255,unique=True) #เก็บ url ไว้ผูกข้อมูล Product
    description = models.TextField(blank=True) #เป็นค่าว่างได้
    price = models.DecimalField(max_digits=20,decimal_places=2) #ราคา Product มีเลข 20 หลัก ทศนิยม 2 ตำแหน่ง
    category = models.ForeignKey(Category,on_delete=models.CASCADE) #ดึงข้อมูล Category มาใช้ใน Product และ on_delete = models.CASCADE คือหากลบอันใดอันนึงให้ลบทั้งหมดเลย
    image = models.ImageField(upload_to="product",blank=True) #เก็บรูปภาพ
    stock = models.IntegerField() #จำนวนชิ้นของ Product
    available = models.BooleanField(default=True) #Product ใช้งานได้ไหม
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    id_express = models.CharField(max_length=255, blank = True, null = True, unique=True)#เก็บไอดีสินค้าใน express
     
    def __str__(self):
        return self.name
    
    class Meta :
        ordering = ('name',)
        verbose_name = 'สินค้า'
        verbose_name_plural = 'ข้อมูลสินค้า'
    
    def get_url(self):
        return reverse('productDetail', args=[self.category.slug, self.slug])

class Cart(models.Model):
    cart_id = models.CharField(max_length=255, blank=True)
    date_add = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

    class Meta :
        db_table = 'cart' # ตั้งชื่อ table ถ้าไม่กำหนดจะตั้งเป็น stock_cart
        ordering = ('date_add',) #เรียงลำดับเวลาตามที่ add เข้าไป        
        verbose_name = 'ตะกร้าสินค้า'
        verbose_name_plural = 'ข้อมูลตะกร้าสินค้า'

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete = models.CASCADE) #ดึงข้อมูล Product มาใช้ใน CartItem และ on_delete = models.CASCADE คือหากลบอันใดอันนึงให้ลบทั้งหมดเลย
    cart = models.ForeignKey(Cart, on_delete = models.CASCADE) #ดึงข้อมูล Cart มาใช้ใน CartItem และ on_delete = models.CASCADE คือหากลบอันใดอันนึงให้ลบทั้งหมดเลย
    quantity = models.IntegerField() #เก็บจำนวนสินค้าที่เพิ่มลงตะกร้า
    active = models.BooleanField(default=True) #CartItem ใช้งานได้ไหม

    class Meta :
        db_table = 'cartItem' # ตั้งชื่อ table ถ้าไม่กำหนดจะตั้งเป็น stock_cartItem
        verbose_name = 'รายการตะกร้าสินค้า'
        verbose_name_plural = 'ข้อมูลรายการตะกร้าสินค้า'

    def sub_total(self):
        return self.product.price * self.quantity #ราคาสินค้า * จำนวนสินค้า
    
    def __str__(self):
        return self.product.name #get ชื่อ product name

class Order(models.Model):
    name=models.CharField(max_length=255,blank=True)
    address=models.CharField(max_length=255,blank=True) #ที่อยู่ลูกค้า
    city=models.CharField(max_length=255,blank=True) #เมือง
    postcode=models.CharField(max_length=255,blank=True) #ไปรษณีย์
    total=models.DecimalField(max_digits=10,decimal_places=2)
    email=models.EmailField(max_length=250,blank=True)
    token=models.CharField(max_length=255,blank=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด

    class Meta:
        db_table='Order'
        ordering=('id',)

    def __str__(self):
        return str(self.id)

class OrderItem(models.Model):
    product=models.CharField(max_length=250)
    quantity=models.IntegerField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    order = models.ForeignKey(Order, on_delete = models.CASCADE)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด

    class Meta:
        db_table = 'OrderItem'
        ordering=('id',)

    def sub_total(self):
        return self.quantity * self.price

    def __str__(self):
        return self.product

class BaseApproveStatus(models.Model):
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'BaseApproveStatus'
        ordering=('id',)
        verbose_name = 'สถานะการอนุมัติ'
        verbose_name_plural = 'ข้อมูลสถานะการอนุมัติ'

    def __str__(self):
        return str(self.name)

class BaseUrgency(models.Model):
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True) #เป็นค่าว่างได้

    class Meta:
        db_table = 'BaseUrgency'
        ordering=('id',)
        verbose_name = 'ระดับความเร่งด่วน'
        verbose_name_plural = 'ข้อมูลระดับความเร่งด่วน'

    def __str__(self):
        return str(self.name + " " + self.description)

class BaseUnit(models.Model):
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'BaseUnit'
        ordering=('id',)
        verbose_name = 'หน่วยสินค้า'
        verbose_name_plural = 'ข้อมูลหน่วยสินค้า'

    def __str__(self):
        return str(self.name)

class BaseCredit(models.Model):
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'BaseCredit'
        ordering=('id',)
        verbose_name = 'เครดิต'
        verbose_name_plural = 'ข้อมูลเครดิต'

    def __str__(self):
        return str(self.name)


class Requisition(models.Model):
    purchase_requisition_id =  models.IntegerField(blank=True, null=True,unique=True)
    name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='name'
    )
    section = models.ForeignKey(Group, on_delete=models.CASCADE,blank=True, null=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    chief_approve_user_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chief_approve_user_name'
    )
    supplies_approve_user_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='supplies_approve_user_name'
    )
    urgency = models.ForeignKey(BaseUrgency, on_delete=models.CASCADE, blank=True, null=True)
    ref_no = models.CharField(max_length = 500, default = requisition_ref_number, null = True, blank = True)

    class Meta:
        db_table = 'Requisition'
        ordering=('-id',)

    def __str__(self):
        return str(self.id)


class RequisitionItem(models.Model):
    requisition_id = models.IntegerField()
    product_name = models.CharField(max_length=255,blank=True)
    description = models.TextField(blank=True) #เป็นค่าว่างได้
    quantity = models.IntegerField()
    machine = models.CharField(max_length=255,blank=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    desired_date = models.DateField(blank=True, null=True)
    unit = models.IntegerField(blank=True, null=True)
    urgency = models.IntegerField(blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    requisit = models.ForeignKey(Requisition, on_delete=models.CASCADE, null=True)
    quantity_pr = models.IntegerField()
    quantity_take = models.IntegerField()

    class Meta:
        db_table = 'RequisitionItem'
        ordering=('id',)
    
    def __str__(self):
        return str(self.product)

class CrudUser(models.Model):
    name = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=100, blank=True)
    age = models.IntegerField(blank=True, null=True)

class PurchaseRequisition(models.Model):
    requisition = models.ForeignKey(Requisition, on_delete = models.CASCADE, null=True)
    stockman_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stockman_user',
        null=True
    )
    stockman_update = models.DateField(blank=True, null=True)
    purchase_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchase_user',
        null=True
    )
    purchase_status = models.ForeignKey(
        BaseApproveStatus,
        on_delete=models.CASCADE,
        related_name='purchase_status',
        null=True
    )
    purchase_update = models.DateField(blank=True, null=True)
    approver_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approver_user',
        null=True
    )
    approver_status = models.ForeignKey(
        BaseApproveStatus,
        on_delete=models.CASCADE,
        related_name='approver_status',
        null=True
    )
    approver_update = models.DateField(blank=True, null=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    note = models.CharField(max_length=255, blank=True)
    ref_no = models.CharField(max_length = 500, default = purchaseRequisition_ref_number, null = True, blank = True)

    class Meta:
        db_table = 'PurchaseRequisition'
        ordering=('-id',)

#ตำแหน่งงาน
class Position(models.Model):
    name = models.CharField(max_length=255,unique=True)

    class Meta:
        db_table = 'Position'
        ordering=('id',)
        verbose_name = 'ประเภทตำแหน่งงาน'
        verbose_name_plural = 'ข้อมูลประเภทตำแหน่งงาน'
    
    def __str__(self):
        return str(self.name)

class BasePermission(models.Model):
    name = models.CharField(max_length=255,unique=True)
    codename = models.CharField(max_length=255,unique=True)
    codename_th = models.CharField(max_length=255,unique=True)

    class Meta:
        db_table = 'BasePermission'
        ordering=('id',)
        verbose_name = 'สิทธิการทำงาน'
        verbose_name_plural = 'ข้อมูลสิทธิการทำงาน'

    def __str__(self):
        return str(self.codename_th)

class BaseSparesType(models.Model):
    name = models.CharField(max_length=255,unique=True)

    class Meta:
        db_table = 'BaseSparesType'
        ordering=('id',)
        verbose_name = 'ชนิดอะไหล่'
        verbose_name_plural = 'ข้อมูลชนิดอะไหล่'
    
    def __str__(self):
        return str(self.name)


class PositionBasePermission(models.Model):
    position = models.ForeignKey(Position, on_delete = models.CASCADE)
    base_permission = models.ForeignKey(BasePermission, on_delete = models.CASCADE)
    class Meta:
        db_table = 'PositionBasePermission'
        ordering=('id',)
        verbose_name = 'ตำแหน่งงานและสิทธิการทำงาน'
        verbose_name_plural = 'ข้อมูลตำแหน่งงานและสิทธิการทำงาน'

#USER PROFILE
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.ForeignKey(Position,on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'ผู้ใช้และตำแหน่งงาน'
        verbose_name_plural = 'ข้อมูลผู้ใช้และตำแหน่งงาน'

    def __str__(self):
        return self.user.username

class Distributor(models.Model):
    id_express = models.CharField(max_length=255, blank = True, null = True, unique=True)#เก็บไอดีสินค้าใน express
    name =  models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True)
    tel = models.CharField(max_length=255, blank = True)
    fax =  models.CharField(max_length=255, blank = True)

    class Meta:
        db_table = 'Distributor'
        ordering=('id',)
        verbose_name = 'ผู้จัดจำหน่าย'
        verbose_name_plural = 'ข้อมูลผู้จัดจำหน่าย'

    def __str__(self):
        return self.name

class BaseVatType(models.Model):
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'BaseVatType'
        ordering=('id',)
        verbose_name = 'ประเภทภาษี'
        verbose_name_plural = 'ข้อมูลประเภทภาษี'

    def __str__(self):
        return str(self.name)

class ComparisonPrice(models.Model):
    organizer = models.ForeignKey(User,on_delete=models.CASCADE)
    base_spares_type = models.ForeignKey(BaseSparesType,on_delete=models.CASCADE, null=True, blank=True)
    select_bidder = models.ForeignKey(Distributor,on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    note = models.CharField(max_length=255, blank = True)
    approver_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cp_approver_user',
        null=True
    )
    approver_status = models.ForeignKey(
        BaseApproveStatus,
        on_delete=models.CASCADE,
        related_name='cp_approver_status',
        null=True
    )
    approver_update = models.DateField(blank=True, null=True)
    examiner_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cp_examiner_user',
        null=True
    )
    examiner_status = models.ForeignKey(
        BaseApproveStatus,
        on_delete=models.CASCADE,
        related_name='cp_examiner_status',
        null=True
    )
    examiner_update = models.DateField(blank=True, null=True)
    ref_no = models.CharField(max_length = 500, default = comparisonPrice_ref_number, null = True, blank = True)

    class Meta:
        db_table = 'ComparisonPrice'
        ordering=('-id',)
    
    def __str__(self):
        return str(self.ref_no)

class PurchaseOrder(models.Model):
    distributor = models.ForeignKey(Distributor,on_delete=models.CASCADE,null = True,blank = True)
    vat_type = models.ForeignKey(BaseVatType,on_delete=models.CASCADE)
    credit = models.ForeignKey(BaseCredit,on_delete=models.CASCADE,null = True,blank = True)
    shipping = models.CharField(max_length=255, blank = True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#รวมเป็นเงิน
    discount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#หักส่วนลด
    total_after_discount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินหลังหักส่วนลด
    vat = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ภาษี
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    note = models.CharField(max_length=255, blank = True)
    stockman_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stockman_user_po',
        null=True
    )
    approver_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approver_user_po',
        null=True
    )
    approver_status = models.ForeignKey(
        BaseApproveStatus,
        on_delete=models.CASCADE,
        related_name='approver_status_po',
        null=True
    )
    approver_update = models.DateField(blank=True, null=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    cp = models.ForeignKey(ComparisonPrice,on_delete=models.CASCADE,null = True)
    ref_no = models.CharField(max_length = 500, default = purchaseOrder_ref_number, null = True, blank = True)

    class Meta:
        db_table = 'PurchaseOrder'
        ordering=('-id',)

class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(RequisitionItem,on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(null=True, blank=True)
    unit = models.ForeignKey(BaseUnit,on_delete=models.CASCADE, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด

    class Meta:
        db_table = 'PurchaseOrderItem'
        ordering=('id',)

class ComparisonPriceDistributor(models.Model):
    distributor = models.ForeignKey(Distributor,on_delete=models.CASCADE, null = True)
    credit = models.ForeignKey(BaseCredit,on_delete=models.CASCADE,null = True)
    vat_type = models.ForeignKey(BaseVatType,on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#รวมเป็นเงิน
    discount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#หักส่วนลด
    total_after_discount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินหลังหักส่วนลด
    vat = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ภาษี
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    cp =  models.ForeignKey(ComparisonPrice,on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'ComparisonPriceDistributor'
        ordering=('id',)

class ComparisonPriceItem(models.Model):
    item = models.ForeignKey(RequisitionItem,on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(null=True, blank=True)
    unit = models.ForeignKey(BaseUnit,on_delete=models.CASCADE, null=True)
    brand = models.CharField(max_length=255, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    bidder =  models.ForeignKey(ComparisonPriceDistributor,on_delete=models.CASCADE, null=True)
    cp =  models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'ComparisonPriceItem'
        ordering=('id',)



