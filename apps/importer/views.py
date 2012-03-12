import urllib

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse

from apps.flashcards.models import (Deck, FactType, CardTemplate, Card,
                                   FieldContent, FieldType, Fact)


@login_required
def importer(request):
    context = {}

    if request.method == 'POST':
        import_facts = []
        lines = request.POST['facts'].split('\n')
        for line in lines:
            if not line.strip():
                continue

            fields = line.split('\t')
            import_facts.append({
                request.POST['col0']: fields[0],
                request.POST['col1']: fields[1],
                request.POST['col2']: fields[2],
            })

        if not len(import_facts):
            query = ''
            if request.POST['deck_name'].strip():
                query = '?' + urllib.urlencode({
                    'deck_name': request.POST['deck_name'],
                })
            return redirect(reverse('importer.views.importer') + query)

        # Now let's import it all.
        
        deck = Deck.objects.create(
            name=request.POST['deck_name'],
            owner=request.user,
        )

        fact_type = FactType.objects.japanese

        card_templates = []
        card_template_names = ['recognition', 'production',
                               'kanji_reading', 'kanji_writing']
        for template in card_template_names:
            if request.POST.get(template) == 'on':
                card_templates.append(getattr(CardTemplate.objects, template))

        for import_fact in import_facts:
            fact = Fact(
                deck=deck,
                fact_type=fact_type,
            )
            fact.save()

            for field_name, text in import_fact.iteritems():
                field_type = getattr(FieldType.objects, field_name)
                content = FieldContent(
                    fact=fact,
                    field_type=field_type,
                    content=text,
                )
                content.save()

            for template in card_templates:
                card = Card.objects.create(
                    fact=fact,
                    template=template,
                )
                card.randomize_new_order()

        context.update({
            'cards_created': deck.card_count,
            'deck': deck,
        })
    return render_to_response('importer/importer.html', context,
        context_instance=RequestContext(request))


