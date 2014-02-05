//configuration crap
require.config({
  urlArgs: "bust="+new Date().getTime(),
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
  // 'widgets/input',
  'widgets/rate',
  'controls',
  ], function(Backbone, Select, Rate, Inputs) {
    //setting up event listeners for clicking
  var start_box = function() {
    console.log('go');
    var data = Inputs.getInputs();
    var req = $.ajax({
      url: '/go',
      type: 'POST',
      data: data
    })
  };
  var stop_box = function() {
    Backbone.trigger('stop_test');
    var req = $.ajax({
      url: '/stop',
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

  var set_serial = function() {
    var data = Inputs.getInputs();
    console.log('connecting to serial');
    var data = Inputs.getInputs();
    var req = $.ajax({
      url: '/set_serial',
      type: 'POST',
      data: data,
      success: function (evt) {alert(evt.data)}
    });
};

  var set_soundcard = function() {
    var data = Inputs.getInputs();
    console.log('connecting to soundcard');
    var data = Inputs.getInputs();
    var req = $.ajax({
      url: '/set_sound_card',
      type: 'POST',
      data: data,
      success: function (evt) {alert(evt.data)}
    });
};


  var populate = function(data) {
    var interval;
    var n_trials_var = new Backbone.Model({rate: 0});
    var n_rewards_var = new Backbone.Model({rate: 0});
    var n_trials_h = new Rate({model: n_trials_var}, {title: 'N Trials', period: ''});
    var n_reward_h = new Rate({model: n_rewards_var}, {title: 'N Reward', period: ''});
    $('#rates').append(n_trials_h.el);
    $('#rates').append(n_reward_h.el);
    Backbone.on('start_test', function() {
      interval = setInterval(function() {
        var req = $.ajax({
          url: 'http://localhost:5000/data',
          type: 'POST',
          data: data
        });
        req.done(function(resp) {
          n_trials_var.set('rate', resp.n_trials)
          n_rewards_var.set('rate', resp.n_reward)
        });
      },5000);
    });
    Backbone.on('stop_test', function() {
       clearInterval(interval);
    });
  };

  var start_site = function() {
    var data = Inputs.getInputs();
    populate(data);
    Backbone.trigger('start_test')
    }



  //kicks everything off once dom is ready 
  $(document).ready(function() {
    Inputs.createInputs();
    $(start_site);
    $('#gobutton').click(start_box)
    //$('#gobutton').click(function() {alert('asdfsdf')})
    //console.log($('#gobutton'));
    $('#stopbutton').click(stop_box)
    $('#resetbutton').click(reset_box)
    $('#mode').change(stop_box)
    $('#soundcard_select').click(set_soundcard)
  });


});
