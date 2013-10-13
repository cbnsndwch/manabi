from django.conf.urls import *


# graph data urls
graph_urlpatterns = patterns('manabi.apps.stats.views',
    url(r'^repetitions.json$',
        'repetitions',
        name='graphs_repetitions'),
    url(r'^due_counts.json$',
        'due_counts',
        name='graphs_due_counts'),

    url(r'^daily_repetition_history.json$',
        'daily_repetition_history',
        name='graphs_daily_repetition_history'),
)



# place app url patterns here
urlpatterns = patterns('manabi.apps.stats.views',
    url(r'^graphs/', include(graph_urlpatterns)),

    #url(r'^scheduling-summary/$',
    #    'scheduling_summary',
    #    name='stats_scheduling_summary'),

    #url(r'^cards/(?P<card_id>\d+).json$', 'card_stats_json',
        #name='api-card_stats'),

    url(r'^cards/(?P<card_id>\d+)/$', 'card_stats',
        name='card_stats'),

    url(r'^$', 'index', name='stats'),
)

