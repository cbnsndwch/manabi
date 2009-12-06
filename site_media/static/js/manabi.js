
manabi_ui = {}

dojo.addOnLoad(function() {
    manabi_ui.body_pane = body_pane; //dijit.byId('body_pane');
});

manabi_ui.xhrLink = function(href) { //, target_pane) {
    //TODO support other target panes
    target_pane = manabi_ui.body_pane;

    target_pane.attr('href', href);

    //TODO scroll to top when page loads?
    //TODO error page too (onDownloadError)
}
