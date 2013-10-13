import datetime
import random

from cachecow.decorators import cached_function
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db import transaction
from django.db.models import Avg
from django.forms import ModelForm
from django.forms.util import ErrorList
from manabi.apps.utils.managers import manager_from

from manabi.apps.manabi_redis.models import redis
from manabi.apps.books.models import Textbook
from constants import DEFAULT_EASE_FACTOR
from constants import GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY
from manabi.apps.flashcards.cachenamespaces import deck_review_stats_namespace
from manabi.apps.flashcards.models.intervals import initial_interval
from itertools import chain
import cards
from manabi.apps import usertagging


class _DeckManager(object):
    def of_user(self, user):
        return self.filter(owner=user, active=True)

    def shared_decks(self):
        return self.filter(shared=True, active=True)

    def synchronized_decks(self, user):
        return self.filter(owner=user, synchronized_with__isnull=False)

DeckManager = manager_from(_DeckManager)


class Deck(models.Model):
    #manager
    objects = DeckManager()

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=2000, blank=True)
    owner = models.ForeignKey(User, db_index=True)

    textbook_source = models.ForeignKey(Textbook, null=True, blank=True)

    picture = models.FileField(upload_to='/deck_media/', null=True, blank=True) 
    #TODO upload to user directory, using .storage

    priority = models.IntegerField(default=0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    # whether this is a publicly shared deck
    shared = models.BooleanField(default=False, blank=True)
    shared_at = models.DateTimeField(null=True, blank=True)
    # or if not, whether it's synchronized with a shared deck
    synchronized_with = models.ForeignKey('self',
            null=True, blank=True, related_name='subscriber_decks')

    # "active" is just a soft deletion flag. "suspended" is temporarily 
    # disabled.
    suspended = models.BooleanField(default=False, db_index=True) 
    active = models.BooleanField(default=True, blank=True, db_index=True)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name, self.owner)
    
    class Meta:
        app_label = 'flashcards'
        ordering = ('name',)
        #TODO unique_together = (('owner', 'name'), )
    
    def get_absolute_url(self):
        return reverse('deck_detail', kwargs={'deck_id': self.id})

    def delete(self, *args, **kwargs):
        # You shouldn't delete a shared deck - just set active=False
        self.subscriber_decks.clear()
        super(Deck, self).delete(*args, **kwargs)

    def fact_tags(self):
        '''
        Returns tags for all facts inside this deck.
        Includes tags on facts made on subscribed facts.
        '''
        #return usertagging.models.Tag.objects.usage_for_queryset(
            #self.facts())
        from facts import Fact
        deck_facts = Fact.objects.with_upstream(
            self.owner, deck=self)
        return usertagging.models.Tag.objects.usage_for_queryset(
            deck_facts)

    #def facts(self):
    #    '''Returns all Facts for this deck,
    #    including subscribed ones, not including subfacts.
    #    '''
    #    from fields import FieldContent
    #    if self.synchronized_with:
    #        updated_fields = FieldContent.objects.filter(fact__deck=self, fact__active=True, fact__synchronized_with__isnull=False) #fact__in=self.subscriber_facts.all())
    #        # 'other' here means non-updated, subscribed
    #        other_facts = Fact.objects.filter(parent_fact__isnull=True, id__in=updated_fields.values_list('fact', flat=True))
    #        other_fields = FieldContent.objects.filter(fact__deck=self.synchronized_with).exclude(fact__active=True, fact__in=other_facts.values_list('synchronized_with', flat=True))
    #        #active_subscribers = active_subscribers | other_fields
    #        return updated_fields | other_fields
    #    else:
    #        return FieldContent.objects.filter(fact__deck=self, fact__active=True)

    def field_contents(self):
        '''
        Returns all FieldContents for facts in this deck,
        preferring updated subscriber fields to subscribed ones,
        when the deck is synchronized.
        '''
        from fields import FieldContent
        if self.synchronized_with:
            updated_fields = FieldContent.objects.filter(
                    fact__deck=self, fact__active=True,
                    fact__synchronized_with__isnull=False) 
            #fact__in=self.subscriber_facts.all())
            # 'other' here means non-updated, subscribed
            other_facts = Fact.objects.filter(
                    parent_fact__isnull=True,
                    id__in=updated_fields.values_list('fact', flat=True))
            other_fields = FieldContent.objects.filter(
                    fact__deck=self.synchronized_with
                    ).exclude(fact__active=True,
                              fact__in=other_facts.values_list(
                                    'synchronized_with', flat=True))
            return updated_fields | other_fields
        else:
            return FieldContent.objects.filter(
                    fact__deck=self, fact__active=True)

    @property
    def has_subscribers(self):
        '''
        Returns whether there are subscribers to this deck, because
        it is shared, or it had been shared before.
        '''
        return self.subscriber_decks.filter(active=True).exists()

    @transaction.commit_on_success    
    def share(self):
        '''
        Shares this deck publicly.
        '''
        if self.synchronized_with:
            raise TypeError('Cannot share synchronized decks (decks which are already synchronized with shared decks).')
        self.shared = True
        self.shared_at = datetime.datetime.utcnow()
        self.save()

    @transaction.commit_on_success
    def unshare(self):
        '''
        Unshares this deck.
        '''
        if not self.shared:
            raise TypeError('This is not a shared deck, so it cannot be unshared.')
        self.shared = False
        self.save()

    def get_subscriber_deck_for_user(self, user):
        '''
        Returns the subscriber deck for `user` of this deck.
        If it doesn't exist, returns None.
        If multiple exist, even though this shouldn't happen,
        we just return the first one.
        '''
        subscriber_decks = self.subscriber_decks.filter(owner=user, active=True)
        if subscriber_decks.exists():
            return subscriber_decks[0]

    @transaction.commit_on_success    
    def subscribe(self, user):
        '''
        Subscribes to this shared deck for the given user.
        They will study this deck as their own, but will 
        still receive updates to content.

        Returns the newly created deck.

        If the user was already subscribed to this deck, 
        returns the existing deck.
        '''
        from facts import Fact

        # check if the user is already subscribed to this deck
        subscriber_deck = self.get_subscriber_deck_for_user(user)
        if subscriber_deck:
            return subscriber_deck

        if not self.shared:
            raise TypeError('This is not a shared deck - cannot subscribe to it.')
        if self.synchronized_with:
            raise TypeError('Cannot share a deck that is already synchronized to a shared deck.')

        #TODO dont allow multiple subscriptions to same deck by same user
        
        # copy the deck
        deck = Deck(
            synchronized_with=self,
            name=self.name,
            description=self.description,
            #TODO implement textbook=shared_deck.textbook, #picture too...
            priority=self.priority,
            textbook_source=self.textbook_source,
            owner_id=user.id)
        deck.save()

        # copy the tags
        deck.tags = usertagging.utils.edit_string_for_tags(self.tags)

        # copy the facts - just the first few as a buffer
        shared_fact_to_fact = {}
        #TODO dont hardcode value here #chain(self.fact_set.all(), Fact.objects.filter(parent_fact__deck=self)):
        for shared_fact in self.fact_set.filter(active=True, parent_fact__isnull=True).order_by('new_fact_ordinal')[:10]: 
            #FIXME get the child facts for this fact too
            #if shared_fact.parent_fact:
            #    #child fact
            #    fact = Fact(
            #        fact_type=shared_fact.fact_type,
            #        active=shared_fact.active) #TODO should it be here?
            #    fact.parent_fact = shared_fact_to_fact[shared_fact.parent_fact]
            #    fact.save()
            #else:
            #   #regular fact
            fact = Fact(
                deck=deck,
                fact_type_id=shared_fact.fact_type_id,
                synchronized_with=shared_fact,
                active=True, #shared_fact.active, #TODO should it be here?
                priority=shared_fact.priority,
                new_fact_ordinal=shared_fact.new_fact_ordinal,
                notes=shared_fact.notes)
            fact.save()
            shared_fact_to_fact[shared_fact] = fact

            # don't copy the field contents for this fact - we'll get them from 
            # the shared fact later

            # copy the cards
            for shared_card in shared_fact.card_set.filter(active=True):
                card = shared_card.copy(fact)
                card.save()
        #done!
        return deck

    def card_count(self):
        return cards.Card.objects.of_deck(self, with_upstream=True).available().count()

    #TODO kill - unused?
    #@property
    #def new_card_count(self):
    #    return Card.objects.approx_new_count(deck=self)
    #    #FIXME do for sync'd decks
    #    return cards.Card.objects.cards_new_count(
    #            self.owner, deck=self, active=True, suspended=False)

    #TODO kill - unused?
    #@property
    #def due_card_count(self):
    #    return cards.Card.objects.cards_due_count(
    #            self.owner, deck=self, active=True, suspended=False)

    @cached_function(namespace=deck_review_stats_namespace)
    def average_ease_factor(self):
        '''
        Includes suspended cards in the calcuation. Doesn't include inactive cards.
        '''
        ease_factors = redis.zrange('ease_factor:deck:{0}'.format(self.id),
                                    0, -1, withscores=True)
        cardinality = len(ease_factors)
        if cardinality:
            return sum(score for val,score in ease_factors) / cardinality
        return DEFAULT_EASE_FACTOR

    @transaction.commit_on_success    
    def delete_cascading(self):
        #FIXME if this is a shared/synced deck
        for fact in self.fact_set.all():
            for card in fact.card_set.all():
                card.delete()
            fact.delete()
        self.delete()

    def export_to_csv(self):
        '''
        Returns an HttpRespone object containing the binary CSV data.
        Decoupling this from HttpResponse is more trouble than it's worth.
        '''
        from django.http import HttpResponse
        import csv, StringIO

        class UnicodeWriter(object):
            '''
            http://djangosnippets.org/snippets/993/
            Usage example:
                fp = open('my-file.csv', 'wb')
                writer = UnicodeWriter(fp)
                writer.writerows([
                    [u'Bob', 22, 7],
                    [u'Sue', 28, 6],
                    [u'Ben', 31, 8],
                    # \xc3\x80 is LATIN CAPITAL LETTER A WITH MACRON
                    ['\xc4\x80dam'.decode('utf8'), 11, 4],
                ])
                fp.close()
            '''
            def __init__(self, f, dialect=csv.excel_tab, encoding="utf-16", **kwds):
                # Redirect output to a queue
                self.queue = StringIO.StringIO()
                self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
                self.stream = f

                # Force BOM
                if encoding=="utf-16":
                    import codecs
                    f.write(codecs.BOM_UTF16)

                self.encoding = encoding

            def writerow(self, row):
                # Modified from original: now using unicode(s) to deal with e.g. ints
                self.writer.writerow([unicode(s).encode("utf-8") for s in row])
                # Fetch UTF-8 output from the queue ...
                data = self.queue.getvalue()
                data = data.decode("utf-8")
                # ... and reencode it into the target encoding
                data = data.encode(self.encoding)

                # strip BOM
                if self.encoding == "utf-16":
                    data = data[2:]

                # write to the target stream
                self.stream.write(data)
                # empty queue
                self.queue.truncate(0)
            
            def writerows(self, rows):
                for row in rows:
                    self.writerow(row)


        # make a valid filename for the deck based on its alphanumeric characters
        import string
        filename = filter(
                lambda c: c in (string.ascii_letters + '0123456789'), self.name)
        if not filename:
            filename = 'manabi_deck'
        filename += '.csv'
        
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)

        writer = UnicodeWriter(response)

        from manabi.apps.flashcards.models import FactType, Fact, FieldType
        fact_type = FactType.objects.get(id=1)
        field_types = FieldType.objects.filter(fact_type=fact_type).order_by('id')
        facts = Fact.objects.with_upstream(self.owner, deck=self)
        card_templates = fact_type.cardtemplate_set.all().order_by('id')

        header = [field.display_name for field in field_types] + \
                [template.name for template in card_templates]
        writer.writerow(header)

        for fact in facts:
            fields = list(field_content.content
                        for field_content
                        in fact.field_contents.order_by('field_type__id'))

            templates = []
            activated_card_templates = [e.template for e in fact.card_set.filter(active=True)]
            for card_template in fact_type.cardtemplate_set.all():
                if card_template  in activated_card_templates:
                    templates.append('on')
                else:
                    templates.append('off')

            writer.writerow(fields + templates)

        response['Content-Length'] = len(response.content)

        return response

usertagging.register(Deck)

