from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.middleware.csrf import get_token
from django.db import transaction



from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .mixins import PeriodCampusFilterMixin
from .models import (
    Campus, Period, EmissionCategory, EmissionSource, EmissionFactor,
    FuelType, WasteType, ExtinguisherType, PaperWeightCatalog,
    ElectricityConsumption, NaturalGasConsumption, FuelConsumption,
    VehicleFleetConsumption, ExtinguisherRefill, WasteRecord,
    PaperConsumption, Flight, GroundTransportRecord, LodgingRecord,
    FieldPracticeTrip, RemovalRecord, CalculationRun, CalculationSourceTrace
)
from .serializers import (
    CampusSerializer, PeriodSerializer, EmissionCategorySerializer,
    EmissionSourceSerializer, EmissionFactorSerializer, FuelTypeSerializer,
    WasteTypeSerializer, ExtinguisherTypeSerializer, PaperWeightCatalogSerializer,
    ElectricityConsumptionSerializer, NaturalGasConsumptionSerializer,
    FuelConsumptionSerializer, VehicleFleetConsumptionSerializer,
    ExtinguisherRefillSerializer, WasteRecordSerializer, PaperConsumptionSerializer, FlightSerializer,
    GroundTransportRecordSerializer, LodgingRecordSerializer,
    FieldPracticeTripSerializer, RemovalRecordSerializer,
    CalculationRunSerializer
)
from .engine.calculation_service import calculate_inventory_run
from .engine.gases_catalog import DEFAULT_METHOD_PROFILE


# =====================================================
# === BASE CONFIGURATION ===============================
# =====================================================

@require_GET
def dashboard(request):
    """Renderiza la interfaz principal del prototipo."""
    # Garantiza que el token CSRF se emita para peticiones POST subsecuentes
    get_token(request)

    return render(request, 'carbon_footprint/dashboard.html')


class BasePermissionViewSet(viewsets.ModelViewSet):
    """Base viewset con permisos básicos y configuración común."""
    permission_classes = [permissions.AllowAny]
    # Nota: para entornos productivos con autenticación, cambiar a IsAuthenticated.


# =====================================================
# === CATÁLOGOS Y CONFIGURACIÓN ========================
# =====================================================

class CampusViewSet(BasePermissionViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer


class PeriodViewSet(BasePermissionViewSet):
    queryset = Period.objects.all()
    serializer_class = PeriodSerializer


class EmissionCategoryViewSet(BasePermissionViewSet):
    queryset = EmissionCategory.objects.all()
    serializer_class = EmissionCategorySerializer


class EmissionSourceViewSet(BasePermissionViewSet):
    queryset = EmissionSource.objects.select_related('category').all()
    serializer_class = EmissionSourceSerializer


class EmissionFactorViewSet(BasePermissionViewSet):
    queryset = EmissionFactor.objects.select_related('source', 'source__category').all()
    serializer_class = EmissionFactorSerializer

    def get_queryset(self):
        queryset = self.queryset
        params = self.request.query_params

        source_code = params.get('source_code')
        source_id = params.get('source_id')
        year_applic = params.get('year_applic')
        gas = params.get('gas')

        if source_code:
            queryset = queryset.filter(source__code=source_code)
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        if year_applic:
            queryset = queryset.filter(year_applic=year_applic)
        if gas:
            queryset = queryset.filter(gas__iexact=gas)

        return queryset


class CalculationRunHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Historical persisted calculation runs for audit and traceability."""

    permission_classes = [permissions.AllowAny]
    queryset = CalculationRun.objects.select_related('period', 'campus').prefetch_related('source_traces').all()
    serializer_class = CalculationRunSerializer

    def get_queryset(self):
        queryset = self.queryset
        params = self.request.query_params

        period_id = params.get('period_id')
        campus_id = params.get('campus_id')
        created_from = params.get('created_from')
        created_to = params.get('created_to')
        ordering = params.get('ordering')

        if period_id:
            queryset = queryset.filter(period_id=period_id)
        if campus_id:
            queryset = queryset.filter(campus_id=campus_id)
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)
        if ordering in ('created_at', '-created_at', 'net_tco2e', '-net_tco2e'):
            queryset = queryset.order_by(ordering)

        return queryset


# =====================================================
# === CATÁLOGOS AUXILIARES =============================
# =====================================================

class FuelTypeViewSet(BasePermissionViewSet):
    queryset = FuelType.objects.all()
    serializer_class = FuelTypeSerializer


class WasteTypeViewSet(BasePermissionViewSet):
    queryset = WasteType.objects.all()
    serializer_class = WasteTypeSerializer


class ExtinguisherTypeViewSet(BasePermissionViewSet):
    queryset = ExtinguisherType.objects.all()
    serializer_class = ExtinguisherTypeSerializer


class PaperWeightCatalogViewSet(BasePermissionViewSet):
    queryset = PaperWeightCatalog.objects.all()
    serializer_class = PaperWeightCatalogSerializer


# =====================================================
# === REGISTROS OPERATIVOS (CRUD PRINCIPALES) ==========
# =====================================================

class ElectricityConsumptionViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = ElectricityConsumption.objects.select_related('campus', 'period').all()
    serializer_class = ElectricityConsumptionSerializer


class NaturalGasConsumptionViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = NaturalGasConsumption.objects.select_related('campus', 'period').all()
    serializer_class = NaturalGasConsumptionSerializer


class FuelConsumptionViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = FuelConsumption.objects.select_related('campus', 'period', 'fuel_type').all()
    serializer_class = FuelConsumptionSerializer


class VehicleFleetConsumptionViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = VehicleFleetConsumption.objects.select_related('campus', 'period', 'fuel_type').all()
    serializer_class = VehicleFleetConsumptionSerializer


class ExtinguisherRefillViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = ExtinguisherRefill.objects.select_related('campus', 'period', 'ext_type').all()
    serializer_class = ExtinguisherRefillSerializer


class WasteRecordViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = WasteRecord.objects.select_related('campus', 'period', 'waste_type').all()
    serializer_class = WasteRecordSerializer


class PaperConsumptionViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = PaperConsumption.objects.select_related('campus', 'period', 'size').all()
    serializer_class = PaperConsumptionSerializer





class FlightViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = Flight.objects.select_related('period').all()
    serializer_class = FlightSerializer


class FieldPracticeTripViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = FieldPracticeTrip.objects.select_related('campus', 'period').all()
    serializer_class = FieldPracticeTripSerializer


class RemovalRecordViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = RemovalRecord.objects.select_related('campus', 'period').all()
    serializer_class = RemovalRecordSerializer


class GroundTransportRecordViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = GroundTransportRecord.objects.select_related('campus', 'period').all()
    serializer_class = GroundTransportRecordSerializer


class LodgingRecordViewSet(PeriodCampusFilterMixin, BasePermissionViewSet):
    queryset = LodgingRecord.objects.select_related('campus', 'period').all()
    serializer_class = LodgingRecordSerializer


class CalculationRunView(APIView):
    """Backend-first, auditable inventory calculation endpoint."""

    permission_classes = [permissions.AllowAny]

    @staticmethod
    def _parse_bool(value, default=True):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ('true', '1', 'yes', 'si', 'on'):
                return True
            if normalized in ('false', '0', 'no', 'off'):
                return False
        return default

    def post(self, request):
        period_id = request.data.get('period_id')
        campus_id = request.data.get('campus_id')
        method_profile = request.data.get('method_profile', DEFAULT_METHOD_PROFILE)
        include_traces = request.data.get('include_traces', True)

        if period_id is None:
            return Response(
                {'detail': 'period_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            period_id = int(period_id)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'period_id must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if campus_id in (None, ''):
            campus_id = None
        else:
            try:
                campus_id = int(campus_id)
            except (TypeError, ValueError):
                return Response(
                    {'detail': 'campus_id must be an integer when provided.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        period_obj = Period.objects.filter(id=period_id).first()
        if not period_obj:
            return Response(
                {'detail': 'period_id does not exist.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        campus_obj = None
        if campus_id is not None:
            campus_obj = Campus.objects.filter(id=campus_id).first()
            if not campus_obj:
                return Response(
                    {'detail': 'campus_id does not exist.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        result = calculate_inventory_run(
            period_id=period_id,
            campus_id=campus_id,
            method_profile=method_profile,
            include_traces=self._parse_bool(include_traces, default=True),
        )

        with transaction.atomic():
            run = CalculationRun.objects.create(
                period=period_obj,
                campus=campus_obj,
                method_profile=method_profile,
                include_traces=self._parse_bool(include_traces, default=True),
                gross_tco2e=result['totals']['gross_tco2e'],
                removals_tco2e=result['totals']['removals_tco2e'],
                net_tco2e=result['totals']['net_tco2e'],
                uncertainty_pct=result['totals']['uncertainty_pct'],
                warnings=result.get('warnings') or [],
            )
            for source in result.get('sources', []):
                CalculationSourceTrace.objects.create(
                    run=run,
                    source_code=source.get('source_code') or '',
                    source_name=source.get('source_name') or '',
                    total_tco2e=source.get('total_tco2e') or 0,
                    uncertainty_pct=source.get('uncertainty_pct') or 0,
                    warnings=source.get('warnings') or [],
                    traces=source.get('traces') or [],
                )

        result['run_id'] = run.id
        return Response(result, status=status.HTTP_200_OK)

