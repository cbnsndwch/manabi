dojo.provide('kanjivg.frames');
dojo.provide('kanjivg.frames.Frames');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');

dojo.require('dojox.gfx');
dojo.require('dojox.gfx.utils');


dojo.declare('kanjivg.frames.Frames', [dijit._Widget, dijit._Templated], {
    templateString: dojo.cache('kanjivg', 'templates/Frames.html'),

    // URL for JSON source file
    src: '',

    postCreate: function(){
        // load image
        dojo.xhrGet({
            handleAs: 'json',
            url: this.src,
            load: dojo.hitch(this, function(json) {
                // The incoming JSON looks like this:
                //   {width:250, height:109, data:[serialized-data-here]}

                var width = json.width;
                var height = json.height;
                var shape_data = json.data;
        
                // Create the surface
                var surface = dojox.gfx.createSurface(this.surfaceNode, width, height);
                
                // Write JSON to group
                var group = surface.createGroup();
                dojox.gfx.utils.deserialize(group, shape_data);
            })
        });
    }
});


