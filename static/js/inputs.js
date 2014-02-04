
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
  var soundInput = function() {
    //a selection widget
    var i = new Select.SelectCollection([]);
    var s = new Select.SelectOption({collection: i, id: 'Sound Card'});
    var fer = $('<div></div>');
    fer.append('Sound Card');
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

    $('#inputs').append(startButton);
    $('#inputs').append(resetButton);
    $('#inputs').append(stopButton);

  };

  //kicks everything off once dom is ready 
  var createInputs = function() {
    soundInput(); 
    prepButtons(); 
  };
  return {createInputs: createInputs, getInputs: getInputs};

});
