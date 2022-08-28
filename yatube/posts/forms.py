from django import forms

from .models import Post, Comment
from django.utils.translation import ugettext_lazy as _


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
