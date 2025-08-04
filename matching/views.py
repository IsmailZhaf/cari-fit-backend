    # apps/jobmatching/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import JobRecommendation
from .serializers import JobRecommendationSerializer

class JobRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permission_classes = [IsAuthenticated]
        
        user = request.user
        limit = request.query_params.get('limit')
        recommendations = JobRecommendation.objects.filter(user=user)

        if limit is not None:
            try:
                limit = int(limit)
                recommendations = recommendations[:limit]
            except ValueError:
                return Response({"error": "Limit must be an integer"}, status=400)  

        if not recommendations.exists():
            return Response({"message": "No job recommendations for this user"}, status=404)

        serializer = JobRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)

    
    
