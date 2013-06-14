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
            if (this.get("status") == 'complete') {
                var eta = blame = s_air = s_tl = s_ed = s_tm = s_ts = '';
            }
            else if (now.isBefore(air)) {
                var s_tl = s_ed = s_tm = s_ts = 'muted';
                var s_air = '';
                if (now.isAfter(air.clone().subtract('hours', 12.5))) { s_air = 'airing_12'; }
                if (now.isAfter(air.clone().subtract('hours', 6.5))) { s_air = 'airing_6'; }
                if (now.isAfter(air.clone().subtract('hours', 3.5))) { s_air = 'airing_3'; }
                if (now.isAfter(air.clone().subtract('hours', 1.5))) { s_air = 'airing_1'; }
                var blame = "Broadcast (" + this.get("channel") + ")";
                if (now.isAfter(air.clone().subtract('minutes', 30))) { s_air = 'airing_now'; }
                else { blame = "Pre-" + blame; }
                var cdobj = countdown(air, function(ts) { eta = ts; $('#'+self.id+'_cd').html(eta.toHTML()); if(eta.value>0) { location.reload() } }, countdown.DAYS|countdown.HOURS|countdown.MINUTES|countdown.SECONDS, 3);
            }
            else {
                var s_tl = s_ed = s_tm = s_ts = 'text-error';
                var s_air = 'error';
                progress = this.get("progress");
                var eta = "Aired 'n Subbing"
                if (progress.translated) { s_tl = 'text-success'; }
                if (progress.edited) { s_ed = 'text-success'; }
                if (progress.timed) { s_tm = 'text-success'; }
                if (progress.typeset) { s_ts = 'text-success'; }
                var st = this.get('staff');
                switch(false) {
                    case progress.encoded: blame = 'Encoding'; break;
                    case progress.translated: blame = 'Translation ('+st.translator.name+')'; break;
                    case progress.edited: blame = 'Editing ('+st.editor.name+')'; break;
                    case progress.timed: blame = 'Timing ('+st.timer.name+')'; break;
                    case progress.typeset: blame = 'Typesetting ('+st.typesetter.name+')'; break;
                    case progress.qc: blame = 'Quality Control'; s_air = 'success'; break;
                }
            }
            return _.extend(this.toJSON(), {
                local_date: air.format('llll'),
                jst_date: airJST.format('llll'),
                eta: eta,
                blame: blame,
                classes: {
                    status: {
                        air: s_air,
                        tl: s_tl,
                        ed: s_ed,
                        tm: s_tm,
                        ts: s_ts
                    }
                }
            });
}
    });
    var Member = Backbone.Model.extend({
        urlRoot: '/staff'
    });
    var Shows = Backbone.Collection.extend({
        model: Show,
        initialize: function(url) {
            this.url = url;
        },
        comparator: function(a, b) {
            if(this.url=="shows/complete"){
                a = a.get('titles').english.toLowerCase();
                b = b.get('titles').english.toLowerCase();
                return a > b ? 1
                    : a < b ? -1
                    :          0;
            }
            else{
                a = moment(a.get('airtime').$date);
                b = moment(b.get('airtime').$date);
                return a.isAfter(b) ?  1
                    : a.isBefore(b) ? -1
                    :                  0;
            }
        }
    });
    var Staff = Backbone.Collection.extend({
        model: Member,
        url: '/staff'
    });
    var ShowsView = Backbone.View.extend({
        tagName: "table",
        className: "pure-table pure-table-horizontal",
        initialize: function(obj, type) {
            this.model.bind("reset", this.render, this);
            this.type = type;
            var self = this;
            this.model.bind("add", function(show) { self.itemview(show, self) });
        },
        render: function(eventName) {
            var self = this;
            _.each(this.model.models, function(show) { self.itemview(show, self) }, this);
            switch(this.type) {
                case "airing": thead = "<th>Series</th><th>Airtime</th><th>Time 'til Air</th><th>Status</th>"; break;
                case "complete": thead = "<th>Series</th><th>Last Aired</th><th>Episodes</th><th>Translator</th><th>Editor</th><th>Timer</th><th>Typesetter</th>"; break;
            }
            thead = '<thead><tr>'+thead+'</tr></thead>';
            $(this.el).prepend(thead);
            return this;
        },
        itemview: function(show, self) {
            switch(self.type) {
                case "airing": item = new AiringItemView({model: show}); break;
                case "complete": item = new CompleteItemView({model: show}); break;
            }
            $(self.el).append(item.render().el);
        },
    });
    var ItemView = Backbone.View.extend({
        tagName: "tr",
        initialize: function(attr) {
            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);
        },
        render: function(eventName) {
            this.prerender(eventName);
            return this;
        },
        prerender: function(eventName) {
            this.jsondeco = this.model.toJSONDecorated();
            $(this.el).html(this.template(this.jsondeco));
            var sid = this.model.id;
            $(this.el).click(function() { app.navigate('shows/'+sid, true); });
        },
        close: function() {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    var AiringItemView = ItemView.extend({
        template: _.template($("#tpl-airing-item").html()),
        render: function(eventName) {
            this.prerender(eventName);
            $(this.el).addClass(this.jsondeco.classes.status.air);
            return this;
        }
    });
    var CompleteItemView = ItemView.extend({
        template: _.template($("#tpl-complete-item").html())
    });
    var ShowDetailView = Backbone.View.extend({
        template: _.template($('#tpl-show-details').html()),
        render: function(eventName) {
            $(this.el).html(this.template(this.model.toJSONDecorated()));
            return this;
        }
    });
    var StaffView = Backbone.View.extend({
        initialize: function(obj, type) {
            this.model.bind("reset", this.render, this);
            var self = this;
            this.model.bind("add", function(member) { self.itemview(member, self) });
        },
        render: function(eventName) {
            var self = this;
            _.each(this.model.models, function(member) { self.itemview(member, self) }, this);
            return this;
        },
        itemview: function(member, self) {
            item = new MemberItemView({model: member});
            $(self.el).append(item.render().el);
        },
    });
    var MemberItemView = Backbone.View.extend({
        template: _.template($("#tpl-member-item").html()),
        initialize: function(attr) {
            this.model.bind("change", this.render, this);
            this.model.bind("destroy", this.close, this);
        },
        render: function(eventName) {
            this.prerender(eventName);
            return this;
        },
        prerender: function(eventName) {
            this.json = this.model.toJSON();
            $(this.el).html(this.template(this.json));
            //var sid = this.model.id;
            //$(this.el).click(function() { app.navigate('staff/'+sid, true); });
        },
        close: function() {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    var AppRouter = Backbone.Router.extend({
        routes: {
            "": "airing",
            "shows/unaired": "future",
            "shows/complete": "completed",
            "shows/incomplete": "incomplete",
            "shows/:id": "muffin",
            "staff": "stafflist"
        },
        loadShows: function(showsToLoad) {
            if (this.loadedShows != showsToLoad) {
                this.loadedShows = showsToLoad;
                this.showList = new Shows(this.loadedShows);
                this.showList.fetch({async: false});
            }
            $('.pure-menu li').removeClass('pure-menu-selected');
            $('#tablefooter').show();
        },
        muffin: function(id) {
            this.show = new Show({id: id});
            this.show.fetch({async: false});
            this.showDetails = new ShowDetailView({model: this.show});
            $('#muffinbox').html(this.showDetails.render().el);
            $('#tablefooter').hide();
            var self = this;
            $('.back-button').click(function() { if (document.referer) { history.back(); } else { self.navigate('', true); } });
        },
        airing: function() {
            this.loadShows("shows/airing");
            $('#nav_airing').addClass('pure-menu-selected');
            this.showsView = new ShowsView({model: this.showList}, "airing");
            $('#muffinbox').html(this.showsView.render().el);
        },
        completed: function() {
            this.loadShows("shows/complete");
            $('#nav_complete').addClass('pure-menu-selected');
            this.showsView = new ShowsView({model: this.showList}, "complete");
            $('#muffinbox').html(this.showsView.render().el);
        },
        incomplete: function() {
            this.loadShows("shows/incomplete");
            $('#nav_incomplete').addClass('pure-menu-selected');
            this.showsView = new ShowsView({model: this.showList}, "airing");
            $('#muffinbox').html(this.showsView.render().el);
        },
        future: function() {
            this.loadShows("shows/unaired");
            $('#nav_future').addClass('pure-menu-selected');
            this.showsView = new ShowsView({model: this.showList}, "airing");
            $('#muffinbox').html(this.showsView.render().el);
        },
        stafflist: function() {
            if (this.loadedShows) {
                this.loadedShows = "";
            }
            this.staffList = new Staff();
            this.staffList.fetch({async: false});
            $('.pure-menu li').removeClass('pure-menu-selected');
            $('#nav_staff').addClass('pure-menu-selected');
            this.staffView = new StaffView({model: this.staffList});
            $('#muffinbox').html(this.staffView.render().el);
        },
    });
    var app = new AppRouter();
    Backbone.history.start();
});
$('#toggle').click(function() {
    $('#basket').toggleClass('active');
    $('#parasol').toggleClass('active');
    $(this).text($(this).text() == '»'?'«':'»');
});
