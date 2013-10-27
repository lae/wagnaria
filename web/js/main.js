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
                'getCompleted': { method: 'GET', url: '/api/1/shows/completed.json', isArray: true }
            });
        }])
    .factory('staff', ['$resource',
        function($resource) {
            return $resource( '/api/1/staff/:memberId.json', {memberId: '@_id.$oid'} );
        }]);

angular.module('Wagnaria')
    .controller('ShowsCtrl', ['$scope', '$state', '$stateParams', 'Shows',
        function($scope, $state, $stateParams, Shows) {
            console.log('loading shows');
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
                    template: '<div id="muffinbox" data-ui-view></div>' +
                        '',
                })
                .state('shows.detail', {
                    url: '/{showId:[0-9a-f]{24}}',
                    templateUrl: 'tpl/shows.detail.html',
                    resolve: {
                        Shows: ['Shows', '$stateParams', function(Shows, $stateParams){ return Shows.get({showId: $stateParams.showId}).$promise; }]
                    },
                    controller: 'ShowsCtrl'
                })
                .state('shows.completed', {
                    url: '/completed',
                    templateUrl: 'tpl/completed.html',
                    resolve: {
                        Shows: ['Shows',
                            function(Shows){ return Shows.getCompleted().$promise; }
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
                });
        }
    ]);

angular.module('Wagnaria')
    .directive('memberHighlight', function() {
        return {
            restrict: 'A',
            scope: { member: '=memberHighlight' },
            template: '{{member.name}}',
            link: function(scope, elm, attrs) {
                //function updateMember() {
                    //elm.text(attrs.memberHighlight.name);
                //}
            }
        }
    })
    .directive('eta', function($timeout) {
        return {
            scope: { airtime: '=eta' },
            template: '{{eta}}',
            link: function postLink(scope, elm, attrs) {
                var timeoutId, eta;
                function updateETA() {
                    var now = moment();
                    var air = moment(scope.airtime);
                    eta = air.from(now);
                    elm.text(eta);
                }
                function timer(nextminute) {
                    timeoutId = $timeout(function() {
                        updateETA();
                        timer(1000);
                    }, nextminute);
                }
                function secondsTilNextMinute() {
                    var current_second = moment().second();
                    return 60 - current_second;
                }
                elm.on('$destroy', function() { $timeout.cancel(timeoutId); });
                updateETA();
                timer(1000);
            }
        }
    });
