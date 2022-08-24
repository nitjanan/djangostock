import os
from django.contrib.auth import models
from django.contrib.auth.models import User
from django import forms
from django.db.models import fields
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.forms import fields, widgets, CheckboxSelectMultiple
from django.contrib.auth.forms import UserCreationForm
from stock.models import  BaseUrgency, Distributor, PurchaseOrder, PurchaseOrderItem, PurchaseRequisition, Requisition, RequisitionItem, PurchaseRequisition,UserProfile,ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor, Receive, ReceiveItem, BaseVisible, BranchCompanyBaseAdress, BaseAddress
from django.utils.translation import gettext_lazy as _
from django.forms import (formset_factory, modelformset_factory, inlineformset_factory)
from django.forms.widgets import ClearableFileInput

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
        self.fields['chief_approve_user_name'] = forms.ModelChoiceField(label='หัวหน้างาน', queryset= User.objects.filter(groups__name='หัวหน้างาน'))
        self.fields['organizer'] = forms.ModelChoiceField(label='ส่งให้เจ้าหน้าที่จัดซื้อ', queryset= User.objects.filter(groups__name='จัดซื้อ', userprofile__branch_company__code = request.session['company_code']))

    class Meta:
        model = Requisition
        fields = ('name','chief_approve_user_name','organizer','urgency', 'memorandum_pdf','branch_company') #สร้าง auto อ้างอิงจากฟิลด์ใน db
        widgets = {
        'urgency': forms.HiddenInput(),
        'name': forms.HiddenInput(),
        'memorandum_pdf' : MyClearableFileInput,
        'branch_company': forms.HiddenInput(),
        }
        labels = {
            'section': _('แผนก'),
            'urgency': _('ระดับความเร่งด่วน'),
            'memorandum_pdf': _('ใบบันทึกข้อความ'),
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

    class Meta:
       model = PurchaseRequisition 
       fields = ('note', 'branch_company', 'organizer')
       widgets = {
        'branch_company': forms.HiddenInput(),
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
       fields = ('ref_no','created','distributor','credit','shipping','vat_type', 'address_company', 'approver_user', 'quotation_pdf')
       widgets = {
        'quotation_pdf' : MyClearableFileInput,
        'distributor': forms.HiddenInput(),#dataList
        'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        }
       labels = {
            'ref_no': _('รหัสใบสั่งซื้อ'),
            'created': _('วันที่สร้างใบสั่งซื้อ'),
            'distributor': _('ผู้จำหน่าย'),
            'credit': _('เครดิต'),
            'shipping': _('ขนส่งโดย'),
            'vat_type': _('ชนิดภาษี'),
            'stockman_user': _('เจ้าหน้าที่จัดซื้อ'),
            'quotation_pdf': _('ใบเสนอราคา'),
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
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

class PurchaseOrderFromComparisonPriceForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (PurchaseOrderFromComparisonPriceForm,self).__init__(*args,**kwargs)
        bc = BranchCompanyBaseAdress.objects.filter(branch_company__code = request.session['company_code'])
        self.fields['address_company'].queryset = BaseAddress.objects.filter(id__in=bc)
        self.fields['approver_user'] = forms.ModelChoiceField(label='ผู้อนุมัติใบสั่งซื้อ', queryset= User.objects.filter(groups__name='ผู้อนุมัติ', userprofile__branch_company__code = request.session['company_code']), required=False)
        #self.fields['cp'] = forms.ModelChoiceField(label='เลขที่ใบเปรียบเทียบราคา', queryset=ComparisonPrice.objects.filter(select_bidder__isnull=False, po_ref_no = "", branch_company__code = request.session['company_code']))

    class Meta:
       model = PurchaseOrder
       fields = ('ref_no','created','cp','shipping', 'address_company', 'approver_user')
       widgets = {
        'cp': forms.HiddenInput(),
        'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        }
       labels = {
            'shipping': _('ขนส่งโดย'),
            'ref_no': _('รหัสใบสั่งซื้อ'),
            'created': _('วันที่สร้างใบสั่งซื้อ'),
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
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
    fields=('item','quantity','unit_price','price','unit','description'),
    extra=1,
    widgets={
        'item': forms.HiddenInput(attrs={'class': 'form-control item'}),#dataList
        'quantity': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control quantity'}),
        'unit_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control unit-price'}),
        'price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control price'}),
    }
)

PurchaseOrderItemInlineFormset = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    fields=('id','item','quantity','unit_price','price','unit','description'),
    extra=1,
    widgets={
        'item': forms.HiddenInput(attrs={'class': 'form-control item'}),#dataList
        'quantity': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control quantity'}),
        'unit_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control unit-price'}),
        'price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control price'}),
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
    fields=('item','quantity','unit','brand','unit_price','price','description'),
    widgets={
        'item': forms.HiddenInput(),#dataList
        'quantity': forms.NumberInput(attrs={}),
        'unit_price': forms.NumberInput(attrs={}),
        'price': forms.NumberInput(attrs={}),
    },
    labels = {
        'item': _('สินค้า'),
    },
    extra=1
)

CPitemInlineFormset = inlineformset_factory(
    ComparisonPriceDistributor,
    ComparisonPriceItem,
    fields=('item','quantity','unit','brand','unit_price','price','description'),
    widgets={
        'item': forms.HiddenInput(),#dataList
        'quantity': forms.NumberInput(attrs={}),
        'unit_price': forms.NumberInput(attrs={}),
        'price': forms.NumberInput(attrs={}),
    },
    labels = {
        'item': _('สินค้า'),
    },
    extra=1
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
       fields = ('select_bidder','base_spares_type','note', 'cm_type', 'address_company')
       widgets={
            'select_bidder': forms.HiddenInput(),#dataList
            'base_spares_type': forms.RadioSelect(attrs={'class':'list-unstyled'}),
            'cm_type': forms.RadioSelect(attrs={'class':'list-unstyled'}),
       }
       labels = {
            'select_bidder': _('เลือกผู้จัดจำหน่าย'),
            'base_spares_type': _('ชนิดอะไหล่'),
            'cm_type': _('ประเภทใบเปรียบเทียบ'),
            'note': _('หมายเหตุ'),
            'address_company': _('ที่อยู่ตามจดทะเบียน'),
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