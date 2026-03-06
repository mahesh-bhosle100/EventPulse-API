from django.urls import path
from .views import EventListCreateView, EventDetailView, CategoryListView, EventReviewListCreateView

urlpatterns = [
    path('', EventListCreateView.as_view(), name='event_list_create'),
    path('<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('<int:event_id>/reviews/', EventReviewListCreateView.as_view(), name='event_reviews'),
]
