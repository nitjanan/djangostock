import os
from django.contrib.auth import models
from django.contrib.auth.models import User
from django import forms
from django.db.models import fields
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.forms import fields, widgets, CheckboxSelectMultiple
from django.contrib.auth.forms import UserCreationForm
from stock.models import  BaseUrgency, Distributor, PurchaseOrder, PurchaseOrderItem, PurchaseRequisition, Requisition, RequisitionItem, PurchaseRequisition,UserProfile,ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor, Receive, ReceiveItem, BaseVisible, BranchCompanyBaseAdress, BaseAddress, PositionBasePermission, RateDistributor, Product, BasePOType, BaseRequisitionType, BaseExpenseDepartment, BaseRepairType, BaseCar, BaseBrokeType, BaseExpenses, BaseAgency, BaseCar, Maintenance, CarLogbook, BaseJobCarDep
from django.utils.translation import gettext_lazy as _
from django.forms import (formset_factory, modelformset_factory, inlineformset_factory)
from django.forms.widgets import ClearableFileInput
import string
from django.db.models import Q
from django_select2.forms import Select2Widget

class MyClearableFileInput(ClearableFileInput):
    initial_text = 'ไฟล์ปัจจุบัน'
    input_text = 'เปลี่ยนไฟล์'
    clear_checkbox_label = 'ลบไฟล์'


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, label='ชื่อจริง') # required=True คือบังคับให้กรอกทุกครั้ง
    last_name = forms.CharField(max_length=100, required=True, label='นามสกุล')
    email = forms.EmailField(max_length=250, help_text='example@gmail.com') #help_text='example@gmail.com' ข้อความตัวอย่างใน textbox

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username','email', 'password1', 'password2', 'is_superuser','is_staff') #สร้าง auto อ้างอิงจากฟิลด์ใน db 

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('position','department')

class RequisitionForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (RequisitionForm,self).__init__(*args,**kwargs)
        #เปลี่ยนการจัดกลุ่มเป็นแบบอื่นเพราะมีเคสที่ใช้เงื่อนไขนี้ไม่ได้
        #self.fields['name'] = forms.ModelChoiceField(label='ชื่อผู้ขอตั้งเบิก', queryset= User.objects.filter(userprofile__branch_company__code = request.session['company_code']))
        #self.fields['chief_approve_user_name'] = forms.ModelChoiceField(label='หัวหน้างาน', queryset= User.objects.filter(groups__name='หัวหน้างาน', userprofile__branch_company__code = request.session['company_code']))
        #self.fields['organizer'] = forms.ModelChoiceField(label='ส่งให้เจ้าหน้าที่จัดซื้อ', queryset= User.objects.filter(groups__name='จัดซื้อ', userprofile__branch_company__code = request.session['company_code']))
        
        #เปลี่ยนเป็นการค้นหาชื่อแทน
        # self.fields['name'] = forms.ModelChoiceField(label='ชื่อผู้ขอตั้งเบิก', queryset= User.objects.all())
        # self.fields['chief_approve_user_name'] = forms.ModelChoiceField(label='หัวหน้างาน', queryset= User.objects.filter(groups__name='หัวหน้างาน'))
        # self.fields['organizer'] = forms.ModelChoiceField(label='ส่งให้เจ้าหน้าที่จัดซื้อ', queryset= User.objects.filter(groups__name='จัดซื้อ', userprofile__branch_company__code = request.session['company_code']))

    name = forms.ModelChoiceField(
        queryset = User.objects.all(),
        label='ชื่อผู้ขอตั้งเบิก',
        required=True
    )

    chief_approve_user_name = forms.ModelChoiceField(
        queryset = User.objects.filter(groups__name='หัวหน้างาน'),
        label='หัวหน้างาน',
        required=True
    )

    rq_type = forms.ModelChoiceField(
        queryset=BaseRequisitionType.objects.filter(~Q(id = 4)),
        widget=forms.Select(attrs={'class': 'is-valid'}),
        label='ประเภทใบขอเบิก',
        required=True
    )
    repair_type = forms.ModelChoiceField(queryset = BaseRepairType.objects.all(), label='ประเภทการซ่อม', required=True)
    #car = forms.ModelChoiceField(queryset = BaseCar.objects.all(), label='เครื่องจักร/ทะเบียนรถ', required=True)
    
    car = forms.ModelChoiceField(
        queryset=BaseCar.objects.all(),
        label='ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน',
        widget=Select2Widget(),
        required=True,
    )
    

    expense_dept = forms.ModelChoiceField(queryset = BaseExpenseDepartment.objects.all(), label='แผนกค่าใช้จ่าย', required=True)
    urgency = forms.ModelChoiceField(queryset = BaseUrgency.objects.all(), label='ระดับความเร่งด่วน', required=True)

    expenses = forms.ModelMultipleChoiceField(
        label='ค่าใช้จ่าย',
        queryset=BaseExpenses.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'radio-inline list-unstyled'}),
        required=True
    )

    agency = forms.ModelChoiceField(queryset = BaseAgency.objects.all(), label='หน่วยงาน', required=True)

    class Meta:
        model = Requisition
        fields = ('name','chief_approve_user_name', 'branch_company', 'agency', 'expense_dept', 'rq_type', 'car', 'repair_type', 'broke_type', 'desired_date', 'urgency', 'mile', 'note', 'expenses', 'memorandum_pdf', 'ma_id', 'ma_ref_no') #สร้าง auto อ้างอิงจากฟิลด์ใน db , 'repair_type', 'car' 04-06-2024 เอาออกก่อน
        widgets = {
        'memorandum_pdf' : MyClearableFileInput,
        'branch_company': forms.HiddenInput(),
        'ma_id': forms.HiddenInput(),
        'ma_ref_no': forms.HiddenInput(),
        'desired_date': forms.DateInput(format=('%d/%m/%Y'), attrs={'class':'form-control', 'placeholder':'Select a date', 'type':'date', 'required':'True'}),
        'car': Select2Widget(attrs={'data-placeholder': 'Search by name or code'}),
        'note': forms.Textarea(attrs={'rows': 3,}),
        }
        labels = {
            'section': _('แผนก'),
            'urgency': _('ระดับความเร่งด่วน'),
            'memorandum_pdf': _('ใบบันทึกข้อความ'),
            'repair_type': _('ประเภทการซ่อม'),
            'car': _('เครื่องจักร/ทะเบียนรถ'),
            'broke_type': _('สาเหตุ'),
            'expense_dept': _('แผนกค่าใช้จ่าย'),
            'desired_date': _('วันที่ต้องการ'),
            'mile': _('*** เลขไมล์/เลขชั่วโมง'),
            'ma_ref_no': _('อ้างอิงเลขที่ใบแจ้งซ่อม'),
        }

class RequisitionItemForm(forms.ModelForm):
    class Meta:
        model = RequisitionItem
        fields = ('requisition_id', 'product_name', 'description', 'quantity','quantity_pr','quantity_take', 'machine','desired_date','unit','urgency','product') #สร้าง auto อ้างอิงจากฟิลด์ใน db
        widgets = {
        'desired_date': forms.DateInput(format=('%d/%m/%Y'), attrs={'class':'form-control', 'placeholder':'Select a date', 'type':'date'}),
        'description': forms.Textarea(attrs={'rows':4, 'cols':15}),
        'requisition_id': forms.HiddenInput(),
        }

RequisitionItemFormset = formset_factory(RequisitionItemForm)
RequisitionItemModelFormset = modelformset_factory(
    RequisitionItem,
    fields = ('product_name', 'description', 'quantity','quantity_take', 'machine','desired_date','unit','urgency'),
    extra=1,
    widgets = {
        'desired_date': forms.DateInput(format=('%d/%m/%Y'), attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date','style': 'width:55px'}),
        'description': forms.Textarea(attrs={'rows':1, 'cols':10}),
    }
)

class PurchaseRequisitionForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (PurchaseRequisitionForm,self).__init__(*args,**kwargs)
        self.fields['organizer'] = forms.ModelChoiceField(label='ส่งให้เจ้าหน้าที่จัดซื้อ', queryset= User.objects.filter(groups__name='จัดซื้อ', userprofile__branch_company__code = request.session['company_code']))
        position = PositionBasePermission.objects.filter(base_permission__codename='CAAPR', branch_company__code = request.session['company_code']).values('position_id')
        user_profile = UserProfile.objects.filter(position__in = position, branch_company__code = request.session['company_code']).values('user__id')
        self.fields['approver_user'] = forms.ModelChoiceField(label='ผู้อนุมัติใบขอซื้อ', queryset = User.objects.filter(id__in = user_profile))
        
        bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = request.session['company_code'])
        self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)

    class Meta:
       model = PurchaseRequisition 
       fields = ('note', 'branch_company', 'organizer', 'approver_user', 'address_company')
       widgets = {
        'branch_company': forms.HiddenInput(),
        'note': forms.Textarea(attrs={'rows': 3,}),
       }
       labels = {
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
        }
#ใบสั่งซื้อ
class PurchaseOrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       if self.instance.branch_company is not None:
           bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.instance.branch_company)
           self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)
           self.fields['approver_user'] = forms.ModelChoiceField(label='ผู้อนุมัติใบสั่งซื้อ', queryset= User.objects.filter(groups__name='ผู้อนุมัติ', userprofile__branch_company__code = self.instance.branch_company) , required=False)

    class Meta:
       model = PurchaseOrder
       fields = ('created','distributor','credit','shipping','vat_type', 'address_company', 'approver_user', 'due_receive_update', 'quotation_pdf', 'po_type',) #'po_type', 17-05-2024
       widgets = {
        'quotation_pdf' : MyClearableFileInput,
        'distributor': forms.HiddenInput(),#dataList
        'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        'due_receive_update' : forms.DateInput(attrs={'class':'form-control is-invalid', 'placeholder':'Select a date', 'type':'date', 'required':''}),
        'po_type': forms.RadioSelect(attrs={'class':'list-unstyled'}),
        }
       labels = {
            'created': _('วันที่สร้างใบสั่งซื้อ'),
            'distributor': _('ผู้จำหน่าย'),
            'credit': _('เครดิต'),
            'shipping': _('ขนส่งโดย'),
            'vat_type': _('ชนิดภาษี'),
            'stockman_user': _('เจ้าหน้าที่จัดซื้อ'),
            'quotation_pdf': _('ใบเสนอราคา'),
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
            'due_receive_update': _('วันที่กำหนดรับของ'),
            'po_type': _('ประเภทใบสั่งซื้อ'),
        }

class PurchaseOrderAddressCompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       if self.instance.branch_company is not None:
           bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.instance.branch_company)
           self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)

    class Meta:
       model = PurchaseOrder
       fields = ('address_company',)
       labels = {
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
        }

class PurchaseOrderCancelForm(forms.ModelForm):
    cancel_reason = forms.CharField(max_length=100, required=True, label='เหตุผลการยกเลิกรายการ')
    class Meta:
       model = PurchaseOrder
       fields = ('cancel_reason',)

class PurchaseOrderFromComparisonPriceForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (PurchaseOrderFromComparisonPriceForm,self).__init__(*args,**kwargs)
        bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = request.session['company_code'])
        self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)
        self.fields['approver_user'] = forms.ModelChoiceField(label='ผู้อนุมัติใบสั่งซื้อ', queryset= User.objects.filter(groups__name='ผู้อนุมัติ', userprofile__branch_company__code = request.session['company_code']), required=False)
        #self.fields['cp'] = forms.ModelChoiceField(label='เลขที่ใบเปรียบเทียบราคา', queryset=ComparisonPrice.objects.filter(select_bidder__isnull=False, po_ref_no = "", branch_company__code = request.session['company_code']))

    class Meta:
       model = PurchaseOrder
       fields = ('created','cp','shipping', 'address_company', 'approver_user', 'due_receive_update', 'po_type',) #'po_type', 17-05-2024
       widgets = {
        'cp': forms.HiddenInput(),
        'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        'due_receive_update' : forms.DateInput(attrs={'class':'form-control is-invalid', 'placeholder':'Select a date', 'type':'date', 'required':''}),
        'po_type': forms.RadioSelect(attrs={'class':'list-unstyled'}),
        }
       labels = {
            'shipping': _('ขนส่งโดย'),
            'created': _('วันที่สร้างใบสั่งซื้อ'),
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
            'due_receive_update': _('วันที่กำหนดรับของ'),
            'po_type': _('ประเภทใบสั่งซื้อ'),
        }


class PurchaseOrderPriceForm(forms.ModelForm):
    class Meta:
       model = PurchaseOrder
       fields = ('total_price','discount','total_after_discount','vat','amount','freight','note','delivery')
       widgets={
        'total_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'discount': forms.TextInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        'total_after_discount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'vat': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'amount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'freight': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        'note': forms.Textarea(attrs={'rows': 3,}),
        }
       labels = {
            'note': _('หมายเหตุ'),
            'delivery': _('สถานที่จัดส่ง'),
        } 

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
       model = PurchaseOrderItem
       fields = ('item','quantity','unit_price','price')

PurchaseOrderItemFormset = formset_factory(PurchaseOrderItemForm)
PurchaseOrderItemModelFormset = modelformset_factory(
    PurchaseOrderItem,
    fields=('item','quantity','unit_price','discount','price','unit','description'),
    extra=1,
    widgets={
        'item': forms.HiddenInput(attrs={'class': 'form-control item'}),#dataList
        'quantity': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control quantity'}),
        'unit_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control unit-price text-right'}),
        'discount': forms.TextInput(attrs={'placeholder':'0.00 ', 'class': 'form-control discount text-right'}),
        'price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control price text-right'}),
    }
)

# 16-01-2024 เปลี่ยน extra=1 เป็น extra=0
PurchaseOrderItemInlineFormset = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    fields=('id','item','quantity','unit_price','discount','price','unit','description'),
    extra=0,
    widgets={
        'item': forms.HiddenInput(attrs={'class': 'form-control item'}),#dataList
        'quantity': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control quantity'}),
        'unit_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control unit-price text-right'}),
        'discount': forms.TextInput(attrs={'placeholder':'0.00 ', 'class': 'form-control discount text-right'}),
        'price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control price text-right'}),
    }
    , can_delete=True
)

class PurchaseOrderReceiptForm(forms.ModelForm):
    class Meta:
       model = PurchaseOrder
       fields = ('receipt_pdf',)
       widgets = {
        'receipt_pdf' : MyClearableFileInput,
        }
       labels = {
            'receipt_pdf': _('ใบรับสินค้า'),
        }

class RequisitionMemorandumForm(forms.ModelForm):
    class Meta:
       model = Requisition
       fields = ('memorandum_pdf',)
       widgets = {
        'memorandum_pdf' : MyClearableFileInput,
        }
       labels = {
            'memorandum_pdf': _('เอกสารแนบ'),
        }

class PurchaseRequisitionAddressCompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       if self.instance.branch_company is not None:
           bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.instance.branch_company)
           self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)

    class Meta:
       model = PurchaseRequisition
       fields = ('address_company',)
       labels = {
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
        }

class PurchaseRequisitionOrganizerForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (PurchaseRequisitionOrganizerForm,self).__init__(*args,**kwargs)
        self.fields['organizer'] = forms.ModelChoiceField(label='ส่งให้เจ้าหน้าที่จัดซื้อ', queryset= User.objects.filter(groups__name='จัดซื้อ', userprofile__branch_company__code = request.session['company_code']))
    
    class Meta:
       model = PurchaseRequisition
       fields = ('organizer',)
       labels = {
            'organizer': _('ที่อยู่ตามจดทะเบียน'),
}

#ใบเปรียบเทียบราคา
class ComparisonPriceForm(forms.ModelForm):
    class Meta:
       model = ComparisonPrice
       fields = ('organizer','approver_status','examiner_status')
       widgets={
            'approver_status': forms.HiddenInput(),
            'examiner_status': forms.HiddenInput(),
       }  
       labels = {
            'organizer': _('ผู้จัดทำ'),
        }

class ComparisonPriceAddressCompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       if self.instance.branch_company is not None:
           bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.instance.branch_company)
           self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)
    
    class Meta:
       model = ComparisonPrice
       fields = ('address_company',)
       labels = {
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
        }

#แม่ ผู้จำหน่ายใบเปรียบเทียบราคา
class CPDForm(forms.Form):
    class Meta:
       model = ComparisonPriceDistributor
       fields = ('distributor','cp','credit')
       widgets={
            'cp': forms.HiddenInput()
        }   
       

#แม่
class CPDModelForm(forms.ModelForm):
    class Meta:
        model = ComparisonPriceDistributor
        fields = ('distributor','cp','total_price','discount','total_after_discount','vat','amount','credit','vat_type', 'freight', 'quotation_pdf')
        widgets={
            'cp': forms.HiddenInput(),
            'distributor' : forms.HiddenInput(),
            'total_price': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'discount': forms.TextInput(attrs={'placeholder':'0.00'}),
            'total_after_discount': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'vat': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'amount': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'freight': forms.NumberInput(attrs={'placeholder':'0.00'}),
            'quotation_pdf': MyClearableFileInput,
        }
        labels = {
            'distributor': _('ผู้จำหน่าย'),
            'total_price': _('รวม'),
            'discount': _('หักส่วนลด'),
            'total_after_discount': _('จำนวนเงินหลังหักส่วนลด'),
            'vat': _('ภาษีมูลค่าเพิ่ม 7%'),
            'vat_type': _('ชนิดภาษี'),
            'amount': _('รวมเป็นเงินทั้งสิ้น'),
            'credit': _('เครดิต'),
            'freight': _('ค่าขนส่ง'),
            'quotation_pdf': _('ใบเสนอราคา'),
        } 

#แม่
CPDFormset = formset_factory(CPDForm)
CPDModelFormset = modelformset_factory(
    ComparisonPriceDistributor,
    fields=('distributor','cp'),
    extra=3,
    labels = {
            'distributor': _('ผู้จำหน่าย'),
    } 
)

#ลูก สินค้าใบเปรียบเทียบราคา
CPitemFormset = modelformset_factory(
    ComparisonPriceItem,
    fields=('item','quantity','unit','brand','unit_price','discount','price','description'),
    widgets={
        'item': forms.HiddenInput(),#dataList
        'quantity': forms.NumberInput(attrs={}),
        'unit_price': forms.NumberInput(attrs={}),
        'discount': forms.TextInput(attrs={'placeholder':'0.00'}),
        'price': forms.NumberInput(attrs={}),
    },
    labels = {
        'item': _('สินค้า'),
    },
    extra=1
)

# 16-01-2024 เปลี่ยน extra=1 เป็น extra=0
CPitemInlineFormset = inlineformset_factory(
    ComparisonPriceDistributor,
    ComparisonPriceItem,
    fields=('item','quantity','unit','brand','unit_price','discount','price','description'),
    widgets={
        'item': forms.HiddenInput(),#dataList
        'quantity': forms.NumberInput(attrs={}),
        'unit_price': forms.NumberInput(attrs={}),
        'discount': forms.TextInput(attrs={'placeholder':'0.00'}),
        'price': forms.NumberInput(attrs={}),
    },
    labels = {
        'item': _('สินค้า'),
    },
    extra=0
    , can_delete=True
)

class CPSelectBidderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       if self.instance.branch_company is not None:
           bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.instance.branch_company)
           self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)

    class Meta:
       model = ComparisonPrice
       fields = ('select_bidder','base_spares_type','note', 'cm_type', 'address_company', 'examiner_user', 'approver_user', 'amount_diff')
       widgets={
            'select_bidder': forms.HiddenInput(),#dataList
            'base_spares_type': forms.RadioSelect(attrs={'class':'list-unstyled'}),
            'cm_type': forms.RadioSelect(attrs={'class':'list-unstyled'}),
            'amount_diff': forms.HiddenInput(),
            'note': forms.Textarea(attrs={'rows': 3,}),
       }
       labels = {
            'select_bidder': _('เลือกผู้จัดจำหน่าย'),
            'base_spares_type': _('ชนิดอะไหล่'),
            'cm_type': _('ประเภทใบเปรียบเทียบ'),
            'note': _('หมายเหตุ'),
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
            'amount_diff': _('ราคาส่วนต่าง/ส่วนลด'),
        }

#ใบรับสินค้า
class ReceiveForm(forms.ModelForm):
    po = forms.ModelChoiceField(label='เลขที่ใบสั่งซื้อ', queryset=PurchaseOrder.objects.filter(approver_status=2))
    class Meta:
       model = Receive
       fields = ('po','tax_invoice','receive_user')
       widgets={
            'receive_user': forms.HiddenInput(),
       }  
       labels = {
            'po': _('เลขที่ใบสั่งซื้อ'),
            'tax_invoice': _('เลขที่ใบกำกับภาษี'),
        }

class ReceivePriceForm(forms.ModelForm):
    class Meta:
       model = Receive
       fields = ('total_price','discount','total_after_discount','vat','amount','freight')
       widgets={
        'total_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        'discount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        'total_after_discount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        'vat': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        'amount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        'freight': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control', 'placeholder':'0.00'}),
        }

class ReceiveItemForm(forms.ModelForm):
    class Meta:
       model = ReceiveItem
       fields = ('item','quantity','unit_price','price')

ReceiveItemInlineFormset = inlineformset_factory(
    Receive,
    ReceiveItem,
    fields=('item','unit_price','price','quantity'),
    widgets={
        'item': forms.HiddenInput(),
        'unit_price': forms.NumberInput(attrs={}),
        'price': forms.NumberInput(attrs={}),
        'quantity': forms.HiddenInput(),
    },
    extra=1,
    max_num=1
)

class RateDistributorForm(forms.ModelForm):
    counsel = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows":"5"}), label='ข้อเสนอแนะ')
    class Meta:
        model = RateDistributor
        fields = ('distributor', 'price_rate','quantity_rate','service_rate','safety_rate','counsel')
        widgets={
                'distributor': forms.HiddenInput(),
                'price_rate': forms.HiddenInput(),
                'quantity_rate': forms.HiddenInput(),
                'service_rate': forms.HiddenInput(),
                'safety_rate': forms.HiddenInput(),
                'total_rate': forms.HiddenInput(),
            }
        

#new admin check error id 23-03-2023
def has_only_en(name):
    char_set = string.ascii_letters + string.digits + "-"
    return all((True if x in char_set else False for x in name))

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสสินค้าผิด ("+ str(id) +") มีตัวอักษรภาษาไทย ไม่สามารถบันทึกได้ กรุณาใส่รหัสสินค้าใหม่")
        if not id.isupper() and not id.replace('-', '').isdigit():  # Check if id contains only uppercase letters
            raise forms.ValidationError(u"รหัสสินค้าผิด ("+ str(id) +") ต้องเป็นตัวพิมพ์ใหญ่เท่านั้น ไม่สามารถบันทึกได้ กรุณาใส่รหัสสินค้าใหม่")
        if id.find('O-') != -1 : #เช็ค O- ในรหัส
            raise forms.ValidationError(u"รหัสสินค้าผิด XX-XO-001 ต้องเป็น XX-X0-001 (ขีดเอ็กซ์โอ ต้องเป็น ขีดเอ็กซ์ศูนย์) ไม่สามารถบันทึกได้ กรุณาใส่รหัสสินค้าใหม่")
        return cleaned_data
    
class BaseCarAdminForm(forms.ModelForm):
    class Meta:
        model = BaseCar
        fields = '__all__'

    def clean(self):
        cleaned_data = self.cleaned_data
        #ลบช่องว่างหน้าและหลัง
        code = cleaned_data.get('code').strip() if cleaned_data.get('code') else ''
        name = cleaned_data.get('name').strip() if cleaned_data.get('name') else ''
        
        hoen = has_only_en(code)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"code เครื่องจักร/ทะเบียนรถ/หน่วยงาน ผิด ("+ str(code) +") มีตัวอักษรภาษาไทย ไม่สามารถบันทึกได้ กรุณาใส่รหัสสินค้าใหม่")
        if not code.isupper():  #เช็คตัวอักษรพิมใหญ่
            raise forms.ValidationError(u"code เครื่องจักร/ทะเบียนรถ/หน่วยงาน ผิด ("+ str(code) +") ต้องเป็นตัวพิมพ์ใหญ่เท่านั้น ไม่สามารถบันทึกได้ กรุณาใส่รหัสสินค้าใหม่")
        
        cleaned_data['code'] = code
        cleaned_data['name'] = name
        return cleaned_data

#####################################################
#################### ใบแจ้งซ่อม #######################
#####################################################
LC_CHOICES =( 
    ("ซ่อมเอง", "ซ่อมเอง"), 
    ("ส่งซ่อมนอก", "ส่งซ่อมนอก"),
) 

BOOL_CHOICES = ((True, 'Yes'), (False, 'No'))

class MaintenanceForm(forms.ModelForm):
    repair_name = forms.ModelChoiceField(
        queryset = User.objects.all(),
        label='ช่างช่อม',
        required=False
    )
    chief_name = forms.ModelChoiceField(
        queryset = User.objects.filter(groups__name='หัวหน้างาน'),
        label='หัวช่างซ่อมบำรุง',
        required=True
    )
    contact_name = forms.ModelChoiceField(
        queryset = User.objects.all(),
        label='ผู้ติดต่อ',
        required=False
    )
    sender_name = forms.ModelChoiceField(
        queryset = User.objects.all(),
        label='ผู้จัดส่งงาน',
        required=False
    )
    location = forms.ChoiceField(choices = LC_CHOICES, label='สถานที่ซ่อม')
    is_complete = forms.TypedChoiceField(
                   coerce=lambda x: x == 'True',
                   choices=((True, 'ปิดสรุปได้ กลับมาใช้งานได้ปกติ'), (False, 'ปิดสรุปไม่ได้ เหตุผล')),
                   widget=forms.RadioSelect
                )

    class Meta:
       model = Maintenance
       fields = ('location', 'repair_type', 'repair_name', 'chief_name', 'chief_update', 'detail', 'repair_note', 'work_hour', 'force_day', 'force_hour', 'start_rp', 'end_rp', 'sum_up', 'ma_type', 'is_complete', 'fail_reason', 'distributor', 'amount','contact_name', 'sender_name', 'ma_pdf')
       widgets = {
         'distributor': forms.HiddenInput(),#dataList
         'detail': forms.Textarea(attrs={'rows': 3}),
         'repair_note': forms.Textarea(attrs={'rows': 3}),
         'sum_up': forms.Textarea(attrs={'rows': 5}),
         'chief_update': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
         'start_rp': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
         'end_rp': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
         'ma_type': forms.RadioSelect(attrs={'class': 'radio-inline list-unstyled'}),
         'fail_reason': forms.Textarea(attrs={'rows': 3, 'style': 'height: 70px;'}),
         'ma_pdf': MyClearableFileInput,
        }
       labels = {
            'location': _('สถานที่ซ่อม'),
            'distributor': _('ชื่อร้าน ส่งซ่อมนอก/ Sub-Contract'),
            'amount': _('ราคา'),
            'chief_update': _('วันที่ / เวลา'),
            'repair_type': _('ประเภทการซ่อม'),
            'ma_type':  _('ประเภทใบแจ้งซ่อม'),
        }

class MaintenanceAddressCompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       if self.instance.branch_company is not None:
           bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = self.instance.branch_company)
           self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)

    class Meta:
       model = Maintenance
       fields = ('address_company',)
       labels = {
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
        }

class CarLogbookForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (CarLogbookForm,self).__init__(*args,**kwargs)
        self.fields['car'].label_from_instance = lambda obj: f"{obj.code} : {obj.name}"  #มี car1 และ car2

    name = forms.ModelChoiceField(
        queryset = User.objects.all(),
        label='ชื่อ',
        required=True
    )    

    car = forms.ModelChoiceField(
        queryset=BaseCar.objects.all(),
        label='ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน',
        widget=Select2Widget(),
        required=True,
        to_field_name='id'
    )

    job1 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.all(), label='รายละเอียดงานที่ 1', required=True)
    job2 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.all(), label='รายละเอียดงานที่ 2', required=False)
    job3 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.all(), label='รายละเอียดงานที่ 3', required=False)
    job4 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.all(), label='รายละเอียดงานที่ 4', required=False)

    class Meta:
        model = CarLogbook
        fields = ('name', 'branch_company', 'car', 'image_mile', 'mile_start', 'mile_end'
                    , 'job1', 'start_job1', 'end_job1', 'exd_job1'
                    , 'job2', 'start_job2', 'end_job2', 'exd_job2'
                    , 'job3', 'start_job3', 'end_job3', 'exd_job3'
                    , 'job4', 'start_job4', 'end_job4', 'exd_job4'
                    , 'note', 'oil', 'gas', 'engine', 'hydraulic', 'grease') #สร้าง auto อ้างอิงจากฟิลด์ใน db , 'repair_type', 'car' 04-06-2024 เอาออกก่อน
        widgets = {
            'image_mile': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/*',   # only images
                    'capture': 'environment'  # open camera by default (on mobile)
                }
            ),
            'branch_company' : forms.HiddenInput(),
            'start_job1': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time','required': 'true'}),
            'end_job1': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time','required': 'true'}),

            'start_job2': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time',}),
            'end_job2': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time',}),

            'start_job3': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time',}),
            'end_job3': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time',}),

            'start_job4': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time',}),
            'end_job4': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time',}),
            'name': Select2Widget(attrs={
                'class': 'form-control django-select2',  # Bootstrap + select2 class
                'style': 'width: 100%;',  # ensures width fills container
            }),
            'car': Select2Widget(attrs={'data-placeholder': 'Search by name or code'}),
            'note': forms.Textarea(attrs={'rows': 3,}),
        }
        labels = {
            'name': _('ชื่อ'),
            'car': _('เครื่องจักร/ทะเบียนรถ'),
        }

class RoiCarLogbookForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (RoiCarLogbookForm,self).__init__(*args,**kwargs)

    name = forms.ModelChoiceField(
        queryset = User.objects.all(),
        label='ชื่อ',
        required=True
    )    

    car = forms.ModelChoiceField(
        queryset=BaseCar.objects.all(),
        label='ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน',
        widget=Select2Widget(),
        required=True,
    )

    job1 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.filter(car_dep = 4), label='สถานที่จัดส่งที่ 1', required=True)
    job2 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.filter(car_dep = 4), label='สถานที่จัดส่งที่ 2', required=False)
    job3 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.filter(car_dep = 4), label='สถานที่จัดส่งที่ 3', required=False)
    job4 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.filter(car_dep = 4), label='สถานที่จัดส่งที่ 4', required=False)
    job5 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.filter(car_dep = 4), label='สถานที่จัดส่งที่ 5', required=False)
    job6 = forms.ModelChoiceField(queryset = BaseJobCarDep.objects.filter(car_dep = 4), label='สถานที่จัดส่งที่ 6', required=False)

    class Meta:
        model = CarLogbook
        fields = ('name', 'branch_company', 'car', 'image_mile', 'mile_start', 'mile_end'
                  , 'mile_start_job1', 'mile_end_job1', 'job1'
                  , 'mile_start_job2', 'mile_end_job2', 'job2'
                  , 'mile_start_job3', 'mile_end_job3', 'job3'
                  , 'mile_start_job4', 'mile_end_job4', 'job4'
                  , 'mile_start_job5', 'mile_end_job5', 'job5'
                  , 'mile_start_job6', 'mile_end_job6', 'job6'
                  , 'note', 'oil', 'gas', 'engine', 'hydraulic', 'grease') #สร้าง auto อ้างอิงจากฟิลด์ใน db , 'repair_type', 'car' 04-06-2024 เอาออกก่อน
        widgets = {
            'image_mile': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/*',   # only images
                    'capture': 'environment'  # open camera by default (on mobile)
                }
            ),
            'branch_company' : forms.HiddenInput(),
            'name': Select2Widget(attrs={
                'class': 'form-control django-select2',  # Bootstrap + select2 class
                'style': 'width: 100%;',  # ensures width fills container
            }),
            'car': Select2Widget(attrs={'data-placeholder': 'Search by name or code'}),
            'note': forms.Textarea(attrs={'rows': 3,}),
        }
        labels = {
            'name': _('ชื่อ'),
            'car': _('เครื่องจักร/ทะเบียนรถ'),
        }


CAR_STATE_CHOICES = (
    ('', '----------'),
    ('สามารถทำการเคลื่อนย้ายได้', 'สามารถทำการเคลื่อนย้ายได้'),
    ('ไม่สามารถทำการเคลื่อนย้ายได้', 'ไม่สามารถทำการเคลื่อนย้ายได้'),
)

# create form Maintenance
class CrMaintenanceForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (CrMaintenanceForm,self).__init__(*args,**kwargs)
        self.fields['car'].label_from_instance = lambda obj: f"{obj.code} : {obj.name}"  #มี car1 และ car2

    name = forms.ModelChoiceField(
        queryset = User.objects.all(),
        label='ชื่อ',
        required=True
    )    

    car = forms.ModelChoiceField(
        queryset=BaseCar.objects.all(),
        label='ทะเบียนรถ/ เครื่องจักร/ หน่วยงาน',
        widget=Select2Widget(),
        required=True,
        to_field_name='id'
    )

    car_state = forms.ChoiceField(choices = CAR_STATE_CHOICES, label='สภาพรถ')

    class Meta:
        model = Maintenance
        fields = ('name', 'branch_company', 'car', 'mile', 'broke_reason', 'car_state'
                  , 'image1', 'image2', 'image3', 'image4', 'approve_status')
        widgets = {
            'image1': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/*',   # only images
                    'capture': 'environment'  # open camera by default (on mobile)
                }
            ),
            'image2': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/*',   # only images
                    'capture': 'environment'  # open camera by default (on mobile)
                }
            ),
            'image3': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/*',   # only images
                    'capture': 'environment'  # open camera by default (on mobile)
                }
            ),
            'image4': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/*',   # only images
                    'capture': 'environment'  # open camera by default (on mobile)
                }
            ),            
            'branch_company' : forms.HiddenInput(),
            'approve_status' : forms.HiddenInput(),
            'name': Select2Widget(attrs={
                'class': 'form-control django-select2',  # Bootstrap + select2 class
                'style': 'width: 100%;',  # ensures width fills container
            }),
            'car': Select2Widget(attrs={'data-placeholder': 'Search by name or code'}),
            'note': forms.Textarea(attrs={'rows': 3,}),
        }
        labels = {
            'name': _('ชื่อ'),
        }