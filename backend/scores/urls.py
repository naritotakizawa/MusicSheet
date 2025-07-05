from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScoreViewSet, PartViewSet, NoteViewSet

router = DefaultRouter()
router.register(r'scores', ScoreViewSet)
router.register(r'parts', PartViewSet)
router.register(r'notes', NoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
