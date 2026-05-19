// UI01 - Anwaltsansicht V1 - JavaScript

// --- Spracherkennung (Mikrofon/Diktat) ---
let recognition = null;
let currentTargetId = null;

function initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.querySelectorAll(".mic-status").forEach(function(el) {
            el.textContent = "Mikrofon-Diktat ist in diesem Browser nicht verfuegbar. Bitte Windows-Diktat oder manuelle Eingabe nutzen.";
        });
        return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = "de-DE";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = function(event) {
        var text = event.results[0][0].transcript;
        var target = document.getElementById(currentTargetId);
        if (target) {
            target.value += (target.value ? " " : "") + text;
        }
        updateMicButton(false);
        var sid = currentTargetId ? currentTargetId.replace("anwaltliche_notiz","notiz").replace("arbeitsauftrag","auftrag") : "";
        var el = sid ? document.getElementById("mic-status-" + sid) : null;
        if (el) el.textContent = "Diktat eingefuegt.";
    };
    recognition.onerror = function(event) {
        updateMicButton(false);
        var sid = currentTargetId ? currentTargetId.replace("anwaltliche_notiz","notiz").replace("arbeitsauftrag","auftrag") : "";
        var el = sid ? document.getElementById("mic-status-" + sid) : null;
        if (el) el.textContent = "Diktatfehler: " + event.error;
    };
    recognition.onend = function() {
        updateMicButton(false);
    };
}

function startDiktat(targetId) {
    if (!recognition) {
        alert("Mikrofon-Diktat ist in diesem Browser nicht verfuegbar. Bitte Windows-Diktat oder manuelle Eingabe nutzen.");
        return;
    }
    if (currentTargetId === targetId && document.querySelector(".mic-btn.recording")) {
        recognition.stop();
        return;
    }
    currentTargetId = targetId;
    updateMicButton(true);
    try {
        recognition.start();
    } catch(e) {
        updateMicButton(false);
    }
}

function updateMicButton(recording) {
    document.querySelectorAll(".mic-btn").forEach(function(btn) {
        if (recording && btn.getAttribute("onclick") && btn.getAttribute("onclick").indexOf(currentTargetId) >= 0) {
            btn.classList.add("recording");
        } else {
            btn.classList.remove("recording");
        }
    });
}

// --- Merkmale ---
function uebernehmeMerkmale() {
    var rows = document.querySelectorAll("#merkmale-table tr");
    var data = {};
    rows.forEach(function(row) {
        var cells = row.querySelectorAll("td");
        if (cells.length >= 2) {
            var key = cells[0].textContent.trim();
            var val = cells[1].textContent.trim();
            data[key] = val;
        }
    });
    console.log("Merkmale uebernommen:", data);
    alert("Merkmale uebernommen (siehe Console).");
}

function verwerfeMerkmale() {
    if (confirm("Merkmale zuruecksetzen?")) {
        location.reload();
    }
}

// --- Entscheidung speichern ---
function speichereEntscheidung() {
    var mandatEl = document.querySelector('input[name="mandat"]:checked');
    var begruendung = document.getElementById("begruendung").value;
    var auftrag = document.getElementById("arbeitsauftrag").value;
    var notiz = document.getElementById("anwaltliche_notiz").value;

    var entscheidung = {
        mandat: mandatEl ? mandatEl.value : null,
        begruendung: begruendung,
        arbeitsauftrag_sekretariat: auftrag,
        anwaltliche_notiz: notiz,
        zeitpunkt: new Date().toISOString()
    };

    var blob = new Blob([JSON.stringify(entscheidung, null, 2)], {type: "application/json"});
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "UI01_ANWALTSNOTIZ.json";
    a.click();
    URL.revokeObjectURL(url);

    var statusEl = document.getElementById("save-status");
    statusEl.textContent = "Entscheidung gespeichert: " + new Date().toLocaleString();
    statusEl.style.color = "#27ae60";
}

// --- Seiten-Navigation ---
document.addEventListener("DOMContentLoaded", function() {
    initSpeech();
    var pageBtns = document.querySelectorAll(".page-btn");
    pageBtns.forEach(function(btn) {
        btn.addEventListener("click", function() {
            pageBtns.forEach(function(b) { b.classList.remove("active"); });
            this.classList.add("active");
            var sid = this.getAttribute("data-sid");
            var sn = this.getAttribute("data-seite");
            document.getElementById("image-container").innerHTML = '<p class="placeholder">Seite ' + sn + ' - ID: ' + sid + '</p>';
        });
    });
    if (pageBtns.length > 0) {
        pageBtns[0].click();
    }
});
