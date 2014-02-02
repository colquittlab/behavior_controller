
//program kickoff
require([
  'backbone',
  'widgets/select',
  ], function(Backbone, Select) {
  
  var prepInputs = function() {
    //a selection widget
    var i = new Select.SelectCollection([]);
    var s = new Select.SelectOption({collection: i});
    var fer = $('<div></div>');
    fer.append('Sound Card');
    fer.append(s.el);
    $('#inputs').append(fer);
    s.$el.change(function() {
      console.log(s.getSelectedOption());
    });
    i.fetch({url:'http://localhost:5000/list_serial_ports', success: function(resp) {console.log('asdfasdf');console.log(resp)}} )
  
  };

  var prepButtons = function() {
    var startButton = $('<button></button>')
      .attr({id: 'gobutton', type: 'button'})
      .text('Start')
      .click(function() {console.log('aa')});
    $('#inputs').append(startButton);;


    //setting up event listeners for clicking
    var start_box = function() {
      var req = $.ajax({
        url: 'http://localhost:5000/go',
        type: 'POST',
        data: 'go'
      });
    };
    var stop_box = function() {
      var req = $.ajax({
        url: 'http://localhost:5000/stop',
        type: 'POST',
        data: 'stop'
      });
    };
    var reset_box = function() {
      var req = $.ajax({
        url: '/reset',
        type: 'POST',
        data: 'reset'
      });
    };
  $('#gobutton').click(start_box)
  //$('#stopbutton').click(stop_box)
  //$('#resetbutton').click(reset_box)



  };
  //kicks everything off once dom is ready 
  $(document).ready(function() {
    prepInputs(); 
    prepButtons(); 
  });
//  var prepInputs = function() {
//    return $('input').val();
//  };
//
//
//
//  var populate = function(data) {
//    var n_trials_var = new Backbone.Model({rate: 0});
//    var n_rewards_var = new Backbone.Model({rate: 0});
//    var n_trials_h = new Rate({model: n_trials_var}, {title: 'N Trials', period: ''});
//    var n_reward_h = new Rate({model: n_rewards_var}, {title: 'N Reward', period: ''});
//    $('#rates').append(n_trials_h.el);
//    $('#rates').append(n_reward_h.el);
//    setInterval(function() {
//      var req = $.ajax({
//        url: 'http://localhost:5000/data',
//        type: 'POST',
//        data: data
//      });
//      req.done(function(resp) {
//        n_trials_var.set('rate', resp.n_trials)
//        n_rewards_var.set('rate', resp.n_reward)
//      });
//    },1000);
//  };
//
//  var start_site = function() {
//    var data = prepInputs();
//    populate(data);
//  };
//
//  var start_box = function() {
//    var req = $.ajax({
//        url: 'http://localhost:5000/go',
//        type: 'POST',
//        data: 'go'
//      }).done(function() {alert('success')});
//  };
//  var stop_box = function() {
//        var req = $.ajax({
//        url: 'http://localhost:5000/stop',
//        type: 'POST',
//        data: 'stop'
//      });
//  };
//    var reset_box = function() {
//    var req = $.ajax({
//        url: 'http://localhost:5000/reset',
//        type: 'POST',
//        data: 'reset'
//      });
//  };



//  $('#gobutton').click(start_box)
//  $('#stopbutton').click(stop_box)
//  $('#resetbutton').click(reset_box)

});
