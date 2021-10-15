"""djangostock URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from stock import views
from django.conf.urls.static import static
from django.conf import settings
from stock import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name="home"),
    path('category/<slug:category_slug>',views.index,name="product_by_category"), # category/fashion ส่งค่า slug ไปด้วยเพื่อกำหมวดหมู่สินค้า และตั้งชื่อเราท์ name = xxx
    path('product/<slug:category_slug>/<slug:product_slug>',views.productPage,name="productDetail"), # product/fashion/shoes
    path('cart/add/<int:product_id>',views.addCart,name="addCart"),
    path('cartdetail',views.cartdetail, name="cartdetail"),
    path('cart/remove/<int:product_id>',views.removeCart,name="removeCart"), #ลบ cart_item ต้องหา id cart และ  id cart_item
    path('account/create',views.signUpView,name="signUp"),
    path('account/login',views.signInView,name="signIn"),
    path('account/logout',views.signOutView,name="signOut"),
    path('search/',views.search,name="search"),
    path('orderHistory/',views.orderHistory,name="orderHistory"),
    path('order/<int:order_id>',views.viewOrder,name="orderDetails"),
    path('cart/thankyou',views.thankyou,name="thankyou"),

    path('requisition/',views.requisition,name="requisition"),
    path('requisition/all/',views.requisitionAll,name="requisitionAll"),
    path('requisition/create',views.createRequisition,name="createRequisition"),
    path('requisition/remove/<int:id>',views.removeRequisition,name="removeRequisition"),
    path('requisition/edit/<int:id>',views.editRequisition,name="editRequisition"),
    path('requisition/show/<int:requisition_id>',views.showRequisition,name="showRequisition"),

    path('requisitionItem/create/<int:requisition_id>',views.createRequisitionItem,name="createRequisitionItem"),
    path('requisitionItem/remove/<int:item_id>',views.removeRequisitionItem,name="removeRequisitionItem"),
    path('requisitionItem/edit/<int:item_id>',views.editRequisitionItem,name="editRequisitionItem"),
    path('requisitionItem/view/<int:requisition_id>',views.crudRequisitionItemView,name="crudRequisitionItemView"),
    path('requisitionItem/crud/<int:requisition_id>',  views.CrudView.as_view(), name='crud_ajax'),
    path('ajax/crud/create/<int:requisition_id>',  views.CreateCrudUser.as_view(), name='crud_ajax_create'),
    path('ajax/crud/update/<int:requisition_id>',  views.UpdateCrudUser.as_view(), name='crud_ajax_update'),
    path('ajax/crud/delete/',  views.DeleteCrudUser.as_view(), name='crud_ajax_delete'),
    path('requisitionItem/editAll/<int:requisition_id>',  views.editAllRequisition, name='editAllRequisition'),

    path('purchaseRequisition/',views.viewPR,name="viewPR"),
    path('purchaseRequisition/prepare',views.preparePR,name="preparePR"),
    path('purchaseRequisition/create/<int:requisition_id>',views.createPR,name="createPR"),
    path('purchaseRequisition/remove/<int:pr_id>',views.removePR,name="removePR"),
    path('purchaseRequisition/edit/<int:pr_id>',views.editPR,name="editPR"),
    path('purchaseRequisition/create/CMorPO/<int:pr_id>',views.createCMorPO,name="createCMorPO"),
    path('purchaseRequisition/show/<int:pr_id>/<str:isAP>',views.showPR,name="showPR"),

    path('purchaseRequisitionApprove/',views.viewPRApprove,name="viewPRApprove"),
    path('purchaseRequisitionApprove/edit/<int:pr_id>',views.editPRApprove,name="editPRApprove"),

    path('purchaseOrder/',views.viewPO,name="viewPO"),
    path('purchaseOrder/prepare',views.preparePO,name="preparePO"),
    path('purchaseOrder/create',views.createPO,name="createPO"),
    path('purchaseOrder/createFromComparePrice',views.createPOFromComparisonPrice,name="createPOFromComparisonPrice"),
    path('purchaseOrder/edit/<int:po_id>',views.editPO,name="editPO"),
    path('purchaseOrder/editPOFromPR/<int:po_id>',views.editPOFromPR,name="editPOFromPR"),
    path('purchaseOrder/editPOFromComparison/<int:po_id>',views.editPOFromComparison,name="editPOFromComparison"),
    path('purchaseOrder/remove/<int:po_id>',views.removePO,name="removePO"),
    path('purchaseOrder/show/<int:po_id>/<str:isAP>',views.showPO,name="showPO"),

    path('purchaseOrderItem/create/<int:po_id>',views.createPOItem,name="createPOItem"),
    path('purchaseOrderItem/edit/<int:po_id>/<str:isFromPR>',views.editPOItem,name="editPOItem"),
    path('purchaseOrderItem/createFromComparisonPrice/<int:po_id>',views.createPOItemFromComparisonPrice,name="createPOItemFromComparisonPrice"),

    path('purchaseOrderApprove/',views.viewPOApprove,name="viewPOApprove"),
    path('purchaseOrderApprove/edit/<int:po_id>',views.editPOApprove,name="editPOApprove"),

    path('comparePricePO/',views.viewComparePricePO,name="viewComparePricePO"),
    path('comparePricePO/prepare',views.prepareComparePricePO,name="prepareComparePricePO"),
    path('comparePricePO/create',views.createComparePricePO,name="createComparePricePO"),
    path('comparePricePO/edit/<int:cp_id>',views.editComparePricePO,name="editComparePricePO"),
    path('comparePricePO/remove/<int:cp_id>',views.removeComparePricePO,name="removeComparePricePO"),
    path('comparePricePO/print/<int:cp_id>',views.printComparePricePO,name="printComparePricePO"),
    path('comparePricePO/show/<int:cp_id>/<str:isAP>',views.showComparePricePO,name="showComparePricePO"),

    path('comparePricePOItem/create/<int:cp_id>',views.createComparePricePOItem,name="createComparePricePOItem"),
    path('comparePricePOItem/edit/<int:cp_id>/<int:cpd_id>',views.editComparePricePOItem,name="editComparePricePOItem"),
    path('comparePricePOItem/editFromPR/<int:cp_id>/<int:cpd_id>',views.editComparePricePOItemFromPR,name="editComparePricePOItemFromPR"),
    path('comparePriceDistributor/remove/<int:cp_id>/<int:cpd_id>',views.removeComparePriceDistributor,name="removeComparePriceDistributor"),

    path('comparePricePOApprove/',views.viewCPApprove,name="viewCPApprove"),
    path('comparePricePOApprove/print/<int:cp_id>',views.printCPApprove,name="printCPApprove"),

    path('searchItemExpress', views.searchItemExpress, name="searchItemExpress"),

]

if settings.DEBUG :
    #/media/product
    urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    #/static/
    urlpatterns+=static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
