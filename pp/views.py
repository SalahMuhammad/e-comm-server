from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json


class ProfitPercentage(APIView):
    json_file_path = 'pp/profitPercentage.json'

    def get_data(self):
        with open(self.json_file_path, 'r') as file:
            data = json.load(file)
        return data
    
    def get(self, request, format=None):
        data = self.get_data()
        return Response(data)

    def post(self, request, format=None):
        data = request.data
        try:
            if (float(data['price2'])) and (float(data['price3'])) and (float(data['price4'])):
                new_data = request.data
                with open(self.json_file_path, 'w') as file:
                    json.dump(new_data, file)

                message = 'تم تحديث البيانات بنجاح'
                return Response({'detail': message}, status=status.HTTP_201_CREATED)
        except Exception as e:
            Response({'detail': f'{e}'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'قيم غير صالحه...'}, status=status.HTTP_400_BAD_REQUEST)
