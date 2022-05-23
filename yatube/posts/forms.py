from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст поста', 'group': 'Группа'}
        help_texts = {'text': 'Заполните содержание поста',
                      'group': 'Укажите группу'}

    def clean_subject(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Нужно заполнить текст поста!')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария'}
        help_texts = {'text': 'Заполните содержание комментария'}

    def clean_subject(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Нужно заполнить текст комментария!')
        return data
