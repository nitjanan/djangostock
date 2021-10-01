from django.contrib.auth import models
from django.contrib.auth.models import User
from django import forms
from django.forms import fields
from django.contrib.auth.forms import UserCreationForm
from stock.models import  PurchaseOrder, PurchaseOrderItem, PurchaseRequisition, Requisition, RequisitionItem, PurchaseRequisition,UserProfile,ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor
from django.utils.translation import gettext_lazy as _
from django.forms import (formset_factory, modelformset_factory, inlineformset_factory)

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True) # required=True คือบังคับให้กรอกทุกครั้ง
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=250, help_text='example@gmail.com') #help_text='example@gmail.com' ข้อความตัวอย่างใน textbox

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username','email', 'password1', 'password2','is_superuser','is_staff') #สร้าง auto อ้างอิงจากฟิลด์ใน db 

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('position',)

class RequisitionForm(forms.ModelForm):
    class Meta:
        model = Requisition
        fields = ('name', 'section','chief_approve_user_name','supplies_approve_user_name','urgency') #สร้าง auto อ้างอิงจากฟิลด์ใน db
        widgets = {
        'urgency': forms.HiddenInput(),
        }
        labels = {
            'name': _('ชื่อผู้ขอตั้งเบิก'),
            'section': _('แผนก'),
            'chief_approve_user_name': _('หัวหน้างาน'),
            'supplies_approve_user_name': _('เจ้าหน้าที่พัสดุ'),
            'urgency': _('ระดับความเร่งด่วน'),
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

class PurchaseRequisitionForm(forms.ModelForm):
    class Meta:
       model = PurchaseRequisition 
       fields = ('note',)

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
       model = PurchaseOrder
       fields = ('distributor','credit','shipping','vat_type','stockman_user','approver_status')
       widgets = {
        'approver_status': forms.HiddenInput(),
        }
       labels = {
            'distributor': _('ผู้จำหน่าย'),
            'credit': _('เครดิต'),
            'shipping': _('ขนส่งโดย'),
            'vat_type': _('ชนิดภาษี'),
            'stockman_user': _('เจ้าหน้าที่จัดซื้อ'),
        }

class PurchaseOrderFromComparisonPriceForm(forms.ModelForm):
    cp = forms.ModelChoiceField(label='เลขที่ใบเปรียบเทียบราคา', queryset=ComparisonPrice.objects.filter(select_bidder__isnull=False))
    class Meta:
       model = PurchaseOrder
       fields = ('cp','shipping')
       labels = {
            'shipping': _('ขนส่งโดย'),
        }  


class PurchaseOrderPriceForm(forms.ModelForm):
    class Meta:
       model = PurchaseOrder
       fields = ('total_price','discount','total_after_discount','vat','amount')
       widgets={
        'total_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'discount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'total_after_discount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'vat': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        'amount': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control','value':'0.00', 'placeholder':'0.00'}),
        }

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
       model = PurchaseOrderItem
       fields = ('item','quantity','unit_price','price')

PurchaseOrderItemFormset = formset_factory(PurchaseOrderItemForm)
PurchaseOrderItemModelFormset = modelformset_factory(
    PurchaseOrderItem,
    fields=('item','quantity','unit_price','price','unit'),
    extra=1,
    widgets={
        'item': forms.HiddenInput(attrs={'class': 'form-control item'}),#dataList
        'quantity': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control quantity','value':'0', 'placeholder':'0'}),
        'unit_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control unit-price','value':'0.00', 'placeholder':'0.00'}),
        'price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control price','value':'0.00', 'placeholder':'0.00'}),
    }
)
PurchaseOrderItemInlineFormset = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    fields=('id','item','quantity','unit_price','price','unit'),
    extra=1,
    widgets={
        'item': forms.HiddenInput(attrs={'class': 'form-control item'}),#dataList
        'quantity': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control quantity','value':'0', 'placeholder':'0'}),
        'unit_price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control unit-price','value':'0.00', 'placeholder':'0.00'}),
        'price': forms.NumberInput(attrs={'size': 3 ,'class': 'form-control price','value':'0.00', 'placeholder':'0.00'}),
    }
    , can_delete=True
)

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
        fields = ('distributor','cp','total_price','discount','total_after_discount','vat','amount','credit','vat_type')
        widgets={
            'cp': forms.HiddenInput(),
            'total_price': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'discount': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'total_after_discount': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'vat': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
            'amount': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
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
    fields=('item','quantity','unit','brand','unit_price','price'),
    widgets={
        'item': forms.HiddenInput(),#dataList
        'quantity': forms.NumberInput(attrs={'value':'0', 'placeholder':'0'}),
        'unit_price': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
        'price': forms.NumberInput(attrs={'value':'0.00', 'placeholder':'0.00'}),
    },
    labels = {
        'item': _('สินค้า'),
    },
    extra=1
)

CPitemInlineFormset = inlineformset_factory(
    ComparisonPriceDistributor,
    ComparisonPriceItem,
    fields=('item','quantity','unit','brand','unit_price','price'),
    widgets={
        'item': forms.HiddenInput(),#dataList
    },
    labels = {
        'item': _('สินค้า'),
    },
    extra=1
    , can_delete=True
)

class CPSelectBidderForm(forms.ModelForm):
    class Meta:
       model = ComparisonPrice
       fields = ('select_bidder','base_spares_type','note')
       widgets={
            'select_bidder': forms.HiddenInput(),#dataList
            'base_spares_type': forms.RadioSelect(attrs={'class':'list-unstyled'}),
       }
       labels = {
            'select_bidder': _('เลือกผู้จัดจำหน่าย'),
            'base_spares_type': _('ชนิดอะไหล่'),
            'note': _('หมายเหตุ'),
        }