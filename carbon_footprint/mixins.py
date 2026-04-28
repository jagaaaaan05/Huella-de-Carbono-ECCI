class PeriodCampusFilterMixin:
    """Optional period/campus filters for operational record endpoints."""

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        period_id = params.get('period_id')
        campus_id = params.get('campus_id')

        if period_id and hasattr(queryset.model, 'period_id'):
            queryset = queryset.filter(period_id=period_id)

        if campus_id and hasattr(queryset.model, 'campus_id'):
            queryset = queryset.filter(campus_id=campus_id)

        return queryset
