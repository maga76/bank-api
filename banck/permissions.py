from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'account'):
            return obj.account.user == request.user
        if hasattr(obj, 'sender'):
            return obj.sender.user == request.user or obj.reciver.user == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
