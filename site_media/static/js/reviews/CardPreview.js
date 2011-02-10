dojo.provide('reviews.CardPreview');
dojo.provide('reviews.CardPreview.Production');
//dojo.provide('facts.CardPreview._CardPreview');
//dojo.provide('facts.CardPreview.ProductionCardPreview');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');



dojo.declare('reviews.CardPreview._base', [dijit._Widget, dijit._Templated], {
    //  summary:

    templateString: dojo.cache('reviews', 'templates/CardPreview.html'),

    frontPrompt: '',
    formContainerNode: null,

    constructor: function(args) {
        this.fields = {
            expression: 'expression',
            meaning: 'meaning',
            reading: 'reading'
        };

        dojo.safeMixin(this, args);
    },

    postCreate: function(){
        //  summary
        //      Initializes the jPlayer plugin widget on this node.
        console.log('startup');
		if(this._started){ return; }
        this.formContainerNode = dojo.query(this.domNode).closest('.fact_form_container')[0];
        console.log('formContainerNode:');
        console.log(this.formContainerNode);
        this._bindFields();
        this.render();

        this.inherited(arguments);
    },

    _bindFields: function() {
        // Binds callbacks to each input field in the form
        // to tell when their values change, so we can re-render.
        var that = this;
        for (var fieldName in this.fields) {
            dojo.query('.field_content.'+fieldName, this.formContainerNode).forEach(function(node){
                var field = dijit.getEnclosingWidget(node);
                var handler = function(fieldName, e){
                    that.fields[fieldName] = field.get('value');
                    that.render();
                };
                // use that.connect so that _Widget automatically unconnects on destroy
                that.connect(field, 'onChange', dojo.hitch(this, handler, fieldName));
                that.connect(field, 'onKeyUp', dojo.hitch(this, handler, fieldName));
            });
        }
    },
    
    render: function() {
        var front = this._renderFront();
        var back = this._renderBack();

        dojo.query(this.frontNode).html(front);
        dojo.query(this.backNode).html(back);
    }
});


dojo.declare('reviews.CardPreview.Production', [reviews.CardPreview._base], {
    _renderFront: function() {
        return dojo.replace('<span class="meaning">{meaning}</span>', this.fields);
    },

    _renderBack: function() {
        return dojo.replace('<span class="expression">{expression}</span><span class="reading">{reading}</span>', this.fields);
    }
});



