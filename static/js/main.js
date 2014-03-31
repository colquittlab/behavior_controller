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
  'widgets/textinput',
  'widgets/rate',
  'controls',
  ], function(Backbone, Select, Text, Rate, Inputs) {
    //setting up event listeners for clicking

  var make_new_box = function() {
    var data = Inputs.getInputs();
    var req = $.ajax({
      url: '/new_box',
      type: 'POST',
      data: data
    })
  };

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

  var beep = function() {
    console.log('beep');
    var data = Inputs.getInputs();
    var req = $.ajax({
      url: '/beep',
      type: 'POST',
      data: data
    })
  };
  var raise_feeder = function() {
    console.log('raise_feeder');
    var data = Inputs.getInputs();
    var req = $.ajax({
      url: '/raise_feeder',
      type: 'POST',
      data: data
    })
  };
  


  var set_serialport = function() {
    var data = Inputs.getInputs();
    console.log('connecting to serial');
    var req = $.ajax({
      url: '/set_serial_port',
      type: 'POST',
      data: data,
      success: function (evt) {alert(evt)}
    });
};

  var set_soundcard = function() {
    console.log('connecting to soundcard');
    var data = Inputs.getInputs();
    console.log(data);
    var req = $.ajax({
      url: '/set_sound_card',
      type: 'POST',
      data: Inputs.getInputs(),
      success: function (evt) {alert(evt)}
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

    $('#soundbox_select').change(make_new_box)
    $('#newboxbutton').click(make_new_box)
    $('#gobutton').click(start_box)
    //console.log($('#gobutton'));
    $('#stopbutton').click(stop_box)
    $('#resetbutton').click(reset_box)
    $('#beepbutton').click(beep)
    $('#feederbutton').click(raise_feeder)
    $('#mode').change(stop_box)
    $('#soundcard_select').click(set_soundcard)
    $('#serialport_select').click(set_serialport)
  });


});
