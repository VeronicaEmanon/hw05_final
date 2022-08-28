from django.contrib import admin

from .models import Group, Post, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description',)
    list_filter = ('title',)
    search_fields = ('text',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'author', 'post',)
    list_filter = ('post',)
    search_filter = ('text',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'user',)
    list_filter = ('user',)
    search_filter = ('author',)

admin.site.register(Post, PostAdmin)

admin.site.register(Group, GroupAdmin)

admin.site.register(Comment, CommentAdmin)

admin.site.register(Follow, FollowAdmin)
