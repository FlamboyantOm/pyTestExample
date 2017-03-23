var app = angular.module('myStatApp', ["chart.js","ngRoute"])


app.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
    $interpolateProvider.endSymbol('}]}');
  });

app.config(function($routeProvider) {
   $routeProvider

    .when("/red", {
        template : "<h1>Banana</h1><p>Bananas contain around 75% water.</p>"
    })
    .when("/blue", {
        template : "<h1>Tomato</h1><p>Tomatoes contain around 95% water.</p>"
    })
    .otherwise({
    
        template : "<h1>None</h1><p>Nothing has been selected,</p>"
    });
    console.log($routeProvider);
});


app.controller('myStatController', function($scope,$http) {
    $scope.counter = 0;
    $scope.selectedType = "Signature Portal Summary :"
    // Bar Chart Signature Statistics
    $scope.barChartSignatureCountOptions={title:{display:true,text:"Typewise Signature Statistics"},scales:{yAxes:[{scaleLabel:{display:true,labelString:'Signatures'}}],xAxes:[{scaleLabel:{display:true,labelString:'Signature Types'}}]  }}
    $scope.barChartSignatureCountLabels = [];
    $scope.barChartSignatureCountData=  []
    $scope.pieChartSignatureCountOptions={title:{display:true,text:"Typewise Signature Statistics"}}

   // Bar Chart User Statistics
    $scope.barChartUserCountOptions={title:{display:true,text:"Userwise Signature Statistics"},scales:{yAxes:[{scaleLabel:{display:true,labelString:'Signatures'}}],xAxes:[{scaleLabel:{display:true,labelString:'Users'}}]  }}
    $scope.barChartUserCountLabels = [];
    $scope.barChartUserCountData=  []

    // Bar Chart Cluster Statistics
    $scope.barChartClusterCountOptions={title:{display:true,text:"Typewise Cluster Statistics"},scales:{yAxes:[{scaleLabel:{display:true,labelString:'Clusters'}}],xAxes:[{scaleLabel:{display:true,labelString:'Signature Types'}}]  }}
    $scope.barChartClusterCountLabels = [];
    $scope.barChartClusterCountData=  []

     // Bar Signature Stages Statistics
    $scope.barChartSigStateCountOptions={title:{display:true,text:"Signature State Statistics"},scales:{yAxes:[{scaleLabel:{display:true,labelString:'Signatures'}}],xAxes:[{scaleLabel:{display:true,labelString:'Signature State'}}]  }}
    $scope.barChartSigStateCountLabels = [];
    $scope.barChartSigStateCountData=  []

    $http.get("/statistics/0/")
        .then(function(response) {
        $scope.types = response.data.main_types ;
        for ( key in response.data.TypeCount){
            $scope.barChartSignatureCountLabels.push($scope.types[key]);
            $scope.barChartSignatureCountData.push(String(response.data.TypeCount[key]))
        }
        for ( key in response.data.UserCount){
            $scope.barChartUserCountLabels.push(key);
            $scope.barChartUserCountData.push(String(response.data.UserCount[key]));
        }
        for ( key in response.data.ClusterCount){
            $scope.barChartClusterCountLabels.push($scope.types[key]);
            $scope.barChartClusterCountData.push(String(response.data.ClusterCount[key]))
        }

        for ( key in response.data.SignatureStages){
            $scope.barChartSigStateCountLabels.push(key);
            $scope.barChartSigStateCountData.push(String(response.data.SignatureStages[key]));
        }


    });


    // event when main dropdown for type is change
    $scope.updateSignatureView = function() {
        $scope.selectedType = $scope.types[$scope.selectedClusterType];
    };






});
