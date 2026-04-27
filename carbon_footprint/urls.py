from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

router = DefaultRouter()
# Catálogos base
router.register(r'campus', views.CampusViewSet)
router.register(r'periods', views.PeriodViewSet)
router.register(r'emission-categories', views.EmissionCategoryViewSet)
router.register(r'emission-sources', views.EmissionSourceViewSet)
router.register(r'emission-factors', views.EmissionFactorViewSet)

# Catálogos auxiliares
router.register(r'fuel-types', views.FuelTypeViewSet)
router.register(r'waste-types', views.WasteTypeViewSet)
router.register(r'extinguisher-types', views.ExtinguisherTypeViewSet)
router.register(r'paper-weight', views.PaperWeightCatalogViewSet)

# Registros operativos
router.register(r'electricity', views.ElectricityConsumptionViewSet)
router.register(r'natural-gas', views.NaturalGasConsumptionViewSet)
router.register(r'fuel', views.FuelConsumptionViewSet)
router.register(r'vehicle-fleet', views.VehicleFleetConsumptionViewSet)
router.register(r'extinguisher-refill', views.ExtinguisherRefillViewSet)
router.register(r'waste', views.WasteRecordViewSet)
router.register(r'paper', views.PaperConsumptionViewSet)
router.register(r'flights', views.FlightViewSet)
router.register(r'ground-transport', views.GroundTransportRecordViewSet)
router.register(r'lodging', views.LodgingRecordViewSet)
router.register(r'field-practice', views.FieldPracticeTripViewSet)
router.register(r'removals', views.RemovalRecordViewSet)
router.register(r'calculation-runs-history', views.CalculationRunHistoryViewSet, basename='calculation-runs-history')

urlpatterns = router.urls + [
	path('calculation-runs/', views.CalculationRunView.as_view(), name='calculation-runs'),
]
