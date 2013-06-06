$(function(){
    moment.lang('en');
    var Show = Backbone.Model.extend({
        urlRoot: '/shows',
        parse: function(res) {
            res.id = res._id.$oid;
            delete res._id;
            return res;
        },
        toJSONDecorated: function(){
            var air = moment(this.get("airtime").$date);
            var airJST = air.clone().utc().lang('ja').add('hours', +9);
            return _.extend(this.toJSON(), {
                local_date: air.format('llll'),
                jst_date: airJST.format('llll'),
                classes: {
                    status: {
                        tl: 'muted',
                        ed: 'muted',
                        tm: 'muted',
                        ts: 'muted'
                    }
                }
            });
}
    });
    var Shows = Backbone.Collection.extend({
        model: Show,
        url: "/shows"
    });
    var ShowListView = Backbone.View.extend({
        tagName: "table",
        className: "table table-bordered table-hover",
        initialize: function() {
            this.model.bind("reset", this.render, this);
            var self = this;
            this.model.bind("add", function (show) {
                $(self.el).append(new ShowListItemView({model: show}).render().el);
            });
        },
        render: function(eventName) {
            _.each(this.model.models, function(show) {
                $(this.el).append(new ShowListItemView({model: show}).render().el);
            }, this);
            return this;
        }
    });
    var ShowListItemView = Backbone.View.extend({
        tagName: "tr",
        template: _.template($('#tpl-show-list-item').html()),
        initialize: function() {
            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);
        },
        render: function(eventName) {
            $(this.el).html(this.template(this.model.toJSONDecorated()));
            return this;
        },
        close: function() {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    var ShowDetailView = Backbone.View.extend({
        template: _.template($('#tpl-show-details').html()),
        render: function(eventName) {
            $(this.el).html(this.template(this.model.toJSONDecorated()));
            return this;
        }
    });
    var AppRouter = Backbone.Router.extend({
        routes: {
            "": "muffinbox",
            "shows/:id": "muffin"
        },
        muffinbox: function() {
            this.showList = new Shows();
            this.showList.fetch({async: false});
            this.showListView = new ShowListView({model: this.showList});
            $('#muffinbox').html(this.showListView.render().el);
            
        },
        muffin: function(id) {
            this.muffinbox();
            this.show = this.showList.get(id);
            this.showDetails = new ShowDetailView({model: this.show});
            $('#muffin').html(this.showDetails.render().el);
            $('#muffin').modal('show');
            self = this;
            $('#muffin').on('hide', function() { self.navigate('', {trigger: true}); });
        }
    });
    var app = new AppRouter();
    Backbone.history.start();
});
