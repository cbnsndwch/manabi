from django.shortcuts import get_object_or_404
from rest_framework import permissions

from manabi.apps.flashcards.models import Deck


class DeckSynchronizationPermission(permissions.BasePermission):
    message = "You don't have permission to add this deck to your library."

    def has_permission(self, request, view):
        if view.action in ['create', 'update']:
            upstream_deck = get_object_or_404(
                Deck, pk=request.data['synchronized_with'])
            return upstream_deck.shared

        return True
