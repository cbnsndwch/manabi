
manabi_ui = {}

dojo.addOnLoad(function() {
    manabi_ui.body_pane = body_pane; //dijit.byId('body_pane');

    //make all the links ajaxy
    manabi_ui.convertLinksToXhr(dojo.body());

    /*body_pane.onDownloadEnd(function(data) {
        console.log('1');
        manabi_ui.convertLinksToXhr(body_pane.domNode);
        console.log('1');
    });*/
});

manabi_ui.xhrLink = function(href) { //, target_pane) {
    //TODO support other target panes
    target_pane = manabi_ui.body_pane;

    target_pane.attr('href', href);

    //TODO scroll to top when page loads?
    //TODO error page too (onDownloadError)
}


/*manabi_ui.truncateSelectDisplayOnChange = function(select_widget) {
    dojo.connect(select_widget, select_widget, 'onChange', function() {
        this._setDisplay('uhhmm');
    }
}*/



manabi_ui.xhrPost = function(url, form, post_redirect_url) {
    manabi_standby.show();

    var xhr_args = {
        'url': url,
        form: form,
        handleAs: 'text',
        load: dojo.hitch(null, function(data) {
                             manabi_ui.xhrLink(post_redirect_url)
                         }, post_redirect_url),
        error: function(error) {
            alert('Error: '+error);
        }
    }

    var def = dojo.xhrPost(xhr_args);
    def.addCallback(function() {
        manabi_standby.hide();
    });
    return def;
}

manabi_ui.convertLinksToXhr = function(container_node) {
    dojo.query('.xhr_link', dojo.byId(container_node)).forEach(
        function(node) {
            dojo.connect(node, 'onclick', dojo.hitch(node, function(evt) {
                dojo.stopEvent(evt);
                manabi_ui.xhrLink(this.href);
            }));
        }
    );
}


//a hack since dijit.form.Select isnt fully data-aware
dojo.addOnLoad(function(){manabi_ui.refreshDeckInput()});
manabi_ui.refreshDeckInput = function() {
    //dojo.byId('deckInputContainer').empty();
    //deckInput.destroy();
    deckInput.removeOption(deckInput.getOptions())
    deckInput.reset();
    decksStore.close();
    decksStore.fetch({
        onItem: function(item) {
            deckInput.addOption({value: decksStore.getValue(item, 'id'), label: decksStore.getValue(item, 'name')});
        }
        });
}
