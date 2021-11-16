from django.contrib import admin
from django.forms import CheckboxSelectMultiple, MultipleChoiceField
from django.db import models
from stock.models import BaseCredit, BaseDelivery, BasePermission, BaseSparesType, BaseUnit, BaseVatType, Category, Position, PositionBasePermission, Product, CartItem, Cart, Order, OrderItem, Requisition, RequisitionItem, BaseApproveStatus, BaseUrgency, UserProfile, Distributor, BaseVisible

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
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

class DistributorAdmin(admin.ModelAdmin):
    list_display = ['id_express','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

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

class BaseCreditAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseDeliveryAdmin(admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 10 #แสดงผล 10 รายการต่อ 1 หน้า
    list_editable = ['name']

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
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(BaseVatType, BaseVatTypeAdmin)
admin.site.register(BaseUnit, BaseUnitAdmin)
admin.site.register(BaseCredit, BaseCreditAdmin)
admin.site.register(BaseSparesType, BaseSparesTypeAdmin)
admin.site.register(BaseDelivery, BaseDeliveryAdmin)
admin.site.register(BaseVisible)