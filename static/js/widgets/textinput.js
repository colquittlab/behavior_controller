define([
 'backbone'
 ], function(Backbone) {
  var TextInputOption = Backbone.View.extend({
    tagName: 'input',
    className: 'text',
    initialize: function(attributes, options) {
      //re-render necessary parts on model change
      var self = this;
      this.collection.on('reset', function() {self.render()});
      this.render();
    },
    render: function() {
      var i = this.collection.map(function(item){
        return '<option value="' + item.get('foo')+ '">'+ item.get('foo') +'</option>';
      });
      this.$el.html(i.join(' '));
    },
  
  });
  var TextInputCollection = Backbone.Collection.extend({
    fetch: function(options) {
      var self = this;
      var req = $.ajax({
          url: options.url,
          type: 'GET'
      }).done(function(resp) {
        var parsed = JSON.parse(resp);
        self.reset(_.map(parsed, function(i) { return {foo: i}})); 
        if (options.success) options.success(parsed);
      });
    },
  });
  var SelectWidget = Backbone.View.extend({
    tagName: 'div',
    className: 'select-widget',
  });
  var output = {
    TextInputOption: TextInputOption,
    TextInputCollection: TextInputCollection,
  };





  return output;
});
