document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([51.505, -0.09], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var coordinates = [];
    var markers = [];

    map.on('click', function (e) {
        var marker = L.marker(e.latlng).addTo(map);
        markers.push(marker);

        coordinates.push({ latitude: e.latlng.lat, longitude: e.latlng.lng });

        document.getElementById('coordinates').value = JSON.stringify(coordinates);
    });
});
