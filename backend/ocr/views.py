import os
import pytesseract
from googletrans import Translator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.conf import settings
import threading
import time
from uuid import uuid4

# In-memory store for file processing status and results
processing_store = {}

def process_file(file_path, result_key):
    try:
        # Perform OCR on the image
        text = pytesseract.image_to_string(file_path)
        print("OCR result:", text)  #

        # Translate the text
        translator = Translator()
        translated_text = translator.translate(text, src='en', dest='fr').text
        print("Translation result:", translated_text) 

        # Save the translated text to a file
        processed_file_path = file_path + '.txt'
        with open(processed_file_path, 'w') as f:
            f.write(translated_text)

        processing_store[result_key]['status'] = 'completed'
        processing_store[result_key]['file_path'] = processed_file_path

    except Exception as e:
        print("Error during processing:", str(e))  
        processing_store[result_key]['status'] = 'failed'
        processing_store[result_key]['error'] = str(e)

class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, format=None):
        print("Request data:", request.data)
        print("Request files:", request.FILES)

        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES['file']
        file_name = str(uuid4())
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name) 
        default_storage.save(file_path, ContentFile(file_obj.read()))

        result_key = str(uuid4())
        processing_store[result_key] = {'status': 'processing', 'file_path': None}

        # Start background processing thread
        threading.Thread(target=process_file, args=(file_path, result_key)).start()

        return Response({'id': result_key}, status=status.HTTP_201_CREATED)

class CheckStatusView(APIView):
    def get(self, request, pk, format=None):
        result = processing_store.get(pk)
        if result:
            return Response({'status': result['status']})
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

class DownloadFileView(APIView):
    def get(self, request, pk, format=None):
        result = processing_store.get(pk)
        if result and result['status'] == 'completed':
            file_path = result['file_path']
            try:
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
            except FileNotFoundError:
                return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)