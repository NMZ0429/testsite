from django import forms
from django.urls import reverse_lazy


class FileUploadableTextArea(forms.Textarea):
    """画像アップロード可能なテキストエリア"""

    class Media:
        js = ['diaries/csrf.js', 'diaries/upload.js']

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if 'class' in self.attrs:
            self.attrs['class'] += ' uploadable vLargeTextField'
        else:
            self.attrs['class'] = 'uploadable vLargeTextField'
        self.attrs['data-url'] = reverse_lazy('diaries:upload')
