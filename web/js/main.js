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
            var now = moment();
            var self = this;
            if (now.isBefore(air)) {
                var s_tl = s_ed = s_tm = s_ts = 'muted';
                var blame = "Pre-Broadcast (" + this.get("channel") + ")";
                var cdobj = countdown(air, function(ts) { eta = ts; $('#'+self.id+'_cd').html(eta.toHTML()); }, countdown.DAYS|countdown.HOURS|countdown.MINUTES|countdown.SECONDS, 3);
            }
            else {
                var s_tl = s_ed = s_tm = s_ts = 'text-error';
                progress = this.get("progress");
                var eta = "Aired 'n Subbing"
                switch(true) {
                    case progress.translated: s_tl = 'text-success';
                    case progress.edited: s_ed = 'text-success';
                    case progress.timed: s_tm = 'text-success';
                    case progress.typeset: s_ts = 'text-success';
                }
                var st = this.get('staff');
                switch(false) {
                    case progress.encoded: blame = 'Encode'; break;
                    case progress.translated: blame = 'Translation ('+st.translator.name+')'; break;
                    case progress.edited: blame = 'Edit ('+st.editor.name+')'; break;
                    case progress.timed: blame = 'Timing ('+st.timer.name+')'; break;
                    case progress.typeset: blame = 'Typesetting ('+st.typesetter.name+')'; break;
                    case progress.qc: blame = 'Quality Control'; break;
                }
            }
            return _.extend(this.toJSON(), {
                local_date: air.format('llll'),
                jst_date: airJST.format('llll'),
                eta: eta,
                blame: blame,
                classes: {
                    status: {
                        tl: s_tl,
                        ed: s_ed,
                        tm: s_tm,
                        ts: s_ts
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
