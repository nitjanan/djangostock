from django.contrib import admin
from django.db.models import fields
from django.forms import CheckboxSelectMultiple, MultipleChoiceField, widgets
from django.db import models
from django.forms.fields import ImageField
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from stock.models import BaseCredit, BaseDelivery, BaseDepartment, BaseIsoCode, BasePermission, BaseSparesType, BaseUnit, BaseVatType, Category, ComparisonPrice, ComparisonPriceDistributor, ComparisonPriceItem, Position, PositionBasePermission, Product, CartItem, Cart, Order, OrderItem, PurchaseOrder, PurchaseRequisition, Requisition, RequisitionItem, BaseApproveStatus, BaseUrgency, UserProfile, Distributor, BaseVisible, ReceiveItem, BaseDistributorType, BaseDistributorGenre, BaseAffiliatedCompany, BasePrefix, PurchaseOrderItem, BaseCMType, BaseBranchCompany, BranchCompanyBaseAdress, BaseAddress, BaseIsoCode, Document, BaseGrade, BasePOType, BaseRepairType, BaseCar, BaseBrokeType, BaseRequisitionType, BaseExpenseDepartment, BaseExpenses, BaseAgency, Invoice, InvoiceItem, RateDistributor, BaseMAType, CarLogbook, Maintenance, BaseCarDepartment, UserCarDepartment, BaseJobCarDep, ApproveCarDepartment
from .resources import ReceiveItemResource, DistributorResource
from django.utils.translation import gettext_lazy as _
from related_admin import RelatedFieldAdmin
from related_admin import getter_for_related_field
from stock.forms import ProductAdminForm, BaseCarAdminForm

# Register your models here.
class CategoryAdmin(ImportExportModelAdmin):
    search_fields = ['slug', 'name']
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
    autocomplete_fields = ['unit','category']

    resource_class = ProductResource
    list_display = ('id', 'name', 'unit', 'slug', 'affiliated', 'qr_code') #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    #new admin check error id 23-03-2023
    fields = ('id', 'name', 'unit', 'description', 'slug', 'category', 'affiliated')
    form = ProductAdminForm
    

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','name','email', 'total','token','created','update'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order','product', 'quantity','price','created','update'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseApproveStatusAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseExpensesAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseIsoCodeAdmin(ImportExportModelAdmin):
    list_display = ['id','r_code','pr_code','cm_code','po_code'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseUrgencyAdmin(ImportExportModelAdmin):
    list_display = ['id','name','description'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class PositionAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class PositionBasePermissionAdmin(ImportExportModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    autocomplete_fields = ['position',]
    list_display = ['id', 'position',]
    search_fields = ['id', 'position__name', 'branch_company__name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseDistributorGenreAdmin(ImportExportModelAdmin):
    search_fields = ['name']
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

class BaseBranchCompanyAdmin(ImportExportModelAdmin):
    list_display = ['id','code','affiliated', 'name', 'invoice_code' , 'oi_invoice_code', 'soc_code', 'oi_soc_code'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BasePrefixAdmin(ImportExportModelAdmin):
    search_fields = ['name']
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseAddressAdmin(ImportExportModelAdmin):
    list_display = ['id','name_th', 'address'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BranchCompanyBaseAdressAdmin(ImportExportModelAdmin):
    list_display = ['id','branch_company', 'address'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

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
        fields = ('created', 'id', 'prefix', 'name', 'type', 'genre', 'credit', 'vat_type', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')
        export_order = ('created', 'id', 'prefix', 'name', 'type', 'genre', 'credit', 'vat_type', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')

class DistributorAdmin(ImportExportModelAdmin):
    autocomplete_fields = ['prefix','genre']

    resource_class = DistributorResource
    list_display = ('id', 'prefix', 'name', 'type', 'genre', 'credit', 'vat_type', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated', 'tex', 'fax')
    search_fields = ('id', 'name','affiliated__name')

class BaseSparesTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseDepartmentAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name']
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
    autocomplete_fields = ['user','position','department']

    list_display = ['user','position','department'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    #list_editable = ['position','department']
    search_fields = ['user__first_name', 'user__last_name', 'position__name']
    readonly_fields = ('signature_preview',)

    def signature_preview(self, obj):
        return obj.signature_preview

    signature_preview.short_description = 'ลายเซ็น preview'
    signature_preview.allow_tags = True

class BaseUnitAdmin(ImportExportModelAdmin):
    search_fields = ['name']
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
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    list_display = ['ref_no', 'pr_ref_no', 'name','supplies_approve_user_name', 'organizer', 'branch_company']
    search_fields = ['ref_no', 'pr_ref_no', 'name__first_name','supplies_approve_user_name__first_name', 'organizer__first_name']

class RequisitionItemAdmin(RelatedFieldAdmin):
    autocomplete_fields = ['product',]
    list_display = ('requisit__ref_no','product_name','product__id','product')
    search_fields = ('requisit__ref_no','product_name','product__id','product__name')

class PurchaseRequisitionAdmin(RelatedFieldAdmin):
    list_display = ('ref_no', 'requisition__ref_no','purchase_user','approver_user','stockman_user', 'organizer')
    search_fields = ('ref_no', 'requisition__ref_no','purchase_user__first_name','approver_user__first_name','stockman_user__first_name', 'organizer__first_name')

class ComparisonPriceAdmin(RelatedFieldAdmin):
    autocomplete_fields = ['select_bidder', 'organizer', 'examiner_user', 'approver_user', 'special_approver_user']

    list_display = ('ref_no','po_ref_no','select_bidder','organizer')
    search_fields = ('ref_no','po_ref_no','select_bidder__name','organizer__first_name')

class ComparisonPriceDistributorAdmin(ImportExportModelAdmin):
    list_display = ['cp','distributor']
    search_fields = ['cp__ref_no','distributor__name']

class ComparisonPriceItemAdmin(RelatedFieldAdmin):
    list_display = ('bidder__cp__ref_no','bidder__distributor__name','item__product__id', 'item__product__name')
    search_fields = ('bidder__cp__ref_no','bidder__distributor__name','item__product__id', 'item__product__name')

class PurchaseOrderAdmin(RelatedFieldAdmin):
    autocomplete_fields = ['distributor', 'stockman_user', 'approver_user']

    list_display = ('ref_no', 'cp__ref_no','distributor', 'stockman_user')
    search_fields = ('ref_no', 'cp__ref_no','distributor__name', 'stockman_user__first_name')

class PurchaseOrderItemAdmin(ImportExportModelAdmin):
    list_display = ['po', 'item']
    search_fields = ['po__ref_no', 'item__product__id', 'item__product__name']

class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id','doc_pdf'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseGradeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BasePOTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    list_editable = ['name']

class BaseRepairTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name','rq_type'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name','rq_type__name']

class BaseCarAdmin(ImportExportModelAdmin):
    list_display = ['id','code','name','rq_type']#แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['code', 'name','rq_type__name']
    form = BaseCarAdminForm

class BaseBrokeTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name']

class BaseRequisitionTypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name']

class BaseExpenseDepartmentAdmin(ImportExportModelAdmin):
    list_display = ['id','name', 'agency'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name', 'agency__name']

class BaseAgencyAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name']

class InvoiceAdmin(ImportExportModelAdmin):
    autocomplete_fields = ['bring_name','payer_name','car']
    list_display = ['ref_no', 'created', 'bring_name', 'payer_name', 'car', 'v_stamp'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ['ref_no', 'created', 'bring_name__first_name', 'payer_name__first_name', 'car']

class InvoiceItemAdmin(RelatedFieldAdmin):
    autocomplete_fields = ['item',]
    list_display = ('iv__ref_no','created' ,'quantity','unit','unit_price','price')
    search_fields = ('iv__ref_no','created' ,'quantity','unit','unit_price','price')

class RateDistributorAdmin(RelatedFieldAdmin):
    list_display = ('id', 'po__ref_no', 'distributor', 'organizer_user')
    search_fields = ('id', 'po__ref_no', 'distributor__name', 'organizer_user__first_name')

class BaseMATypeAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class CarLogbookAdmin(ImportExportModelAdmin):
    autocomplete_fields = ['car','car_tail', 'name']

    list_display = ['ref_no', 'car', 'name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ('ref_no', 'name__first_name', 'car__name', 'car__code')

class MaintenanceAdmin(ImportExportModelAdmin):
    autocomplete_fields = ['car', 'name', 'approve_name', 'repair_type', 'repair_name', 'chief_name', 'organizer', 'distributor', 'contact_name', 'sender_name']

    list_display = ['ref_no', 'car','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ('ref_no', 'name__first_name', 'car__name', 'car__code')

class BaseCarDepartmentAdmin(ImportExportModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name',]

class BaseJobCarDepAdmin(ImportExportModelAdmin):
    list_display = ['id','name', 'car_dep'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name', 'car_dep']

class UserCarDepartmentAdmin(ImportExportModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    autocomplete_fields = ['user', 'car']

    list_display = ['user', 'car', 'car_dep', 'in_comp'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['user__first_name', 'car', 'car_dep', 'in_comp']

class ApproveCarDepartmentAdmin(ImportExportModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    autocomplete_fields = ['user',]
    list_display = ['id', 'user',]
    search_fields = ['id', 'car_dep__name', 'branch_company__name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

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
admin.site.register(BaseExpenses, BaseExpensesAdmin)
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
admin.site.register(BaseBranchCompany, BaseBranchCompanyAdmin)
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
admin.site.register(BaseAddress, BaseAddressAdmin)
admin.site.register(BranchCompanyBaseAdress, BranchCompanyBaseAdressAdmin)
admin.site.register(BaseIsoCode, BaseIsoCodeAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(BaseGrade, BaseGradeAdmin)
admin.site.register(BasePOType, BasePOTypeAdmin)
admin.site.register(BaseRepairType, BaseRepairTypeAdmin)
admin.site.register(BaseCar, BaseCarAdmin)
admin.site.register(BaseBrokeType, BaseBrokeTypeAdmin)
admin.site.register(BaseRequisitionType, BaseRequisitionTypeAdmin)
admin.site.register(BaseExpenseDepartment, BaseExpenseDepartmentAdmin)
admin.site.register(BaseAgency, BaseAgencyAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceItem, InvoiceItemAdmin)
admin.site.register(RateDistributor, RateDistributorAdmin)
admin.site.register(BaseMAType, BaseMATypeAdmin)
admin.site.register(CarLogbook, CarLogbookAdmin)
admin.site.register(Maintenance, MaintenanceAdmin)
admin.site.register(BaseCarDepartment, BaseCarDepartmentAdmin)
admin.site.register(BaseJobCarDep, BaseJobCarDepAdmin)
admin.site.register(UserCarDepartment, UserCarDepartmentAdmin)
admin.site.register(ApproveCarDepartment, ApproveCarDepartmentAdmin)