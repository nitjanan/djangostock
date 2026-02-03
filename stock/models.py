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
from datetime import date, timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.template.defaultfilters import truncatechars
import pytz
import os
from stock.formatChecker import ContentTypeRestrictedFileField
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw, ImageOps
import segno
from django.db.models import Sum

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

def invoice_ref_number(branch_company):
    today = datetime.datetime.now()
    year = str(int(today.strftime('%Y')) + 543)[2:4]
    month = str(today.strftime('%m'))
    YM = year + month

    bbc = BaseBranchCompany.objects.get(code = branch_company)
    if bbc.invoice_code:
        format = bbc.invoice_code + YM

        try:
            last_no = Invoice.objects.all().filter(ref_no__contains=format, branch_company__code = branch_company).order_by('id').last()
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
    else:
        new_no = None
    return new_no

def maintenance_ref_number(branch_company):
    #tz = pytz.timezone('Asia/Bangkok')
    today = datetime.datetime.now()
    year = str(int(today.strftime('%Y')) + 543)[2:4]
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'M'+ str(branch_company) + YM

    try:
        last_no = Maintenance.objects.all().filter(ref_no__contains=format).order_by('id').last()
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

def carLogbook_ref_number(branch_company):
    #tz = pytz.timezone('Asia/Bangkok')
    today = datetime.datetime.now()
    year = str(int(today.strftime('%Y')) + 543)[2:4]
    month = str(today.strftime('%m'))
    YM = year + month
    format = 'L'+ str(branch_company) + YM

    try:
        last_no = CarLogbook.objects.all().filter(ref_no__contains=format).order_by('id').last()
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

class BaseExpenses(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสค่าใช้จ่าย")#เก็บไอดีค่าใช้จ่าย
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อค่าใช้จ่าย")

    class Meta:
        db_table = 'BaseExpenses'
        ordering=('id',)
        verbose_name = 'ค่าใช้จ่าย'
        verbose_name_plural = 'ข้อมูลค่าใช้จ่าย'
    
    def __str__(self):
        return str(self.name)

class BaseRequisitionType(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อประเภทใบขอเบิก")
    iso_code = models.CharField(max_length=255, blank=True, null = True, verbose_name="iso code")

    class Meta:
        db_table = 'BaseRequisitionType'
        ordering=('id',)
        verbose_name = 'ประเภทใบขอเบิก'
        verbose_name_plural = 'ข้อมูลประเภทใบขอเบิก'

    def __str__(self):
        return str(self.name)

class BaseAgency(models.Model):
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'BaseAgency'
        ordering=('id',)
        verbose_name = 'หน่วยงาน'
        verbose_name_plural = 'ข้อมูลหน่วยงาน'

    def __str__(self):
        return str(self.name)

class BaseExpenseDepartment(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสแผนกค่าใช้จ่าย")#แผนกค่าใช้จ่าย
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อแผนกค่าใช้จ่าย")
    agency = models.ForeignKey(BaseAgency, on_delete=models.CASCADE, blank=True, null=True) #หน่วยงาน

    class Meta:
        db_table = 'BaseExpenseDepartment'
        ordering=('id',)
        verbose_name = 'แผนกค่าใช้จ่าย'
        verbose_name_plural = 'ข้อมูลแผนกค่าใช้จ่าย'
    
    def __str__(self):
        return str(self.name)
    
class BaseRepairType(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสประเภทการซ่อม")#เก็บประเภทการซ่อม
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อประเภทการซ่อม")
    rq_type = models.ForeignKey(BaseRequisitionType, on_delete=models.CASCADE, blank=True, null=True, verbose_name="ประเภทใบขอเบิก") #ประเภทใบขอเบิก

    class Meta:
        db_table = 'BaseRepairType'
        ordering=('id',)
        verbose_name = 'ประเภทการซ่อม'
        verbose_name_plural = 'ข้อมูลประเภทการซ่อม'
    
    def __str__(self):
        return str(self.name)
    
class BaseBrokeType(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อเหตุผล/สาเหตุที่ต้องซ่อม")
    rq_type = models.ForeignKey(BaseRequisitionType, on_delete=models.CASCADE, blank=True, null=True, verbose_name="ประเภทใบขอเบิก") #ประเภทใบขอเบิก

    class Meta:
        db_table = 'BaseBrokeType'
        ordering=('id',)
        verbose_name = 'เหตุผล/สาเหตุที่ต้องซ่อม'
        verbose_name_plural = 'ข้อมูลเหตุผล/สาเหตุที่ต้องซ่อม'
    
    def __str__(self):
        return str(self.name)
    
class BaseCarDepartment(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อแผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน")

    class Meta:
        db_table = 'BaseCarDepartment'
        ordering=('id',)
        verbose_name = 'แผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน'
        verbose_name_plural = 'ข้อมูลแผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน'

    def __str__(self):
        return self.name
    
class BaseCar(models.Model):
    code = models.CharField(unique=True, max_length=255, blank=False, null=True, verbose_name="code")
    name = models.CharField(max_length=255, blank=False, null=True, verbose_name="ชื่อทะเบียนรถ/เครื่องจักร/หน่วยงาน")
    rq_type = models.ForeignKey(BaseRequisitionType, on_delete=models.CASCADE, blank=True, null=True, verbose_name="ประเภทใบขอเบิก") #ประเภทใบขอเบิก
    car_dep = models.ForeignKey(BaseCarDepartment,on_delete=models.CASCADE,null=True, blank=True, verbose_name="แผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน")
    pm_round = models.IntegerField(blank=True, null=True, verbose_name="รอบทำ PM ทุก ๆ (กิโลเมตร หรือ ชั่วโมง)")

    class Meta:
        db_table = 'BaseCar'
        ordering=('id',)
        verbose_name = 'ทะเบียนรถ/เครื่องจักร/หน่วยงาน'
        verbose_name_plural = 'ข้อมูลทะเบียนรถ/เครื่องจักร/หน่วยงาน'
        unique_together = 'name', 'code'
    
    def __str__(self):
        return str(self.name) + str(self.code)

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
    invoice_code = models.CharField(max_length=255, verbose_name="โค้ดจ่ายสินค้าภายใน - อะไหล่", blank = True, null = True)
    oi_invoice_code = models.CharField(max_length=255, verbose_name="โค้ดจ่ายสินค้าภายใน - น้ำมัน", blank = True, null = True)
    soc_code = models.CharField(max_length=255, verbose_name="โค้ดขายเชื่อบุคคลภายนอก - อะไหล่", blank = True, null = True)
    oi_soc_code = models.CharField(max_length=255, verbose_name="โค้ดขายเชื่อบุคคลภายนอก - น้ำมัน", blank = True, null = True)

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

    
class BaseJobCarDep(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="รายละเอียดงาน")
    car_dep = models.ForeignKey(BaseCarDepartment,on_delete=models.CASCADE,null=True, blank=True, verbose_name="แผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน")
    expense_dept = models.ManyToManyField(
        BaseExpenseDepartment,
        blank=True,
        verbose_name="แผนกค่าใช้จ่าย",
        limit_choices_to={'agency__id': 1}  # ✅ only allow agency.id = 1
    )#แผนกค่าใช้จ่ายมีมากกว่า 1

    class Meta:
        db_table = 'BaseJobCarDep'
        ordering=('id',)
        verbose_name = 'รายละเอียดงานและแผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน'
        verbose_name_plural = 'ข้อมูลรายละเอียดงานและแผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน'

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
    price = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank = True, verbose_name="ราคา") #ราคา Product มีเลข 12 หลัก ทศนิยม 2 ตำแหน่ง
    category = models.ForeignKey(Category,on_delete=models.CASCADE, null=True, blank = True, verbose_name="หมวดหมู่สินค้า") #ดึงข้อมูล Category มาใช้ใน Product และ on_delete = models.CASCADE คือหากลบอันใดอันนึงให้ลบทั้งหมดเลย
    image = models.ImageField(upload_to="product",blank=True, verbose_name="รูปภาพ") #เก็บรูปภาพ
    stock = models.IntegerField(null=True, blank = True, verbose_name="จำนวนสินค้าในสต็อก") #จำนวนชิ้นของ Product
    available = models.BooleanField(default=True, verbose_name="ใช้งานอยู่") #Product ใช้งานได้ไหม
    created = models.DateField(auto_now_add=True, verbose_name="วันที่สร้าง") #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True, verbose_name="วันที่อัพเดท") #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    affiliated = models.ForeignKey(BaseAffiliatedCompany, on_delete=models.CASCADE, blank = True, null = True, verbose_name="สังกัดบริษัท")
    qr_code = models.ImageField(null=True, blank=True, upload_to = "pd_qr_codes/", verbose_name="qr code")

    def save(self, *args, **kwargs):

        # สินค้า QR Code 27-05-2025
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=5,
                border=1,  # Set border size to 2
            )
            qr.add_data(self.id)
            qr.make(fit=True)
            qrcode_img = qr.make_image(fill_color="black", back_color="white")

            # Crop the QR code image to remove the border
            image_data = qrcode_img.get_image()
            image_data = image_data.crop((2, 2, image_data.size[0] - 2, image_data.size[1] - 2))

            # Create a new image and paste the cropped QR code onto it
            canvas = Image.new('RGB', (image_data.size[0], image_data.size[1]), 'white')
            canvas.paste(image_data)

            # Save the QR code image
            fname = f'qr_code_{self.id}.png'
            buffer = BytesIO()
            canvas.save(buffer, 'PNG')
            self.qr_code.save(fname, File(buffer), save=False)
            canvas.close()

        super(Product, self).save(*args, **kwargs)
     
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
    purchase_requisition_id =  models.IntegerField(blank=True, null=True,unique=True)#อ้างอิง id pr
    pr_ref_no = models.CharField(max_length = 255, null = True, blank = True)#อ้างอิง เลขที่ pr
    invoice_id = models.IntegerField(blank=True, null=True,unique=True)#อ้างอิง id iv
    iv_ref_no = models.CharField(max_length = 255, null = True, blank = True)#อ้างอิง เลขที่ iv
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
    urgency = models.ForeignKey(BaseUrgency, on_delete=models.CASCADE, blank=True, null=True)#ระดับความเร่งด่วน
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    is_edit = models.BooleanField(default=True)#ยังแก้ไขได้ กรณีที่ยังไม่ได้อนุมัติใบขอซื้อหรือใบจ่ายสินค้าภายใน
    memorandum_pdf = ContentTypeRestrictedFileField(upload_to='pdfs/memorandum/%Y/%m/%d', content_types=['application/msword', 'text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/gif','image/vnd.microsoft.icon','image/jpeg','image/png','application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.rar','text/plain','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip','application/x-7z-compressed','application/x-zip-compressed'], max_upload_size=5242880 ,blank=True, null=True)
    organizer = models.ForeignKey(User,on_delete=models.CASCADE, related_name='organizer', blank=True, null=True)#เจ้าหน้าที่จัดซื้อที่เป็นผู้จัดทำ
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    repair_type = models.ForeignKey(BaseRepairType, on_delete=models.CASCADE, blank=True, null=True)#ประเภทการซ่อม
    broke_type = models.ForeignKey(BaseBrokeType, on_delete=models.CASCADE, blank=True, null=True) #เหตุผล/สาเหตุ
    rq_type = models.ForeignKey(BaseRequisitionType, on_delete=models.CASCADE, blank=True, null=True) #ประเภทใบขอเบิก
    car = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True) #ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน
    expense_dept = models.ForeignKey(BaseExpenseDepartment, on_delete=models.CASCADE, blank=True, null=True) #แผนกค่าใช้จ่าย
    desired_date = models.DateField(blank=True, null=True) #วันที่ต้องการ
    expenses = models.ManyToManyField(BaseExpenses, blank=True, null=True, verbose_name="ค่าใช้จ่าย")#ค่าใช้จ่าย checkbox
    note = models.TextField(blank=True, null = True, verbose_name="หมายเหตุ/เหตุผล")
    agency = models.ForeignKey(BaseAgency, on_delete=models.CASCADE, blank=True, null=True) #หน่วยงาน
    mile = models.CharField(max_length = 255, null = True, blank = True, verbose_name="เลขไมล์/เลขชั่วโมง")
    qr_code = models.ImageField(null=True, blank=True, upload_to = "r_qr_codes/", verbose_name="qr code")
    ma_id = models.IntegerField(blank=True, null=True)#อ้างอิง id Maintenance
    ma_ref_no = models.CharField(max_length=255, null = True, blank = True) #อ้างอิง ref_no Maintenance

    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = requisition_ref_number(self.branch_company)

        # ใบขอเบิก QR Code 10-02-2025
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=5,
                border=1,  # Set border size to 2
            )
            qr.add_data(self.ref_no)
            qr.make(fit=True)
            qrcode_img = qr.make_image(fill_color="black", back_color="white")

            # Crop the QR code image to remove the border
            image_data = qrcode_img.get_image()
            image_data = image_data.crop((2, 2, image_data.size[0] - 2, image_data.size[1] - 2))

            # Create a new image and paste the cropped QR code onto it
            canvas = Image.new('RGB', (image_data.size[0], image_data.size[1]), 'white')
            canvas.paste(image_data)

            # Save the QR code image
            fname = f'qr_code-{self.ref_no}.png'
            buffer = BytesIO()
            canvas.save(buffer, 'PNG')
            self.qr_code.save(fname, File(buffer), save=False)
            canvas.close()

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
    quantity = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)#จำนวนที่ขอเบิก
    machine = models.CharField(max_length=255,blank=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    desired_date = models.DateField(blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    urgency = models.IntegerField(blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    requisit = models.ForeignKey(Requisition, on_delete=models.CASCADE, null=True, blank=True)#จำนวนที่ออกใบขอซื้อ
    quantity_pr = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)#จำนวนที่จ่ายไป
    quantity_take = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)#จำนวนที่ซื้อแล้ว
    quantity_used = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True, default = 0.0)#จำนวนสินค้าที่ดึงไปทำแล้ว
    is_used = models.BooleanField(default=False)#สถานะที่บอกว่านำไปใช้ใน pr หรือ cm หรือยัง
    is_receive = models.BooleanField(default=False) #สถานะว่ารับเข้าไปแล้ว

    class Meta:
        db_table = 'RequisitionItem'
        ordering=('id',)
    
    def __str__(self):
        return str(self.product)

class Invoice(models.Model):
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    bring_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bring_name',
        verbose_name='ผู้เบิก'
    )
    payer_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payer_name',
        verbose_name='ผู้จ่าย'
    )
    car = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True, verbose_name="หมายเหตุ")#ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน จากใบขอเบิก
    note = models.CharField(max_length = 255, null = True, blank = True, verbose_name="หมายเหตุเพิ่มเติม")#หมายเหตุ จากใบขอเบิก
    expense_dept = models.ForeignKey(BaseExpenseDepartment, on_delete=models.CASCADE, blank=True, null=True, verbose_name="แผนกค่าใช้จ่าย") #แผนกค่าใช้จ่าย
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True) #บริษัท
    requisit = models.ForeignKey(Requisition, on_delete=models.CASCADE, null=True, blank=True) #เก็บเลขที่ใบขอเบิก
    total_price = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)
    v_stamp = models.DateTimeField(auto_now=True)
    is_express = models.BooleanField(default=False) #นำข้อมูลเข้า express แล้ว

    def save(self, *args, **kwargs):
        if self.ref_no is None:
            self.ref_no = invoice_ref_number(self.branch_company)
        super(Invoice, self).save(*args, **kwargs)

    class Meta:
        db_table = 'Invoice'
        ordering=('-id',)
        unique_together = 'ref_no', 'branch_company'

    def __str__(self):
        return str(self.id)

class InvoiceItem(models.Model):
    iv = models.ForeignKey(Invoice,on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(RequisitionItem,on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)
    price = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    v_stamp = models.DateTimeField(auto_now=True)
    is_express = models.BooleanField(default=False) #นำข้อมูลเข้า express แล้ว

    class Meta:
        db_table = 'InvoiceItem'
        ordering=('id',)

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
    stockman_update = models.DateTimeField(blank=True, null=True)
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
    purchase_update = models.DateTimeField(blank=True, null=True)
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
    approver_update = models.DateTimeField(blank=True, null=True)
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    note = models.TextField(blank=True, null = True, verbose_name="หมายเหตุ/เหตุผล")
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    organizer = models.ForeignKey(User,on_delete=models.CASCADE, related_name='organizer_user', null = True, blank = True)#เจ้าหน้าที่จัดซื้อที่เป็นผู้จัดทำ
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    is_complete = models.BooleanField(default=False) #ทำรายการขอซื้อหมดแล้ว
    is_re_approve = models.BooleanField(default=False)

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
    ap_amount_max = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True, verbose_name="ยอดเงินที่อนุมัติใบเปรียบเทียบมากสุด")#ยอดเงินอนุมัติใบเปรียบเทียบมากสุด

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
    
class BasePOType(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสประเภทใบสั่งซื้อ")#เก็บไอดีประเภทใบสั่งซื้อ
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อประเภทใบสั่งซื้อ")

    class Meta:
        db_table = 'BasePOType'
        ordering=('id',)
        verbose_name = 'ประเภทใบสั่งซื้อ'
        verbose_name_plural = 'ข้อมูลประเภทใบสั่งซื้อ'
    
    def __str__(self):
        return str(self.name)
    
class BaseMAType(models.Model):
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสประเภทใบแจ้งซ่อม")#เก็บไอดีประเภทใบสั่งซื้อ
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อประเภทใบแจ้งซ่อม")

    class Meta:
        db_table = 'BaseMAType'
        ordering=('id',)
        verbose_name = 'ประเภทใบแจ้งซ่อม'
        verbose_name_plural = 'ข้อมูลประเภทใบแจ้งซ่อม'
    
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
    registration_pdf = ContentTypeRestrictedFileField(upload_to='pdfs/registration/distributor/%Y/%m/%d', content_types=['application/msword', 'text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/gif','image/vnd.microsoft.icon','image/jpeg','image/png','application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.rar','text/plain','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip','application/x-7z-compressed','application/x-zip-compressed'], max_upload_size=5242880 ,blank=True, null=True, verbose_name="หนังสือรับรองบริษัท")
    created = models.DateField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง

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
    id = models.CharField(primary_key=True, max_length=255, unique=True, verbose_name="รหัสประเภทใบเปรียบเทียบเทียบราคา")#เก็บไอดีใบเปรียบเทียบเทียบราคา
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
    note = models.TextField(blank=True, null = True, verbose_name="หมายเหตุ/เหตุผล")
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
    approver_update = models.DateTimeField(blank=True, null=True)
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
    examiner_update = models.DateTimeField(blank=True, null=True)  
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
    special_approver_update = models.DateTimeField(blank=True, null=True)
    is_special_approve_cm = models.BooleanField(default=False)
    select_bidder_update = models.DateField(blank=True, null=True)
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    po_ref_no = models.CharField(max_length=255, blank = True)
    cm_type = models.ForeignKey(BaseCMType,on_delete=models.CASCADE, null=True, blank=True)
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    is_re_approve = models.BooleanField(default=False)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    amount_diff = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#ราคาที่เทียบกันระหว่างร้านที่ 1 และ 2

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
    total_price = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#รวมเป็นเงิน
    discount = models.CharField(max_length=255, blank = True, null = True)#หักส่วนลด
    total_after_discount = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#จำนวนเงินหลังหักส่วนลด
    vat = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#ภาษี
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    note = models.TextField(blank=True, null = True, verbose_name="หมายเหตุ")
    freight = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#ค่าขนส่ง
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
    approver_update = models.DateTimeField(blank=True, null=True)
    created = models.DateField(default=timezone.now) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    cp = models.ForeignKey(ComparisonPrice,on_delete=models.CASCADE,null = True, blank = True)
    pr = models.ForeignKey(PurchaseRequisition,on_delete=models.CASCADE,null = True, blank = True)
    ref_no = models.CharField(max_length = 255, null = True, blank = True,unique=True)
    quotation_pdf = ContentTypeRestrictedFileField(upload_to='pdfs/quotation/PO/%Y/%m/%d', content_types=['application/msword', 'text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/gif','image/vnd.microsoft.icon','image/jpeg','image/png','application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.rar','text/plain','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip','application/x-7z-compressed','application/x-zip-compressed'], max_upload_size=5242880 ,blank=True, null=True)
    delivery = models.ForeignKey(BaseDelivery,on_delete=models.CASCADE,null = True, blank = True)
    is_receive = models.BooleanField(default=False) #สถานะว่ารับเข้าไปแล้ว
    receive_update = models.DateField(blank=True, null=True) #วันที่รับสินค้า
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    receipt_pdf = ContentTypeRestrictedFileField(upload_to='pdfs/receipt/RC_PO/%Y/%m/%d', content_types=['application/msword', 'text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/gif','image/vnd.microsoft.icon','image/jpeg','image/png','application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.rar','text/plain','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip','application/x-7z-compressed','application/x-zip-compressed'], max_upload_size=5242880 ,blank=True, null=True)
    is_re_approve = models.BooleanField(default=False)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    cancel_reason = models.CharField(max_length=255, blank = True, null = True)
    is_cancel = models.BooleanField(default=False)
    due_receive_update = models.DateField(blank=True, null=True) #วันที่กำหนดรับของ
    qr_code = models.ImageField(null=True, blank=True, upload_to = "qr_codes/",verbose_name="qr code")
    po_type = models.ForeignKey(BasePOType, on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = purchaseOrder_ref_number(self.branch_company)

        # QR Code 17-05-2024
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,  # Set border size to 2
            )
            qr.add_data(self.ref_no)
            qr.make(fit=True)
            qrcode_img = qr.make_image(fill_color="black", back_color="white")

            # Crop the QR code image to remove the border
            image_data = qrcode_img.get_image()
            image_data = image_data.crop((2, 2, image_data.size[0] - 2, image_data.size[1] - 2))

            # Create a new image and paste the cropped QR code onto it
            canvas = Image.new('RGB', (image_data.size[0], image_data.size[1]), 'white')
            canvas.paste(image_data)

            # Save the QR code image
            fname = f'qr_code-{self.ref_no}.png'
            buffer = BytesIO()
            canvas.save(buffer, 'PNG')
            self.qr_code.save(fname, File(buffer), save=False)
            canvas.close()

        super(PurchaseOrder, self).save(*args, **kwargs)


    class Meta:
        db_table = 'PurchaseOrder'
        ordering=('-id',)
    
    def __str__(self):
        return str(self.ref_no)

class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(RequisitionItem,on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)
    unit = models.ForeignKey(BaseUnit,on_delete=models.CASCADE, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)
    discount = models.CharField(max_length=255, blank = True, null = True)#ส่วนลด ทศนิยม and %
    price = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)
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
    total_price = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#รวมเป็นเงิน
    discount = models.CharField(max_length=255, blank = True, null = True)#หักส่วนลด
    total_after_discount = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#จำนวนเงินหลังหักส่วนลด
    vat = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#ภาษี
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    freight = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#ค่าขนส่ง
    created = models.DateField(auto_now_add=True) #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    cp =  models.ForeignKey(ComparisonPrice,on_delete=models.CASCADE, null=True)
    quotation_pdf = ContentTypeRestrictedFileField(upload_to='pdfs/quotation/CM/%Y/%m/%d', content_types=['application/msword', 'text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/gif','image/vnd.microsoft.icon','image/jpeg','image/png','application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.rar','text/plain','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip','application/x-7z-compressed','application/x-zip-compressed'], max_upload_size=5242880 ,blank=True, null=True)
    is_select = models.BooleanField(default=False)

    class Meta:
        db_table = 'ComparisonPriceDistributor'
        ordering=('id',)

class ComparisonPriceItem(models.Model):
    item = models.ForeignKey(RequisitionItem,on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)
    unit = models.ForeignKey(BaseUnit,on_delete=models.CASCADE, null=True)
    brand = models.CharField(max_length=255, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4, blank = True, null = True)
    discount = models.CharField(max_length=255, blank = True, null = True)#ส่วนลด ทศนิยม and %
    price = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)
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
    note = models.CharField(max_length=255, null = True, blank = True)
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
    doc_pdf = ContentTypeRestrictedFileField(upload_to='pdfs/document/', content_types=['application/msword', 'text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/gif','image/vnd.microsoft.icon','image/jpeg','image/png','application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.rar','text/plain','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip','application/x-7z-compressed','application/x-zip-compressed'], max_upload_size=5242880 ,blank=True, null=True)
    
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

###############################################################################
############################## Express DB #####################################
###############################################################################

############################ ใบจ่ายภายใน อะไหล่, น้ำมัน ###########################
class ExOESTNH(models.Model):
    recordid = models.AutoField(primary_key=True)
    docnum = models.CharField(max_length=12, blank=True, null=True)
    docdat = models.DateField(blank=True, null=True)
    posopr = models.CharField(max_length=1, blank=True, null=True)
    depcod = models.CharField(max_length=2, blank=True, null=True)
    loccod = models.CharField(max_length=4, blank=True, null=True)
    refnum = models.CharField(max_length=12, blank=True, null=True)
    comcod = models.CharField(max_length=10, blank=True, null=True)
    remark = models.CharField(max_length=120, blank=True, null=True)
    note1 = models.CharField(max_length=120, blank=True, null=True)
    note2 = models.CharField(max_length=120, blank=True, null=True)
    note3 = models.CharField(max_length=120, blank=True, null=True)
    audtuser = models.CharField(max_length=120, blank=True, null=True)
    audttime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'OESTNH'
        managed = False
        indexes = [
            models.Index(fields=['docnum', 'comcod'], name='OESTNH_ID1'),
            models.Index(fields=['docdat', 'comcod'], name='OESTNH_ID2'),
            models.Index(fields=['docdat', 'posopr', 'comcod'], name='OESTNH_ID3'),
            models.Index(fields=['comcod', 'refnum'], name='OESTNH_ID4'),
            models.Index(fields=['docnum', 'remark'], name='OESTNH_ID5'),
            models.Index(fields=['docnum', 'comcod', 'note1', 'note2', 'note3'], name='OESTNH_ID6'),
        ]

    def get_items(self):
        list_stkcod = list(ExOESTND.objects.using('pg_db').filter(docnum=self.docnum, comcod=self.comcod).values_list('stkcod',flat=True))
        product = Product.objects.filter(id__in = list_stkcod)
        return "<br>".join([f"{p.id} : {p.name}" for p in product])
    
    def get_depnam(self):
        details = BaseExpenseDepartment.objects.filter(id = self.depcod)
        return ", ".join([f"{d.id} {d.name}" for d in details])
    
    def get_repair(self):
        details = BaseRepairType.objects.filter(id = self.note2.strip())
        return ", ".join([f"{d.id} {d.name}" for d in details])
    
    def get_total_price(self):
        result = ExOESTND.objects.using('pg_db').filter(docnum=self.docnum, comcod=self.comcod).aggregate(sum_amount=Sum('trnval'))
        return result['sum_amount'] or 0
    
    def __str__(self):
        return f"{self.docnum} - {self.refnum}"
    

class ExOESTND(models.Model):
    recordid = models.AutoField(primary_key=True)
    docnum = models.CharField(max_length=12, blank=True, null=True)
    seqnum = models.IntegerField(blank=True, null=True)
    loccod = models.CharField(max_length=10, blank=True, null=True)
    comcod = models.CharField(max_length=10, blank=True, null=True)
    stktyp = models.CharField(max_length=10, blank=True, null=True)
    stkcod = models.CharField(max_length=20, blank=True, null=True)
    stkdes = models.CharField(max_length=60, blank=True, null=True)
    ordqty = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tfactor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unitpr = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tqucod = models.CharField(max_length=10, blank=True, null=True)
    trnval = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unitnam = models.CharField(max_length=35, blank=True, null=True)
    stknote = models.CharField(max_length=50, blank=True, null=True)
    audtuser = models.CharField(max_length=50, blank=True, null=True)
    audttime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'OESTND'
        managed = False
        indexes = [
            models.Index(fields=['docnum', 'comcod'], name='OESTND_ID1'),
            models.Index(fields=['docnum', 'loccod', 'comcod'], name='OESTND_ID2'),
            models.Index(fields=['comcod', 'stkcod', 'stktyp'], name='OESTND_ID3'),
        ]

    def __str__(self):
        return f"{self.docnum} - {self.stkcod}"

############################ ขายเงินเชื่อ อะไหล่, น้ำมัน ###########################
class ExOEINVD(models.Model):
    recordid = models.AutoField(primary_key=True)
    docnum = models.CharField(max_length=12, null=True, blank=True)
    sonum = models.CharField(max_length=12, null=True, blank=True)
    seqnum = models.IntegerField(null=True, blank=True)
    loccod = models.CharField(max_length=10, null=True, blank=True)
    stktyp = models.CharField(max_length=10, null=True, blank=True)
    stkcod = models.CharField(max_length=20, null=True, blank=True)
    stkdes = models.CharField(max_length=60, null=True, blank=True)
    ordqty = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cancelqty = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    remqty = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tfactor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unitpr = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tqucod = models.CharField(max_length=10, null=True, blank=True)
    disc = models.CharField(max_length=10, null=True, blank=True)
    discamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    trnval = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    trnwg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unitnam = models.CharField(max_length=35, null=True, blank=True)
    stknote = models.CharField(max_length=50, null=True, blank=True)
    audtuser = models.CharField(max_length=50, null=True, blank=True)
    audttime = models.DateTimeField(auto_now_add=True)
    stkdisc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    apmpr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qtybag = models.IntegerField(default=0)
    qtykg = models.IntegerField(default=0)
    rectyp = models.IntegerField(default=3)
    advamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cfactor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    comcod = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'OEINVD'
        indexes = [
            models.Index(fields=['sonum'], name='OEINVD_ID1'),
            models.Index(fields=['stkcod'], name='OEINVD_ID2'),
            models.Index(fields=['docnum'], name='OEINVD_ID3'),
            models.Index(fields=['sonum', 'loccod', 'stkcod'], name='OEINVD_ID4'),
        ]
        verbose_name = "OEINVD"
        verbose_name_plural = "OEINVD"

    def __str__(self):
        return f"{self.docnum} - {self.stkcod}"
    
class ExOEINVH(models.Model):
    recordid = models.AutoField(primary_key=True)
    docnum = models.CharField(max_length=12, null=True, blank=True)
    docdate = models.DateField(null=True, blank=True)
    sorectyp = models.IntegerField(null=True, blank=True)
    flgvat = models.IntegerField(null=True, blank=True)
    depcod = models.CharField(max_length=5, null=True, blank=True)
    slmcod = models.CharField(max_length=10, null=True, blank=True)
    cuscod = models.CharField(max_length=10, null=True, blank=True)
    youref = models.CharField(max_length=30, null=True, blank=True)
    paytrm = models.IntegerField(null=True, blank=True)
    dlvdate = models.DateField(null=True, blank=True)
    nxtseq = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    disc = models.CharField(max_length=10, null=True, blank=True)
    discamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vatrat = models.IntegerField(null=True, blank=True)
    vatamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    netamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    netval = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    docstat = models.CharField(max_length=1, null=True, blank=True)
    cusnam = models.CharField(max_length=60, null=True, blank=True)
    addr01 = models.CharField(max_length=50, null=True, blank=True)
    addr02 = models.CharField(max_length=120, null=True, blank=True)
    addr03 = models.CharField(max_length=30, null=True, blank=True)
    zipcod = models.CharField(max_length=5, null=True, blank=True)
    contact = models.CharField(max_length=40, null=True, blank=True)
    telnum = models.CharField(max_length=50, null=True, blank=True)
    term = models.CharField(max_length=85, null=True, blank=True)
    sonum = models.CharField(max_length=15, null=True, blank=True)
    areacod = models.CharField(max_length=10, null=True, blank=True)
    shipto = models.CharField(max_length=10, null=True, blank=True)
    sogrp1 = models.IntegerField(default=0)
    sogrp2 = models.IntegerField(default=0)
    note1 = models.CharField(max_length=150, null=True, blank=True)
    note2 = models.CharField(max_length=150, null=True, blank=True)
    note3 = models.CharField(max_length=150, null=True, blank=True)
    truck = models.CharField(max_length=35, null=True, blank=True)
    bagtot = models.IntegerField(default=0)
    kgtot = models.IntegerField(default=0)
    queue = models.IntegerField(default=0)
    audtuser = models.CharField(max_length=50, null=True, blank=True)
    audttime = models.DateTimeField(auto_now_add=True)
    rectyp = models.IntegerField(default=3)
    dlvamt = models.IntegerField(default=0)
    dlvqty = models.IntegerField(default=1)
    posttime = models.DateTimeField(null=True, blank=True)
    accpost = models.DateTimeField(null=True, blank=True)
    ivgrp1 = models.IntegerField(default=0)
    remamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    rcvamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    apmtot = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    advamt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cmplapp = models.CharField(max_length=1, null=True, blank=True)
    cusship1 = models.CharField(max_length=50, null=True, blank=True)
    cusship2 = models.CharField(max_length=50, null=True, blank=True)
    comcod = models.CharField(max_length=10, null=True, blank=True)
    cusgrp = models.CharField(max_length=50, null=True, blank=True)
    custyp = models.CharField(max_length=4, null=True, blank=True)

    class Meta:
        db_table = 'OEINVH'
        managed = False
        unique_together = (('docnum', 'comcod'),)
        indexes = [
            models.Index(fields=['sonum'], name='OEINVH_ID1'),
            models.Index(fields=['docdate'], name='OEINVH_ID2'),
        ]
        verbose_name = "OEINVH"
        verbose_name_plural = "OEINVHs"

    def get_items(self):
        details = ExOEINVD.objects.using('pg_db').filter(docnum=self.docnum, comcod=self.comcod)
        return "<br>".join([f"{d.stkcod} : {d.stkdes}" for d in details])

    def __str__(self):
        return f"{self.docnum} - {self.cuscod}"

class Maintenance(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="รหัสการซ่อม")#เก็บไอดีรหัสการซ่อม
    uniq_code = models.CharField(max_length=10, blank = True, null = True)#UNIQUEID() ใน appsheet
    created = models.DateTimeField(default=timezone.now, verbose_name="วันที่สร้าง")
    update = models.DateTimeField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    car = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True, related_name='ma_car1', verbose_name="ทะเบียนรถ") #ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน
    car_tail = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True, related_name='ma_car2', verbose_name="ทะเบียนรถ (หาง)") #ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน (หาง)
    name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ma_name',
        verbose_name="ผู้แจ้งซ่อม"
    )
    broke_reason = models.CharField(max_length=255, blank=True, null = True, verbose_name="อาการเสีย")
    car_state = models.CharField(max_length=255, blank=True, null = True, verbose_name="สภาพรถ")#สามารถเคลื่อนที่ได้และไม่สามารถเคลื่อนที่ได้
    image1 = models.ImageField(null=True, blank=True, upload_to = "maintenance/%Y/%m/%d",verbose_name="รูปภาพที่ 1")
    image2 = models.ImageField(null=True, blank=True, upload_to = "maintenance/%Y/%m/%d",verbose_name="รูปภาพที่ 2")
    image3 = models.ImageField(null=True, blank=True, upload_to = "maintenance/%Y/%m/%d",verbose_name="รูปภาพที่ 3")
    image4 = models.ImageField(null=True, blank=True, upload_to = "maintenance/%Y/%m/%d",verbose_name="รูปภาพที่ 4")
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    ref_no = models.CharField(max_length = 255, null = True, blank = True)
    approve_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ma_ap_name',
        verbose_name="ผู้อนุมัติซ่อม"
    )
    approve_update = models.DateTimeField(null=True, blank=True)
    approve_status = models.CharField(blank=True, null=True, max_length=255, verbose_name="สถานะอนุมัติซ่อม")
    ma_type = models.ForeignKey(BaseMAType, on_delete=models.CASCADE, blank=True, null=True)#ประเภทใบแจ้งซ่อม
    location = models.CharField(blank=True, null=True, max_length=255, verbose_name="สถานที่ซ่อม")
    start_rp = models.DateTimeField(blank=True, null = True, verbose_name="วันที่เริ่มดำเนินการ")
    end_rp = models.DateTimeField(blank=True, null = True, verbose_name="วันที่กำหนดเสร็จ")
    repair_type = models.ForeignKey(BaseRepairType, on_delete=models.CASCADE, blank=True, null=True)#ประเภทการซ่อม
    # ส่วนที่ 2
    repair_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ma_rp_name',
        verbose_name="ช่างซ่อม"
    )
    chief_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ma_ch_name',
        verbose_name="หัวหน้าช่างซ่อม"
    )
    chief_update = models.DateTimeField(null=True, blank=True)
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ma_og_name',
        verbose_name="พัสดุซ่อมบำรุง (ผู้จัดทำ)"
    )
    mile = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์/เลขชั่วโมง ตอนแจ้งซ่อม")
    detail = models.TextField(blank=True, null = True, verbose_name="อธิบายงาน/รายละเอียด")
    repair_note = models.TextField(blank=True, null = True, verbose_name="ช่างผู้ดำเนินการ")
    work_hour = models.IntegerField(null=True, blank = True, verbose_name="ชม.ทำงาน (ชม.)")
    force_day = models.IntegerField(null=True, blank = True, verbose_name="ใช้แรง (วัน)")
    force_hour = models.IntegerField(null=True, blank = True, verbose_name="ใช้แรง (ชม.)")
    #ส่วนที่ 3
    distributor = models.ForeignKey(Distributor,on_delete=models.CASCADE,null = True,blank = True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank = True, null = True)#จำนวนเงินทั้งสิ้น
    contact_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ma_ct_name',
        verbose_name="ผู้ติดต่อ"
    )
    sender_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ma_sd_name',
        verbose_name="ผู้จัดส่งงาน"
    )
    #ส่วนสรุป
    sum_up = models.TextField(blank=True, null = True, verbose_name="สรุปงานซ่อม/ความคิดเห็น")
    is_complete = models.BooleanField(blank=True, null = True)#สถานะ ปิดสรุปใช้งานได้
    fail_reason = models.TextField(blank=True, null = True, verbose_name="เหตุผลที่ปิดสรุปไม่ได้")#เหตุผลที่ปิดสรุปไม่ได้
    ma_pdf = ContentTypeRestrictedFileField(upload_to='pdfs/maintenance/%Y/%m/%d', content_types=['application/msword', 'text/csv','application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/gif','image/vnd.microsoft.icon','image/jpeg','image/png','application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.rar','text/plain','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/zip','application/x-7z-compressed','application/x-zip-compressed'], max_upload_size=5242880 ,blank=True, null=True, verbose_name="ไฟล์แนบ")
    err_log = models.TextField(blank=True, null = True, verbose_name="error log")
    is_cancel = models.BooleanField(default=False)#สถานะ ยกเลิกรายการ ข้อมูลจะไปอยู่ในแท็ปประวัติ

    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = maintenance_ref_number(self.branch_company)
        super(Maintenance, self).save(*args, **kwargs)

    class Meta:
        db_table = 'Maintenance'
        ordering=('-id',)
        verbose_name = 'ใบแจ้งซ่อม'
        verbose_name_plural = 'ข้อมูลใบแจ้งซ่อม'

class CarLogbook(models.Model):
    id = models.AutoField(primary_key=True)#เก็บไอดีรหัสบันทึกการใช้รถ
    uniq_code = models.CharField(max_length=10, blank = True, null = True)#UNIQUEID() ใน appsheet
    series = models.IntegerField(null=True, blank = True, verbose_name="ลำดับ")
    created = models.DateTimeField(default=timezone.now, verbose_name="วันที่สร้าง")
    update = models.DateTimeField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    car = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True, related_name='cl_car1', verbose_name="ทะเบียนรถ") #ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน (หัว)
    car_tail = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True, related_name='cl_car2', verbose_name="ทะเบียนรถ (หาง)") #ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน (หาง)
    name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='cl_name',
        verbose_name="ผู้บันทึกการใช้รถ"
    )
    branch_company = models.ForeignKey(BaseBranchCompany, on_delete=models.CASCADE, blank=True, null=True)
    address_company = models.ForeignKey(BaseAddress, on_delete=models.CASCADE, blank=True, null=True)
    ref_no = models.CharField(max_length = 255, null = True, blank = True)

    oil = models.DecimalField(max_digits=8,decimal_places=2, null=True, blank = True, verbose_name="น้ำมันโซล่า ( ลิตร )")
    gas = models.DecimalField(max_digits=8,decimal_places=2, null=True, blank = True, verbose_name="น้ำเบนซิล ( ลิตร )")
    engine = models.DecimalField(max_digits=8,decimal_places=2, null=True, blank = True, verbose_name="น้ำมันเครื่อง ( ลิตร )")
    hydraulic = models.DecimalField(max_digits=8,decimal_places=2, null=True, blank = True, verbose_name="น้ำมันไฮโดรลิค ( ลิตร )")
    grease = models.DecimalField(max_digits=8,decimal_places=2, null=True, blank = True, verbose_name="จารบี ( ลิตร )")
    mile_start = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์เริ่ม")
    mile_end = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์สิ้นสุด")
    diff_mile = models.IntegerField(null=True, blank = True, verbose_name="diff mile")
    
    job1_id = models.IntegerField(blank=True, null=True, verbose_name="id รายละเอียดงานที่ 1")
    job1 = models.CharField(blank=True, null=True, max_length=255, verbose_name="รายละเอียดงานที่ 1")
    start_job1 = models.TimeField(blank=True, null=True, verbose_name="เวลาเริ่มงานที่ 1")
    end_job1 = models.TimeField(blank=True, null=True, verbose_name="เวลาสิ้นสุดงานที่ 1")
    diff_time_job1 = models.DurationField(null=True, blank=True)  # store the difference

    mile_start_job1 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์เริ่มต้นงานที่ 1")
    mile_end_job1 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์สิ้นสุดงานที่ 1")
    diff_mile_job1 = models.IntegerField(null=True, blank = True, verbose_name="diff mile งานที่ 1")
    exd_job1 = models.ForeignKey(BaseExpenseDepartment,
                on_delete=models.CASCADE,
                blank=True, null=True,
                related_name='exd_j1',
                verbose_name="แผนกค่าใช้จ่ายงานที่ 1") #แผนกค่าใช้จ่าย

    job2_id = models.IntegerField(blank=True, null=True, verbose_name="id รายละเอียดงานที่ 2")
    job2 = models.CharField(blank=True, null=True, max_length=255, verbose_name="รายละเอียดงานที่ 2")
    start_job2 = models.TimeField(blank=True, null=True, verbose_name="เวลาเริ่มงานที่ 2")
    end_job2 = models.TimeField(blank=True, null=True, verbose_name="เวลาสิ้นสุดงานที่ 2")
    diff_time_job2 = models.DurationField(null=True, blank=True)  # store the difference

    mile_start_job2 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์เริ่มต้นงานที่ 2")
    mile_end_job2 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์สิ้นสุดงานที่ 2")
    diff_mile_job2 = models.IntegerField(null=True, blank = True, verbose_name="diff mile งานที่ 2")
    exd_job2 = models.ForeignKey(BaseExpenseDepartment,
                on_delete=models.CASCADE,
                blank=True, null=True,
                related_name='exd_j2',
                verbose_name="แผนกค่าใช้จ่ายงานที่ 2") #แผนกค่าใช้จ่าย

    job3_id = models.IntegerField(blank=True, null=True, verbose_name="id รายละเอียดงานที่ 3")
    job3 = models.CharField(blank=True, null=True, max_length=255, verbose_name="รายละเอียดงานที่ 3")
    start_job3 = models.TimeField(blank=True, null=True, verbose_name="เวลาเริ่มงานที่ 3")
    end_job3 = models.TimeField(blank=True, null=True, verbose_name="เวลาสิ้นสุดงานที่ 3")
    diff_time_job3 = models.DurationField(null=True, blank=True)  # store the difference

    mile_start_job3 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์เริ่มต้นงานที่ 3")
    mile_end_job3 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์สิ้นสุดงานที่ 3")
    diff_mile_job3 = models.IntegerField(null=True, blank = True, verbose_name="diff mile งานที่ 3")
    exd_job3 = models.ForeignKey(BaseExpenseDepartment,
                on_delete=models.CASCADE,
                blank=True, null=True,
                related_name='exd_j3',
                verbose_name="แผนกค่าใช้จ่ายงานที่ 3") #แผนกค่าใช้จ่าย

    job4_id = models.IntegerField(blank=True, null=True, verbose_name="id รายละเอียดงานที่ 4")
    job4 = models.CharField(blank=True, null=True, max_length=255, verbose_name="รายละเอียดงานที่ 4")
    start_job4 = models.TimeField(blank=True, null=True, verbose_name="เวลาเริ่มงานที่ 4")
    end_job4 = models.TimeField(blank=True, null=True, verbose_name="เวลาสิ้นสุดงานที่ 4")
    diff_time_job4 = models.DurationField(null=True, blank=True)  # store the difference

    mile_start_job4 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์เริ่มต้นงานที่ 4")
    mile_end_job4 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์สิ้นสุดงานที่ 4")
    diff_mile_job4 = models.IntegerField(null=True, blank = True, verbose_name="diff mile งานที่ 4")
    exd_job4 = models.ForeignKey(BaseExpenseDepartment,
                on_delete=models.CASCADE,
                blank=True, null=True,
                related_name='exd_j4',
                verbose_name="แผนกค่าใช้จ่ายงานที่ 4") #แผนกค่าใช้จ่าย

    job5_id = models.IntegerField(blank=True, null=True, verbose_name="id รายละเอียดงานที่ 5")
    job5 = models.CharField(blank=True, null=True, max_length=255, verbose_name="รายละเอียดงานที่ 5")
    mile_start_job5 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์เริ่มต้นงานที่ 5")
    mile_end_job5 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์สิ้นสุดงานที่ 5")
    diff_mile_job5 = models.IntegerField(null=True, blank = True, verbose_name="diff mile งานที่ 5")

    job6_id = models.IntegerField(blank=True, null=True, verbose_name="id รายละเอียดงานที่ 6")
    job6 = models.CharField(blank=True, null=True, max_length=255, verbose_name="รายละเอียดงานที่ 6")
    mile_start_job6 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์เริ่มต้นงานที่ 6")
    mile_end_job6 = models.IntegerField(null=True, blank = True, verbose_name="เลขไมล์สิ้นสุดงานที่ 6")
    diff_mile_job6 = models.IntegerField(null=True, blank = True, verbose_name="diff mile งานที่ 6")

    note = models.TextField(blank=True, null = True, verbose_name="หมายเหตุ")#หมายเหตุ
    err_log = models.TextField(blank=True, null = True, verbose_name="error log")
    image_mile = models.ImageField(null=True, blank=True, upload_to = "car_log_book/%Y/%m/%d",verbose_name="รูปภาพเลขไมล์เริ่มต้น")

    is_cancel = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self.address_company is None:
            company = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.branch_company).first()
            self.address_company = company.address
        if self.ref_no is None:
            self.ref_no = carLogbook_ref_number(self.branch_company)
        if self.mile_start is None: #ROI คำนวนเลขไมล์เริ่ม auto
           self.mile_start = self.mile_start_job1
        if self.mile_end is None: #ROI คำนวนเลขไมล์จบ auto
            values = [
                self.mile_end_job1,
                self.mile_end_job2,
                self.mile_end_job3,
                self.mile_end_job4,
                self.mile_end_job5,
                self.mile_end_job6,
            ]

            # Filter out None values
            values = [v for v in values if v is not None]

            self.mile_end = max(values) if values else None

        if self.start_job1 and self.end_job1:
            self.diff_time_job1 = calculateDiffTime(self.start_job1, self.end_job1)

        if self.start_job2 and self.end_job2:
            self.diff_time_job2 = calculateDiffTime(self.start_job2, self.end_job2)

        if self.start_job3 and self.end_job3:
            self.diff_time_job3 = calculateDiffTime(self.start_job3, self.end_job3)
            
        if self.start_job4 and self.end_job4:
            self.diff_time_job4 = calculateDiffTime(self.start_job4, self.end_job4)

        if self.mile_start_job1 and self.mile_end_job1:
            self.diff_mile_job1 = self.mile_end_job1 - self.mile_start_job1

        if self.mile_start_job2 and self.mile_end_job2:
            self.diff_mile_job2 = self.mile_end_job2 - self.mile_start_job2

        if self.mile_start_job3 and self.mile_end_job3:
            self.diff_mile_job3 = self.mile_end_job3 - self.mile_start_job3

        if self.mile_start_job4 and self.mile_end_job4:
            self.diff_mile_job4 = self.mile_end_job4 - self.mile_start_job4

        if self.mile_start_job5 and self.mile_end_job5:
            self.diff_mile_job5 = self.mile_end_job5 - self.mile_start_job5

        if self.mile_start_job6 and self.mile_end_job6:
            self.diff_mile_job6 = self.mile_end_job6 - self.mile_start_job6

        if self.mile_start and self.mile_end:
            self.diff_mile = self.mile_end - self.mile_start
        
        super(CarLogbook, self).save(*args, **kwargs)

    class Meta:
        db_table = 'CarLogbook'
        ordering=('-id',)
        verbose_name = 'ใบบันทึกการใช้งานรถ'
        verbose_name_plural = 'ข้อมูลใบบันทึกการใช้งานรถ'

def calculateDiffTime(start_time, end_time):
    start_dt = datetime.datetime.combine(date.today(), start_time)
    end_dt = datetime.datetime.combine(date.today(), end_time)
    # Handle case where end_time is on the next day
    if end_dt < start_dt:
         end_dt += timedelta(days=1)
    return end_dt - start_dt

#USER + CarDepartment
class UserCarDepartment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True, verbose_name="ผู้ใช้")
    car = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True, related_name='ucd_car1', verbose_name="ทะเบียนรถ") #ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน (หัว)
    in_comp = models.ForeignKey(BaseBranchCompany,on_delete=models.CASCADE,null=True, blank=True,verbose_name="สังกัดบริษัทที่อยู่")

    class Meta:
        verbose_name = 'ผู้ใช้และทะเบียนรถและสังกัด'
        verbose_name_plural = 'ข้อมูลผู้ใช้และทะเบียนรถและสังกัด'

    def __str__(self):
        return self.user.username
    
class ApproveCarDepartment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="ผู้อนุมติ")
    car_dep = models.ManyToManyField(BaseCarDepartment, verbose_name="แผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน")
    branch_company = models.ManyToManyField(BaseBranchCompany,verbose_name="สิทธิการอนุมัติตามบริษัท")
    class Meta:
        db_table = 'ApproveCarDepartment'
        ordering=('id',)
        verbose_name = 'ผู้อนุม้ติและสิทธิการอนุมัติแผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน'
        verbose_name_plural = 'ข้อมูลผู้อนุม้ติและสิทธิการอนุมัติแผนกทะเบียนรถ/เครื่องจักร/หน่วยงาน'

    def __str__(self):
        return str(self.user.username)
    
#เก็บข้อมูลการทำ PM ล่าสุด
class PmRoundItem(models.Model):
    car = models.ForeignKey(BaseCar, on_delete=models.CASCADE, blank=True, null=True, verbose_name="ทะเบียนรถ/ เครื่องจักร") #ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน
    created = models.DateTimeField(default=timezone.now, verbose_name="วันที่ทำ PM")
    update = models.DateField(auto_now=True) #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    num_pm = models.IntegerField(blank=True, null=True, verbose_name="เลขที่ทำ PM ล่าสุด")
    ma_id = models.IntegerField(blank=True, null=True , verbose_name="อ้างอิง id Maintenance")#อ้างอิง id Maintenance
    ma_ref_no = models.CharField(max_length=255, null = True, blank = True, verbose_name="อ้างอิง ref_no Maintenance") #อ้างอิง ref_no Maintenance

    class Meta:
        db_table = 'PmRoundItem'
        ordering=('id',)
        verbose_name = 'การทำ PM ล่าสุด'
        verbose_name_plural = 'ข้อมูลการทำ PM ล่าสุด'