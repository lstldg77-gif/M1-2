// --- Global State ---
const API_BASE_URL = window.__API_BASE_URL__ || window.location.origin;
let activeConversationId = null;
let currentChart = null;
let currentTaskPollInterval = null;
let currentGeneratedAudioUrl = null;
let currentTrackTitle = "Suno_Track";
let plannedMusicPrompts = [];
let generatedTracks = [];

// --- DOM Loaded Initialization ---
document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initTheme();
    loadSummaryData();
    loadDataTable();
    loadConversationsList();
});

// --- Tab Switching ---
function initTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            tab.classList.add("active");
            const targetTab = document.getElementById(tab.dataset.tab);
            if (targetTab) {
                targetTab.classList.add("active");
            }

            // Refresh data when switching to relevant tabs
            if (tab.dataset.tab === "tab-data") {
                loadSummaryData();
                loadDataTable();
            } else if (tab.dataset.tab === "tab-history") {
                loadConversationsList();
            }
        });
    });
}

// --- Theme Toggle ---
function initTheme() {
    const themeBtn = document.getElementById("theme-toggle");
    themeBtn.addEventListener("click", () => {
        document.body.classList.toggle("light-theme");
        const isLight = document.body.classList.contains("light-theme");
        themeBtn.innerHTML = isLight ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    });
}

// --- AI Chat Logic ---
async function sendMessage() {
    const input = document.getElementById("chat-input");
    const messageText = input.value.trim();
    if (!messageText) return;

    input.value = "";
    appendChatMessage("user", messageText);

    // Show loading assistant bubble
    const loadingId = "loading-" + Date.now();
    appendLoadingMessage(loadingId);

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: messageText,
                conversation_id: activeConversationId
            })
        });

        removeMessage(loadingId);

        if (!response.ok) {
            const err = await response.json();
            appendChatMessage("assistant", `❌ 오류 발생: ${err.detail || '응답을 받지 못했습니다.'}`);
            return;
        }

        const data = await response.json();
        activeConversationId = data.conversation_id;

        // Append AI Reply
        appendChatMessage("assistant", data.reply);

        // If Suno Prompts were generated directly in chat
        if (data.suno_prompts && data.suno_prompts.length > 0) {
            renderChatPrompts(data.suno_prompts);
            renderPromptsGrid(data.suno_prompts);
        }

        // Refresh Summary Badge
        if (data.summary_context) {
            updateSummaryBadge(data.summary_context);
        }
    } catch (error) {
        removeMessage(loadingId);
        appendChatMessage("assistant", `❌ 통신 오류: ${error.message}`);
    }
}

function sendQuickMessage(text) {
    document.getElementById("chat-input").value = text;
    sendMessage();
}

function applyThemePreset(themeText) {
    const input = document.getElementById("chat-input");
    if (!input) return;

    input.value = themeText;
    input.focus();
    const themeButtons = document.querySelectorAll(".theme-tag");
    themeButtons.forEach(btn => {
        btn.classList.toggle("selected", btn.dataset.theme === themeText);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".theme-tag").forEach(button => {
        button.addEventListener("click", () => {
            applyThemePreset(button.dataset.theme);
        });
    });
});

function appendChatMessage(role, content) {
    const chatContainer = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    
    // Process markdown line breaks
    const formattedContent = content.replace(/\n/g, "<br>");
    msgDiv.innerHTML = `<div class="message-content">${formattedContent}</div>`;

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendLoadingMessage(id) {
    const chatContainer = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message assistant";
    msgDiv.id = id;
    msgDiv.innerHTML = `
        <div class="message-content">
            <i class="fa-solid fa-spinner fa-spin"></i> 저장된 시계열 데이터 요약을 반영하여 답변을 생성 중입니다...
        </div>
    `;
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function renderChatPrompts(prompts) {
    const chatContainer = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message assistant";

    let html = `<div class="message-content"><strong>🎵 AI 추천 Suno 음악 프롬프트 10가지가 기획되었습니다!</strong><br><br>`;
    html += `<div style="display:flex; flex-direction:column; gap:0.6rem; margin-top:0.5rem;">`;

    prompts.slice(0, 5).forEach((p, idx) => {
        html += `
            <div style="background:rgba(0,0,0,0.25); padding:0.6rem; border-radius:8px; font-size:0.85rem;">
                <strong>#${idx + 1} ${p.title}</strong> (${p.mood_keyword})<br>
                <span style="color:var(--text-secondary); font-size:0.8rem;">${p.suno_prompt}</span><br>
                <button class="btn btn-sm btn-primary mt-2" onclick="switchToMusicAndGenerate('${p.title.replace(/'/g, "")}', '${p.suno_prompt.replace(/'/g, "")}', '${p.lyrics ? p.lyrics.replace(/'/g, "").replace(/\n/g, " ") : ""}')">
                    <i class="fa-solid fa-play"></i> 이 곡 바로 생성하기
                </button>
            </div>
        `;
    });

    html += `</div><p class="mt-2 text-muted" style="font-size:0.8rem;">전체 10가지 프롬프트는 'Suno AI 스튜디오' 탭에서 모두 확인하실 수 있습니다.</p></div>`;
    msgDiv.innerHTML = html;
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function updateSummaryBadge(summary) {
    const badgeBox = document.getElementById("chat-summary-badge");
    if (!badgeBox || !summary) return;
    badgeBox.innerHTML = `
        <span class="badge" title="${summary.period}">
            📊 평균 컨디션: <strong>${summary.metrics.average}</strong> (${summary.trend})
        </span>
    `;
}

// --- Time Series Data CRUD Logic ---
async function loadSummaryData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/data/summary`);
        if (!response.ok) return;
        const summary = await response.json();

        document.getElementById("stat-period").textContent = summary.period;
        document.getElementById("stat-count").textContent = `${summary.count}개`;
        document.getElementById("stat-average").textContent = summary.metrics.average;
        document.getElementById("stat-trend").textContent = summary.trend;

        updateSummaryBadge(summary);
    } catch (e) {
        console.error("Summary fetch error:", e);
    }
}

async function loadDataTable() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/data`);
        if (!response.ok) return;
        const items = await response.json();

        document.getElementById("data-table-count").textContent = `총 ${items.length}건`;

        const tbody = document.getElementById("data-table-body");
        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4">등록된 데이터가 없습니다.</td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        items.slice(-50).reverse().forEach(item => { // show recent 50
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${item.date}</strong></td>
                <td><span class="badge ${item.value >= 7 ? 'badge-success' : item.value >= 4 ? 'badge-info' : 'badge-warning'}">${item.value}</span></td>
                <td>${item.memo}</td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="editDataItem('${item.id}', '${item.date}', ${item.value}, '${item.memo.replace(/'/g, "\\'")}')">수정</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteDataItem('${item.id}')">삭제</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        renderMoodChart(items);
    } catch (e) {
        console.error("Table fetch error:", e);
    }
}

function renderMoodChart(items) {
    const canvas = document.getElementById("moodChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    // Take last 30 data points for clean display
    const chartItems = items.slice(-35);
    const labels = chartItems.map(i => i.date);
    const values = chartItems.map(i => i.value);

    if (currentChart) {
        currentChart.destroy();
    }

    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '컨디션/기분 지수 (1-10)',
                data: values,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                fill: true,
                tension: 0.35,
                pointRadius: 4,
                pointBackgroundColor: '#818cf8'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 10, grid: { color: 'rgba(255, 255, 255, 0.08)' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            }
        }
    });
}

async function handleDataFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById("data-id").value;
    const date = document.getElementById("data-date").value;
    const value = parseFloat(document.getElementById("data-value").value);
    const memo = document.getElementById("data-memo").value.trim();

    const payload = { date, value, memo };
    const method = id ? "PUT" : "POST";
    const url = id ? `${API_BASE_URL}/api/data/${id}` : `${API_BASE_URL}/api/data`;

    try {
        const res = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert(id ? "데이터가 수정되었습니다." : "새 데이터가 성공적으로 추가되었습니다.");
            resetDataForm();
            loadSummaryData();
            loadDataTable();
        } else {
            const err = await res.json();
            alert(`오류: ${err.detail || '데이터 저장 실패'}`);
        }
    } catch (err) {
        alert(`통신 오류: ${err.message}`);
    }
}

function editDataItem(id, date, value, memo) {
    document.getElementById("data-id").value = id;
    document.getElementById("data-date").value = date;
    document.getElementById("data-value").value = value;
    document.getElementById("data-memo").value = memo;

    document.getElementById("form-title").innerHTML = '<i class="fa-solid fa-pen-to-square"></i> 컨디션 데이터 수정';
    document.getElementById("form-submit-btn").innerHTML = '<i class="fa-solid fa-check"></i> 수정 완료';
    document.getElementById("form-cancel-btn").style.display = "inline-flex";
}

function resetDataForm() {
    document.getElementById("data-id").value = "";
    document.getElementById("data-form").reset();
    document.getElementById("form-title").innerHTML = '<i class="fa-solid fa-plus-circle"></i> 새 컨디션 데이터 추가';
    document.getElementById("form-submit-btn").innerHTML = '<i class="fa-solid fa-check"></i> 데이터 저장';
    document.getElementById("form-cancel-btn").style.display = "none";
}

async function deleteDataItem(id) {
    if (!confirm("정말 이 시계열 항목을 삭제하시겠습니까?")) return;

    try {
        const res = await fetch(`${API_BASE_URL}/api/data/${id}`, { method: "DELETE" });
        if (res.ok) {
            loadSummaryData();
            loadDataTable();
        } else {
            alert("삭제에 실패했습니다.");
        }
    } catch (e) {
        alert(`오류: ${e.message}`);
    }
}

async function exportDataCSV() {
    const res = await fetch(`${API_BASE_URL}/api/data`);
    const items = await res.json();
    let csv = "\uFEFFDate,Value,Memo\n";
    items.forEach(i => {
        csv += `"${i.date}",${i.value},"${i.memo.replace(/"/g, '""')}"\n`;
    });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `condition_data_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
}

async function exportDataJSON() {
    const res = await fetch(`${API_BASE_URL}/api/data`);
    const items = await res.json();
    const blob = new Blob([JSON.stringify(items, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `condition_data_${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
}

// --- Suno AI Music Studio Logic ---
async function planMusicPrompts() {
    const count = Number(document.querySelector('input[name="prompt-count"]:checked')?.value || 10);
    const selectedTheme = document.getElementById("music-theme").value.trim();
    const moodInput = document.getElementById("music-mood").value.trim();
    const condition = document.getElementById("music-condition").value.trim() || "야근 후 피로";
    const custom = document.getElementById("music-custom").value.trim();
    const instruments = document.getElementById("music-instruments").value.trim();
    const includeLyrics = document.querySelector('input[name="lyrics-option"]:checked')?.value !== "no";

    const mood = selectedTheme || moodInput || "평화롭고 잔잔함";
    const combinedCustom = [selectedTheme, custom, instruments].filter(Boolean).join(" / ");

    const grid = document.getElementById("prompts-grid");
    const sectionTitle = document.getElementById("prompts-section-title");
    if (sectionTitle) {
        sectionTitle.innerHTML = `<i class="fa-solid fa-list-check"></i> ${count}가지 추천 Suno 프롬프트 목록`;
    }
    grid.innerHTML = `<div class="prompt-placeholder"><i class="fa-solid fa-spinner fa-spin"></i> AI가 ${count}가지 Suno 맞춤 음악 프롬프트(${includeLyrics ? '가사 포함' : '가사 미포함 연주곡'})를 생성 중입니다...</div>`;

    try {
        const res = await fetch(`${API_BASE_URL}/api/music/plan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                mood,
                condition,
                custom_request: combinedCustom,
                include_lyrics: includeLyrics,
                count
            })
        });

        if (!res.ok) {
            grid.innerHTML = `<div class="prompt-placeholder">❌ 프롬프트 생성에 실패했습니다.</div>`;
            return;
        }

        const data = await res.json();
        plannedMusicPrompts = data.prompts || [];
        const generateAllButton = document.getElementById("generate-all-btn");
        if (generateAllButton) generateAllButton.disabled = plannedMusicPrompts.length === 0;
        renderPromptsGrid(data.prompts);
    } catch (e) {
        grid.innerHTML = `<div class="prompt-placeholder">❌ 오류: ${e.message}</div>`;
    }
}

function renderPromptsGrid(prompts) {
    const grid = document.getElementById("prompts-grid");
    grid.innerHTML = "";
    plannedMusicPrompts = prompts || [];
    const generateAllButton = document.getElementById("generate-all-btn");
    if (generateAllButton) generateAllButton.disabled = plannedMusicPrompts.length === 0;

    plannedMusicPrompts.forEach((p, idx) => {
        const card = document.createElement("div");
        card.className = "prompt-card";

        const titleText = p.title || `Track ${idx + 1}`;
        const lyricsText = p.lyrics || "[Instrumental]";
        const sunoPromptText = p.suno_prompt || "";

        card.innerHTML = `
            <div>
                <div class="prompt-header">
                    <span class="prompt-number">#${idx + 1}</span>
                    <span class="badge-mood">${p.mood_keyword || '맞춤 힐링'}</span>
                </div>
                <div class="prompt-title">${titleText}</div>
                <div class="prompt-lyrics">${lyricsText}</div>
                <div class="prompt-tag">🎵 ${sunoPromptText}</div>
            </div>
            <button class="btn btn-primary btn-block mt-2" onclick="generateSunoTrack('${sunoPromptText.replace(/'/g, "")}', '${titleText.replace(/'/g, "")}', '${lyricsText.replace(/'/g, "").replace(/\n/g, " ")}')">
                <i class="fa-solid fa-compact-disc"></i> 이 프롬프트로 음원 생성하기
            </button>
        `;
        grid.appendChild(card);
    });
}

async function generateAllSunoTracks() {
    if (!plannedMusicPrompts.length) {
        alert("먼저 생성할 음악 프롬프트를 만들어 주세요.");
        return;
    }

    const button = document.getElementById("generate-all-btn");
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 전체 음원 생성 중...';
    }

    const monitor = document.getElementById("generation-monitor");
    const total = plannedMusicPrompts.length;
    let completed = 0;
    let failed = 0;

    for (const promptItem of plannedMusicPrompts) {
        const title = promptItem.title || `Track ${completed + failed + 1}`;
        const prompt = promptItem.suno_prompt || "";
        const lyrics = promptItem.lyrics || "[Instrumental]";
        if (monitor) {
            monitor.style.display = "block";
            document.getElementById("monitor-task-id").textContent = `전체 생성 ${completed + failed + 1}/${total}`;
            document.getElementById("monitor-status-text").textContent = `${title} 생성 중...`;
        }

        try {
            const track = await requestAndWaitForTrack(prompt, title, lyrics);
            generatedTracks.push(track);
            completed += 1;
            renderGeneratedTracks();
        } catch (error) {
            failed += 1;
            generatedTracks.push({ title, prompt, status: "ERROR", error: error.message });
            renderGeneratedTracks();
        }
    }

    if (monitor) monitor.style.display = "none";
    if (button) {
        button.disabled = false;
        button.innerHTML = '<i class="fa-solid fa-layer-group"></i> 생성된 프롬프트 전체 음원 자동 생성';
    }
    alert(`전체 생성 작업이 끝났습니다. 성공 ${completed}곡, 실패 ${failed}곡`);
}

async function requestAndWaitForTrack(prompt, title, lyrics) {
    const res = await fetch(`${API_BASE_URL}/api/music/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, title, lyrics })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "음원 생성 요청 실패");

    for (let attempt = 0; attempt < 60; attempt += 1) {
        const statusRes = await fetch(`${API_BASE_URL}/api/music/status/${data.task_id}`);
        const statusData = await statusRes.json();
        if (statusData.status === "SUCCESS" && statusData.audio_url) {
            return { title, prompt, audioUrl: statusData.audio_url, status: "SUCCESS" };
        }
        if (["ERROR", "FAILED", "FAILURE"].includes(statusData.status)) {
            throw new Error(statusData.message || "음원 생성 실패");
        }
        const progress = Math.min(95, 20 + attempt * 1.2);
        document.getElementById("progress-bar-fill").style.width = `${progress}%`;
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
    throw new Error("생성 시간이 초과되었습니다.");
}

function renderGeneratedTracks() {
    const card = document.getElementById("generated-tracks-card");
    const list = document.getElementById("generated-tracks-list");
    const count = document.getElementById("generated-tracks-count");
    if (!card || !list || !count) return;

    card.style.display = generatedTracks.length ? "block" : "none";
    count.textContent = `${generatedTracks.length}곡`;
    list.innerHTML = "";

    generatedTracks.forEach((track, index) => {
        const item = document.createElement("article");
        item.className = `generated-track ${track.status === "ERROR" ? "generated-track-error" : ""}`;
        const title = document.createElement("h4");
        title.textContent = `${index + 1}. ${track.title}`;
        item.appendChild(title);

        if (track.status === "ERROR") {
            const error = document.createElement("p");
            error.className = "text-muted";
            error.textContent = `생성 실패: ${track.error}`;
            item.appendChild(error);
        } else {
            const audio = document.createElement("audio");
            audio.controls = true;
            audio.preload = "metadata";
            audio.src = track.audioUrl;
            item.appendChild(audio);

            const actions = document.createElement("div");
            actions.className = "generated-track-actions";
            actions.innerHTML = `
                <button class="btn btn-sm btn-success"><i class="fa-solid fa-desktop"></i> PC 저장</button>
                <button class="btn btn-sm btn-outline"><i class="fa-solid fa-download"></i> 다운로드</button>
                <button class="btn btn-sm btn-danger"><i class="fa-solid fa-trash"></i> 삭제</button>`;
            actions.children[0].addEventListener("click", () => downloadTrackToLocalPC(track));
            actions.children[1].addEventListener("click", () => downloadTrackInBrowser(track));
            actions.children[2].addEventListener("click", () => {
                generatedTracks.splice(index, 1);
                renderGeneratedTracks();
            });
            item.appendChild(actions);
        }
        list.appendChild(item);
    });
}

async function downloadTrackToLocalPC(track) {
    try {
        const res = await fetch(`${API_BASE_URL}/api/music/download`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ audio_url: track.audioUrl, file_name: `${track.title}.mp3` })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "다운로드 실패");
        alert(`내 PC에 저장했습니다.\n${data.file_path}`);
    } catch (error) {
        alert(`PC 저장 실패: ${error.message}`);
    }
}

function downloadTrackInBrowser(track) {
    const link = document.createElement("a");
    link.href = track.audioUrl;
    link.target = "_blank";
    link.download = `${track.title}.mp3`;
    document.body.appendChild(link);
    link.click();
    link.remove();
}

function switchToMusicAndGenerate(title, prompt, lyrics) {
    document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

    const musicTabBtn = document.querySelector('[data-tab="tab-music"]');
    const musicTab = document.getElementById("tab-music");
    if (musicTabBtn && musicTab) {
        musicTabBtn.classList.add("active");
        musicTab.classList.add("active");
    }

    generateSunoTrack(prompt, title, lyrics);
}

async function generateSunoTrack(prompt, title, lyrics) {
    currentTrackTitle = title || "suno_music";
    const monitor = document.getElementById("generation-monitor");
    const playerCard = document.getElementById("result-player-card");

    monitor.style.display = "block";
    playerCard.style.display = "none";
    document.getElementById("progress-bar-fill").style.width = "15%";
    document.getElementById("monitor-status-text").textContent = "Apiframe Suno API에 음원 생성을 요청하고 있습니다...";

    try {
        const res = await fetch(`${API_BASE_URL}/api/music/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt, title, lyrics })
        });

        if (!res.ok) {
            const err = await res.json();
            alert(`음원 생성 실패: ${err.detail || '오류 발생'}`);
            monitor.style.display = "none";
            return;
        }

        const data = await res.json();
        document.getElementById("monitor-task-id").textContent = `Task ID: ${data.task_id}`;
        
        // Start Polling
        startStatusPolling(data.task_id, title, prompt);
    } catch (e) {
        alert(`통신 오류: ${e.message}`);
        monitor.style.display = "none";
    }
}

function startStatusPolling(taskId, title, prompt) {
    if (currentTaskPollInterval) clearInterval(currentTaskPollInterval);

    let progress = 20;
    currentTaskPollInterval = setInterval(async () => {
        try {
            progress = Math.min(95, progress + 8);
            document.getElementById("progress-bar-fill").style.width = `${progress}%`;

            const res = await fetch(`${API_BASE_URL}/api/music/status/${taskId}`);
            if (!res.ok) return;

            const data = await res.json();
            document.getElementById("monitor-status-text").textContent = data.message || `생성 진행 중 (${data.status})`;

            if (data.status === "SUCCESS" && data.audio_url) {
                clearInterval(currentTaskPollInterval);
                document.getElementById("progress-bar-fill").style.width = "100%";

                setTimeout(() => {
                    document.getElementById("generation-monitor").style.display = "none";
                    showAudioPlayer(data.audio_url, title, prompt);
                }, 800);
            }
        } catch (e) {
            console.error("Polling error:", e);
        }
    }, 5000); // Poll every 5 seconds
}

function showAudioPlayer(audioUrl, title, prompt) {
    currentGeneratedAudioUrl = audioUrl;
    const playerCard = document.getElementById("result-player-card");
    const player = document.getElementById("audio-player");

    document.getElementById("player-title").textContent = title || "생성된 Suno 트랙";
    document.getElementById("player-prompt").textContent = prompt || "";
    player.src = audioUrl;
    playerCard.style.display = "block";
    player.play();
}

async function downloadToLocalPC() {
    if (!currentGeneratedAudioUrl) {
        alert("다운로드할 음원이 없습니다.");
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/api/music/download`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                audio_url: currentGeneratedAudioUrl,
                file_name: `${currentTrackTitle}.mp3`
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert(`✅ 내 PC 지정 폴더로 음원 다운로드 성공!\n저장 경로: ${data.file_path}`);
        } else {
            alert(`❌ 다운로드 실패: ${data.detail || '서버 오류'}`);
        }
    } catch (e) {
        alert(`오류 발생: ${e.message}`);
    }
}

function downloadBrowser() {
    if (!currentGeneratedAudioUrl) return;
    const a = document.createElement("a");
    a.href = currentGeneratedAudioUrl;
    a.target = "_blank";
    a.download = `${currentTrackTitle}.mp3`;
    document.body.appendChild(a);
    a.click();
    a.remove();
}

// --- Conversations History Logic ---
async function loadConversationsList() {
    const listEl = document.getElementById("history-list");
    try {
        const res = await fetch(`${API_BASE_URL}/api/conversations`);
        if (!res.ok) return;

        const sessions = await res.json();
        if (sessions.length === 0) {
            listEl.innerHTML = `<p class="text-center py-4">저장된 대화 기록이 없습니다.</p>`;
            return;
        }

        listEl.innerHTML = "";
        sessions.forEach(s => {
            const item = document.createElement("div");
            item.className = "history-item";
            const updatedDate = s.updated_at ? new Date(s.updated_at).toLocaleString() : '최근';
            const msgCount = s.messages ? s.messages.length : 0;

            item.innerHTML = `
                <div class="history-info">
                    <h4>💬 ${s.title || '대화 세션'}</h4>
                    <p>마지막 대화: ${updatedDate} | 메시지 ${msgCount}개</p>
                </div>
                <div style="display:flex; gap:0.5rem;">
                    <button class="btn btn-sm btn-primary" onclick="loadConversationSession('${s.id}')">
                        <i class="fa-solid fa-folder-open"></i> 불러오기
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteConversationSession('${s.id}')">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            `;
            listEl.appendChild(item);
        });
    } catch (e) {
        listEl.innerHTML = `<p class="text-center py-4 text-muted">대화 목록 불러오기 실패: ${e.message}</p>`;
    }
}

async function loadConversationSession(convId) {
    try {
        const res = await fetch(`${API_BASE_URL}/api/conversations/${convId}`);
        if (!res.ok) return;

        const session = await res.json();
        activeConversationId = session.id;

        // Switch to Chat tab
        document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

        document.querySelector('[data-tab="tab-chat"]').classList.add("active");
        document.getElementById("tab-chat").classList.add("active");

        // Clear and reload messages
        const chatContainer = document.getElementById("chat-messages");
        chatContainer.innerHTML = "";

        session.messages.forEach(m => {
            appendChatMessage(m.role, m.content);
        });

        alert(`💬 '${session.title}' 대화 세션을 성공적으로 불러왔습니다.`);
    } catch (e) {
        alert(`불러오기 오류: ${e.message}`);
    }
}

async function deleteConversationSession(convId) {
    if (!confirm("이 대화 세션을 삭제하시겠습니까?")) return;

    try {
        const res = await fetch(`${API_BASE_URL}/api/conversations/${convId}`, { method: "DELETE" });
        if (res.ok) {
            loadConversationsList();
        } else {
            alert("삭제에 실패했습니다.");
        }
    } catch (e) {
        alert(`오류: ${e.message}`);
    }
}
