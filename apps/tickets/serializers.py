from rest_framework import serializers
from .models import TicketType


class TicketTypeSerializer(serializers.ModelSerializer):
    available_quantity = serializers.ReadOnlyField()
    sold_count = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = TicketType
        fields = [
            'id', 'event', 'name', 'ticket_type', 'description',
            'price', 'total_quantity', 'available_quantity',
            'sold_count', 'is_available', 'sale_start', 'sale_end',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'event']

    def validate(self, attrs):
        if attrs.get('sale_start') and attrs.get('sale_end'):
            if attrs['sale_end'] <= attrs['sale_start']:
                raise serializers.ValidationError('sale_end must be after sale_start')
        price = attrs.get('price')
        if price is not None and price < 0:
            raise serializers.ValidationError('price must be zero or greater')
        total_quantity = attrs.get('total_quantity')
        if total_quantity is not None and total_quantity <= 0:
            raise serializers.ValidationError('total_quantity must be greater than 0')
        return attrs
