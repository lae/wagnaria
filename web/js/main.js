$(function(){
    var Show = Backbone.Model.extend({
        urlRoot: '/shows'
    });
    var Shows = Backbone.Collection.extend({
        model: Show,
        url: "/shows"
    });
    var ShowListView = Backbone.View.extend({
        tagName: "ul",
        initialize: function(){
            this.model.bind("reset", this.render, this);
            var self = this;
            this.model.bind("add", function (show) {
                $(self.el).append(new ShowListItemView({model: show}).render().el);
            });
        },
        render: function(eventName) {
            _.each(this.model.models, function(show) {
                console.log("Adding a show?");
                $(this.el).append(new ShowListItemView({model: show}).render().el);
            }, this);
            return this;
        }
    });
    var ShowListItemView = Backbone.View.extend({
        tagName: "li",
        template: _.template($('#tpl-show-list-item').html()),
        initialize: function() {
            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);
        },
        render: function(eventName) {
            $(this.el).html(this.template(this.model.toJSON()));
            return this;
        },
        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    var ShowView = Backbone.View.extend({
        template: _.template($('#tpl-show-info').html()),
        render:function (eventName) {
            $(this.el).html(this.template(this.model.toJSON()));
            return this;
        }
    });
    var AppRouter = Backbone.Router.extend({
        routes: {
            "": "list",
            "shows/:id":"list"
        },
        list: function() {
            this.showList = new Shows();
            this.showList.fetch({async: false});
            this.showListView = new ShowListView({model: this.showList});
            $('#showlist').html(this.showListView.render().el);
        }
    });
    var app = new AppRouter();
    Backbone.history.start();
});
