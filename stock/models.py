from django.db.models.deletion import CASCADE
from django.db.models.expressions import F
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import Group, User
import stock
from django.db import models
from django.urls import reverse
from django.core.validators import MaxLengthValidator
from django.core.files.storage import FileSystemStorage
import datetime
from datetime import date
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.template.defaultfilters import truncatechars
import pytz
import os

def requisition_ref_number(branch_company):
    #tz = pytz.timezone('Asia/Bangkok')
    today = datetime.datetime.now()
    year = str(int(today.strftime('%Y')) + 543)[2:4]
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'Q'+ str(branch_company) + YM

    try:
        last_no = Requisition.objects.all().filter(ref_no__contains=format).order_by('id').last()
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

def purchaseRequisition_ref_number(branch_company):
    today = datetime.datetime.now()
    year = str(int(today.strftime('%Y')) + 543)[2:4]
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'R'+ str(branch_company) + YM

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

def comparisonPrice_ref_number(branch_company):
    today = datetime.datetime.now()
    year = str(int(today.strftime('%Y')) + 543)[2:4]
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'C'+ str(branch_company) + YM

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

def purchaseOrder_ref_number(branch_company):
    today = datetime.datetime.now()
    year = str(int(today.strftime('%Y')) + 543)[2:4]
    month = str(today.strftime('%m'))
    YM = year + month
    format = str(branch_company) + YM

    try:
        last_no = PurchaseOrder.objects.all().filter(ref_no__contains=format).order_by('id').last()
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

def receive_ref_number():
    today = datetime.datetime.now()
    year = str(today.strftime('%y'))
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'RC'+ YM

    try:
        last_no = Receive.objects.all().filter(ref_no__contains=format).order_by('id').last()
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

# Create your models here.
def get_first_name(self):
    return self.first_name + " " + self.last_name
User.add_to_class("__str__", get_first_name)

class BaseIsoCode(models.Model):
    r_code = models.TextField(max_length=255, verbose_name="รหัส iso ใบขอเบิก")
    pr_code = models.TextField(max_length=255, verbose_name="รหัส iso ใบขอซื้อ")
    cm_code = models.TextField(max_length=255, verbose_name="รหัส iso ใบเปรียบเทียบ")
    po_code = models.TextField(max_length=255, verbose_name="รหัส iso ใบสั่งซื้อ")

    class Meta:
        db_table = 'BaseIsoCode'
        ordering=('id',)
        verbose_name = 'รหัส iso'
        verbose_name_plural = 'ข้อมูลรหัส iso'
    
    def __str__(self):
        return str(self.id)

class BaseAffiliatedCompany(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="โค้ดบริษัท")
    name_sh = models.CharField(max_length=255, blank=True, null = True, verbose_name="ชื่อบริษัทย่อ")
    name_th = models.CharField(max_length=255, blank=True, null = True, verbose_name="ชื่อบริษัทไทย")
    name_eng = models.CharField(max_length=255, blank=True, null = True, verbose_name="ชื่อบริษัทอังกฤษ")
    address = models.CharField(max_length=255, blank=True, null = True, verbose_name="ที่อยู่")
    tel = models.CharField(max_length=255, blank = True, null = True, verbose_name="เบอร์โทร")
    tex = models.CharField(max_length=255, blank = True, null = True, verbose_name="เลขประจำตัวผู้เสียภาษี")
    branch = models.CharField(max_length=255, blank = True, null = True, verbose_name="สาขา")
    logo = models.ImageField(null=True, blank=True, upload_to = "company/",verbose_name="โลโก้บริษัท")
    iso_code = models.ForeignKey(BaseIsoCode, on_delete=models.CASCADE, blank = True, null = True, verbose_name="รหัส iso")

    class Meta:
        db_table = 'BaseAffiliatedCompany'
        ordering=('id',)
        verbose_name = 'สังกัดบริษัท'
        verbose_name_plural = 'ข้อมูลสังกัดบริษัท'

    @property
    def logo_preview(self):
        if self.logo:
            return mark_safe('<img src="{}" height="100" />'.format(self.logo.url))
        return ""

    def __str__(self):
        return self.name

class BaseBranchCompany(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสสาขาบริษัท")
    code = models.CharField(max_length=255,unique=True, verbose_name="โค้ดสาขาบริษัท")
    affiliated = models.ForeignKey(BaseAffiliatedCompany, on_delete=models.CASCADE, blank = True, null = True,related_name='branch_affiliated', verbose_name="ชื่อสังกัดบริษัท")
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อสาขาบริษัท", blank = True, null = True)

    class Meta:
        db_table = 'BaseBranchCompany'
        ordering=('id',)
        verbose_name = 'สาขาบริษัท'
        verbose_name_plural = 'ข้อมูลสาขาบริษัท'

    def __str__(self):
        return self.code

class BaseUnit(models.Model):
    name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อหน่วยสินค้า")

    class Meta:
        db_table = 'BaseUnit'
        ordering=('name',)
        verbose_name = 'หน่วยสินค้า'
        verbose_name_plural = 'ข้อมูลหน่วยสินค้า'

    def __str__(self):
        return str(self.name)

class BaseDepartment(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อแผนก")

    class Meta:
        db_table = 'BaseDepartment'
        ordering=('id',)
        verbose_name = 'แผนก'
        verbose_name_plural = 'ข้อมูลแผนก'

    def __str__(self):
        return self.name
    
class BaseGrade(models.Model):
    name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อเกรด")

    class Meta:
        db_table = 'BaseGrade'
        ordering=('name',)
        verbose_name = 'เกรด'
        verbose_name_plural = 'ข้อมูลเกรด'

    def __str__(self):
        return str(self.name)

class Category(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อหมวดหมู่สินค้า") #ชื่อโหมดที่ไม่ซ้ำกัน
    slug = models.SlugField(max_length=255,unique=True, verbose_name="ลิ้งค์") #เก็บ url ไว้ผูกข้อมูล Category

    def __str__(self):
        return self.name
        
    class Meta :
        ordering = ('name',)
        ordering = ('id',)
        verbose_name = 'หมวดหมู่สินค้า'
        verbose_name_plural = 'ข้อมูลหมวดหมู่สินค้า'
    
    def get_url(self):
        return reverse('product_by_category', args=[self.slug])

class Product(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสสินค้า")#เก็บไอดีสินค้าใน express
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อสินค้า") #ชื่อโหมดที่ไม่ซ้ำกัน
    unit = models.ForeignKey(BaseUnit, on_delete=models.CASCADE, null=True, blank = True, verbose_name="หน่วยสินค้า")
    slug = models.SlugField(max_length=255,unique=True, verbose_name="ลิ้งค์") #เก็บ url ไว้ผูกข้อมูล Product
    description = models.TextField(blank=True, verbose_name="รายละเอียด") #เป็นค่าว่างได้
    price = models.DecimalField(max_digits=20,decimal_places=2, null=True, blank = True, verbose_name="ราคา") #ราคา Product มีเลข 20 หลัก ทศนิยม 2 ตำแหน่ง
    category = models.ForeignKey(Category,on_delete=models.CASCADE, null=True, blank = True, verbose_name="หมวดหมู่สินค้า") #ดึงข้อมูล Category มาใช้ใน Product และ on_delete = models.CASCADE คือหากลบอันใดอันนึงให้ลบทั้งหมดเลย
    image = models.ImageField(upload_to="product",blank=True, verbose_name="รูปภาพ") #เก็บรูปภาพ
    stock = models.IntegerField(null=True, blank = True, verbose_name="จำนวนสินค้าในสต็อก") #จำนวนชิ้นของ Product
    available = models.BooleanField(default=True, verbose_name="ใช้งานอยู่") #Product ใช้งานได้ไหม
    created = models.DateField(auto_now_add=True, verbose_name="วันที่สร้าง") #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True, verbose_name="วันที่อัพเดท") #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    affiliated = models.ForeignKey(BaseAffiliatedCompany, on_delete=models.CASCADE, blank = True, null = True, verbose_name="สังกัดบริษัท")
     
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
    name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อระดับความเร่งด่วน")
    description = models.TextField(blank=True, verbose_name="รายละเอียดระดับความเร่งด่วน") #เป็นค่าว่างได้

    class Meta:
        db_table = 'BaseUrgency'
        ordering=('id',)
        verbose_name = 'ระดับความเร่งด่วน'
        verbose_name_plural = 'ข้อมูลระดับความเร่งด่วน'

    def __str__(self):
        return str(self.name + " " + self.description)

class BaseCredit(models.Model):
    name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อเครดิต")

    class Meta:
        db_table = 'BaseCredit'
        ordering=('id',)
        verbose_name = 'เครดิต'
        verbose_name_plural = 'ข้อมูลเครดิต'

    def __str__(self):
        return str(self.name)


class BaseAddress(models.Model):
    name_th = models.CharField(max_length=255, blank=True, null = True, verbose_name="ชื่อบริษัทไทย")
    name_eng = models.CharField(max_length=255, blank=True, null = True, verbose_name="ชื่อบริษัทอังกฤษ")
    address = models.CharField(max_length=255, blank=True, null = True, verbose_name="ที่อยู่")
    tel = models.CharField(max_length=255, blank = True, null = True, verbose_name="เบอร์โทร")
    tex = models.CharField(max_length=255, blank = True, null = True, verbose_name="เลขประจำตัวผู้เสียภาษี")
    branch = models.CharField(max_length=255, blank = True, null = True, verbose_name="สาขา")
    logo = models.ImageField(null=True, blank=True, upload_to = "company/",verbose_name="โลโก้บริษัท")

    class Meta:
        db_table = 'BaseAddress'
        ordering=('id',)
        verbose_name = 'ที่อยู่ตามจดทะเบียนบริษัท'
        verbose_name_plural = 'ข้อมูลที่อยู่ตามจดทะเบียนบริษัท'

    @property
    def logo_preview(self):
        if self.logo:
            return mark_safe('<img src="{}" height="100" />'.format(self.logo.url))
        return ""

    def __str__(self):
        return self.name_th + " " + self.address

class BranchCompanyBaseAdress(models.Model):
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    address = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    class Meta:
        db_table = 'BranchCompanyBaseAdress'
        ordering=('id',)
        verbose_name = 'บริษัทและที่อยู่ตามจดทะเบียน'
        verbose_name_plural = 'ข้อมูลบริษัทและที่อยู่ตามจดทะเบียน'

    def __str__(self):
        return str(self.address)

class Requisition(models.Model):
    purchase_requisition_id =  models.IntegerField(blank=True, null=True,unique=True)
    pr_ref_no = models.CharField(max_length = 255, null = True, blank = True)
    name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='name'
    )
    section = models.ForeignKey(BaseDepartment, on_delete=models.CASCADE,blank=True, null=True)
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
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    is_edit = models.BooleanField(default=True)
    memorandum_pdf = models.FileField(null=True, blank=True, upload_to='pdfs/memorandum/%Y/%m/%d')
    organizer = models.ForeignKey(User,on_delete=models.CASCADE, related_name='organizer')#เจ้าหน้าที่จัดซื้อที่เป็นผู้จัดทำ
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = requisition_ref_number(self.branch_company)
        super(Requisition, self).save(*args, **kwargs)

    class Meta:
        db_table = 'Requisition'
        ordering=('-id',)

    def __str__(self):
        return str(self.id)

class RequisitionItem(models.Model):
    requisition_id = models.IntegerField()
    product_name = models.CharField(max_length=255,blank=True)
    description = models.TextField(blank=True) #เป็นค่าว่างได้
    quantity = models.DecimalField(max_digits=10, decimal_places=4, blank = True, null = True)
    machine = models.CharField(max_length=255,blank=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    desired_date = models.DateField(blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    urgency = models.IntegerField(blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    requisit = models.ForeignKey(Requisition, on_delete=models.CASCADE, null=True, blank=True)
    quantity_pr = models.DecimalField(max_digits=10, decimal_places=4, blank = True, null = True)
    quantity_take = models.DecimalField(max_digits=10, decimal_places=4, blank = True, null = True)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=4, blank = True, null = True, default = 0.0)#จำนวนสินค้าที่ดึงไปทำแล้ว
    is_used = models.BooleanField(default=False)#สถานะที่บอกว่านำไปใช้ใน pr หรือ cm หรือยัง
    is_receive = models.BooleanField(default=False) #สถานะว่ารับเข้าไปแล้ว

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
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    organizer = models.ForeignKey(User,on_delete=models.CASCADE, related_name='organizer_user', null = True, blank = True)#เจ้าหน้าที่จัดซื้อที่เป็นผู้จัดทำ
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    is_complete = models.BooleanField(default=False) #ทำรายการขอซื้อหมดแล้ว

    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = purchaseRequisition_ref_number(self.branch_company)
        super(PurchaseRequisition, self).save(*args, **kwargs)

    class Meta:
        db_table = 'PurchaseRequisition'
        ordering=('-id',)

#ตำแหน่งงาน
class Position(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อตำแหน่งงาน")

    class Meta:
        db_table = 'Position'
        ordering=('id',)
        verbose_name = 'ตำแหน่งงาน'
        verbose_name_plural = 'ข้อมูลตำแหน่งงาน'
    
    def __str__(self):
        return str(self.name)

class BasePermission(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อสิทธิการทำงาน")
    codename = models.CharField(max_length=255,unique=True, verbose_name="โค้ด")
    codename_th = models.CharField(max_length=255,unique=True, verbose_name="โค้ดไทย")
    ap_amount_min = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True, verbose_name="ยอดเงินที่อนุมัติใบเปรียบเทียบน้อยสุด")#ยอดเงินอนุมัติใบเปรียบเทียบน้อยสุด
    ap_amount_max = models.DecimalField(max_digits=20, decimal_places=2, blank = True, null = True, verbose_name="ยอดเงินที่อนุมัติใบเปรียบเทียบมากสุด")#ยอดเงินอนุมัติใบเปรียบเทียบมากสุด

    class Meta:
        db_table = 'BasePermission'
        ordering=('id',)
        verbose_name = 'สิทธิการทำงาน'
        verbose_name_plural = 'ข้อมูลสิทธิการทำงาน'

    def __str__(self):
        return str(self.codename_th)

class BaseSparesType(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชนิดอะไหล่")

    class Meta:
        db_table = 'BaseSparesType'
        ordering=('id',)
        verbose_name = 'ชนิดอะไหล่'
        verbose_name_plural = 'ข้อมูลชนิดอะไหล่'
    
    def __str__(self):
        return str(self.name)


class PositionBasePermission(models.Model):
    position = models.ForeignKey(Position, on_delete = models.CASCADE, verbose_name="ตำแหน่งงาน")
    base_permission = models.ManyToManyField(BasePermission, verbose_name="สิทธิการทำงาน")
    branch_company = models.ManyToManyField(BaseBranchCompany,verbose_name="สิทธิการอนุมัติตามบริษัท")
    class Meta:
        db_table = 'PositionBasePermission'
        ordering=('id',)
        verbose_name = 'ตำแหน่งงานและสิทธิการทำงาน'
        verbose_name_plural = 'ข้อมูลตำแหน่งงานและสิทธิการทำงาน'

    def __str__(self):
        return str(self.position.name)

class BaseVisible(models.Model):       
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อแท็บการใช้งาน")

    class Meta:
        db_table = 'BaseVisible'
        ordering=('id',)
        verbose_name = 'แท็บการใช้งาน'
        verbose_name_plural = 'ข้อมูลแท็บการใช้งาน'
    
    def __str__(self):
        return str(self.name)

#USER PROFILE
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True, verbose_name="ผู้ใช้")
    position = models.ForeignKey(Position,on_delete=models.CASCADE,null=True, blank=True, verbose_name="ตำแหน่งงาน")
    department = models.ForeignKey(BaseDepartment,on_delete=models.CASCADE,null=True, blank=True, verbose_name="แผนก")
    signature = models.ImageField(null=True, blank=True, upload_to = "signature/",verbose_name="ลายเซ็น")
    visible = models.ManyToManyField(BaseVisible,verbose_name="การมองเห็นแท็ปการใช้งาน")
    branch_company = models.ManyToManyField(BaseBranchCompany,verbose_name="การมองเห็นแท็ปบริษัท")

    class Meta:
        verbose_name = 'ผู้ใช้และตำแหน่งงาน'
        verbose_name_plural = 'ข้อมูลผู้ใช้และตำแหน่งงาน'
        
    @property
    def signature_preview(self):
        if self.signature:
            return mark_safe('<img src="{}" height="100" />'.format(self.signature.url))
        return ""

    def __str__(self):
        return self.user.username

class BaseDistributorType(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสชนิดของผู้จัดจำหน่าย")
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อชนิดของผู้จัดจำหน่าย")

    class Meta:
        db_table = 'BaseDistributorType'
        ordering=('id',)
        verbose_name = 'ชนิดของผู้จัดจำหน่าย'
        verbose_name_plural = 'ข้อมูลชนิดของผู้จัดจำหน่าย'

    def __str__(self):
        return self.name

class BaseDistributorGenre(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสประเภทของผู้จัดจำหน่าย")#เก็บไอดีประเภทผู้จัดจำหน่าย
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อประเภทของผู้จัดจำหน่าย")

    class Meta:
        db_table = 'BaseDistributorGenre'
        ordering=('id',)
        verbose_name = 'ประเภทของผู้จัดจำหน่าย'
        verbose_name_plural = 'ข้อมูลประเภทของผู้จัดจำหน่าย'

    def __str__(self):
        return self.name

class BasePrefix(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสคำนำหน้านาม")#เก็บไอดีคำนำหน้า
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อคำนำหน้านาม")

    class Meta:
        db_table = 'BasePrefix'
        ordering=('id',)
        verbose_name = 'คำนำหน้านาม'
        verbose_name_plural = 'ข้อมูลคำนำหน้านาม'

    def __str__(self):
        return self.name

class BaseVatType(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสชนิดภาษี")#เก็บไอดีชนิดภาษี
    name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อชนิดภาษี")

    class Meta:
        db_table = 'BaseVatType'
        ordering=('id',)
        verbose_name = 'ชนิดภาษี'
        verbose_name_plural = 'ข้อมูลชนิดภาษี'

    def __str__(self):
        return str(self.name)

class Distributor(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสผู้จัดจำหน่าย")#เก็บไอดีสินค้าใน express
    prefix = models.ForeignKey(BasePrefix, on_delete=models.CASCADE, blank = True, null = True, verbose_name="คำนำหน้า")
    name =  models.CharField(max_length=255, blank = True, null = True, verbose_name="ชื่อผู้จัดจำหน่าย")
    type = models.ForeignKey(BaseDistributorType, on_delete=models.CASCADE, blank = True, null = True, verbose_name="ชนิดของผู้จัดจำหน่าย")
    genre = models.ForeignKey(BaseDistributorGenre, on_delete=models.CASCADE, blank = True, null = True, verbose_name="ประเภทของผู้จัดจำหน่าย")
    credit = models.ForeignKey(BaseCredit, on_delete=models.CASCADE, blank = True, null = True, verbose_name="เครดิต")
    vat_type = models.ForeignKey(BaseVatType, on_delete=models.CASCADE, blank = True, null = True, verbose_name="ชนิดภาษี")
    discount = models.CharField(max_length=255, blank = True, null = True, verbose_name="ส่วนลด")
    credit_limit = models.CharField(max_length=255, blank = True, null = True, verbose_name="ยอดวงเงิน")
    account_number = models.CharField(max_length=255, blank = True, null = True, verbose_name="เลขบัญชี")
    address = models.TextField(blank=True, null = True, verbose_name="ที่อยู่")
    tel = models.CharField(max_length=255, blank = True, null = True, verbose_name="เบอร์โทร+เบอร์แฟกส์")
    payment = models.CharField(max_length=255, blank = True, null = True, verbose_name="เงื่อนไขการชำระเงิน")
    contact = models.CharField(max_length=255, blank = True, null = True, verbose_name="ผู้ติดต่อ")
    affiliated = models.ForeignKey(BaseAffiliatedCompany, on_delete=models.CASCADE, blank = True, null = True, verbose_name="สังกัดบริษัท")
    tex = models.CharField(max_length=255, blank = True, null = True, verbose_name="เลขประจำตัวผู้เสียภาษี")#เลขประจำตัวผู้เสียภาษี
    fax =  models.CharField(max_length=255, blank = True, null = True, verbose_name="แฟกส์")
    registration_pdf = models.FileField(null=True, blank=True, upload_to='pdfs/registration/distributor/%Y/%m/%d', verbose_name="หนังสือรับรองบริษัท")

    class Meta:
        db_table = 'Distributor'
        ordering=('id',)
        verbose_name = 'ผู้จัดจำหน่าย'
        verbose_name_plural = 'ข้อมูลผู้จัดจำหน่าย'

    def __str__(self):
        return self.name


class BaseDelivery(models.Model):
    name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อสถานที่จัดส่ง")

    class Meta:
        db_table = 'BaseDelivery'
        ordering=('id',)
        verbose_name = 'สถานที่จัดส่ง'
        verbose_name_plural = 'ข้อมูลสถานที่จัดส่ง'

    def __str__(self):
        return str(self.name)

class BaseCMType(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสประเภทใบเปรียบเทียบเทียบราคา")#เก็บไอดีชนิดภาษี
    name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อประเภทใบเปรียบเทียบเทียบราคา")
    codename = models.CharField(max_length=255, verbose_name="โค้ด", blank=True, null=True)

    class Meta:
        db_table = 'BaseCMType'
        ordering=('id',)
        verbose_name = 'ประเภทใบเปรียบเทียบเทียบราคา'
        verbose_name_plural = 'ข้อมูลประเภทใบเปรียบเทียบเทียบราคา'

    def __str__(self):
        return str(self.name)

class ComparisonPrice(models.Model):
    organizer = models.ForeignKey(User,on_delete=models.CASCADE)
    base_spares_type = models.ForeignKey(BaseSparesType,on_delete=models.CASCADE, null=True, blank=True)
    select_bidder = models.ForeignKey(Distributor,on_delete=models.CASCADE, null=True) #ร้านที่เลือก
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
    special_approver_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cp_special_approver_user',
        null=True,
        blank=True
    )
    special_approver_status = models.ForeignKey(
        BaseApproveStatus,
        on_delete=models.CASCADE,
        related_name='cp_special_approver_status',
        null=True
    )
    special_approver_update = models.DateField(blank=True, null=True)
    is_special_approve_cm = models.BooleanField(default=False)
    select_bidder_update = models.DateField(blank=True, null=True)
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    po_ref_no = models.CharField(max_length=255, blank = True)
    cm_type = models.ForeignKey(BaseCMType,on_delete=models.CASCADE, null=True, blank=True)
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    is_re_approve = models.BooleanField(default=False)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    amount_diff = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ราคาที่เทียบกันระหว่างร้านที่ 1 และ 2

    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = comparisonPrice_ref_number(self.branch_company)
            
        super(ComparisonPrice, self).save(*args, **kwargs)

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
    discount = models.CharField(max_length=255, blank = True, null = True)#หักส่วนลด
    total_after_discount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินหลังหักส่วนลด
    vat = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ภาษี
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    note = models.CharField(max_length=255, blank = True)
    freight = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ค่าขนส่ง
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
        null=True,
        blank=True
    )
    approver_status = models.ForeignKey(
        BaseApproveStatus,
        on_delete=models.CASCADE,
        related_name='approver_status_po',
        null=True
    )
    approver_update = models.DateField(blank=True, null=True)
    created = models.DateField(default=timezone.now) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    cp = models.ForeignKey(ComparisonPrice,on_delete=models.CASCADE,null = True, blank = True)
    pr = models.ForeignKey(PurchaseRequisition,on_delete=models.CASCADE,null = True, blank = True)
    ref_no = models.CharField(max_length = 255, null = True, blank = True,unique=True)
    quotation_pdf = models.FileField(null=True, blank=True, upload_to='pdfs/quotation/PO/%Y/%m/%d')
    delivery = models.ForeignKey(BaseDelivery,on_delete=models.CASCADE,null = True, blank = True)
    is_receive = models.BooleanField(default=False) #สถานะว่ารับเข้าไปแล้ว
    receive_update = models.DateField(blank=True, null=True) #วันที่รับสินค้า
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    receipt_pdf = models.FileField(null=True, blank=True, upload_to='pdfs/receipt/RC_PO/%Y/%m/%d')
    is_re_approve = models.BooleanField(default=False)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    cancel_reason = models.CharField(max_length=255, blank = True, null = True)
    is_cancel = models.BooleanField(default=False)
    due_receive_update = models.DateField(blank=True, null=True) #วันที่กำหนดรับของ

    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = purchaseOrder_ref_number(self.branch_company)
            
        super(PurchaseOrder, self).save(*args, **kwargs)

    class Meta:
        db_table = 'PurchaseOrder'
        ordering=('-id',)
    
    def __str__(self):
        return str(self.ref_no)

class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(RequisitionItem,on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=4, blank = True, null = True)
    unit = models.ForeignKey(BaseUnit,on_delete=models.CASCADE, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    is_receive = models.BooleanField(default=False) #สถานะว่ารับเข้าไปแล้ว
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'PurchaseOrderItem'
        ordering=('id',)

class ComparisonPriceDistributor(models.Model):
    distributor = models.ForeignKey(Distributor,on_delete=models.CASCADE, null = True)
    credit = models.ForeignKey(BaseCredit,on_delete=models.CASCADE,null = True, blank = True)
    vat_type = models.ForeignKey(BaseVatType,on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#รวมเป็นเงิน
    discount = models.CharField(max_length=255, blank = True, null = True)#หักส่วนลด
    total_after_discount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินหลังหักส่วนลด
    vat = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ภาษี
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    freight = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ค่าขนส่ง
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    cp =  models.ForeignKey(ComparisonPrice,on_delete=models.CASCADE, null=True)
    quotation_pdf = models.FileField(null=True, blank=True, upload_to='pdfs/quotation/CM/%Y/%m/%d')
    is_select = models.BooleanField(default=False)

    class Meta:
        db_table = 'ComparisonPriceDistributor'
        ordering=('id',)

class ComparisonPriceItem(models.Model):
    item = models.ForeignKey(RequisitionItem,on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=4, blank = True, null = True)
    unit = models.ForeignKey(BaseUnit,on_delete=models.CASCADE, null=True)
    brand = models.CharField(max_length=255, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    bidder =  models.ForeignKey(ComparisonPriceDistributor,on_delete=models.CASCADE, null=True)
    cp =  models.IntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'ComparisonPriceItem'
        ordering=('id',)

class Receive(models.Model):
    po = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,null = True,blank = True)
    tax_invoice =  models.CharField(max_length=255, blank = True, null = True)#เลขที่บิล
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#รวมเป็นเงิน
    discount = models.CharField(max_length=255, blank = True, null = True)#หักส่วนลด
    total_after_discount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินหลังหักส่วนลด
    vat_type = models.ForeignKey(BaseVatType,on_delete=models.CASCADE)
    vat = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ภาษี
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    freight = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)#ค่าขนส่ง
    note = models.CharField(max_length=255, blank = True)
    receive_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='receive_user',
        null=True
    )
    receive_update = models.DateField(auto_now_add=True)
    created = models.DateField(max_length=255, blank = True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    ref_no = models.CharField(max_length = 255, default = receive_ref_number, null = True, blank = True)
    pay = models.CharField(max_length=255, blank = True)
    due_date = models.DateField(null = True, blank = True)
    distributor = models.ForeignKey(Distributor,on_delete=models.CASCADE, null = True)
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'Receive'
        ordering=('-id',)

class ReceiveItem(models.Model):
    item = models.ForeignKey(PurchaseOrderItem,on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(null=True, blank=True)
    unit = models.ForeignKey(BaseUnit,on_delete=models.CASCADE, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank = True, null = True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    rc =  models.ForeignKey(Receive,on_delete=models.CASCADE,null = True,blank = True)

    class Meta:
        db_table = 'ReceiveItem'
        ordering=('id',)

class Document(models.Model):
    doc_pdf = models.FileField(null=True, blank=True, upload_to='pdfs/document/')
    
    class Meta:
        db_table = 'Document'
        ordering=('id',)
    
    def filename(self):
        return os.path.basename(self.doc_pdf.name)

class RateDistributor(models.Model):
    distributor = models.ForeignKey(Distributor,on_delete=models.CASCADE, null = True)
    price_rate = models.IntegerField(null=True, blank=True)#ราคา
    quantity_rate = models.IntegerField(null=True, blank=True)#คุณภาพงาน
    duration_rate = models.IntegerField(null=True, blank=True)#ระยะเวลา
    service_rate = models.IntegerField(null=True, blank=True)#การบริการ
    safety_rate = models.IntegerField(null=True, blank=True)#การจัดการสิ่งแวดล้อม/ความปลอดภัย
    total_rate = models.IntegerField(null=True, blank=True)#รวมคะแนน
    grade = models.ForeignKey(BaseGrade,on_delete=models.CASCADE, null = True)#เกรด
    counsel = models.TextField(blank=True, null = True)
    organizer_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rate_organizer_user',
        null=True
    )#ผู้ประเมิน
    organizer_update = models.DateField(auto_now=True)#วันที่ประเมิน
    po = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,null = True,blank = True)#ผูกกับใบสั่งซื้อ

    class Meta:
        db_table = 'RateDistributor'
        ordering=('id',)
