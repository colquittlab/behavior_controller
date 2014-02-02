
//program kickoff
define([
  'backbone',
  'widgets/select',
  ], function(Backbone, Select) {
  
  var soundInput = function() {
    //a selection widget
    var i = new Select.SelectCollection([]);
    var s = new Select.SelectOption({collection: i, id: 'Sound Card'});
    var fer = $('<div></div>');
    fer.append('Sound Card');
    fer.append(s.el);
    $('#inputs').append(fer);
    //s.$el.change(function() {
    //  console.log(s.getSelectedOption());
    //});
    i.fetch({url:'http://localhost:5000/list_serial_ports', success: function(resp) {console.log('asdfasdf');console.log(resp)}} )
  
  };

  var prepButtons = function() {
    var startButton = $('<button></button>')
      .attr({id: 'gobutton', type: 'button'})
      .text('Start');
    var resetButton = $('<button></button>')
      .attr({id: 'resetbutton', type: 'button'})
      .text('Reset');

    $('#inputs').append(startButton);
    $('#inputs').append(resetButton);

  };

  //kicks everything off once dom is ready 
  var createInputs = function() {
    soundInput(); 
    prepButtons(); 
  };
  return {createInputs: createInputs};

});
