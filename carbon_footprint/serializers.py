from rest_framework import serializers
from .models import (
    Campus, Period, EmissionCategory, EmissionSource, EmissionFactor,
    FuelType, WasteType, ExtinguisherType, PaperWeightCatalog,
    ElectricityConsumption, NaturalGasConsumption, FuelConsumption,
    VehicleFleetConsumption, ExtinguisherRefill, WasteRecord,
    PaperConsumption, WaterConsumption, Flight, GroundTransportRecord, LodgingRecord,
    FieldPracticeTrip, RemovalRecord, CalculationRun, CalculationSourceTrace
)


def validate_positive(value, field_name):
    if value is not None and value < 0:
        raise serializers.ValidationError(f"{field_name} debe ser un valor positivo.")
    return value

# =====================================================
# === SERIALIZERS BASE / CATÁLOGOS =====================
# =====================================================

class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ['id', 'name', 'city', 'locality', 'area_m2', 'notes']


class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ['id', 'year', 'month', 'start_date', 'end_date']


class EmissionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionCategory
        fields = ['id', 'code', 'name', 'description']


class EmissionSourceSerializer(serializers.ModelSerializer):
    category = EmissionCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionCategory.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = EmissionSource
        fields = ['id', 'category', 'category_id', 'code', 'name', 'unit_default']


class EmissionFactorSerializer(serializers.ModelSerializer):
    source = EmissionSourceSerializer(read_only=True)
    source_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionSource.objects.all(), source='source', write_only=True, required=False
    )
    source_code = serializers.CharField(source='source.code', read_only=True)

    class Meta:
        model = EmissionFactor
        fields = [
            'id', 'source', 'source_id', 'source_code', 'agent', 'gas', 'factor_value', 'unit',
            'source_ref', 'year_applic', 'gwp_100yr', 'uncertainty_pct'
        ]


class FuelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelType
        fields = ['fuel_code', 'description']


class WasteTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteType
        fields = ['waste_code', 'description']


class ExtinguisherTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtinguisherType
        fields = ['ext_code', 'description', 'gwp_100yr']


class PaperWeightCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperWeightCatalog
        fields = ['size', 'kg_per_ream']


# =====================================================
# === REGISTROS OPERATIVOS (CRUD) ======================
# =====================================================

class ElectricityConsumptionSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)
    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = ElectricityConsumption
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'description',
            'kwh', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_kwh(self, value):
        return validate_positive(value, 'kwh')


class NaturalGasConsumptionSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    fuel_type = FuelTypeSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)
    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    fuel_type_id = serializers.PrimaryKeyRelatedField(queryset=FuelType.objects.all(), source='fuel_type', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = NaturalGasConsumption
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'fuel_type', 'fuel_type_id',
            'm3', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]


class FuelConsumptionSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    fuel_type = FuelTypeSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    fuel_type_id = serializers.PrimaryKeyRelatedField(queryset=FuelType.objects.all(), source='fuel_type', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = FuelConsumption
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'description', 'fuel_type', 'fuel_type_id',
            'unit', 'amount', 'scope', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_amount(self, value):
        return validate_positive(value, 'amount')


class VehicleFleetConsumptionSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    fuel_type = FuelTypeSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    fuel_type_id = serializers.PrimaryKeyRelatedField(queryset=FuelType.objects.all(), source='fuel_type', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = VehicleFleetConsumption
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'description',
            'fuel_type', 'fuel_type_id', 'unit', 'amount', 'km_traveled',
            'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_amount(self, value):
        return validate_positive(value, 'amount')

    def validate_km_traveled(self, value):
        return validate_positive(value, 'km_traveled')


class ExtinguisherRefillSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    ext_type = ExtinguisherTypeSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    ext_type_id = serializers.PrimaryKeyRelatedField(queryset=ExtinguisherType.objects.all(), source='ext_type', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = ExtinguisherRefill
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'description',
            'ext_type', 'ext_type_id', 'unit', 'amount', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]


class WasteRecordSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    waste_type = WasteTypeSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    waste_type_id = serializers.PrimaryKeyRelatedField(queryset=WasteType.objects.all(), source='waste_type', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = WasteRecord
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'waste_type', 'waste_type_id',
            'unit', 'amount', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_amount(self, value):
        return validate_positive(value, 'amount')


class PaperConsumptionSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    size = PaperWeightCatalogSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    size_id = serializers.PrimaryKeyRelatedField(queryset=PaperWeightCatalog.objects.all(), source='size', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = PaperConsumption
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'size', 'size_id',
            'reams', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_reams(self, value):
        return validate_positive(value, 'reams')



class WaterConsumptionSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)
    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = WaterConsumption
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id', 'description',
            'm3', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_m3(self, value):
        return validate_positive(value, 'm3')


class FlightSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)
    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Flight
        fields = [
            'id', 'period', 'period_id', 'description', 'origin', 'destination',
            'passengers', 'km', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]


class FieldPracticeTripSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = FieldPracticeTrip
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id',
            'description', 'origin', 'destination', 'km_oneway', 'total_km',
            'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]


class RemovalRecordSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)

    class Meta:
        model = RemovalRecord
        fields = ['id', 'period', 'period_id', 'campus', 'campus_id', 'rtype', 'tco2e']

    def validate_tco2e(self, value):
        # Removals are stored as positive values; sign inversion happens at reporting layer.
        return validate_positive(value, 'tco2e')


class GroundTransportRecordSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = GroundTransportRecord
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id',
            'description', 'unit', 'amount', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_amount(self, value):
        return validate_positive(value, 'amount')


class LodgingRecordSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    emission_factor = EmissionFactorSerializer(read_only=True)

    period_id = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all(), source='period', write_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(queryset=Campus.objects.all(), source='campus', write_only=True)
    emission_factor_id = serializers.PrimaryKeyRelatedField(
        queryset=EmissionFactor.objects.all(), source='emission_factor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = LodgingRecord
        fields = [
            'id', 'period', 'period_id', 'campus', 'campus_id',
            'description', 'nights', 'emission_factor', 'emission_factor_id', 'total_tco2e'
        ]

    def validate_nights(self, value):
        return validate_positive(value, 'nights')


class CalculationSourceTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationSourceTrace
        fields = [
            'id', 'source_code', 'source_name', 'total_tco2e',
            'uncertainty_pct', 'warnings', 'traces'
        ]


class CalculationRunSerializer(serializers.ModelSerializer):
    period = PeriodSerializer(read_only=True)
    campus = CampusSerializer(read_only=True)
    source_traces = CalculationSourceTraceSerializer(many=True, read_only=True)

    class Meta:
        model = CalculationRun
        fields = [
            'id', 'period', 'campus', 'method_profile', 'include_traces',
            'gross_tco2e', 'removals_tco2e', 'net_tco2e', 'uncertainty_pct',
            'warnings', 'created_at', 'source_traces'
        ]
