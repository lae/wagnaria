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
            return $resource( '/api/1/shows/:showId.json', {showId: '@_id.$oid'} );
        }])
    .factory('staff', ['$resource',
        function($resource) {
            return $resource( '/api/1/staff/:memberId.json', {memberId: '@_id.$oid'} );
        }]);

angular.module('Wagnaria')
    .config([
        '$stateProvider', '$urlRouterProvider',
        function($stateProvider, $urlRouterProvider) {
            $urlRouterProvider
                .when('/', '/shows')
                .otherwise('/shows');
            $stateProvider
                .state('shows', {
                    url: '/shows',
                    templateUrl: 'tpl/shows.html',
                    resolve: {
                        Shows: ['Shows',
                            function(Shows){ console.log(Shows); return Shows.query().$promise; }
                        ]
                    },
                    controller: ['$scope', '$state', 'Shows',
                        function($scope, $state, Shows) {
                            console.log('loading shows');
                            $scope.shows = Shows;
                            $scope.localise_date = function(date) {
                                return moment(date).format('llll');
                            };
                        }]
                });
        }
    ]);
