var App = {}
var App = {
Models : {},
Collections: {},	
Views: {},
Router: {}
};
 
//DECLARING MODEL
App.Models.Post = Backbone.Model.extend({});
 
// DECLARING Collection
App.Collections.Blog = Backbone.Collection.extend({
model: App.Models.Post,
url: '/api/get_recent_posts/'
});
 
// DECLARING BLOG VIEW
App.Views.Blog = Backbone.View.extend({
el: 'li',
initialize: function(){
_.bindAll(this);
this.collection = new App.Collections.Blog;
this.collection.on('reset', this.render, this);
this.collection.fetch();
//console.log('initialize function');
},
render: function(){
//_.bindAll(this, 'render');
//console.log(this.collection);
var posts = this.collection.models[0].attributes; //actual response as the format is not the best
console.log(posts);
var template = _.template( $("#posts_template").html(), posts );
this.$el.html( template );
return this;
}
});
 
 
App.blogView = new App.Views.Blog({el: $('#posts-container')});
