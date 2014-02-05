
//program kickoff
define([
  'backbone',
  'widgets/select',
  ], function(Backbone, Select) {
  
  var getInputs= function() {
    //returns an array of strings of inputs
    var inputlist = _.map($('select'), function(item) {
      var selected = $(item).find("option:selected");
      return [$(item).attr('id'), selected[0] ? selected[0].innerHTML : null]; 
    });
    //checks to look for null value and returns null if so
    var one = _.find(inputlist, function(i) { return i[1] === null});
    if (one) return null;
    var inputmap = _.object(inputlist);
    return inputmap;
  };
  var soundSelect = function() {
    //a selection widget
    var i = new Select.SelectCollection([]);
    var s = new Select.SelectOption({collection: i, id: 'soundcard_select'});
    var fer = $('<div></div>');
    fer.append('Sound Card: ');
    fer.append(s.el);
    $('#inputs').append(fer);
    s.$el.change(function() {
      console.log(getInputs());
    });
    i.fetch({
      url:'http://localhost:5000/list_sound_cards',
      success: function(resp) {console.log('Sound Card Fetch:');console.log(resp)}
    });
  
  };
  var serialSelect = function() {
    //a selection widget
    var i = new Select.SelectCollection([]);
    var s = new Select.SelectOption({collection: i, id: 'serialport_select'});
    var fer = $('<div></div>');
    fer.append('Serial Port: ');
    fer.append(s.el);
    $('#inputs').append(fer);
    s.$el.change(function() {
      console.log(getInputs());
    });
    i.fetch({
      url:'http://localhost:5000/list_serial_ports',
      success: function(resp) {console.log('Serial Port Fetch');console.log(resp)}
    });
  };
  var modeSelect = function() {
    //a selection widget
    var i = new Select.SelectCollection([]);
    var s = new Select.SelectOption({collection: i, id: 'mode'});
    var fer = $('<div></div>');
    fer.append('Mode: ');
    fer.append(s.el);
    $('#inputs').append(fer);
    s.$el.change(function() {
      console.log(getInputs());
    });
    i.fetch({
      url:'http://localhost:5000/list_modes',
      success: function(resp) {console.log('Mode fetch');console.log(resp)}
    });
  };
  var birdnameInput = function() {
    //a selection widget
    var i = new Input.InputCollection([]);
    var s = new Input.SelectOption({collection: i, id: 'birdname'});
    var fer = $('</br><div></div>');
    fer.append('Bird Name: ');
    fer.append(s.el);
    $('#inputs').append(fer);
    s.$el.change(function() {
      console.log(getInputs());
    });
    i.fetch({
      url:'http://localhost:5000/list_serial_ports',
      success: function(resp) {console.log('asdfasdf');console.log(resp)}
    });
  };

  var prepButtons = function() {
    var startButton = $('<button></button>')
      .attr({id: 'gobutton', type: 'button'})
      .text('Start');
    var resetButton = $('<button></button>')
      .attr({id: 'resetbutton', type: 'button'})
      .text('Reset');
    var stopButton = $('<button></button>')
      .attr({id: 'stopbutton', type: 'button'})
      .text('stop');

    $('#buttons').append(startButton);
    $('#buttons').append(resetButton);
    $('#buttons').append(stopButton);

  };

  //kicks everything off once dom is ready 
  var createInputs = function() {
    soundSelect(); 
    serialSelect(); 
    // birdnameInput();
    modeSelect();
    prepButtons(); 
  };
  return {createInputs: createInputs, getInputs: getInputs};

});
