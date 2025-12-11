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
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import(
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

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

    path('reset_password/',
     auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"),
     name="reset_password"),

    path('reset_password_sent/', 
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_sent.html"), 
        name="password_reset_done"),

    path('reset/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_form.html"), 
     name="password_reset_confirm"),

    path('reset_password_complete/', 
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_done.html"), 
        name="password_reset_complete"),

    path('search/',views.search,name="search"),
    path('orderHistory/',views.orderHistory,name="orderHistory"),
    path('order/<int:order_id>',views.viewOrder,name="orderDetails"),
    path('cart/thankyou',views.thankyou,name="thankyou"),

    path('requisition/',views.requisition,name="requisition"),
    path('requisition/all/',views.requisitionAll,name="requisitionAll"),
    path('requisition/create',views.createRequisition,name="createRequisition"),
    path('requisition/remove/<int:id>',views.removeRequisition,name="removeRequisition"),
    path('requisition/edit/<int:id>',views.editRequisition,name="editRequisition"),
    path('requisition/show/<int:requisition_id>/<int:mode>',views.showRequisition,name="showRequisition"),

    path('requisitionItem/create/<int:requisition_id>',views.createRequisitionItem,name="createRequisitionItem"),
    path('requisitionItem/remove/<int:item_id>',views.removeRequisitionItem,name="removeRequisitionItem"),
    path('requisitionItem/edit/<int:item_id>',views.editRequisitionItem,name="editRequisitionItem"),
    path('requisitionItem/view/<int:requisition_id>',views.crudRequisitionItemView,name="crudRequisitionItemView"),
    path('requisitionItem/crud/<int:requisition_id>', login_required(views.CrudView.as_view()), name='crud_ajax'),
    path('ajax/crud/create/<int:requisition_id>',  login_required(views.CreateCrudUser.as_view()), name='crud_ajax_create'),
    path('ajax/crud/update/<int:requisition_id>',  login_required(views.UpdateCrudUser.as_view()), name='crud_ajax_update'),
    path('ajax/crud/delete/',  views.DeleteCrudUser.as_view(), name='crud_ajax_delete'),
    path('requisitionItem/editAll/<int:requisition_id>', views.editAllRequisition, name='editAllRequisition'),

    path('purchaseRequisition/',views.viewPR,name="viewPR"),
    path('purchaseRequisition/prepare',views.preparePR,name="preparePR"),
    path('purchaseRequisition/create/<int:requisition_id>',views.createPR,name="createPR"),
    path('purchaseRequisition/remove/<int:pr_id>',views.removePR,name="removePR"),
    path('purchaseRequisition/edit/<int:pr_id>',views.editPR,name="editPR"),
    path('purchaseRequisition/create/CMorPO/<int:pr_id>',views.createCMorPO,name="createCMorPO"),
    path('purchaseRequisition/show/<int:pr_id>/<int:mode>',views.showPR,name="showPR"),
    path('purchaseRequisition/reApprove/<int:pr_id>',views.reApprovePR,name="reApprovePR"),
    path('purchaseRequisition/close/<int:pr_id>',views.closePR,name="closePR"),
    path('purchaseRequisition/reBuy/<int:pr_id>',views.reBuyPR,name="reBuyPR"),

    path('invoice/cu/<int:rq_id>',views.CUInvoiceAndItem,name="CUInvoiceAndItem"),

    path('purchaseRequisitionApprove/',views.viewPRApprove,name="viewPRApprove"),
    path('purchaseRequisitionApprove/edit/<int:pr_id>/<str:isFromHome>',views.editPRApprove,name="editPRApprove"),

    path('purchaseOrder/',views.viewPO,name="viewPO"),
    path('purchaseOrder/prepare',views.preparePO,name="preparePO"),
    path('purchaseOrder/create',views.createPO,name="createPO"),
    path('purchaseOrder/createFromComparePrice/<int:cp_id>',views.createPOFromComparisonPrice,name="createPOFromComparisonPrice"),
    path('purchaseOrder/edit/<int:po_id>',views.editPO,name="editPO"),
    path('purchaseOrder/editPOFromPR/<int:po_id>',views.editPOFromPR,name="editPOFromPR"),
    path('purchaseOrder/editPOFromComparison/<int:po_id>',views.editPOFromComparison,name="editPOFromComparison"),
    path('purchaseOrder/remove/<int:po_id>',views.removePO,name="removePO"),
    path('purchaseOrder/show/<int:po_id>/<int:mode>',views.showPO,name="showPO"),

    path('purchaseOrderItem/create/<int:po_id>',views.createPOItem,name="createPOItem"),
    path('purchaseOrderItem/edit/<int:po_id>/<str:isFromPR>/<str:isReApprove>',views.editPOItem,name="editPOItem"),
    path('purchaseOrderItem/createFromComparisonPrice/<int:po_id>',views.createPOItemFromComparisonPrice,name="createPOItemFromComparisonPrice"),

    path('purchaseOrderApprove/',views.viewPOApprove,name="viewPOApprove"),
    path('purchaseOrderApprove/edit/<int:po_id>/<str:isFromHome>',views.editPOApprove,name="editPOApprove"),

    path('comparePricePO/',views.viewComparePricePO,name="viewComparePricePO"),
    path('comparePricePO/prepare',views.prepareComparePricePO,name="prepareComparePricePO"),
    path('comparePricePO/create',views.createComparePricePO,name="createComparePricePO"),
    path('comparePricePO/edit/<int:cp_id>',views.editComparePricePO,name="editComparePricePO"),
    path('comparePricePO/remove/<int:cp_id>',views.removeComparePricePO,name="removeComparePricePO"),
    path('comparePricePO/print/<int:cp_id>',views.printComparePricePO,name="printComparePricePO"),
    path('comparePricePO/show/<int:cp_id>/<int:mode>',views.showComparePricePO,name="showComparePricePO"),

    path('comparePricePOItem/create/<int:cp_id>/<str:isReApprove>',views.createComparePricePOItem,name="createComparePricePOItem"),
    path('comparePricePOItem/edit/<int:cp_id>/<int:cpd_id>',views.editComparePricePOItem,name="editComparePricePOItem"),
    path('comparePricePOItem/editFromPR/<int:cp_id>/<int:cpd_id>',views.editComparePricePOItemFromPR,name="editComparePricePOItemFromPR"),
    path('comparePriceDistributor/remove/<int:cp_id>/<int:cpd_id>',views.removeComparePriceDistributor,name="removeComparePriceDistributor"),

    path('comparePricePOApprove/',views.viewCPApprove,name="viewCPApprove"),
    path('comparePricePOApprove/print/<int:cp_id>/<str:isFromHome>',views.printCPApprove,name="printCPApprove"),

    path('searchItemExpress', views.searchItemExpress, name="searchItemExpress"),
    path('setSessionCompany', views.setSessionCompany, name="setSessionCompany"),
    path('searchDataDistributor', views.searchDataDistributor, name="searchDataDistributor"),
    path('searchExaminerAndApproverUser', views.searchExaminerAndApproverUser, name="searchExaminerAndApproverUser"),
    path('setDataDistributor', views.setDataDistributor, name="setDataDistributor"),
    path('searchLastPoItem', views.searchLastPoItem, name="searchLastPoItem"),
    path('getRateDistributor', views.getRateDistributor, name="getRateDistributor"),
    path('searchRepairType', views.searchRepairType, name="searchRepairType"),
    path('searchExpenseDept', views.searchExpenseDept, name="searchExpenseDept"),
    path('setDataProductExpress', views.setDataProductExpress, name="setDataProductExpress"),

    path('receive/',views.viewReceive,name="viewReceive"),
    path('receive/create',views.createReceive,name="createReceive"),
    path('receive/remove/<int:rc_id>',views.removeReceive,name="removeReceive"),
    path('receive/show/<int:rc_id>',views.showReceive,name="showReceive"),
    path('receive/upload', views.uploadReceive,name="uploadReceive"),
    path('receive/confirmUpload', views.confirmUpload,name="confirmUpload"),

    path('receiveItem/edit/<int:rc_id>',views.editReceiveItem,name="editReceiveItem"),

    path('export/', views.export ,name="export"),

    path('history/requisition/',views.viewRequisitionHistory,name="viewRequisitionHistory"),
    path('history/maintenance/',views.viewMAHistory,name="viewMAHistory"),
    path('history/purchaseRequisition/',views.viewPRHistory,name="viewPRHistory"),
    path('history/purchaseOrder/',views.viewPOHistory,name="viewPOHistory"),
    path('history/comparePricePO/',views.viewComparePricePOHistory,name="viewComparePricePOHistory"),

    path('report/requisition/export/excel', views.exportExcelRQ, name='exportExcelRQ'),

    path('history/incomplete/requisition/',views.viewRequisitionHistoryIncomplete,name="viewRequisitionHistoryIncomplete"),
    path('history/incomplete/purchaseRequisition/',views.viewPRHistoryIncomplete,name="viewPRHistoryIncomplete"),
    path('history/incomplete/purchaseOrder/',views.viewPOHistoryIncomplete,name="viewPOHistoryIncomplete"),
    path('history/incomplete/comparePricePO/',views.viewComparePricePOHistoryIncomplete,name="viewComparePricePOHistoryIncomplete"),

    path('autocompalteDistributor/',views.autocompalteDistributor,name="autocompalteDistributor"),

    path('report/purchaseOrder/',views.viewPOReport,name="viewPOReport"),
    path('report/purchaseOrder/export/excel', views.exportExcelPO, name='exportExcelPO'),
    path('report/purchaseOrder/item',views.viewPOItemReport,name="viewPOItemReport"),
    path('report/RateDistributor/',views.viewRateDistributorReport,name="viewRateDistributorReport"),
    path('report/carLogBook/',views.viewCLReport,name="viewCLReport"),

    path('report/purchaseOrderToExpress/export/excel', views.exportExcelPOToExpress, name='exportExcelPOToExpress'),
    path('report/invoiceToExpress/export/excel', views.exportExcelIVToExpress, name='exportExcelIVToExpress'),

    path('rateDistributor/show/<str:pk>',views.showRateDistributor,name="showRateDistributor"),
    path('rateDistributor/export/excel',views.exportToExcelRateDistributor,name="exportToExcelRateDistributor"),

    path('report/purchaseOrderItem/export/excel/by/value', views.exportExcelSummaryByProductValue, name='exportExcelSummaryByProductValue'),
    path('report/purchaseOrderItem/export/excel/by/frequently', views.exportExcelSummaryByProductFrequently, name='exportExcelSummaryByProductFrequently'),
    path('report/purchaseOrderItem/export/excel/by/expense', views.exportExcelByExpense, name='exportExcelByExpense'),

    path('invoice/',views.viewInvoice,name="viewInvoice"),
    path('invoice/show/<int:iv_id>/<int:mode>',views.showInvoice,name="showInvoice"),
    path('invoice/remove/<int:iv_id>',views.removeInvoice,name="removeInvoice"),


    path('ex/invoice/old',views.viewExInvoice_old,name="viewExInvoice_old"),
    path('report/invoice/export/excel/by/expense', views.exportExcelByIVExpense, name='exportExcelByIVExpense'),
    path('report/invoice/export/excel/by/registration/repair', views.exportToExcelRegistrationAndRepair, name='exportToExcelRegistrationAndRepair'),
    path('report/invoice/export/excel/expenses/by/registration', views.exportToExcelAllExpensesRegistration, name='exportToExcelAllExpensesRegistration'),
    path('updateInvoiceFromExpress/',views.updateInvoiceFromExpress,name="updateInvoiceFromExpress"),


    path('ex/invoice/',views.viewExInvoice,name="viewExInvoice"),
    path('ex/oil/invoice',views.viewExOiInvoice,name="viewExOiInvoice"),
    path('ex/soc/',views.viewExSOC,name="viewExSOC"),
    path('ex/oil/soc/',views.viewExOiSOC,name="viewExOiSOC"),

    path('car-search/', views.car_search, name='car_search'),

    path('login/api/', views.LoginApiView.as_view(), name="login_api"),
    path('signup/api/', views.SignUpApiView.as_view(), name="signup_api"),

    path('jwt/create/', TokenObtainPairView.as_view(), name="jwt_create"),
    path('jwt/refresh/', TokenRefreshView.as_view(), name="token_refresh"),
    path('jwt/verify/', TokenVerifyView.as_view(), name="token_verify"),

    path('po/api/',views.apiOverviewPO,name="apiOverviewPO"),
    path('po/api/detail/<str:ref_no>/',views.detailPO,name="detailPO"),
    path('po/items/api/detail/<str:ref_no>/',views.detailPOItems,name="detailPOItems"),
    path('po/product/api/detail/<str:ref_no>/<str:prod_id>',views.detailPOProductItems,name="detailPOProductItems"),
    
    path('po/api/all/between/<str:start_date>/<str:end_date>/',views.allPO,name="allPO"),
    path('po/items/api/all/between/<str:start_date>/<str:end_date>/',views.allPOItems,name="allPOItems"),

    path('export/products/', views.export_products, name='export_products'),
    path('products/create_qr_code/', views.create_qr_code, name='create_qr_code'),

    path("api/maintenance_appsheet/", views.maintenance_appsheet, name="maintenance_appsheet"),
    path("api/maintenance_appsheet/update/", views.update_maintenance_appsheet, name="update_maintenance_appsheet"),

    path('maintenance/',views.viewMA,name="viewMA"),
    path('maintenance/show/<int:ma_id>/<int:mode>',views.showMA,name="showMA"),
    path('maintenance/edit/<int:ma_id>',views.editMA,name="editMA"),
    path('maintenance/cancel/<int:ma_id>',views.cancelMA,name="cancelMA"),
    path('maintenance/create/',views.createMA,name="createMA"),

    path('maintenanceApprove',views.viewMAApprove,name="viewMAApprove"),
    path('maintenanceApprove/edit/<int:ma_id>/<int:mode>',views.editMAApprove,name="editMAApprove"),

    path('autocompalte_maintenance/',views.autocompalte_maintenance,name="autocompalte_maintenance"),
    path('searchDataMaintenance', views.searchDataMaintenance, name="searchDataMaintenance"),

    path("api/carLogBook_appsheet/", views.carLogBook_appsheet, name="carLogBook_appsheet"),
    path("api/roi_carLogBook_appsheet/", views.roi_carLogBook_appsheet, name="roi_carLogBook_appsheet"),
    path('carLogBook/',views.viewCL,name="viewCL"),
    path('carLogBook/excel/daily',views.excelDailyCL,name="excelDailyCL"),
    path('carLogBook/create/',views.createCL,name="createCL"),
    path('carLogBook/roi/create/',views.createCLRoi,name="createCLRoi"),
    path('job_car_dep_autocomplete/',views.job_car_dep_autocomplete,name="job_car_dep_autocomplete"),
    path('searchExpenseDeptByJob/',views.searchExpenseDeptByJob,name="searchExpenseDeptByJob"),
    path('searchJobByCarDep/',views.searchJobByCarDep,name="searchJobByCarDep"),
    path('excelExpensesByCarLog/',views.excelExpensesByCarLog,name="excelExpensesByCarLog"),

    path("mobileMenu/", views.mobileMenu, name="mobileMenu"),

    path('car/api/',views.apiOverviewCar,name="apiOverviewCar"),
    path('car/api/all/',views.allCar,name="allCar"),

    path('driver/car/api/',views.apiOverviewDriverAndCar,name="apiOverviewDriverAndCar"),
    path('driver/car/api/all/',views.allDriverAndCar,name="allDriverAndCar"),

    path('searchPmRound/',views.searchPmRound,name="searchPmRound"),
]

if settings.DEBUG :
    #/media/product
    urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    #/static/
    urlpatterns+=static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
