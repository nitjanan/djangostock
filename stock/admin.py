from django.contrib import admin
from django.db.models import fields
from django.forms import CheckboxSelectMultiple, MultipleChoiceField, widgets
from django.db import models
from django.forms.fields import ImageField
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from stock.models import BaseCredit, BaseDelivery, BaseDepartment, BasePermission, BaseSparesType, BaseUnit, BaseVatType, Category, ComparisonPrice, ComparisonPriceDistributor, ComparisonPriceItem, Position, PositionBasePermission, Product, CartItem, Cart, Order, OrderItem, PurchaseOrder, PurchaseRequisition, Requisition, RequisitionItem, BaseApproveStatus, BaseUrgency, UserProfile, Distributor, BaseVisible, ReceiveItem, BaseDistributorType, BaseDistributorGenre, BaseAffiliatedCompany, BasePrefix, PurchaseOrderItem, BaseCMType, BaseBranchCompany
from .resources import ReceiveItemResource, DistributorResource
from django.utils.translation import ugettext_lazy as _
from related_admin import RelatedFieldAdmin
from related_admin import getter_for_related_field

# Register your models here.
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'slug') #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 15 #แสดงผล 10 รายการต่อ 1 หน้า

class ProductResource(resources.ModelResource):

    unit = fields.Field(
        column_name='unit',
        attribute='unit',
        widget=ForeignKeyWidget(BaseUnit, 'name'))

    affiliated = fields.Field(
        column_name='affiliated',
        attribute='affiliated',
        widget=ForeignKeyWidget(BaseAffiliatedCompany, 'name'))
    
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'slug'))

    class Meta:
        model = Product
        fields = ('id', 'name', 'unit', 'slug', 'category', 'affiliated')
        export_order = ('id', 'name', 'unit', 'slug', 'category', 'affiliated')

class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ('id', 'name', 'unit', 'slug', 'affiliated') #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','name','email', 'total','token','created','update'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order','product', 'quantity','price','created','update'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseApproveStatusAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseUrgencyAdmin(ImportExportModelAdmin):
    list_display = ['id','name','description'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class PositionAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class PositionBasePermissionAdmin(ImportExportModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    list_display = ['position']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseDistributorGenreAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseDistributorTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseAffiliatedCompanyAdmin(ImportExportModelAdmin):
    list_display = ['id','name','name_th', 'logo_preview'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    readonly_fields = ('logo_preview',)

    def logo_preview(self, obj):
        return obj.logo_preview

    logo_preview.short_description = 'โลโก้บริษัท preview'
    logo_preview.allow_tags = True

class BasePrefixAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
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
        fields = ('id', 'prefix', 'name', 'type', 'genre', 'credit', 'vat_type', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')
        export_order = ('id', 'prefix', 'name', 'type', 'genre', 'credit', 'vat_type', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')

class DistributorAdmin(ImportExportModelAdmin):
    resource_class = DistributorResource
    list_display = ('id', 'prefix', 'name', 'type', 'genre', 'credit', 'vat_type', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')
    search_fields = ('id', 'name')

class BaseSparesTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseDepartmentAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseVatTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class UserProfileAdmin(ImportExportModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    list_display = ['user','position','department'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['position','department']
    search_fields = ['user__first_name', 'user__last_name']
    readonly_fields = ('signature_preview',)

    def signature_preview(self, obj):
        return obj.signature_preview

    signature_preview.short_description = 'ลายเซ็น preview'
    signature_preview.allow_tags = True

class BaseUnitAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseCreditAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseDeliveryAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class ReceiveItemAdmin(ImportExportModelAdmin):
    list_display = ('item', 'quantity', 'unit','unit_price','price', 'rc_id')

class BasePermissionAdmin(ImportExportModelAdmin):
    list_display = ('codename','codename_th',)

class BaseVisibleAdmin(ImportExportModelAdmin):
    list_display = ('name',)

class BaseCMTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name','codename'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class RequisitionAdmin(ImportExportModelAdmin):
    list_display = ['ref_no', 'pr_ref_no', 'name','supplies_approve_user_name', 'organizer', 'branch_company']
    search_fields = ['ref_no', 'pr_ref_no', 'name__first_name','supplies_approve_user_name__first_name', 'organizer__first_name']

class RequisitionItemAdmin(RelatedFieldAdmin):
    list_display = ('requisit__ref_no','product_name','product__id','product')
    search_fields = ('requisit__ref_no','product_name','product__id','product__name')

class PurchaseRequisitionAdmin(RelatedFieldAdmin):
    list_display = ('ref_no', 'requisition__ref_no','purchase_user','approver_user','stockman_user', 'organizer')
    search_fields = ('ref_no', 'requisition__ref_no','purchase_user__first_name','approver_user__first_name','stockman_user__first_name', 'organizer__first_name')

class ComparisonPriceAdmin(RelatedFieldAdmin):
    list_display = ('ref_no','po_ref_no','select_bidder','organizer')
    search_fields = ('ref_no','po_ref_no','select_bidder__name','organizer__first_name')

class ComparisonPriceDistributorAdmin(RelatedFieldAdmin):
    list_display = ('cp__ref_no','distributor')
    search_fields = ('cp__ref_no','distributor__name')

class ComparisonPriceItemAdmin(RelatedFieldAdmin):
    list_display = ('bidder__cp__ref_no','bidder__distributor__name','item__product__id', 'item__product__name')
    search_fields = ('bidder__cp__ref_no','bidder__distributor__name','item__product__id', 'item__product__name')

class PurchaseOrderAdmin(RelatedFieldAdmin):
    list_display = ('ref_no', 'cp__ref_no','distributor', 'stockman_user')
    search_fields = ('ref_no', 'cp__ref_no','distributor__name', 'stockman_user__first_name')

class PurchaseOrderItemAdmin(RelatedFieldAdmin):
    list_display = ('po__ref_no', 'item__product__id', 'item__product__name')
    search_fields = ('po__ref_no', 'item__product__id', 'item__product__name')

    
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
#admin.site.register(CartItem)
#admin.site.register(Cart)
#admin.site.register(OrderItem, OrderItemAdmin)
#admin.site.register(Order, OrderAdmin)
admin.site.register(Requisition, RequisitionAdmin)
admin.site.register(RequisitionItem, RequisitionItemAdmin)
admin.site.register(PurchaseRequisition, PurchaseRequisitionAdmin)
admin.site.register(PurchaseOrderItem, PurchaseOrderItemAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(ComparisonPrice, ComparisonPriceAdmin)
admin.site.register(ComparisonPriceDistributor, ComparisonPriceDistributorAdmin)
admin.site.register(ComparisonPriceItem, ComparisonPriceItemAdmin)
admin.site.register(BaseDepartment, BaseDepartmentAdmin)
admin.site.register(BaseApproveStatus, BaseApproveStatusAdmin)
admin.site.register(BaseUrgency, BaseUrgencyAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(PositionBasePermission, PositionBasePermissionAdmin)
admin.site.register(BasePermission, BasePermissionAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BaseDistributorType, BaseDistributorTypeAdmin)
admin.site.register(BaseDistributorGenre, BaseDistributorGenreAdmin)
admin.site.register(BaseAffiliatedCompany, BaseAffiliatedCompanyAdmin)
admin.site.register(BaseBranchCompany)
admin.site.register(BasePrefix, BasePrefixAdmin)
admin.site.register(Distributor, DistributorAdmin)
admin.site.register(BaseVatType, BaseVatTypeAdmin)
admin.site.register(BaseUnit, BaseUnitAdmin)
admin.site.register(BaseCredit, BaseCreditAdmin)
admin.site.register(BaseSparesType, BaseSparesTypeAdmin)
admin.site.register(BaseDelivery, BaseDeliveryAdmin)
admin.site.register(BaseVisible, BaseVisibleAdmin)
admin.site.register(ReceiveItem, ReceiveItemAdmin)
admin.site.register(BaseCMType, BaseCMTypeAdmin)