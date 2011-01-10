dojo.provide('kanjivg._base');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');

dojo.require('dojox.gfx');
dojo.require('dojox.gfx.utils');


dojo.declare('kanajivg.Frames', [dijit._Widget, dijit._Templates], {
    templateString: dojo.cache('kanjivg', 'templates/Frames.html'),

    // URL for JSON source file
    src: '',

    postCreate: function(){
        // load image
        dojo.xhrGet({
            handleAs: 'json',
            url: this.src,
            load: function(json) {
                // Create the surface
                var surface = dojox.gfx.createSurface(this.surfaceNode, 500, 500);
                
                // Write JSON to group
                var group = surface.createGroup();
                dojox.gfx.utils.deserialize(group, json);
            }
    }
});


dojo.declare('jdic.audio.Player', [dijit._Widget, dijit._Templated], {
    //  summary:
    //      A widget wrapper for the jPlayer plugin for jQuery,
    //      optimized to work with our JDicAudioServer.
    //
    //  audioServer: JDicAudioServer
    //  kana: String
    //  kanji: String

    templateString: dojo.cache('jdic', 'templates/JDicAudioPlayer.html'),

    audioServer: null,
    kana: '',
    kanji: '',
    src: '',
    autoplay: false,

    postCreate: function(){
        // Start out hidden, until the file begins to load.
        dojo.style(this.domNode, 'display', 'none');
    },
    
    startup: function(){
        //  summary
        //      Initializes the jPlayer plugin widget on this node.
        var node = this.jPlayerNode;

        this.src = this.audioServer.fileUrl(this.kanji, this.kana);

        
        // jQuery plugin instantiation
        $(document).ready(dojo.hitch(this, function() {
            $(node).jPlayer({
                ready: dojo.hitch(null, function(jdicAudioPlayer) {
                    var player = $(this).jPlayer('setMedia', {
                        mp3: jdicAudioPlayer.src
                    });
                    if (jdicAudioPlayer.autoplay) {
                        $(this).jPlayer('play');
                    };
                }, this),

                swfPath: dojo.moduleUrl('jdic', 'jPlayer').toString(),

                solution: 'html, flash'
            });
            $(node).bind($.jPlayer.event.error + '.jdic', function(event) {
                // Wait until the data has loaded to show the 
                // audio player. This lets us keep it hidden if 
                // the file does not exist.
            });

            var showWidget = dojo.hitch(this, function() {
                dojo.style(this.domNode, 'display', 'block');
            });

            // Using ".jp-show" namespace so we can easily 
            // remove this event
            $(node).bind($.jPlayer.event.progress + '.jdic', showWidget);
            $(node).bind($.jPlayer.event.loadeddata + '.jdic', showWidget);
            $(node).bind($.jPlayer.event.play + '.jdic', showWidget);

        }));
    },

    destroy: function(){
        $(this.jplayerNode).jPlayer('stop');
        $(this.jplayerNode).unbind('.jdic');
    }
});

/*dojo.ready(function(){
var s = new jdic.audio.Server('http://jdic.manabi.org/audio/');
var p = new jdic.audio.Player({audioServer: s, kana: 'きょう', kanji: '今日', autoplay:true}).placeAt('footer', 'last');
p.startup();
});*/
