let players = [];
let editingId = null;

/* ========== Load Data ========== */
async function loadPlayers() {
  const res = await fetch("/api/players");
  players = await res.json();
  renderPlayers();
  loadStats("all");
}

/* ========== Render List ========== */
function renderPlayers() {
  const list = document.getElementById("playerList");
  list.innerHTML = "";
  players.forEach((p) => {
    const div = document.createElement("div");
    div.className = "player-card flex justify-between items-center";
    div.innerHTML = `
      <span><b>${p.name}</b> — ${p.position}, ${p.age}t</span>
      <span class="flex gap-2 items-center">
        ⚽ ${p.goals} | 🎯 ${p.assists}
        <button class="btn btn-secondary" onclick="openEdit(${p.id})">✏</button>
        <button class="btn btn-secondary" onclick="deletePlayer(${p.id})">🗑</button>
      </span>
    `;
    list.appendChild(div);
  });
}

/* ========== Stats với filter vị trí ========== */
async function loadStats(filter="all") {
  const res = await fetch("/api/stats");
  const s = await res.json();
  const stats = document.getElementById("teamStats");
  const MAX_GOALS = 200, MAX_ASSISTS = 200;

  let html = `
    <div class="mb-3">
      <label><b>Xem thống kê theo vị trí:</b></label>
      <select id="statsFilter" class="metric-select w-auto ml-2">
        <option value="all">Tất cả</option>
        <option value="Forward">Forward</option>
        <option value="Midfielder">Midfielder</option>
        <option value="Defender">Defender</option>
        <option value="Goalkeeper">Goalkeeper</option>
      </select>
    </div>
  `;

  if(filter==="all"){
    html += `
      <div class="grid-3">
        <div><b>Tổng cầu thủ:</b> ${s.total}</div>
        <div>
          <b>Tổng goals:</b> ${s.sum_goals}
          <div class="progress mt-1">
            <div class="progress-bar bg-blue-500" style="width:${Math.min((s.sum_goals/MAX_GOALS)*100,100)}%"></div>
          </div>
        </div>
        <div>
          <b>Tổng assists:</b> ${s.sum_assists}
          <div class="progress mt-1">
            <div class="progress-bar bg-purple-500" style="width:${Math.min((s.sum_assists/MAX_ASSISTS)*100,100)}%"></div>
          </div>
        </div>
        <div>
          <b>Stamina TB:</b> ${s.avg_stamina}
          <div class="progress mt-1">
            <div class="progress-bar bg-green-500" style="width:${s.avg_stamina}%"></div>
          </div>
        </div>
        <div><b>Top scorer:</b> ${s.top_scorer?.name || "N/A"} (${s.top_scorer?.goals || 0})</div>
        <div><b>GK CS nhiều nhất:</b> ${s.top_gk?.name || "N/A"} (${s.top_gk?.clean_sheets || 0})</div>
      </div>
    `;
  } else {
    const subset = players.filter(p=>p.position===filter);
    html += renderPositionStats(subset, filter);
  }

  stats.innerHTML = html;
  document.getElementById("statsFilter").value = filter;
  document.getElementById("statsFilter").onchange = e => loadStats(e.target.value);
}

function renderPositionStats(subset, pos){
  if(!subset.length) return `<p class="empty-chart">Không có dữ liệu cho ${pos}</p>`;

  if(pos==="Goalkeeper"){
    const maxCS = Math.max(...subset.map(p=>p.clean_sheets||0));
    const top = subset.find(p=>p.clean_sheets===maxCS);
    return `
      <div><b>Số GK:</b> ${subset.length}</div>
      <div><b>GK CS nhiều nhất:</b> ${top?.name} (${top?.clean_sheets})</div>
    `;
  }
  if(pos==="Defender"){
    const tackles = subset.reduce((a,p)=>a+(+p.tackles||0),0);
    const clearances = subset.reduce((a,p)=>a+(+p.clearances||0),0);
    return `
      <div><b>Số DEF:</b> ${subset.length}</div>
      <div><b>Tackles tổng:</b> ${tackles}</div>
      <div><b>Clearances tổng:</b> ${clearances}</div>
    `;
  }
  if(pos==="Midfielder"){
    const passes = subset.reduce((a,p)=>a+(+p.passes_completed||0),0);
    const keypasses = subset.reduce((a,p)=>a+(+p.key_passes||0),0);
    return `
      <div><b>Số MID:</b> ${subset.length}</div>
      <div><b>Passes completed:</b> ${passes}</div>
      <div><b>Key passes:</b> ${keypasses}</div>
    `;
  }
  if(pos==="Forward"){
    const goals = subset.reduce((a,p)=>a+(+p.goals||0),0);
    const shots = subset.reduce((a,p)=>a+(+p.shots||0),0);
    return `
      <div><b>Số FWD:</b> ${subset.length}</div>
      <div><b>Tổng goals:</b> ${goals}</div>
      <div><b>Tổng shots:</b> ${shots}</div>
    `;
  }
}

/* ========== Add Player ========== */
document.getElementById("btnAdd").onclick = async () => {
  const player = collectForm("");
  if (!player) return;
  await fetch("/api/players", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify(player)
  });
  clearForm("");
  loadPlayers();
};

/* ========== Edit Player ========== */
function openEdit(id){
  const p = players.find(x=>x.id===id);
  if(!p) return;
  editingId = id; // nhớ id
  document.getElementById("editModal").classList.add("show");

  fillForm("e_", p);
  toggleFields("e_", p.position);
}

document.getElementById("btnSave").onclick = async () => {
  if(!editingId) return;
  const player = collectForm("e_");
  if (!player) return;

  player.id = editingId; // gắn lại id để update đúng cầu thủ

  await fetch(`/api/players/${editingId}`, {
    method:"PUT",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify(player)
  });
  closeModal();
  loadPlayers();
};

document.getElementById("btnCancel").onclick = closeModal;
function closeModal(){ 
  document.getElementById("editModal").classList.remove("show");
  editingId = null;
}

/* ========== Delete Player ========== */
async function deletePlayer(id){
  if(!confirm("Xóa cầu thủ này?")) return;
  await fetch(`/api/players/${id}`, { method:"DELETE" });
  loadPlayers();
}

/* ========== Helpers cho Form ========== */
function collectForm(prefix){
  const name = document.getElementById(prefix+"name").value.trim();
  const age = +document.getElementById(prefix+"age").value;
  const position = document.getElementById(prefix+"position").value;

  if(!name || !position) { alert("Tên và vị trí bắt buộc"); return null; }

  const obj = {
    name, age, position,
    goals:+(document.getElementById(prefix+"goals")?.value||0),
    assists:+(document.getElementById(prefix+"assists")?.value||0),
    stamina:+(document.getElementById(prefix+"stamina")?.value||0),
    games:0, clean_sheets:0, saves:0, high_claims:0, catches:0,
    tackles:0, clearances:0, blocks:0, interceptions:0,
    passes_completed:0, key_passes:0, ball_recoveries:0,
    dribbles:0, shots:0, shots_on_target:0, chances_created:0
  };

  if(position==="Goalkeeper"){
    obj.games = +document.getElementById(prefix+"games")?.value||0;
    obj.clean_sheets = +document.getElementById(prefix+"clean_sheets")?.value||0;
    obj.saves = +document.getElementById(prefix+"saves")?.value||0;
    obj.high_claims = +document.getElementById(prefix+"high_claims")?.value||0;
    obj.catches = +document.getElementById(prefix+"catches")?.value||0;
  }
  if(position==="Defender"){
    obj.tackles = +document.getElementById(prefix+"tackles")?.value||0;
    obj.clearances = +document.getElementById(prefix+"clearances")?.value||0;
    obj.blocks = +document.getElementById(prefix+"blocks")?.value||0;
    obj.interceptions = +document.getElementById(prefix+"interceptions")?.value||0;
  }
  if(position==="Midfielder"){
    obj.passes_completed = +document.getElementById(prefix+"passes_completed")?.value||0;
    obj.key_passes = +document.getElementById(prefix+"key_passes")?.value||0;
    obj.ball_recoveries = +document.getElementById(prefix+"ball_recoveries")?.value||0;
    obj.dribbles = +document.getElementById(prefix+"mf_dribbles")?.value||0;
  }
  if(position==="Forward"){
    obj.shots = +document.getElementById(prefix+"shots")?.value||0;
    obj.shots_on_target = +document.getElementById(prefix+"shots_on_target")?.value||0;
    obj.dribbles = +document.getElementById(prefix+"fw_dribbles")?.value||0;
    obj.chances_created = +document.getElementById(prefix+"chances_created")?.value||0;
  }

  return obj;
}

function fillForm(prefix, p){
  document.getElementById(prefix+"name").value = p.name;
  document.getElementById(prefix+"age").value = p.age;
  document.getElementById(prefix+"position").value = p.position;
  document.getElementById(prefix+"goals").value = p.goals;
  document.getElementById(prefix+"assists").value = p.assists;
  document.getElementById(prefix+"stamina").value = p.stamina;

  ["games","clean_sheets","saves","high_claims","catches",
   "tackles","clearances","blocks","interceptions",
   "passes_completed","key_passes","ball_recoveries",
   "shots","shots_on_target","chances_created"].forEach(f=>{
    if(document.getElementById(prefix+f)) document.getElementById(prefix+f).value = p[f]||0;
  });
  if(document.getElementById(prefix+"mf_dribbles")) document.getElementById(prefix+"mf_dribbles").value = p.dribbles||0;
  if(document.getElementById(prefix+"fw_dribbles")) document.getElementById(prefix+"fw_dribbles").value = p.dribbles||0;
}

function clearForm(prefix){
  ["name","age","position","goals","assists","stamina",
   "games","clean_sheets","saves","high_claims","catches",
   "tackles","clearances","blocks","interceptions",
   "passes_completed","key_passes","ball_recoveries",
   "mf_dribbles","fw_dribbles",
   "shots","shots_on_target","chances_created"].forEach(f=>{
    if(document.getElementById(prefix+f)) document.getElementById(prefix+f).value = "";
  });
}

/* ========== Toggle Fields by Position ========== */
function toggleFields(prefix, pos){
  document.getElementById(prefix+"gkFields").style.display = (pos==="Goalkeeper") ? "grid" : "none";
  document.getElementById(prefix+"defFields").style.display = (pos==="Defender") ? "grid" : "none";
  document.getElementById(prefix+"midFields").style.display = (pos==="Midfielder") ? "grid" : "none";
  document.getElementById(prefix+"fwdFields").style.display = (pos==="Forward") ? "grid" : "none";
}

document.getElementById("position").onchange = e => toggleFields("", e.target.value);
document.getElementById("e_position").onchange = e => toggleFields("e_", e.target.value);

/* ========== Init ========== */
loadPlayers();

