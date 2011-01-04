dojo.provide('jdic.audio');
dojo.provide('jdic.audio.JDicAudioServer');
dojo.provide('jdic.audio.JDicAudioPlayer');

dojo.require('dijit._Widget');
dojo.require('dijit._Templated');

dojo.declare('jdic.audio.Server', null, { 
    constructor: function(base_url) {
        //  Summary:
        //      A simple wrapper around a JDIC audio file server. It just 
        //      provides the proper URLs for given Japanese vocab items.
        //  description:
        //      It takes one parameter:
        //          base_url:    The root URL of a HTTP file server - this
        //                       directory should contain all the MP3 files
        //                       with filenames of form:
        //                          [reading] - [expession/kanji].mp3
        //                       The URL must end with '/'
        this.base_url = base_url;

        /*if (kwArgs && kwArgs.url_encoding) {
            this.url_encoding = kwArgs.url_encoding;
        }*/
    },

    fileUrl: function(kana, kanji) {
        //  Summary:
        //      Returns a URL corresponding to the MP3 file for the given 
        //      kana and kanji. This file may or may not exist, though.
        //      So catch 404 errors when using this function's return value.

        return this.base_url + encodeURIComponent(kana) + ' - ' + encodeURIComponent(kanji) + '.mp3';
    }
});


dojo.declare('jdic.audio.Player', [dijit._Widget, dijit._Templated], {
    //  summary:
    //      A widget wrapper for the jPlayer plugin for jQuery, optimized 
    //      to work with our JDicAudioServer.
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

    startup: function(){
        //  summary
        //      Initializes the jPlayer plugin widget on this node.
        var node = this.jPlayerNode;

        this.src = this.audioServer.fileUrl(this.kana, this.kanji);

        
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

        }));
    }
});

/*dojo.ready(function(){
var s = new jdic.audio.Server('http://jdic.manabi.org/audio/');
var p = new jdic.audio.Player({audioServer: s, kana: 'きょう', kanji: '今日', autoplay:true}).placeAt('footer', 'last');
p.startup();
});*/
