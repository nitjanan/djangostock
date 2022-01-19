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
    distributor  = django_filters.CharFilter(field_name="distributor__name", lookup_expr='icontains')
    ref_no  = django_filters.CharFilter(field_name="ref_no", lookup_expr='icontains')
    stockman_user = django_filters.ModelChoiceFilter(field_name="stockman_user", queryset= User.objects.filter(groups__name='จัดซื้อ'))

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