var mapDiv = document.getElementById('map');
var map = new google.maps.Map(mapDiv, {
  center: new google.maps.LatLng(46, 11),
  mapTypeId: google.maps.MapTypeId.SATELLITE,
  zoom: 7
});
