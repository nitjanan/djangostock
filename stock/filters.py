from django.db.models import fields
from django.db.models.fields import DateField
from django.forms.widgets import DateInput, TextInput
import django_filters
from django_filters import DateFilter
from .models import *
from django.utils.translation import gettext_lazy as _

class RequisitionFilter(django_filters.FilterSet):
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    id = django_filters.NumberFilter(field_name="id", widget = TextInput(attrs={'size': 3 ,'class': 'numberinput' }))
    organizer =  django_filters.ModelChoiceFilter(field_name="organizer", queryset= User.objects.filter(groups__name='จัดซื้อ'))
    name = django_filters.CharFilter(field_name="name__first_name", lookup_expr='icontains')
    ref_no  = django_filters.CharFilter(field_name="ref_no", lookup_expr='icontains')

    class Meta:
        model = Requisition
        fields = ('id', 'name', 'section','created','urgency','organizer','chief_approve_user_name')
        #fields = ('id', 'name', 'section','created', 'chief_approve_status', 'supplies_approve_status')
        #ดึงทุก field
        # fields = '__all__'

RequisitionFilter.base_filters['id'].label = 'รหัส'
RequisitionFilter.base_filters['ref_no'].label = 'รหัส'
RequisitionFilter.base_filters['name'].label = 'ชื่อผู้ตั้งเบิก'
RequisitionFilter.base_filters['section'].label = 'แผนก'
RequisitionFilter.base_filters['start_created'].label = 'วันที่ตั้งเบิก'
RequisitionFilter.base_filters['end_created'].label = 'ถึง'
RequisitionFilter.base_filters['urgency'].label = 'ความเร่งด่วน'
RequisitionFilter.base_filters['chief_approve_user_name'].label = 'หัวหน้างาน'
RequisitionFilter.base_filters['organizer'].label = 'ส่งให้เจ้าหน้าที่จัดซื้อ'

class PurchaseRequisitionFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name="id", widget = TextInput(attrs={'size': 3 ,'class': 'numberinput' }))
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    purchase_user =  django_filters.ModelChoiceFilter(field_name="purchase_user", queryset= User.objects.filter(groups__name='หัวหน้างาน'))
    ref_no  = django_filters.CharFilter(field_name="ref_no", lookup_expr='icontains')
    requisition__name = django_filters.CharFilter(field_name="requisition__name__first_name", lookup_expr='icontains')
    organizer =  django_filters.ModelChoiceFilter(field_name="organizer", queryset= User.objects.filter(groups__name='จัดซื้อ'))

    class Meta:
        model = PurchaseRequisition
        fields = ('id','requisition', 'requisition__name','requisition__section','requisition__urgency','created','purchase_user','purchase_status','approver_status', 'organizer')

PurchaseRequisitionFilter.base_filters['id'].label = 'รหัส'
PurchaseRequisitionFilter.base_filters['ref_no'].label = 'รหัส'
PurchaseRequisitionFilter.base_filters['purchase_user'].label = 'ชื่อผู้ขอซื้อ'
PurchaseRequisitionFilter.base_filters['requisition'].label = 'รหัสใบขอเบิก'
PurchaseRequisitionFilter.base_filters['requisition__name'].label = 'ชื่อผู้ขอเบิก'
PurchaseRequisitionFilter.base_filters['requisition__section'].label = 'แผนก'
PurchaseRequisitionFilter.base_filters['requisition__urgency'].label = 'ความเร่งด่วน'
PurchaseRequisitionFilter.base_filters['purchase_status'].label = 'ผู้ขอซื้อ'
PurchaseRequisitionFilter.base_filters['approver_status'].label = 'ผู้อนุมัติ'
PurchaseRequisitionFilter.base_filters['start_created'].label = 'วันที่ขอซื้อ'
PurchaseRequisitionFilter.base_filters['end_created'].label = 'ถึง'
PurchaseRequisitionFilter.base_filters['organizer'].label = 'เจ้าหน้าที่จัดซื้อ'


class PurchaseOrderFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name="id", widget = TextInput(attrs={'size': 3 ,'class': 'numberinput' }))
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    distributor  = django_filters.CharFilter(field_name="distributor__name", lookup_expr='startswith')
    ref_no  = django_filters.CharFilter(field_name="ref_no", lookup_expr='icontains')
    stockman_user = django_filters.ModelChoiceFilter(field_name="stockman_user", queryset= User.objects.filter(groups__name='จัดซื้อ'))
    amount_min  = django_filters.CharFilter(field_name="amount", lookup_expr='gte')
    amount_max  = django_filters.CharFilter(field_name="amount", lookup_expr='lte')

    class Meta:
        model = PurchaseOrder
        fields = ('id', 'credit','shipping','created','approver_status', 'stockman_user')

PurchaseOrderFilter.base_filters['id'].label = 'รหัส'
PurchaseOrderFilter.base_filters['ref_no'].label = 'รหัส'
PurchaseOrderFilter.base_filters['distributor'].label = 'ชื่อผู้จำหน่าย'
PurchaseOrderFilter.base_filters['credit'].label = 'เครดิต'
PurchaseOrderFilter.base_filters['shipping'].label = 'ขนส่งโดย'
PurchaseOrderFilter.base_filters['start_created'].label = 'วันที่สั่งซื้อ'
PurchaseOrderFilter.base_filters['end_created'].label = 'ถึง'
PurchaseOrderFilter.base_filters['approver_status'].label = 'ผู้อนุมัติ'
PurchaseOrderFilter.base_filters['stockman_user'].label = 'ผู้สั่งสินค้า'
PurchaseOrderFilter.base_filters['amount_min'].label = 'ราคา'
PurchaseOrderFilter.base_filters['amount_max'].label = 'ถึง'

class PurchaseOrderItemFilter(django_filters.FilterSet):
    item_product_id_from  = django_filters.CharFilter(field_name="item__product_id", lookup_expr='gte')
    item_product_id_to  = django_filters.CharFilter(field_name="item__product_id", lookup_expr='lte')
    item_product_name = django_filters.CharFilter(field_name="item__product_name", lookup_expr='icontains')
    item_machine = django_filters.CharFilter(field_name="item__machine", lookup_expr='icontains')
    start_created = django_filters.DateFilter(field_name = "po__created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "po__created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    distributor  = django_filters.CharFilter(field_name="po__distributor__name", lookup_expr='startswith')
    stockman_user = django_filters.ModelChoiceFilter(field_name="po__stockman_user", queryset= User.objects.filter(groups__name='จัดซื้อ'))
    unit_price_min  = django_filters.CharFilter(field_name="unit_price", lookup_expr='gte')
    unit_price_max  = django_filters.CharFilter(field_name="unit_price", lookup_expr='lte')
    category = django_filters.ModelChoiceFilter(field_name="item__product__category__name", queryset= Category.objects.all())
    po_ref_no = django_filters.CharFilter(field_name="po__ref_no", lookup_expr='icontains')

    class Meta:
        model = PurchaseOrderItem
        fields = ('item__product_id', 'item__product_name','po__created','po__distributor__name','po__stockman_user', 'unit_price', 'item__product__category__name', 'po_ref_no')

PurchaseOrderItemFilter.base_filters['item_product_id_from'].label = 'รหัสสินค้าจาก'
PurchaseOrderItemFilter.base_filters['item_product_id_to'].label = 'ถึง'
PurchaseOrderItemFilter.base_filters['item_product_name'].label = 'ชื่อสินค้า'
PurchaseOrderItemFilter.base_filters['item_machine'].label = 'ใช้ในระบบงาน'
PurchaseOrderItemFilter.base_filters['start_created'].label = 'วันที่สั่งซื้อ'
PurchaseOrderItemFilter.base_filters['end_created'].label = 'ถึง'
PurchaseOrderItemFilter.base_filters['distributor'].label = 'ชื่อผู้จำหน่าย'
PurchaseOrderItemFilter.base_filters['stockman_user'].label = 'ผู้สั่งสินค้า'
PurchaseOrderItemFilter.base_filters['unit_price_min'].label = 'ราคาต่อหน่วยจาก'
PurchaseOrderItemFilter.base_filters['unit_price_max'].label = 'ถึง'
PurchaseOrderItemFilter.base_filters['category'].label = 'หมวดหมู่สินค้า'
PurchaseOrderItemFilter.base_filters['po_ref_no'].label = 'เลขที่ใบสั่ง'

class ComparisonPriceFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name="id", widget = TextInput(attrs={'size': 3 ,'class': 'numberinput' }))
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    organizer =  django_filters.ModelChoiceFilter(field_name="organizer", queryset= User.objects.filter(groups__name='จัดซื้อ'))
    select_bidder  = django_filters.CharFilter(field_name="select_bidder__name", lookup_expr='icontains')
    ref_no  = django_filters.CharFilter(field_name="ref_no", lookup_expr='icontains')

    class Meta:
        model = ComparisonPrice
        fields = ('id','organizer','created','approver_status','examiner_status')
        filter_overrides = {
                    models.CharField: {
                        'filter_class': django_filters.CharFilter,
                        'extra': lambda f: {
                            'lookup_expr': 'icontains',
                        },
                    },
                }

ComparisonPriceFilter.base_filters['id'].label = 'รหัส'
ComparisonPriceFilter.base_filters['ref_no'].label = 'รหัส'
ComparisonPriceFilter.base_filters['organizer'].label = 'ผู้จัดทำ'
ComparisonPriceFilter.base_filters['start_created'].label = 'วันที่สร้าง'
ComparisonPriceFilter.base_filters['end_created'].label = 'ถึง'
ComparisonPriceFilter.base_filters['approver_status'].label = 'ผู้อนุมัติ'
ComparisonPriceFilter.base_filters['examiner_status'].label = 'ผู้ตรวจสอบ'
ComparisonPriceFilter.base_filters['select_bidder'].label = 'ร้านที่เลือก'

class ReceiveFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name="id", widget = TextInput(attrs={'size': 3 ,'class': 'numberinput' }))
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))

    class Meta:
        model = Receive
        fields = ('id','ref_no','po__ref_no','po__distributor', 'po__credit','po__shipping','created')

ReceiveFilter.base_filters['id'].label = 'รหัส'
ReceiveFilter.base_filters['ref_no'].label = 'รหัส'
ReceiveFilter.base_filters['po__ref_no'].label = 'รหัสใบสั่งซื้อ'
ReceiveFilter.base_filters['start_created'].label = 'วันที่รับเข้า'
ReceiveFilter.base_filters['end_created'].label = 'ถึง'
ReceiveFilter.base_filters['po__distributor'].label = 'ผู้จำหน่าย'
ReceiveFilter.base_filters['po__credit'].label = 'เครดิต'

class RateDistributorFilter(django_filters.FilterSet):
    start_created = django_filters.DateFilter(field_name = "po__created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "po__created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    distributor_id_from  = django_filters.CharFilter(field_name="distributor__id", lookup_expr='gte')
    distributor_id_to  = django_filters.CharFilter(field_name="distributor__id", lookup_expr='lte')
    distributor  = django_filters.CharFilter(field_name="distributor__name", lookup_expr='icontains')
    organizer_user = django_filters.ModelChoiceFilter(field_name="organizer_user", queryset= User.objects.filter(groups__name='จัดซื้อ'))

    class Meta:
        model = RateDistributor
        fields = ('po__created', 'distributor_id_from','distributor__name','organizer_user',)

RateDistributorFilter.base_filters['start_created'].label = 'วันที่ประเมิน'
RateDistributorFilter.base_filters['end_created'].label = 'ถึง'
RateDistributorFilter.base_filters['distributor_id_from'].label = 'รหัสผู้จำหน่าย'
RateDistributorFilter.base_filters['distributor_id_to'].label = 'ถึง'
RateDistributorFilter.base_filters['distributor'].label = 'ชื่อผู้จำหน่าย'
RateDistributorFilter.base_filters['organizer_user'].label = 'ผู้ประเมิน'


class DistributorFilter(django_filters.FilterSet):
    distributor_id_from  = django_filters.CharFilter(field_name="id", lookup_expr='gte')
    distributor_id_to  = django_filters.CharFilter(field_name="id", lookup_expr='lte')
    distributor  = django_filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Distributor
        fields = ('distributor_id_from', 'distributor_id_to','distributor',)

DistributorFilter.base_filters['distributor_id_from'].label = 'รหัสผู้จำหน่าย'
DistributorFilter.base_filters['distributor_id_to'].label = 'ถึง'
DistributorFilter.base_filters['distributor'].label = 'ชื่อผู้จำหน่าย'

class InvoidFilter(django_filters.FilterSet):
    ref_no  = django_filters.CharFilter(field_name="ref_no", lookup_expr='icontains')
    bring_name = django_filters.CharFilter(field_name="bring_name__first_name", lookup_expr='icontains')
    payer_name = django_filters.ModelChoiceFilter(field_name="payer_name", queryset= User.objects.filter(groups__name='พัสดุ'))
    car = django_filters.ModelChoiceFilter(field_name="car", queryset= BaseCar.objects.filter().all())
    expense_dept = django_filters.ModelChoiceFilter(field_name="expense_dept", queryset= BaseExpenseDepartment.objects.filter().all())
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))

    class Meta:
        model = PurchaseOrder
        fields = ('ref_no', 'bring_name','payer_name','car','expense_dept', 'created')

InvoidFilter.base_filters['ref_no'].label = 'รหัส'
InvoidFilter.base_filters['bring_name'].label = 'ผู้เบิก'
InvoidFilter.base_filters['payer_name'].label = 'ผู้จ่าย'
InvoidFilter.base_filters['expense_dept'].label = 'แผนกค่าใช้จ่าย'
InvoidFilter.base_filters['start_created'].label = 'วันที่จ่าย'
InvoidFilter.base_filters['end_created'].label = 'ถึง'

class ExOESTNHFilter(django_filters.FilterSet):
    docnum  = django_filters.CharFilter(field_name="docnum", lookup_expr='icontains')
    remark = django_filters.CharFilter(field_name="remark", lookup_expr='icontains')
    start_created = django_filters.DateFilter(field_name = "docdat", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "docdat", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    depcod =  django_filters.CharFilter(field_name="depcod")
    depname = django_filters.CharFilter(method='filter_by_depname', label='แผนกคชจ.')

    def filter_by_depname(self, queryset, name, value):
        matching_depcodes = list(
            BaseExpenseDepartment.objects.filter(name__icontains=value).values_list('id', flat=True)
        )
        return queryset.filter(depcod__in=matching_depcodes)

    class Meta:
        model = ExOESTNH
        fields = ['docnum', 'remark','docdat']

ExOESTNHFilter.base_filters['docnum'].label = 'รหัส'
ExOESTNHFilter.base_filters['remark'].label = 'หมายเหตุ'
ExOESTNHFilter.base_filters['start_created'].label = 'วันที่จ่าย'
ExOESTNHFilter.base_filters['end_created'].label = 'ถึง'

class ExOEINVHFilter(django_filters.FilterSet):
    docnum  = django_filters.CharFilter(field_name="docnum", lookup_expr='icontains')
    cuscod = django_filters.CharFilter(field_name="cuscod", lookup_expr='icontains')
    cusnam = django_filters.CharFilter(field_name="cusnam", lookup_expr='icontains')
    start_created = django_filters.DateFilter(field_name = "docdate", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "docdate", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))

    class Meta:
        model = ExOEINVH
        fields = ('docnum', 'cuscod', 'docdate')

ExOEINVHFilter.base_filters['docnum'].label = 'รหัส'
ExOEINVHFilter.base_filters['cuscod'].label = 'รหัสลูกค้า'
ExOEINVHFilter.base_filters['cusnam'].label = 'ชื่อลูกค้า'
ExOEINVHFilter.base_filters['start_created'].label = 'วันที่จ่าย'
ExOEINVHFilter.base_filters['end_created'].label = 'ถึง'