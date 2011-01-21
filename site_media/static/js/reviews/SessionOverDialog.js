dojo.provide('reviews.SessionOverDialog');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');
dojo.require('dijit.Dialog');

dojo.require('manabi');


dojo.declare('reviews.SessionOverDialog', [dijit._Widget, dijit._Templated], {
    templateString: dojo.cache('reviews', 'templates/SessionOverDialog.html'),
    widgetsInTemplate: true,

    constructor: function(session) {
        this.session = session;
        this.deckId = session.deckId;
        //TODO tags too
    },

    /*_getSchedulingSummaryData: function() {
        return manabi.xhrGet({
            url: '/stats/scheduling-summary/',
            content: { deck: this.deck, tags: this.tags }
        });
    },

    _showSchedulingSummary: function(summaryData) {
        // show the summary data which is computed server-side
        // (which is not particular to this review session)
        //TODO we don't actually use these yet...
        this._getSchedulingSummaryData().then(dojo.hitch(this, function(data){
            //this.
        }));
    },*/

    postCreate: function() {
        this.inherited(arguments);
        this.reviewCount.innerHTML = manabi.plural(this.session.reviewCount, 'card');
    },

    startup: function() {
        this.inherited(arguments);

console.log(this.session);
console.log(this.session.reviewCountPerGrade);
        // render the piechart which breaks down the reviewed cards
        // (uses jQuery)
        $(dojo.hitch(this, function(){
            var piechart = new Highcharts.Chart({
                chart: {
                    renderTo: this.reviewChart,
                    //plotBackgroundColor: null,
                    //plotBorderWidth: null,
                    //plotShadow: false
                },
                title: null,
                credits: { enabled: false },
                //title: {
                    //text: 'Browser market shares at a specific website, 2010'
                //},
                tooltip: {
                    formatter: function() {
                        return '<strong>'+ this.point.name +'</strong>: '+ this.y +' ';
                    }
                },
                plotOptions: {
                    pie: {
                        //allowPointSelect: true,
                        //cursor: 'pointer',
                        dataLabels: {
                            enabled: true,
                            //color: Highcharts.theme.textColor || '#000000',
                            //connectorColor: Highcharts.theme.textColor || '#000000',
                            formatter: function() {
                                return '<b>'+ this.point.name +'</b>: ' + this.y + ' ';
                            }
                        }
                    }
                },
                series: [{
                    type: 'pie',
                    //name: 'Browser share',
                    data: [
                        {
                            name: 'Correct cards',
                            y: this.session.successfulReviewCount(),
                            color: '#66cf66',
                        },
                        {
                            name: 'Incorrect cards',
                            y: this.session.failedReviewCount(),
                            color: '#ff3939',
                        }
                        //['Unanswered due cards', this.
                        //['Unseen new cards', this.
                    ]
                }]
            });
        }));
        
    },

    show: function() {
        this.dialog.show();
    },
    hide: function() {
        this.dialog.hide();
    },

    //_set
});




