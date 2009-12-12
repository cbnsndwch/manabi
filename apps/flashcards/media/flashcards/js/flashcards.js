  dojo.require("dijit.Dialog");
  dojo.require("dijit.form.TextBox");
  dojo.require("dijit.form.Button");
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
  dojo.require("dojox.form.BusyButton");
  dojo.require("dojox.widget.Standby");
  dojo.require("dojox.grid.DataGrid");
  //dojo.require("dijit.layout.TabContainer");
  dojo.require("dijit.Declaration");
  dojo.require("dojo.data.ItemFileWriteStore");
  dojo.require("dijit.form.NumberSpinner");
  //dojo.require("dijit.layout.BorderContainer");
  dojo.require("dijit.TooltipDialog");
  dojo.require("dijit.form.Select");
  //dojo.require("dojox.grid.EnhancedGrid");
  dojo.require("dojox.layout.FloatingPane"); 
  

  // If you're reading this code, please be warned that this section is quite messy.
  // I wrote it while I was still learning JS and Dojo. I think my later output is much
  // cleaner. I'll try to fix this stuff up soon though before it bites me back.

  //general utility methods
  //TODO move this to its own file
  var manabi_utils = {};
  manabi_utils.isCopyKey = function(e) {
    return (e.metaKey || e.ctrlKey);
  }


  //TODO all this code and globals really need to be encapsulated
  //this is a start on encapsulating new stuff I add:
  //object to hold things for the Fact Add dialog.
  var fact_add_ui = {};

  fact_add_ui.keyboard_shortcut_connection = null;

  fact_add_ui.setKeyboardShortcuts = function() {
    fact_add_ui.keyboard_shortcut_connection = dojo.connect(factAddDialog, 'onKeyPress', function(e) {
        var k = dojo.keys;

        if (manabi_utils.isCopyKey(e)) {
            //meta (on mac) or ctrl (on PC) is pressed
            switch(e.charOrCode) {
                case k.ENTER:
                    //submit form
                    dojo.stopEvent(e);
                    fact_add_ui.factAddFormSubmit();
                    break;
            }

        }/*
        switch(e.charOrCode) {
            case k.
            case dojo.keys.LEFT:
            case 'h':
                 // go left
            
       }
       dojo.stopEvent(e);*/
    });
  };

  fact_add_ui.unsetKeyboardShortcuts = function() {
    dojo.disconnect(fact_add_ui.keyboard_shortcut_connection);
  };
  
  
  function ajaxLink(url, container_id) {
      dijit.byId(container_id).attr('href', url);
  }
  
  
  
  function factFormSubmit(submitSuccessCallback, submitErrorCallback, _cardTemplatesInput, _factAddForm, factId, showStandby) {
      if (showStandby) {
          //factAddDialogStandby.attr('target', factAddFormDialog);
          //factAddDialogStandby.show();console.log('1.75');
          factAddFormSubmitButton.attr('disabled', true);
      }
      var cardTemplatesValue = _cardTemplatesInput.attr('value');
      var tempCardCounter = 0;
      var newCardTemplatesValue = {};
      var factAddFormValue = _factAddForm.attr('value');
      cardTemplatesValue = dojo.forEach(cardTemplatesValue, function(val){
          var newKey = 'card-'+(tempCardCounter++)+'-template';
          factAddFormValue[newKey] = val;
      });
      
      factAddFormValue['fact-fact_type'] = 1; //FIXME temp hack - assume Japanese
      factAddFormValue['card-TOTAL_FORMS'] = tempCardCounter.toString();
      factAddFormValue['card-INITIAL_FORMS'] = '0'; //tempCounter; //todo:if i allow adding card templates in this dialog, must update this
      factAddFormValue['field_content-TOTAL_FORMS'] = fieldContentInputCount.toString();
      factAddFormValue['field_content-INITIAL_FORMS'] = factId ? fieldContentInputCount.toString() : '0'; //fieldContentInputCount; //todo:if i allow adding card templates in this dialog, must update this
      //factAddFormValue['fact-id']
      //alert('submitted w/args:\n' + dojo.toJson(factAddFormValue));
      
      var xhrArgs = {
          url: factId ? '/flashcards/rest/facts/'+factId : '/flashcards/rest/facts',//url: '/flashcards/rest/decks/'+factAddFormValue['fact-deck']+'/facts', //TODO get URI restfully
          content: factAddFormValue,
          handleAs: 'json',
          load: function(data){
              if (data.success) {
                  submitSuccessCallback(data, tempCardCounter);
              } else {
                  submitErrorCallback(data, tempCardCounter);
              }
          },
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
      dojo.query('textarea',factAddDialog.domNode).forEach(function(node, index, arr){
              node.value=''; });

      //destroy any error messages
      dojo.query('#factFields > .field_content_error').empty();

      //focus the first text field
      dojo.query('textarea', factAddDialog.domNode)[0].focus();
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
            //todo:pull values from the fact store for that id*/
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
                  //console.log(factFieldValues);
                  //console.log('id'+fieldsStore.getValue(item, 'id'));
                  //console.log(factFieldValues['id'+fieldsStore.getValue(item, 'id')][0]);
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
  
  
  //create field inputs, and refresh card templates
  //TODO redundant code refactor
  function createFieldInputs(evt, cardTemplatesOnCompleteCallback, factFieldsOnCompleteCallback) { //todo:refactor into 2 meths
      if (evt) {
          //add card template options
          var cardTemplatesStore = new dojo.data.ItemFileReadStore({url: '/flashcards/rest/fact_types/'+evt+'/card_templates', jsId:'cardTemplatesStore'});
          var cardTemplatesInput = dijit.byId('cardTemplatesInput');
          cardTemplatesInput.removeOption(cardTemplatesInput.getOptions());

          dojo.query('div#factFields >').forEach(function(node, index, arr) {
              if (dijit.byId(node.id)) {
                  dijit.byId(node.id).destroy();
              }
          });
          dojo.empty('factFields');
          
          var cardTemplateCounter = 0;
          cardTemplatesStore.fetch({
              onItem: function(item){
                 if (cardTemplatesStore.getValue(item, 'generate_by_default')) {
                     cardTemplatesInput.addOption({value: cardTemplatesStore.getValue(item, 'id')+"", label: cardTemplatesStore.getValue(item, 'name'), selected: 'selected'});
                 } else {
                     cardTemplatesInput.addOption({value: cardTemplatesStore.getValue(item, 'id')+"", label: cardTemplatesStore.getValue(item, 'name')});
                 }
                 //dojo.place('<input type="hidden" name="card_template-'+cardTemplateCounter+'-id" id="id_card_template-'+cardTemplateCounter+'-id" />', 'cardTemplatesHiddenInput', 'last');
              }, //Todo:select defaults (must be at least 1)
              onComplete: function(items) {
                  //todo:select the defaults.
                  cardTemplatesOnCompleteCallback(items);
              }
          });
          
          //add FieldContent textboxes (based on Fields)
          var fieldsStore = new dojo.data.ItemFileReadStore({url:'/flashcards/rest/fact_types/'+evt+'/fields', jsId:'fieldsStore', clearOnClose:true}); //todo:try with marked up one instead
          var fieldCounter = 0;
          fieldsStore.fetch({
              onItem: function(item) {
                  var tempFieldCounter = fieldCounter++; 
                  var fieldContentHeaderHTML = '<div><strong>'+fieldsStore.getValue(item, 'name')+':</strong>';
                  if (!fieldsStore.getValue(item, 'blank')) {
                      fieldContentHeaderHTML += ' (required)';
                  }
                  dojo.place(fieldContentHeaderHTML, 'factFields', 'last');
                  dojo.place('<div id="id_field_content-'+tempFieldCounter+'-content-errors" class="field_content_error" />', 'factFields', 'last');
                  var fieldTextarea = new dijit.form.SimpleTextarea({
                      name: 'field_content-'+tempFieldCounter+'-content', //fieldsStore.getValue(item, 'name'),
                      id: 'id_field_content-'+tempFieldCounter+'-content',
                      jsId: 'id_field_content_'+tempFieldCounter+'_content',
                      value: "",
                      style: "width:300px;",
                      rows: '2'
                  }).placeAt('factFields', 'last');
                  
                  //dojo.place('<input type="hidden" dojoType="dijit.form.TextBox" name="field_content-'+tempFieldCounter+'-field" id="id_field_content-'+tempFieldCounter+'id" value="'+fieldsStore.getValue(item, 'id')+'" />', 'factFields', 'last');
                  new dijit.form.TextBox({
                      name: 'field_content-'+tempFieldCounter+'-field_type',
                      id: 'id_field_content-'+tempFieldCounter+'-field_type',
                      jsId: 'id_field_content_'+tempFieldCounter+'_field_type',
                      value: fieldsStore.getValue(item, 'id'),
                      type: 'hidden'
                  }).placeAt('factFields', 'last');

                  dojo.place('</div>', 'factFields', 'last');
                  //dijit.byId(nodeName).addOption({value : dataStore.getValue(item, 'id'), label: dataStore.getValue(item, 'name')});
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
  var fieldContentInputCount = 3;//FIXME this is a terrible legacy hack... (was null;)
  
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
              dojo.byId('id_field_content-'+idx+'-content-errors').innerHTML = '<font color="red"><i>'+errorMsg.content.join('<br>')+'</i></font>';
          } else {
              dojo.empty(dojo.byId('id_field_content-'+idx+'-content-errors'));
          }
      });
      factAddFormSubmitButton.attr('disabled', false);
    }, cardTemplatesInput, factAddForm, null, true);
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
        form_values['field_content-INITIAL_FORMS'] = 
            fact_id ? field_count.toString() : '0';

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
                    console.log(fact_ui._submit_success_callback);
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
    
    fact_ui.clearFactSearch = function() {
            var cards_factSearchField = dijit.byId('cards_factSearchField');
            cards_factSearchField.attr('value', '');
            cards_clearFactSearchButton.domNode.style.visibility='hidden';
            var store = cards_factsGrid.store;
            store.close();
            //FIXME hack until we find a cleaner way to do this
            store.url = '/flashcards/rest/facts.json?fact_type=1';
            store.fetch();
            cards_factsGrid.sort(); //forces a refresh
    }

