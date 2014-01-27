define([
 'backbone'
 ], function(Backbone) {
  var RateView = Backbone.View.extend({
    className: 'widget-number',
    initialize: function(attributes, options) {
      //title for each widget
      var title = $('<h1></h1>')
        .text(options.title)
        .addClass('title');

      //active rate, changes upon state change
      var rate = $('<h2></h2>')
        .text(this.model.get('rate'))
        .addClass('value');

      //metric
      var period = $('<p></p>')
        .text(options.period)
        .addClass('period');

      //adding to DOM
      this.$el.append(title);
      this.$el.append(rate);
      this.$el.append(period);

      //re-render necessary parts on model change
      var self = this;
      this.model.on('change:rate', function() {
        rate.text(self.model.get('rate'));
      });
    }
  
  });
  return RateView;
});
