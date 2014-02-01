//program kickoff
require([
  'backbone',
  'widgets/select',
  ], function(Backbone, Select, Rate) {
  var prepInputs = function() {
    return $('input').val();
  };



  var populate = function(data) {
    setInterval(function() {
      var req = $.ajax({
        url: 'http://localhost:5000/data',
        type: 'POST',
        data: data
      });
      req.done(function(resp) {
        //set data for rates
        //n_trials_var.set('rate', resp.n_trials)
        //n_rewards_var.set('rate', resp.n_reward)
      });
    },1000);
  };

  var start_site = function() {
    var data = prepInputs();
    populate(data);
  };

  var start_box = function() {
    var req = $.ajax({
        url: 'http://localhost:5000/go',
        type: 'POST',
        data: 'go'
      }).done(function() {alert('success')});
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
        url: 'http://localhost:5000/reset',
        type: 'POST',
        data: 'reset'
      });
  };


  //kicks everything off once dom is ready 
  $(document).ready(function() {
    $(start_site);
    var req = $.ajax({
        url: 'http://localhost:5000/list_serial_ports',
        type: 'GET'
    }).done(function(resp) {
      var i = new Backbone.Collection(_.map(JSON.parse(resp), function(i) { return {foo: i}}));
      var s = new Select({collection: i});
      $('body').append(s.el);
      s.$el.change(function() {
        console.log(s.getSelectedOption());
      })
    });
  });

  $('#gobutton').click(start_box)
  $('#stopbutton').click(stop_box)
  $('#resetbutton').click(reset_box)

});
