
manabi_ui = {}


dojo.addOnLoad(function() {
    manabi_ui.body_pane = body_pane; //dijit.byId('body_pane');

    //make all the links ajaxy
    manabi_ui.convertLinksToXhr(dojo.body());
});


// history support (via hash change)
if (document.URL.indexOf('#') != -1) {
    manabi_ui._baseURL = document.URL.substring(0, document.URL.indexOf('#'));
} else {
    manabi_ui._baseURL = document.URL;
}

manabi_ui.onHashChange = function(hash) {
    if (!hash) {
        manabi_ui._xhrLinkLoad('/home');
    } else if (manabi_ui._currentPageHash != hash) {
        // load the page given in the hash
        manabi_ui._xhrLinkLoad(hash);
    }
};

dojo.ready(function() {
    dojo.subscribe("/dojo/hashchange", manabi_ui.onHashChange);
    var hash = dojo.hash();
    console.log(hash);
    if (hash) {
        manabi_ui._xhrLinkLoad(hash);
    } else {
        manabi_ui._xhrLinkLoad('/home');
    }
});




manabi_ui._xhrLinkLoad = function(hash) {
    manabi_ui._currentPageHash = hash;
    // load the page
    var target_pane = manabi_ui.body_pane;
    var href = hash;
    if (href[0] == '/') {
        href = href.substring(1);
    }
    target_pane.attr('href', hash);
};

manabi_ui.xhrLink = function(href) { //, target_pane) {
    // set the URL hash for browser history
    var hash = href.replace(manabi_ui._baseURL, '');
    if (hash[0] != '/') {
        hash = '/' + hash;
    }
    dojo.hash(hash);

    manabi_ui._xhrLinkLoad(hash);
    //TODO scroll to top when page loads?
    //TODO error page too (onDownloadError)
}


/*manabi_ui.truncateSelectDisplayOnChange = function(select_widget) {
    dojo.connect(select_widget, select_widget, 'onChange', function() {
        this._setDisplay('uhhmm');
    }
}*/



manabi_ui.xhrPost = function(url, form, post_redirect_url) {
    if (form == undefined) { form = null; }
    if (post_redirect_url == undefined) { post_redirect_url = null; }

    manabi_standby.show();

    var xhr_args = {
        'url': url,
        form: form,
        handleAs: 'json',
        load: dojo.hitch(null, function(url, data) {
            if ('post_redirect' in data) {
                manabi_ui.xhrLink(data.post_redirect);
            } else {
                if (post_redirect_url) {
                    manabi_ui.xhrLink(post_redirect_url);
                }
            }
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


manabi_ui.refreshSelectInput = function(input_id, options) {
    select = dijit.byId(input_id);
    select.removeOption(select.getOptions());
    select.reset();
    options.forEach(function(option) {
        select.addOption(option);
    });
};

manabi_ui._getOptionsFromStore = function(store) {
    var options = new Array();
    var def = new dojo.Deferred();
    store.close();
    store.fetch({
        onItem: dojo.hitch(this, function(store, item) {
            options.push({value: store.getValue(item, 'id'), label: store.getValue(item, 'name')});
        }, store),
        onComplete: dojo.hitch(this, function(def, options) {
            def.callback(options);
        }, def, options),
    });
    return def;
}


//a hack since dijit.form.Select isnt fully data-aware
dojo.addOnLoad(function(){manabi_ui.refreshDeckInput()});
manabi_ui.refreshDeckInput = function() {
    //dojo.byId('deckInputContainer').empty();
    //deckInput.destroy();

    var options_def = manabi_ui._getOptionsFromStore(decksStore);
    options_def.addCallback(function(options) {
        manabi_ui.refreshSelectInput(deckInput, options);
        if (typeof cards_deckFilterInput != 'undefined') {
            options.unshift({value: '-1', label: 'All decks'});
            manabi_ui.refreshSelectInput(cards_deckFilterInput, options);
        }
    });

    reviews_decksStore.close();
    reviews_decksStore.fetch({
        onComplete: function() {
            reviews_decksGrid.sort();
        }
    });
}



//add trim() to string objects
if(typeof(String.prototype.trim) === "undefined")
{
    String.prototype.trim = function() 
    {
        return String(this).replace(/^\s+|\s+$/g, '');
    };
}




