'use strict';

moment.lang('en');

angular.module('Wagnaria', ['ui.router', 'ngResource'])
    .run([
        '$rootScope', '$state', '$stateParams',
        function ($rootScope, $state, $stateParams) {
            $rootScope.$state = $state;
            $rootScope.$stateParams = $stateParams;
            console.log('running');
        }])
    .factory('Shows', ['$resource',
        function($resource) {
            return $resource( '/api/1/shows/:showId.json', {showId: '@_id.$oid'}, {
                'getAiring': { method: 'GET', url: '/api/1/shows/airing.json', isArray: true },
                'getCompleted': { method: 'GET', url: '/api/1/shows/completed.json', isArray: true },
                'getIncomplete': { method: 'GET', url: '/api/1/shows/incomplete.json', isArray: true },
                'getUnaired': { method: 'GET', url: '/api/1/shows/unaired.json', isArray: true }
            });
        }])
    .factory('Staff', ['$resource',
        function($resource) {
            return $resource( '/api/1/staff/:memberId.json', {memberId: '@_id.$oid'} );
        }]);

angular.module('Wagnaria')
    .controller('ShowsCtrl', ['$scope', '$state', '$stateParams', 'Shows',
        function($scope, $state, $stateParams, Shows) {
            if($stateParams.showId) {
                $scope.show = Shows;
            } else {
                $scope.shows = Shows;
            }
            $scope.localise_date = function(date) {
                return moment(date).format('llll');
            };
            $scope.nipify_date = function(date) {
                return moment(date).utc().lang('ja').add('hours', +9).format('llll');
            }
            $scope.setSort = function(newSort) {
                this.reverse = this.sorted == newSort ? !this.reverse : false;
                this.sorted = newSort;
            }
        }
    ])
    .controller('StaffCtrl', ['$scope', '$state', '$stateParams', 'Staff',
        function($scope, $state, $stateParams, Staff) {
            console.log('loading staff');
            if($stateParams.memberId) {
                $scope.member = Staff;
            } else {
                $scope.staff = Staff;
            }
            $scope.setSort = function(newSort) {
                this.reverse = this.sorted == newSort ? !this.reverse : false;
                this.sorted = newSort;
            }
        }
    ])
    .controller('StatusCtrl', ['$scope', '$http',
        function($scope, $http) {
            var loadCounts = function() {
                $http({method: 'GET', url: '/api/1/shows/status.json'})
                .success(function (data) {
                    $scope.counts = data;
                })
                .error(function(data, status) {
                    console.log(status + data);
                });
            }
            loadCounts();
        }
    ]);

angular.module('Wagnaria')
    .config([
        '$stateProvider', '$urlRouterProvider',
        function($stateProvider, $urlRouterProvider) {
            $urlRouterProvider
                .when('/', '/shows/airing')
                .otherwise('/shows/airing');
            $stateProvider
                .state('shows', {
                    url: '/shows',
                    abstract: true,
                    template: '<div id="muffinbox" data-ui-view></div>',
                })
                .state('staff', {
                    url: '/staff',
                    abstract: true,
                    template: '<div id="muffinbox" data-ui-view></div>',
                })
                .state('shows.detail', {
                    url: '/{showId:[0-9a-f]{24}}',
                    templateUrl: 'tpl/shows.detail.html',
                    resolve: {
                        Shows: ['Shows', '$stateParams', function(Shows, $stateParams){ return Shows.get({showId: $stateParams.showId}).$promise; }]
                    },
                    controller: 'ShowsCtrl'
                })
                .state('shows.complete', {
                    url: '/completed',
                    templateUrl: 'tpl/completed.html',
                    resolve: {
                        Shows: ['Shows',
                            function(Shows){ return Shows.getCompleted().$promise; }
                        ]
                    },
                    controller: 'ShowsCtrl'
                })
                .state('shows.incomplete', {
                    url: '/incomplete',
                    templateUrl: 'tpl/airing.html',
                    resolve: {
                        Shows: ['Shows',
                            function(Shows){ return Shows.getIncomplete().$promise; }
                        ]
                    },
                    controller: 'ShowsCtrl'
                })
                .state('shows.unaired', {
                    url: '/unaired',
                    templateUrl: 'tpl/airing.html',
                    resolve: {
                        Shows: ['Shows',
                            function(Shows){ return Shows.getUnaired().$promise; }
                        ]
                    },
                    controller: 'ShowsCtrl'
                })
                .state('shows.airing', {
                    url: '/airing',
                    templateUrl: 'tpl/airing.html',
                    resolve: {
                        Shows: ['Shows',
                            function(Shows){ return Shows.getAiring().$promise; }
                        ]
                    },
                    controller: 'ShowsCtrl'
                })
                .state('staff.all', {
                    url: '/all',
                    templateUrl: 'tpl/staff.html',
                    resolve: {
                        Staff: ['Staff',
                            function(Staff){ return Staff.query().$promise; }
                        ]
                    },
                    controller: 'StaffCtrl'
                });
        }
    ]);

angular.module('Wagnaria')
    .directive('memberHighlight', function() {
        return {
            restrict: 'A',
            scope: { memberName: '@', progress: '@', status: '@' },
            template: '{{memberName}}',
            link: function(scope, elm, attrs) {
                if(scope.status == 'airing' || scope.status == 'incomplete'){
                    elm.addClass('staff-status-' + scope.progress);
                }
            }
        }
    })
    .directive('eta', function($timeout) {
        return {
            scope: { airtime: '=eta' },
            template: '{{eta}}',
            link: function postLink(scope, elm, attrs) {
                var timeoutId, eta, eta_min;
                function updateETA() {
                    var now = moment();
                    var air = moment(scope.airtime);
                    eta = air.from(now);
                    elm.text(eta);
                    eta_min = air.diff(now, 'minutes');
                    if(eta_min <= -30) { elm.parent().removeClass('airing'); elm.parent().addClass('subbing'); }
                    if(eta_min > -30 && eta_min <= 0) { elm.parent().removeClass('airing_1'); elm.parent().addClass('airing_now'); }
                    if(eta_min > 0 && eta_min <= 60) { elm.parent().removeClass('airing_3'); elm.parent().addClass('airing_1'); }
                    if(eta_min > 60 && eta_min <= 180) { elm.parent().removeClass('airing_6'); elm.parent().addClass('airing_3'); }
                    if(eta_min > 180 && eta_min <= 360) { elm.parent().removeClass('airing_12'); elm.parent().addClass('airing_6'); }
                    if(eta_min > 360 && eta_min <= 720) { elm.parent().addClass('airing_12'); }
                }
                function timer(nextminute) {
                    timeoutId = $timeout(function() {
                        updateETA();
                        timer(60000);
                    }, nextminute);
                }
                function secondsTilNextMinute() {
                    var current_second = moment().second();
                    return 60 - current_second;
                }
                elm.on('$destroy', function() { $timeout.cancel(timeoutId); });
                updateETA();
                timer(secondsTilNextMinute*1000);
            }
        }
    });
