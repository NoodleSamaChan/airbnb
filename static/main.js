const searchbar = document.getElementById("searchbar");

const map = L.map('map').setView([51.505, -0.09], 13);
const popup = L.popup();

const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

async function update_announce(bounds) {
  // tl.lat = ne.lat
  // tl.lng = sw.lng
  // br.lat = sw.lat
  // br.lng = ne.lng
  let tl_lat = bounds._northEast.lat;
  let tl_lng = bounds._southWest.lng;
  let br_lat = bounds._southWest.lat;
  let br_lng = bounds._northEast.lng;

  let query = `http://127.0.0.1:5000/lair?tl_lat=${tl_lat}&tl_lng=${tl_lng}&br_lat=${br_lat}&br_lng=${br_lng}`;
  if (searchbar.value != "") {
    let search = searchbar.value;
    query += `&search=${search}`;
  }
  console.log(query);

  let results = await fetch(query, {
    method: "GET"
  });
  let ret = await results.json();

  // TODO: Le payload est mal formé ici
  console.log(ret);
}

function update_points(e) {
  let bounds = map.getBounds();
  update_announce(bounds);  
}

map.on('moveend', update_points);
map.on('zoomend', update_points);
searchbar.addEventListener('input', update_points);


function onMapClick(e) {
  console.log(e.latlng);

  let lat = e.latlng.lat;
  let lng = e.latlng.lng;
  popup
    .setLatLng(e.latlng)
    .setContent(`
<form action="" class="create_announce" onsubmit="insertDocument();return false;">
  <div class="form-example">
    <label for="titre">Titre de l'annonce</label>
    <input type="text" id="title" required />
  </div>
  <div class="form-example">
    <label for="description">Description</label>
    <input type="text" id="description" required />
  </div>
  <div class="form-example">
    <label for="image">URL de l'image</label>
    <input type="text" id="image" required />
  </div>
  <div class="form-example" style="display: none">
    <label for="lat">lat</label>
    <input type="text" id="lat" value="${lat}"/>
  </div>
  <div class="form-example" style="display: none">
    <label for="lng">lng</label>
    <input type="text" id="lng" value="${lng}"/>
  </div>
  <div class="form-example">
    <input type="submit" value="Créer" />
  </div>
</form>
`)
    .openOn(map);
}

async function insertDocument() {
  let title = document.getElementById("title").value;
  let description = document.getElementById("description").value;
  let image = document.getElementById("image").value;
  let lat = document.getElementById("lat").value;
  let lng = document.getElementById("lng").value;

  let payload = {
    title: title,
    description: description,
    image: image,
    lat: Number(lat),
    lon: Number(lng),
  };
  console.log("Sending payload", payload);  
  let response = await fetch("http://127.0.0.1:5000/lair", {
    method: "POST",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  });
  let ret = await response.json();
  // TODO: Handle the error
  // console.log(ret);  
  map.closePopup();
}

map.on('click', onMapClick);