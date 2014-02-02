//configuration crap
require.config({
  paths: {
    'underscore': 'vendor/underscore/underscore',
    'backbone': 'vendor/backbone/backbone',
    'jquery': 'vendor/jquery/jquery-2.0.3.min',
  
  },
  shim: {
    "underscore": {
      "exports": "_"
    },
    "backbone": {
      "deps": ["underscore", "jquery"],
      "exports": "Backbone"
    }
  }
});

//program kickoff
require([
  'backbone',
  'widgets/select',
  'widgets/rate',
  'inputs'
  ], function(Backbone, Select, Rate, Inputs) {
  var prepInputs = function() {
    return $('input').val();
  };



  var populate = function(data) {
    var n_trials_var = new Backbone.Model({rate: 0});
    var n_rewards_var = new Backbone.Model({rate: 0});
    var n_trials_h = new Rate({model: n_trials_var}, {title: 'N Trials', period: ''});
    var n_reward_h = new Rate({model: n_rewards_var}, {title: 'N Reward', period: ''});
    $('#rates').append(n_trials_h.el);
    $('#rates').append(n_reward_h.el);
    setInterval(function() {
      var req = $.ajax({
        url: 'http://localhost:5000/data',
        type: 'POST',
        data: data
      });
      req.done(function(resp) {
        n_trials_var.set('rate', resp.n_trials)
        n_rewards_var.set('rate', resp.n_reward)
      });
    },1000);
  };

  var start_site = function() {
    var data = prepInputs();
    populate(data);
  };



  //kicks everything off once dom is ready 
  $(document).ready(function() {
    $(start_site);
  });


});
