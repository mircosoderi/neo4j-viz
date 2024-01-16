isInit = false;

function update() {
  let req = new XMLHttpRequest();
  if(!isInit) { req.open("GET", "http://localhost:5000/dot?type=full", true); isInit = true; }
  else { req.open("GET", "http://localhost:5000/dot?type=partial", true); }
  req.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
       postMessage(req.responseText);
       lastUpdate = Date.now();
    }
  };
  req.send(null);
}

setInterval(update,5000);

onmessage = (e) => { 
	let req = new XMLHttpRequest();
	req.open("DELETE", "http://localhost:5000/dot/"+e.data, true);
	req.send(null);
};
