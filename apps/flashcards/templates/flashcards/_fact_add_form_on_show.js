
dojo.ready(function(){
    dojo.query('textarea', factAddForm.domNode).forEach(function(node) {
        var widget = dijit.getEnclosingWidget(node);
        widget.resize();
    });
    dojo.query('div.hidden_in_form', factAddForm.domNode).forEach(function(node) {
        var to_hide = true;
        var text_nodes = dojo.query('textarea', node);
        if (text_nodes.length) {
            var widget = dijit.getEnclosingWidget(text_nodes[0]);

            if (widget.get('value').trim() !== '') {
                to_hide = false;
            }
            if (to_hide) {
                node.style.display = 'none';
                //unhide the 'Add ...' link, which shows this hidden field
                dojo.query(node).prev()[0].style.display = '';
            }
        }
    });
});

