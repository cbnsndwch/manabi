  dojo.require("dijit.Dialog");
  dojo.require("dijit.form.TextBox");
  dojo.require("dijit.form.Button");
  dojo.require("dijit.form.ToggleButton");
  //dojo.require("dijit.form.FilteringSelect");
  dojo.require("dojo.data.ItemFileReadStore");
  dojo.require("dijit.form.MultiSelect");
  //dojo.require("dojox.form.DropDownSelect");
  dojo.require("dijit.form.Textarea");
  dojo.require("dijit.form.SimpleTextarea");
  dojo.require("dojo.DeferredList");
  dojo.require("dojox.form.CheckedMultiSelect");
  dojo.require("dijit.form.Form");
  dojo.require("dijit.layout.ContentPane");
  dojo.require("dojox.layout.ContentPane");
  //dojo.require("dojox.form.BusyButton");
  dojo.require("dojox.widget.Standby");
  dojo.require("dojox.grid.DataGrid");
  //dojo.require("dijit.layout.TabContainer");
  dojo.require("dijit.Declaration");
  dojo.require("dojo.data.ItemFileWriteStore");
  dojo.require("dijit.form.NumberSpinner");
  //dojo.require("dijit.layout.BorderContainer");
  dojo.require("dijit.TooltipDialog");
  dojo.require("dijit.form.Select");
  dojo.require("dojox.grid._RadioSelector");
  dojo.require("dijit.form.FilteringSelect");
  //dojo.require("dojox.grid.EnhancedGrid");
  //dojo.require("dojox.layout.FloatingPane"); 
  dojo.require("dojo.NodeList-traverse");
  dojo.require("dijit.Tooltip");
  dojo.require("dojox.timing");
  dojo.require("dojox.widget.Dialog");
  dojo.require("dojo.hash");
  
  

  // If you're reading this code, please be warned that this section is quite messy.
  // I wrote it while I was still learning JS and Dojo. I think my later output is much
  // cleaner. I'll try to fix this stuff up soon though before it bites me back.

  //general utility methods
  //TODO move this to its own file
  var manabi_utils = {};


  //TODO all this code and globals really need to be encapsulated
  //this is a start on encapsulating new stuff I add:
  //object to hold things for the Fact Add dialog.
  var fact_add_ui = {};

  fact_add_ui.keyboard_shortcut_connection = null;

  fact_add_ui.setKeyboardShortcuts = function() {
    fact_add_ui.keyboard_shortcut_connection = dojo.connect(factAddDialog, 'onKeyPress', function(e) {
        var k = dojo.keys;

        if (dojo.isCopyKey(e)) {
            //meta (on mac) or ctrl (on PC) is pressed
            switch(e.charOrCode) {
                case k.ENTER:
                    //submit form
                    dojo.stopEvent(e);
                    fact_add_ui.factAddFormSubmit();
                    break;
            }
        }
    });
  };

  fact_add_ui.unsetKeyboardShortcuts = function() {
    dojo.disconnect(fact_add_ui.keyboard_shortcut_connection);
  };
  
  
  function ajaxLink(url, container_id) {
      dijit.byId(container_id).attr('href', url);
  }
  
  
  
  function factFormSubmit(submitSuccessCallback, submitErrorCallback, _factAddForm, factId, showStandby) {
      if (showStandby) {
          //factAddDialogStandby.attr('target', factAddFormDialog);
          factAddFormSubmitButton.attr('disabled', true);
      }
      //var cardTemplatesValue = _cardTemplatesInput.attr('value');
      //var tempCardCounter = 0;
      //var newCardTemplatesValue = {};
      var factAddFormValue = _factAddForm.attr('value');
      
      /*cardTemplatesValue = dojo.forEach(cardTemplatesValue, function(val){
          var newKey = 'card-'+(tempCardCounter++)+'-template';
          factAddFormValue[newKey] = val;
      });*/
      var tempCardCounter = 0;
      for (var key in factAddFormValue) {
          if (key.indexOf('card_template') == 0 && factAddFormValue[key].length) {
            tempCardCounter++;
          }
      }

      factAddFormValue['fact-fact_type'] = 1; //FIXME temp hack - assume Japanese
      //factAddFormValue['card-TOTAL_FORMS'] = tempCardCounter.toString();
      //factAddFormValue['card-INITIAL_FORMS'] = '0'; //tempCounter; //todo:if i allow adding card templates in this dialog, must update this
      factAddFormValue['field_content-TOTAL_FORMS'] = fieldContentInputCount.toString();
      factAddFormValue['field_content-INITIAL_FORMS'] = factId ? fieldContentInputCount.toString() : '0'; //fieldContentInputCount; //todo:if i allow adding card templates in this dialog, must update this
      //factAddFormValue['fact-id']
      //alert('submitted w/args:\n' + dojo.toJson(factAddFormValue));
      
      var xhrArgs = {
          url: factId ? '/flashcards/rest/facts/'+factId : '/flashcards/rest/facts',//url: '/flashcards/rest/decks/'+factAddFormValue['fact-deck']+'/facts', //TODO get URI restfully
          content: factAddFormValue,
          handleAs: 'json',
          load: dojo.hitch(null, function(tempCardCounter, data){
              if (data.success) {
                  submitSuccessCallback(data, tempCardCounter);
                  //if the fact editing grid is open, update it
                  if (typeof cards_factsGrid != 'undefined') {
                      var store = cards_factsGrid.store;
                      store.close();
                      store.fetch();
                      cards_factsGrid.sort();
                  }
              } else {
                  submitErrorCallback(data, tempCardCounter);
              }
          }, tempCardCounter),
          error: function(error){
              submitErrorCallback(data, tempCardCounter); //TODO other callback
          }
      }
      //dojo.byId("response2").innerHTML = "Message being sent..."
      //Call the asynchronous xhrPost
      dojo.xhrPost(xhrArgs); //var deferred = 
      //dojo.place('Added '+tempCardCounter.toString()+' cards for '+'what'+'<br>','factAddFormResults', 'last');
  }
  
  function resetFactAddForm() {
      //factAddForm.reset(); //don't reset everything... just the field contents
      dojo.query('.dijitTextBox:not([type=hidden]), .dijitTextarea:not([type=hidden])',factAddDialog.domNode).forEach(function(node, index, arr){
              node.value=''; }); //TODO clear via dijit, not dom

      //reset multi-choice fields
      dojo.query('.dijitSelect', dojo.byId('factFields')).forEach(function(node, index, arr) {
              var widget = dijit.getEnclosingWidget(node);
              widget.attr('value', 'none');
      });

      //reset hidden fields
      dojo.query('.hiddenFieldLink', factAddDialog.domNode).forEach(function(node) {
              node.style.display = '';
              dojo.query(node).next()[0].style.display = 'none';
      });

      //destroy any error messages
      dojo.query('.field_content_error', dojo.byId('factAddFormWrapper')).empty();

      //focus the first text field
      dojo.query('.dijitTextBox:not([type=hidden]), .dijitTextarea:not([type=hidden])', factAddDialog.domNode)[0].focus(); //FIXME for textboxes
  }
  
  function createFieldInputsForUpdate(domNode, factTypeId, factFieldValues, cardTemplatesOnCompleteCallback, factFieldsOnCompleteCallback) { //todo:refactor into 2 meths
      if (factTypeId) {
          //add card template options
          var cardUpdateTemplatesStore = new dojo.data.ItemFileReadStore({url: '/flashcards/rest/facts/'+factFieldValues['fact-id'][0]+'/card_templates'});
          var cardUpdateTemplatesButton = new DropDownMultiSelect({inputId: 'cardUpdateTemplatesInput'+factTypeId});//TODO counter suffix
          var cardUpdateTemplatesInput = dijit.byId('cardUpdateTemplatesInput'+factTypeId);
          
          //hidden form elements, for fact id
          var hiddenFactField = new dijit.form.TextBox({value:'PUT', name:'_method', type:'hidden'});//dojo.place('<input type=\"hidden\" name=\"fact\" value=\"'+factTypeId+'\">', domNode, 'last');
          hiddenFactField.placeAt(domNode, 'last');
          hiddenFactField = new dijit.form.TextBox({value:factTypeId, name:'fact-id', type:'hidden'});//dojo.place('<input type=\"hidden\" name=\"fact\" value=\"'+factTypeId+'\">', domNode, 'last');
          hiddenFactField.placeAt(domNode, 'last');
          cardUpdateTemplatesButton.placeAt(domNode, 'last');
            //todo:pull values from the fact store for that id
          var formPrefix = 'form_'+factTypeId+'-';
          var cardTemplateCounter = 0;
          cardUpdateTemplatesStore.fetch({
              onItem: function(item){
                 if (cardUpdateTemplatesStore.getValue(item, 'activated_for_fact')) {
                     cardUpdateTemplatesInput.addOption({value: cardUpdateTemplatesStore.getValue(item, 'card_template')['id']+"", label: cardUpdateTemplatesStore.getValue(item, 'card_template')['name'], selected: 'selected'});
                 } else {
                     cardUpdateTemplatesInput.addOption({value: cardUpdateTemplatesStore.getValue(item, 'card_template')['id']+"", label: cardUpdateTemplatesStore.getValue(item, 'card_template')['name']});
                 }
              },
              onComplete: function(items) {
                  cardTemplatesOnCompleteCallback(items);
              }
          });
          
          //add FieldContent textboxes (based on Fields)
          var fieldsStore = new dojo.data.ItemFileReadStore({url:'/flashcards/rest/fact_types/'+factTypeId+'/fields', clearOnClose:true}); //todo:try with marked up one instead
          var fieldCounter = 0;
          fieldsStore.fetch({
              onItem: function(item) {
                  var tempFieldCounter = fieldCounter++; 
                  var fieldContentHeaderHTML = '<div><strong>'+fieldsStore.getValue(item, 'name')+':</strong>';
                  if (!fieldsStore.getValue(item, 'blank')) {
                      fieldContentHeaderHTML += ' (required)';
                  }
                  dojo.place(fieldContentHeaderHTML, domNode, 'last');
                  dojo.place('<div id="id_field_content-'+tempFieldCounter+'-content-errors" class="field_content_error" />', domNode, 'last');
                  var fieldTextarea = new dijit.form.SimpleTextarea({
                      name: 'field_content-'+tempFieldCounter+'-content', //fieldsStore.getValue(item, 'name'),
                      'class': 'field_content',
                      id: formPrefix+'id_field_content-'+tempFieldCounter+'-content',
                      jsId: formPrefix+'id_field_content_'+tempFieldCounter+'_content',
                      value: factFieldValues['id'+fieldsStore.getValue(item, 'id')][0],//"",
                      style: "width:300px;",
                      rows: '2'
                  }).placeAt(domNode, 'last');
                  fieldTextarea.attr('gridStoreItemId', 'id'+fieldsStore.getValue(item, 'id')); //TODO this is a hack - all this code needs to be refactored
                  
                  //dojo.place('<input type="hidden" dojoType="dijit.form.TextBox" name="field_content-'+tempFieldCounter+'-field" id="id_field_content-'+tempFieldCounter+'id" value="'+fieldsStore.getValue(item, 'id')+'" />', 'factFields', 'last');
                  new dijit.form.TextBox({
                      name: 'field_content-'+tempFieldCounter+'-field_type',
                      id: formPrefix+'id_field_content-'+tempFieldCounter+'-field_type',
                      jsId: formPrefix+'id_field_content_'+tempFieldCounter+'_field_type',
                      value: fieldsStore.getValue(item, 'id'),
                      type: 'hidden'
                  }).placeAt(domNode, 'last');
                  
                  new dijit.form.TextBox({
                      name: 'field_content-'+tempFieldCounter+'-id',
                      value: factFieldValues['id'+fieldsStore.getValue(item, 'id')+'_field-content-id'][0],
                      type: 'hidden'
                  }).placeAt(domNode, 'last');

                  dojo.place('</div>', domNode, 'last');
              },
              onComplete: function(items) {
                  fieldContentInputCount = fieldCounter;
                  factFieldsOnCompleteCallback(items);
              }
          });
      }
  }
  
  
  var factTypeInputOnChangeHandle = null;
  var lastCardTemplatesInputValue = null;
  var fieldContentInputCount = 4;//FIXME this is a terrible legacy hack... (was null;)
  
  function appendLineToAddedCardHistory(node, text) {
    //append a line, but if there are too many lines, delete the first line
    //(this is messy...)
    existing_lines = node.innerHTML.split('<br>');
    if (existing_lines.length > 4) {
        //delete first line
        existing_lines.shift();
        node.innerHTML = existing_lines.join('<br>');
    } else if (existing_lines.length == 1) {
        text = '<br>' + text;
    }
    node.innerHTML += text + '<br>';
  }

  fact_add_ui.factAddFormSubmit = function() {
    //var cardTemplatesInput = dijit.byId('cardTemplatesInput');
    factFormSubmit(function(data, tempCardCounter){
    //dojo.place('Added '+tempCardCounter.toString()+' cards for '+factAddFormValue['field_content-0-content']+'<br>','factAddFormResults', 'last');
      if (dojo.trim(factAddFormResults.containerNode.innerHTML) == '') {
          factAddFormResults.containerNode.innerHTML = '';
      }
      appendLineToAddedCardHistory(factAddFormResults.containerNode, 'Added '+tempCardCounter.toString()+' cards for '+dijit.byId('id_field_content-0-content').attr('value'));
      resetFactAddForm();
      factAddFormSubmitButton.attr('disabled', false);
    }, function(data, tempCardCounter) {
      //show field_content errors
      fieldContentErrors = data.errors.field_content;//[errors][field_content];
      dojo.forEach(fieldContentErrors, function(errorMsg, idx) {
          if ('content' in errorMsg) {
              dojo.byId('id_field_content-'+idx+'-content-errors').innerHTML = '<font color="red"><em>'+errorMsg.content.join('<br>')+'</em></font>';
          } else {
              var node_to_empty = dojo.byId('id_field_content-'+idx+'-content-errors');
              if (node_to_empty) {
                dojo.empty(node_to_empty);
              }
          }
      });
      
      if (data.errors.fact.length && 'tags' in data.errors.fact[0]) {
          dojo.byId('fact-tag-errors').innerHTML = '<font color="red"><em>' + data.errors.fact[0].tags.join('<br>') + '</em></font>';
      } else {
          dojo.query('#fact-tag-errors').empty();
      }
      factAddFormSubmitButton.attr('disabled', false);
    }, factAddForm, null, true);
  }
  
  //connect to Add Fact form submit
  dojo.addOnLoad(function() {
          dojo.connect(factAddForm, 'onSubmit', function(e) {
            e.preventDefault();
            fact_add_ui.factAddFormSubmit();
          });
  });



    //------------------------------------------

    //the new class for fact editing
    fact_ui = {};

    dojo.addOnLoad(function() {
        fact_ui.facts_grid_normal_height = '300px'; //TODO figure out how to make the height as tall as window
        fact_ui.facts_grid_minimized_height = '145px';
    });
    

    fact_ui.showFactEditForm = function(fact_id, submit_success_callback) {
        //fact_ui.selected_fact_row_index = row_index;
        fact_ui._submit_success_callback = submit_success_callback;

        //cards_factsGrid.domNode.style.height = fact_ui.facts_grid_minimized_height;
        //cards_factsGrid.resize();
        //cards_factsGrid.scrollToRow(row_index); //TODO this can be a little awkward, moving too often
        cards_factEditorContainer.attr('href', 'flashcards/facts/' + fact_id + '/update');
        //cards_factEditorContainer.domNode.style.display = '';
        cards_factEditorContainer.show();
        dojo.query('.dijitDialogCloseIcon',cards_factEditorContainer.domNode)[0].style.visibility='hidden';
    }

    fact_ui.hideFactEditForm = function() {
        //cards_factEditorContainer.domNode.style.display = 'none';
        //cards_factEditorContainer.attr('content', '');
        //re-expand the facts grid
        //cards_factsGrid.domNode.style.height = fact_ui.facts_grid_normal_height;
        //cards_factsGrid.resize();
        cards_factEditorContainer.hide();
    }

    fact_ui.submitFactForm = function(fact_form, fact_id) {
        // currently used for updating facts
        //factForm must be a dijit form
        //fact_id is optional - if specified, it means we're updating a fact
        //TODO return a deferred instead of taking in success/error callbacks

        //disable the submit button while processing
        submit_button = dijit.getEnclosingWidget(dojo.query('button[type=submit]', fact_form.domNode)[0])
        submit_button.attr('disabled', true);

        form_values = fact_form.attr('value');

        var card_templates_input = dijit.getEnclosingWidget(dojo.query('.cards_cardTemplates', fact_form.domNode)[0]);
        var card_templates = card_templates_input.attr('value');
        var card_counter = 0;
        dojo.forEach(card_templates, function(val) {
            var new_key = 'card-' + (card_counter++) + '-template';
            form_values[new_key] = val;
        });
        
        //get the number of fields
        field_count = dojo.query('.cards_fieldContent', fact_form.domNode).length;

        //assemble the form submission values
        form_values['fact-fact_type'] = '1'; //TODO temp hack - assume Japanese
        form_values['card-TOTAL_FORMS'] = card_counter.toString();
        form_values['card-INITIAL_FORMS'] = '0';
        form_values['field_content-TOTAL_FORMS'] = field_count.toString();
        /*form_values['field_content-INITIAL_FORMS'] = 
            fact_id ? field_count.toString() : '0';*/

        //submit the form
        var submit_error_callback = function(data, card_counter) {
            field_content_errors = data.errors.field_content;
            dojo.forEach(field_content_errors, function(error_message, idx) {
                //idx corresponds to the nth field content
                field_content_error_divs = dojo.query('.field_content_error', fact_form.domNode);
                if ('content' in error_message) {
                    field_content_error_divs[idx].innerHTML = error_message.content.join('<br>');
                } else {
                    dojo.empty(field_content_error_divs[idx]);
                }
            });
        }

        var xhrArgs = {
            url: fact_id ? 
                     '/flashcards/rest/facts/'+fact_id : 
                     '/flashcards/rest/facts',
            content: form_values,
            handleAs: 'json',
            load: function(data){
                if (data.success) {
                    fact_ui._submit_success_callback(data, card_counter);

                } else {
                    submit_error_callback(data, card_counter);
                }
                submit_button.attr('disabled', false);
            },
            error: function(error){
                submit_error_callback(data, card_counter); //TODO other callback for this
                submit_button.attr('disabled', false);
            }
        }
        dojo.xhrPost(xhrArgs); //var deferred = 
        //dojo.place('Added '+tempCardCounter.toString()+' cards for '+'what'+'<br>','factAddFormResults', 'last');
        
    }

    fact_ui.facts_url_query = {fact_type: 1};

    fact_ui.clearFilter = function(filter_name) {
        var store = cards_factsGrid.store;
        store.close();
        delete fact_ui.facts_url_query[filter_name];
        store.url = '/flashcards/rest/facts?' + dojo.objectToQuery(fact_ui.facts_url_query);
        store.fetch();
        cards_factsGrid.sort(); //forces a refresh
    };


    fact_ui.clearFactSearch = function() {
            var cards_factSearchField = dijit.byId('cards_factSearchField');
            fact_ui.current_search_url_parameter = '';
            cards_factSearchField.attr('value', '');
            cards_clearFactSearchButton.domNode.style.visibility = 'hidden';
            fact_ui.clearFilter('search');
    };

    fact_ui.clearTagFilters = function() {
            var cards_factFilterByTagInput = dijit.byId('cards_factFilterByTagInput');
            fact_ui.current_tag_filter_list = new Array();
            cards_factFilterByTagInput.reset();
            cards_clearTagFiltersButton.domNode.style.visibility = 'hidden';
            fact_ui.clearFilter('tags');
    };

    //fact_ui.addTagFilterDiv = function(container_node) {
    //    container_node.

    fact_ui._generateReading = function(expression) {
        //outputs the reading for expression to the reading_field
        //var expression = expression_field.attr('value');
        var ret_def = new dojo.Deferred();
        var xhr_args = {
            url: 'flashcards/rest/generate_reading',
            content: {expression: expression},
            handleAs: 'json',
            headers: { "Content-Type": "application/x-www-form-urlencoded; charset=utf-8" },
            load: dojo.hitch(null, function(success_def, data) {
                if (data.success) {
                    success_def.callback(data.reading);
                } else {
                    success_def.errback(data); //FIXME errback?
                }
            }, ret_def)
        };
        dojo.xhrPost(xhr_args);
        return ret_def;
    };

    fact_ui.generateReading = function(expression, reading_field, show_standby) {
        var reading_field = dijit.byId(reading_field);
        if (expression.trim() != '') {
            reading_field.attr('disabled', true);        

            var def = fact_ui._generateReading(expression);

            var standby = null;

            if (show_standby) {
                standby = new dojox.widget.Standby({
                    target: dijit.byId(reading_field).domNode.id
                });
                dojo.body().appendChild(standby.domNode);
                standby.startup();
                standby.show();
            }
            def.addCallback(dojo.hitch(null, function(reading_field, expression, standby, reading) {
                if (reading.trim()) { // != expression.trim()) {
                    reading_field.attr('value', reading);
                }
                if (standby) {
                    standby.hide();
                    standby.destroy();
                }
                dijit.byId(reading_field).attr('disabled', false);            
            }, dijit.byId(reading_field), expression, standby));
        } else {
            dijit.byId(reading_field).attr('value', '');
        }
    };


    fact_ui.showFactAddDialog = function(deck_id) {
        if (deck_id == undefined) { deck_id = null; }
        if (deck_id) {
            //FIXME set it, hide the select
            deckInput.attr('value', deck_id.toString());
        }
        factAddDialog.show();
    };


