var app = angular.module('plunker', ['nvd3']);

// TODO check if any parameters have changed if not dont fire new job retrieve old data

app.controller('MainCtrl', function($scope,$log,$http,$timeout) {
    var now = Date.now();
    var max = now;
    max = new Date(max);
    max.setDate(max.getDate() + 1);
$scope.example =  {
         value: new Date(now),
         min:new Date(now),
         max:max
       };

$scope.init=function (a) {
  $scope.fields =a;
  $scope.loading = true;
  $scope.choice = null;
    $log.log(a);
};
  $scope.options = {
            chart: {
                type: 'lineChart',
                height: 450,
                margin : {
                    top: 20,
                    right: 20,
                    bottom: 40,
                    left: 55
                },
                x: function(d){ return d.x; },
                y: function(d){ return d.y; },
                useInteractiveGuideline: true,
                dispatch: {
                    stateChange: function(e){ console.log("stateChange"); },
                    changeState: function(e){ console.log("changeState"); },
                    tooltipShow: function(e){ console.log("tooltipShow"); },
                    tooltipHide: function(e){ console.log("tooltipHide"); }
                },
                xAxis: {
                    axisLabel: 'Distance (km)'
                },
                yAxis: {
                    axisLabel: 'Value',
                    tickFormat: function(d){
                        return d3.format('.02f')(d);
                    },
                    axisLabelDistance: -10
                },
                callback: function(chart){
                    console.log("!!! lineChart callback !!!");
                }
            },
            title: {
                enable: true,
                text: 'Title for Line Chart'
            },
            subtitle: {
                enable: true,
                text: 'Subtitle for simple line chart. Lorem ipsum dolor sit amet, at eam blandit sadipscing, vim adhuc sanctus disputando ex, cu usu affert alienum urbanitas.',
                css: {
                    'text-align': 'center',
                    'margin': '10px 13px 0px 7px'
                }
            },
            caption: {
                enable: true,
                html: '<b>Figure 1.</b> Lorem ipsum dolor sit amet, at eam blandit sadipscing, <span style="text-decoration: underline;">vim adhuc sanctus disputando ex</span>, cu usu affert alienum urbanitas. <i>Cum in purto erat, mea ne nominavi persecuti reformidans.</i> Docendi blandit abhorreant ea has, minim tantas alterum pro eu. <span style="color: darkred;">Exerci graeci ad vix, elit tacimates ea duo</span>. Id mel eruditi fuisset. Stet vidit patrioque in pro, eum ex veri verterem abhorreant, id unum oportere intellegam nec<sup>[1, <a href="https://github.com/krispo/angular-nvd3" target="_blank">2</a>, 3]</sup>.',
                css: {
                    'text-align': 'justify',
                    'margin': '10px 13px 0px 7px'
                }
            },
            zoom: {
                    //NOTE: All attributes below are optional
                    enabled: true,
                    scaleExtent: [1, 10],
                    useFixedDomain: true,
                    useNiceScale: false,
                    horizontalOff: false,
                    verticalOff: false,
                    unzoomEventType: 'dblclick.zoom'
                }};

        $scope.data = null;
        $scope.loading = true;

        $scope.getResults = function() {

      $log.log('test');

      // get the URL from the input
        var course_id = $scope.choice;
        var date_time = new Date ($scope.example.value);
        Date.prototype.getUnixTime = function() { return this.getTime()/1000|0 };
        var unix = date_time.getUnixTime();
      // fire the API request
      $http.post('/start', {'course_id': course_id,'date_time':unix}).
        success(function(results) {
          $log.log(results);
          getData(results);
          //$scope.data = null;
          $scope.loading = true;
          $scope.submitButtonText = 'Loading...';
          $scope.urlerror = false;
        }).
        error(function(error) {
          $log.log(error);
        });

    };
    function getData(jobID) {

        var timeout = '';

        var poller = function () {
            // fire another request
            $http.get('/results?jobid=' + jobID).success(function (data, status, headers, config) {
                if (status === 202) {
                    $log.log(data, status);
                } else if (status === 200) {
                    //$log.log(data);


                    $scope.submitButtonText = "Submit";
                    // $scope.b= JSON.parse(data);
                    $log.log(data)
                    //var testdata = d3.zip(data[0].x,data[0].y);
                    var hr=[];
                    var alts = [];
                    for (var i = 0; i < (data[0].x.length); i++) {
                alts.push({x: data[0].x[i], y: data[0].y[i]});
                hr.push({x: data[0].x[i], y: data[0].hr[i]});    }


            var meme = [
                {
                    values: alts,      //values - represents the array of {x,y} data points
                    key: data[0].key[1], //key  - the name of the series.
                    color: '#ff4a52',  //color - optional: choose your own line color.
                    strokeWidth: 2,
                    classed: 'dashed',
                    area: true
                },
                {
                    values: hr,
                    key: 'Time Wave',
                    color: '#2ca02c'
                }/*,
                {
                    values: sin2,
                    key: 'Another sine wave',
                    color: '#7777ff',
                    area: true      //area - set to true if you want this line to turn into a filled area chart.
                }*/
            ];
                    $log.log(meme);
                    $scope.data = meme;
                    $scope.loading = false;
                    window.dispatchEvent(new Event('resize'));

                    $timeout.cancel(timeout);
                    //do_plot(data);


                    return false;
                }
                // continue to call the poller() function every 2 seconds
                // until the timeout is cancelled
                timeout = $timeout(poller, 2000);
            }).error(function (error) {
                $log.log(error);
                $scope.loading = false;
                $scope.submitButtonText = "Submit";
                $scope.urlerror = true;
            });
        };


        poller();

    }

        /*Random Data Generator */
        function sinAndCos() {
            var sin = [],sin2 = [],
                cos = [];

            //Data is represented as an array of {x,y} pairs.
            for (var i = 0; i < 100; i++) {
                sin.push({x: i, y: Math.sin(i/10)});
                sin2.push({x: i, y: i % 10 == 5 ? null : Math.sin(i/10) *0.25 + 0.5});
                cos.push({x: i, y: .5 * Math.cos(i/10+ 2) + Math.random() / 10});
            }

            //Line chart data should be sent as an array of series objects.
            var meme = [
                {
                    values: sin,      //values - represents the array of {x,y} data points
                    key: 'Sine Wave', //key  - the name of the series.
                    color: '#ff4a52',  //color - optional: choose your own line color.
                    strokeWidth: 2,
                    classed: 'dashed'
                },
                {
                    values: cos,
                    key: 'Cosine Wave',
                    color: '#2ca02c'
                },
                {
                    values: sin2,
                    key: 'Another sine wave',
                    color: '#7777ff',
                    area: true      //area - set to true if you want this line to turn into a filled area chart.
                }
            ];


            $log.log(meme);
            return meme;
        }
});