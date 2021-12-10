from django.contrib import admin
from django.db.models import fields
from django.forms import CheckboxSelectMultiple, MultipleChoiceField, widgets
from django.db import models
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from stock.models import BaseCredit, BaseDelivery, BasePermission, BaseSparesType, BaseUnit, BaseVatType, Category, Position, PositionBasePermission, Product, CartItem, Cart, Order, OrderItem, Requisition, RequisitionItem, BaseApproveStatus, BaseUrgency, UserProfile, Distributor, BaseVisible, ReceiveItem, BaseDistributorType, BaseDistributorGenre, BaseAffiliatedCompany, BasePrefix
from .resources import ReceiveItemResource, DistributorResource

# Register your models here.
class ProductAdmin(ImportExportModelAdmin):
    list_display = ['name', 'price','stock','created','update'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_editable = ['price','stock'] #แก้ไขค่าได้เลยในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','name','email', 'total','token','created','update'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order','product', 'quantity','price','created','update'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า

class BaseApproveStatusAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า

class BaseUrgencyAdmin(admin.ModelAdmin):
    list_display = ['id','name','description'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า

class PositionAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class PositionBasePermissionAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    list_display = ['position']
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า

class BaseDistributorGenreAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseDistributorTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseAffiliatedCompanyAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class BasePrefixAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class DistributorResource(resources.ModelResource):

    prefix = fields.Field(
        column_name='prefix',
        attribute='prefix',
        widget=ForeignKeyWidget(BasePrefix, 'name'))

    type = fields.Field(
        column_name='type',
        attribute='type',
        widget=ForeignKeyWidget(BaseDistributorType, 'name'))

    genre = fields.Field(
        column_name='genre',
        attribute='genre',
        widget=ForeignKeyWidget(BaseDistributorGenre, 'name'))

    credit = fields.Field(
        column_name='credit',
        attribute='credit',
        widget=ForeignKeyWidget(BaseCredit, 'name'))

    affiliated = fields.Field(
        column_name='affiliated',
        attribute='affiliated',
        widget=ForeignKeyWidget(BaseAffiliatedCompany, 'name'))

    class Meta:
        model = Distributor
        fields = ('id', 'prefix', 'name', 'type', 'genre', 'credit', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')
        export_order = ('id', 'prefix', 'name', 'type', 'genre', 'credit', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')

class DistributorAdmin(ImportExportModelAdmin):
    resource_class = DistributorResource
    list_display = ('id', 'prefix', 'name', 'type', 'genre', 'credit', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')

class BaseSparesTypeAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseVatTypeAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class UserProfileAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    list_display = ['user','position'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['position']

class BaseUnitAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseCreditAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseDeliveryAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class ReceiveItemAdmin(ImportExportModelAdmin):
    list_display = ('item', 'quantity', 'unit','unit_price','price', 'rc_id')
    
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
#admin.site.register(CartItem)
#admin.site.register(Cart)
#admin.site.register(OrderItem, OrderItemAdmin)
#admin.site.register(Order, OrderAdmin)
#admin.site.register(Requisition)
#admin.site.register(RequisitionItem)
admin.site.register(BaseApproveStatus, BaseApproveStatusAdmin)
admin.site.register(BaseUrgency, BaseUrgencyAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(PositionBasePermission, PositionBasePermissionAdmin)
admin.site.register(BasePermission)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BaseDistributorType, BaseDistributorTypeAdmin)
admin.site.register(BaseDistributorGenre, BaseDistributorGenreAdmin)
admin.site.register(BaseAffiliatedCompany, BaseAffiliatedCompanyAdmin)
admin.site.register(BasePrefix, BasePrefixAdmin)
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(BaseVatType, BaseVatTypeAdmin)
admin.site.register(BaseUnit, BaseUnitAdmin)
admin.site.register(BaseCredit, BaseCreditAdmin)
admin.site.register(BaseSparesType, BaseSparesTypeAdmin)
admin.site.register(BaseDelivery, BaseDeliveryAdmin)
admin.site.register(BaseVisible)
admin.site.register(ReceiveItem, ReceiveItemAdmin)