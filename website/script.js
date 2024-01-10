let socket = null;

const WS_URL = "ws://localhost:7799/";
const WS_TIMEOUT = 3000;

const STATE = {
	CONNECTED: "connected",
	DISCONNECTED: "disconnected",
	CONNECTING: "connecting",
	ERROR: "error",
};

// let settingsStore = {
// 	toggles: [
// 		{
// 			value: true,
// 			type: "toggle",
// 			display_name: "Settings test",
// 		},
// 	],
// 	values: [
// 		{
// 			value: "",
// 			type: "text",
// 			display_name: "text input",
// 		},
// 		{
// 			value: 10,
// 			type: "number",
// 			min: 1,
// 			max: 99,
// 			display_name: "number input",
// 		},
// 	],
// };

let currentTab = 0;

let currentStocks = {};
let statistics = {};
let buys = [];
let sells = [];

let currentState = {
	state: STATE.CONNECTING,
	lastError: null,
};

function connectSocket() {
	console.log("connecting...");
	setState(STATE.CONNECTING);
	socket = new WebSocket(WS_URL);

	socket.onopen = handleOpen;
	socket.onclose = handleClose;
	socket.onerror = handleError;
	socket.onmessage = handleMessage;
}

function handleOpen(event) {
	console.log("connected");
	setState(STATE.CONNECTED);
}

function handleClose(event) {
	console.log("disconnected");
	setState(STATE.DISCONNECTED);
	setTimeout(connectSocket, WS_TIMEOUT);
}

function handleError(event) {
	console.log("error");
	setState(STATE.ERROR);
	currentState.lastError = event;
	// showModal("Error", "An error occured");
}

function handleMessage(event) {
	let data = JSON.parse(event.data);
	//console.log("received Message: " + JSON.stringify(data));
	if (data.type == "modal") {
		showModal(data.title, data.message);
	} else if (data.type == "courses") {
		currentStocks = data;
		createTabs();
	} else if (data.type == "stats") {
		statistics = data;
		updateStats();
	} else if (data.type == "buys") {
		store_buys(data);
	} else if (data.type == "sells") {
		store_sells(data);
	} else {
		console.log("unknown message type");
	}
}

function setState(state) {
	currentState.state = state;
	setStatusIndicator();
}

function setStatusIndicator() {
	switch (currentState.state) {
		case STATE.CONNECTED:
			document.querySelector("header").classList.add("connected");
			document.querySelector("header").classList.remove("connecting");
			document.querySelector("header").classList.remove("disconnected");
			document.querySelector("header").classList.remove("error");
			document.getElementById("status").innerText = STATE.CONNECTED;
			break;
		case STATE.CONNECTING:
			document.querySelector("header").classList.remove("connected");
			document.querySelector("header").classList.add("connecting");
			document.querySelector("header").classList.remove("disconnected");
			document.querySelector("header").classList.remove("error");
			document.getElementById("status").innerText = STATE.CONNECTING;
			break;
		case STATE.DISCONNECTED:
			document.querySelector("header").classList.remove("connected");
			document.querySelector("header").classList.remove("connecting");
			document.querySelector("header").classList.add("disconnected");
			document.querySelector("header").classList.remove("error");
			document.getElementById("status").innerText = STATE.DISCONNECTED;
			break;
		case STATE.ERROR:
			document.querySelector("header").classList.remove("connected");
			document.querySelector("header").classList.remove("connecting");
			document.querySelector("header").classList.remove("disconnected");
			document.querySelector("header").classList.add("error");
			document.getElementById("status").innerText = STATE.ERROR;
			break;
	}
}

function updateStats() {
	if (statistics.data == undefined) {
		return;
	}
	let gcapital = document.getElementById("gcapital");
	let acapital = document.getElementById("acapital");
	let margin = document.getElementById("margin");
	let guv = document.getElementById("guv");

	gcapital.innerText = "€ " + statistics.data.gcapital.toFixed(2);

	if (statistics.data.acapital > statistics.data.gcapital) {
		acapital.classList.add("green");
		acapital.classList.remove("red");
	} else {
		acapital.classList.add("red");
		acapital.classList.remove("green");
	}
	acapital.innerText = "€ " + statistics.data.acapital.toFixed(2);

	if (statistics.data.guv >= 0) {
		guv.classList.add("green");
		guv.classList.remove("red");
	} else {
		guv.classList.add("red");
		guv.classList.remove("green");
	}
	guv.innerText = "€ " + statistics.data.guv.toFixed(2);

	margin.innerText = "€ " + statistics.data.margin.toFixed(2);
}

// We implemented the settings, but we found out that we don't need them with the current implementation. Leaving them here for future use.
// function settings() {
// 	if (localStorage.getItem("settings") != null) {
// 		settingsStore = JSON.parse(localStorage.getItem("settings"));
// 	}
// 	let toggles = settingsStore.toggles;
// 	let sets = settingsStore.values;

// 	let modalBackdrop = document.createElement("div");
// 	modalBackdrop.classList.add("modal-backdrop");

// 	let modal = document.createElement("form");
// 	modal.classList.add("modal");

// 	let modalTitle = document.createElement("h1");
// 	modalTitle.classList.add("modal-title");
// 	modalTitle.innerText = "Settings";

// 	let btnWrap = document.createElement("div");
// 	btnWrap.className = "btn-wrap";

// 	let cancelButton = document.createElement("button");
// 	cancelButton.classList.add("btn-cancel");
// 	cancelButton.innerText = "Cancel";
// 	cancelButton.addEventListener("click", (e) => {
// 		modalBackdrop.remove();
// 	});

// 	let saveButton = document.createElement("button");
// 	saveButton.classList.add("btn-save");
// 	saveButton.innerText = "Save";
// 	saveButton.addEventListener("click", (e) => {
// 		for (let i = 0; i < toggles.length; i++) {
// 			toggles[i].value = document.getElementById("tog:" + toggles[i].display_name).checked;
// 		}
// 		for (let i = 0; i < sets.length; i++) {
// 			sets[i].value = document.getElementById("set:" + sets[i].display_name).value;
// 		}
// 		localStorage.setItem("settings", JSON.stringify(settingsStore));
// 		modalBackdrop.remove();
// 	});

// 	modal.addEventListener("submit", (e) => {
// 		e.preventDefault();
// 		saveButton.click();
// 	});

// 	modal.appendChild(modalTitle);

// 	for (let i = 0; i < toggles.length; i++) {
// 		let div = document.createElement("div");
// 		div.classList.add("settingsDiv");
// 		let toggle = document.createElement("p");
// 		toggle.classList.add("toggleText");
// 		toggle.innerText = toggles[i].display_name;
// 		div.appendChild(toggle);

// 		let toggleCbx = document.createElement("input");
// 		toggleCbx.type = "checkbox";
// 		toggleCbx.classList.add("toggleBtn");
// 		toggleCbx.id = "tog:" + toggles[i].display_name;
// 		toggleCbx.checked = toggles[i].value;
// 		div.appendChild(toggleCbx);
// 		modal.appendChild(div);
// 	}

// 	for (let i = 0; i < sets.length; i++) {
// 		let div = document.createElement("div");
// 		div.classList.add("settingsDiv");
// 		let set = document.createElement("p");
// 		set.classList.add("setText");
// 		set.innerText = sets[i].display_name;
// 		div.appendChild(set);

// 		let setInp = document.createElement("input");
// 		setInp.classList.add("setInp");
// 		setInp.id = "set:" + sets[i].display_name;
// 		setInp.type = sets[i].type;
// 		setInp.min = sets[i].min;
// 		setInp.max = sets[i].max;
// 		setInp.value = sets[i].value;
// 		div.appendChild(setInp);
// 		modal.appendChild(div);
// 	}

// 	btnWrap.appendChild(cancelButton);
// 	btnWrap.appendChild(saveButton);
// 	modal.appendChild(btnWrap);
// 	modalBackdrop.appendChild(modal);
// 	document.body.appendChild(modalBackdrop);
// }

function showModal(title, message) {
	let modalBackdrop = document.createElement("div");
	modalBackdrop.classList.add("modal-backdrop");

	let modal = document.createElement("div");
	modal.classList.add("modal");

	let modalTitle = document.createElement("h1");
	modalTitle.classList.add("modal-title");
	modalTitle.innerText = title;

	let modalMessage = document.createElement("p");
	modalMessage.classList.add("modal-message");
	modalMessage.innerText = message == null ? "" : message;

	let modalButton = document.createElement("button");
	modalButton.classList.add("btn");
	modalButton.innerText = "OK";
	modalButton.addEventListener("click", (e) => {
		modalBackdrop.remove();
	});

	modal.appendChild(modalTitle);

	modal.appendChild(modalMessage);
	modal.appendChild(modalButton);
	modalBackdrop.appendChild(modal);
	document.body.appendChild(modalBackdrop);
}

function createTabs() {
	let tabs = document.getElementsByClassName("head")[0];

	if (Object.keys(currentStocks).length > 1) {
		tabs.innerHTML = "";
	}
	for (let i = 1; i < Object.keys(currentStocks).length; i++) {
		let tab = document.createElement("button");
		tab.classList.add("stockbutton");
		tab.innerText = Object.keys(currentStocks)[i];
		if (i == currentTab + 1) {
			tab.classList.add("stock-active");
		}
		tab.addEventListener("click", (e) => {
			let active = document.getElementsByClassName("stock-active")[0];
			if (active != null) {
				active.classList.remove("stock-active");
			}
			tab.classList.add("stock-active");
			currentTab = i - 1;
			draw_candlesticks(currentStocks[tab.innerText]);
			draw_buys(tab.innerText);
			draw_sells(tab.innerText);
		});
		tabs.appendChild(tab);
	}
	if (tabs.children.length > 0 && currentTab != -1) {
		tabs.children[currentTab].click();
	} else if (tabs.children.length == 0) {
		document.getElementById("sticks").innerHTML = "no data";
		currentTab = 0;
	}
}

function draw_candlesticks(data) {
	if (data == undefined) {
		return;
	}
	let sticks = document.getElementById("sticks");

	if (data.data == undefined) {
		console.log("no data");
		sticks.innerHTML = "no data";
		return;
	}

	document.getElementsByClassName("stockbutton stock-active")[0].innerText = data.data.name;

	let low = data.data.lowest;
	let high = data.data.highest;
	let step = (high - low) / 39;

	let numbers = [];
	for (let i = 0; i < 39; i++) {
		numbers.push((low + i * step).toFixed(2));
	}
	numbers.push(high.toFixed(2));

	for (let i = 0; i < 40; i++) {
		document.getElementById("prices").children[i].innerText = numbers[Math.abs(i - 39)];
	}

	// abortion
	sticks.innerHTML = "";

	for (let i = 34; i > -1; i--) {
		let stick = document.createElement("div");
		stick.className = "stick";

		let type =
			data.data.prices["" + i].open < data.data.prices["" + i].close ? "st-green" : "st-red";
		stick.classList.add(type);

		wickTop = document.createElement("div");
		wickTop.className = "wickTop";
		wickTop.style.height =
			((data.data.prices["" + i].high -
				(type == "st-green"
					? data.data.prices["" + i].close
					: data.data.prices["" + i].open)) /
				step) *
				1.75 +
			"vh";
		stick.appendChild(wickTop);

		cbody = document.createElement("div");
		cbody.className = "body";
		cbody.style.height =
			(Math.abs(data.data.prices["" + i].open - data.data.prices["" + i].close) / step) *
				1.75 +
			"vh";
		stick.appendChild(cbody);

		wickBottom = document.createElement("div");
		wickBottom.className = "wickBottom";
		wickBottom.style.height =
			(((type == "st-green"
				? data.data.prices["" + i].open
				: data.data.prices["" + i].close) -
				data.data.prices["" + i].low) /
				step) *
				1.75 +
			"vh";
		stick.appendChild(wickBottom);

		popup = document.createElement("div");
		popup.className = "popup";
		popup.style.marginTop = "-" + cbody.style.height;

		p1 = document.createElement("p");
		p1.innerText = "open: " + data.data.prices["" + i].open.toFixed(2);
		popup.appendChild(p1);
		p2 = document.createElement("p");
		p2.innerText = "close: " + data.data.prices["" + i].close.toFixed(2);
		popup.appendChild(p2);
		p3 = document.createElement("p");
		p3.innerText = "high: " + data.data.prices["" + i].high.toFixed(2);
		popup.appendChild(p3);
		p4 = document.createElement("p");
		p4.innerText = "low: " + data.data.prices["" + i].low.toFixed(2);
		popup.appendChild(p4);

		stick.appendChild(popup);

		stick.style.marginTop =
			((data.data.highest - data.data.prices["" + i].high) / step) * 1.75 + 0.875 + "vh";

		sticks.appendChild(stick);
	}
}

function store_buys(data) {
	if (data.data == undefined) {
		return;
	}
	buys.push(data.data);
}

function store_sells(data) {
	if (data.data == undefined) {
		return;
	}
	sells.push(data.data);
}

function draw_buys(epic) {
	const currentTime = Date.now() / 1000; // Current time in seconds
	const thirtyFiveMinutes = 35 * 60; // 35 minutes in seconds

	let results = [];

	buys.forEach((item) => {
		Object.keys(item).forEach((key) => {
			if (key === epic) {
				results.push(item[key]);
			}
		});
	});

	let results2 = [];

	results.forEach((item) => {
		item.forEach((dict) => {
			if (currentTime - dict.timestamp <= thirtyFiveMinutes) {
				results2.push(dict);
			}
		});
	});

	let indicators = document.getElementById("indicators");
	Array.from(indicators.children).forEach((e) => {
		if (e.className == "ind-buy") {
			e.remove();
		}
	});

	results2.forEach((dict) => {
		let ind = document.createElement("div");
		ind.className = "ind-buy";
		let leftindent = 2 * (35 - Math.ceil((currentTime - dict.timestamp) / 60)) + 0.25;
		ind.style.marginLeft = leftindent + "vw";
		indicators.appendChild(ind);
	});
}

function draw_sells(epic) {
	const currentTime = Date.now() / 1000; // Current time in seconds
	const thirtyFiveMinutes = 35 * 60; // 35 minutes in seconds

	let results = [];

	sells.forEach((item) => {
		Object.keys(item).forEach((key) => {
			if (key === epic) {
				results.push(item[key]);
			}
		});
	});

	let results2 = [];

	results.forEach((item) => {
		item.forEach((dict) => {
			if (currentTime - dict.timestamp <= thirtyFiveMinutes) {
				results2.push(dict);
			}
		});
	});

	let indicators = document.getElementById("indicators");
	Array.from(indicators.children).forEach((e) => {
		if (e.className == "ind-sell") {
			e.remove();
		}
	});

	results2.forEach((dict) => {
		let ind = document.createElement("div");
		ind.className = "ind-sell";
		let leftindent = 2 * (35 - Math.ceil((currentTime - dict.timestamp) / 60)) + 0.25;
		ind.style.marginLeft = leftindent + "vw";
		indicators.appendChild(ind);
	});
}

connectSocket();

document.querySelector(".view .head").addEventListener(
	"wheel",
	(e) => {
		e.preventDefault();

		e.currentTarget.scrollLeft += e.deltaY;
	},
	{passive: false}
);
