(function () {
  const PAGE = document.body.dataset.page || "console";
  const API_BASE = window.BILIGLASS_API_BASE || "";
  const state = {
    bootstrap: null,
    bound: false,
    pollTimer: null,
    toastTimer: null,
    backendErrorShown: false,
    local: {
      files: [],
      sourceMode: "file",
    },
    selectedOutputFormat: "txt",
    selectedDevice: "auto",
    selectedModel: "base",
    selectedOutputDir: "",
    selectedToggles: {
      auto_open_dir: true,
      delete_audio_after_transcribe: true,
      check_updates: false,
    },
  };

  function $(selector, root = document) {
    return root.querySelector(selector);
  }

  function $all(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatDuration(seconds) {
    const total = Number(seconds || 0);
    const minutes = Math.floor(total / 60);
    const secs = Math.floor(total % 60);
    return `${minutes}:${String(secs).padStart(2, "0")}`;
  }

  function formatDate(ts) {
    const date = new Date((ts || Date.now() / 1000) * 1000);
    return date.toLocaleString("zh-CN", { hour12: false });
  }

  function taskStatusIcon(task) {
    switch (task.status_key) {
      case "DOWNLOADING":
        return "downloading";
      case "TRANSCRIBING":
        return "graphic_eq";
      case "COMPLETED":
        return "check_circle";
      case "FAILED":
        return "error";
      case "STOPPED":
        return "pause_circle";
      default:
        return "schedule";
    }
  }

  function taskAccent(task) {
    switch (task.status_key) {
      case "DOWNLOADING":
        return "from-secondary to-tertiary";
      case "TRANSCRIBING":
        return "from-primary to-primary-container";
      case "COMPLETED":
        return "from-tertiary to-secondary-fixed-dim";
      case "FAILED":
        return "from-error to-error-container";
      case "STOPPED":
        return "from-zinc-400 to-zinc-500";
      default:
        return "from-zinc-300 to-zinc-400";
    }
  }

  function taskPrimaryAction(task) {
    if (task.status_key === "COMPLETED") {
      return { icon: "folder_open", label: "打开目录", action: "open" };
    }
    if (task.status_key === "FAILED" || task.status_key === "STOPPED") {
      return { icon: "replay", label: "重试", action: "retry" };
    }
    return { icon: "pause_circle", label: "停止", action: "stop" };
  }

  function taskDisplayTitle(task) {
    if (task.source_type === "local") {
      return task.source_name || task.title || "本地文件";
    }
    return task.title || "未命名视频";
  }

  function taskDisplaySubtitle(task) {
    if (task.source_type === "local") {
      return task.source_name || task.bvid || "本地文件";
    }
    return `UP: ${task['up主'] || "未知UP主"}`;
  }

  function taskDisplayBadge(task) {
    return task.source_type === "local" ? "本地转写" : "Bilibili";
  }

  async function request(path, options = {}) {
    const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
    const headers = { ...(options.headers || {}) };
    if (!isFormData && !headers["Content-Type"] && !headers["content-type"]) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...headers,
        ...(options.headers || {}),
      },
    });

    const contentType = response.headers.get("content-type") || "";
    const body = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const errorMessage = body && typeof body === "object" ? body.error || "请求失败" : String(body || "请求失败");
      throw new Error(errorMessage);
    }

    return body;
  }

  function showToast(message, tone = "default") {
    let container = $("#biliglass-toast-root");
    if (!container) {
      container = document.createElement("div");
      container.id = "biliglass-toast-root";
      container.className = "fixed bottom-6 right-6 z-[9999] flex flex-col gap-2";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    const palette = {
      default: "bg-white text-on-surface border-white/60",
      success: "bg-emerald-500 text-white",
      error: "bg-red-500 text-white",
    };
    toast.className = `max-w-sm rounded-2xl px-4 py-3 shadow-2xl backdrop-blur-md border ${palette[tone] || palette.default}`;
    toast.textContent = message;
    container.appendChild(toast);

    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => {
      toast.remove();
    }, 2600);
  }

  function findSectionByHeading(text) {
    return $all("section").find((section) => {
      const heading = section.querySelector("h3, h2");
      return heading && heading.textContent.includes(text);
    });
  }

  function updateTextInside(root, selector, value) {
    const node = root ? $(selector, root) : null;
    if (node) node.textContent = value;
  }

  function renderStatusCards(bootstrap) {
    const cookieCard = $all("section").find((section) => section.querySelector("h4")?.textContent.includes("Cookie 状态"));
    const gpuCard = $all("section").find((section) => section.querySelector("h4")?.textContent.includes("GPU 加速"));
    const storageCard = $all("section").find((section) => section.querySelector("h4")?.textContent.includes("存储容量"));

    if (cookieCard) {
      const value = cookieCard.querySelector("h4");
      const detail = cookieCard.querySelector("p.text-xs.text-tertiary, p.text-xs.text-on-surface-variant, p.text-xs.text-primary");
      if (value) value.textContent = bootstrap.cookie.verified ? "已登录" : bootstrap.cookie.saved ? "待验证" : "未配置";
      if (detail) detail.textContent = bootstrap.cookie.message || "Cookie 状态待更新";
    }

    if (gpuCard) {
      const value = gpuCard.querySelector("h4");
      const detail = gpuCard.querySelector("p.text-xs.text-primary, p.text-xs.text-on-surface-variant");
      if (value) value.textContent = bootstrap.hardware.cuda_available ? "CUDA GPU" : "CPU";
      if (detail) detail.textContent = bootstrap.hardware.cuda_available ? "GPU 已就绪" : "当前使用 CPU 处理";
    }

    if (storageCard) {
      const value = storageCard.querySelector("h4");
      const bar = storageCard.querySelector(".w-32.h-1\\.5 > div");
      if (value) value.textContent = `${bootstrap.storage.used_gb.toFixed(1)} GB`;
      if (bar) bar.style.width = `${Math.min(100, Math.max(8, bootstrap.storage.used_gb * 3))}%`;
    }
  }

  function renderTaskCard(task) {
    const primary = taskPrimaryAction(task);
    const progress = Math.max(0, Math.min(100, Number(task.progress || 0)));
    const remainingMinutes = task.duration && progress > 0
      ? Math.max(0, Math.round(((100 - progress) / Math.max(progress, 1)) * (task.duration / 60)))
      : Math.ceil((100 - progress) / 10);
    const cover = task.cover
      ? `<img class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" src="${escapeHtml(task.cover)}" alt="${escapeHtml(task.title)}"/>`
      : `<div class="w-full h-full bg-gradient-to-br from-primary/25 via-primary-container/20 to-tertiary/20 flex items-center justify-center"><span class="material-symbols-outlined text-white text-4xl drop-shadow">${task.source_type === "local" ? "audio_file" : taskStatusIcon(task)}</span></div>`;

    const stageChips = [];
    if (task.status_key === "PENDING") {
      stageChips.push(`<span class="flex items-center gap-1 text-on-surface-variant"><span class="material-symbols-outlined text-sm">schedule</span>${task.source_type === "local" ? "等待转写" : "等待处理"}</span>`);
    }
    if (task.status_key === "DOWNLOADING") {
      stageChips.push(task.source_type === "local"
        ? `<span class="flex items-center gap-1 text-tertiary"><span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">check_circle</span>文件已导入</span>`
        : `<span class="flex items-center gap-1 text-tertiary"><span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">check_circle</span>视频下载</span>`);
      stageChips.push(`<span class="flex items-center gap-1 text-primary"><span class="material-symbols-outlined text-sm">downloading</span>语音识别</span>`);
    }
    if (task.status_key === "TRANSCRIBING") {
      stageChips.push(task.source_type === "local"
        ? `<span class="flex items-center gap-1 text-tertiary"><span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">check_circle</span>文件已导入</span>`
        : `<span class="flex items-center gap-1 text-tertiary"><span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">check_circle</span>视频下载</span>`);
      stageChips.push(`<span class="flex items-center gap-1 text-primary"><span class="material-symbols-outlined text-sm">graphic_eq</span>语音识别</span>`);
    }
    if (task.status_key === "COMPLETED") {
      stageChips.push(`<span class="flex items-center gap-1 text-tertiary"><span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">check_circle</span>${task.source_type === "local" ? "转写完成" : "全部完成"}</span>`);
      if (task.subtitle_path) {
        stageChips.push(`<span class="flex items-center gap-1 text-primary"><span class="material-symbols-outlined text-sm">description</span>字幕已保存</span>`);
      }
    }
    if (task.status_key === "FAILED") {
      stageChips.push(`<span class="flex items-center gap-1 text-error"><span class="material-symbols-outlined text-sm">error</span>${escapeHtml(task.error_msg || "处理失败")}</span>`);
    }
    if (task.status_key === "STOPPED") {
      stageChips.push(`<span class="flex items-center gap-1 text-on-surface-variant"><span class="material-symbols-outlined text-sm">pause_circle</span>已停止</span>`);
    }

    const actionButton = task.status_key === "COMPLETED"
      ? `<button class="task-action p-3 text-on-surface-variant hover:text-tertiary hover:bg-tertiary/10 rounded-xl transition-colors active:scale-95" data-task-id="${escapeHtml(task.id)}" data-action="open" title="打开目录"><span class="material-symbols-outlined">${primary.icon}</span></button>`
      : `<button class="task-action p-3 text-on-surface-variant hover:text-error hover:bg-error/10 rounded-xl transition-colors active:scale-95" data-task-id="${escapeHtml(task.id)}" data-action="${primary.action}" title="${primary.label}"><span class="material-symbols-outlined">${primary.icon}</span></button>`;

    return `
      <div class="bg-surface-container-lowest p-5 rounded-2xl border border-white/50 shadow-sm hover:shadow-md transition-shadow group">
        <div class="flex flex-col lg:flex-row gap-6 items-center">
          <div class="w-full lg:w-48 aspect-video rounded-xl bg-surface-container-high overflow-hidden relative shrink-0">
            ${cover}
            <div class="absolute inset-0 bg-black/20 flex items-center justify-center">
              <span class="material-symbols-outlined text-white text-3xl">play_circle</span>
            </div>
            <div class="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/60 text-white text-[10px] rounded">${escapeHtml(task.duration_str || formatDuration(task.duration))}</div>
          </div>
          <div class="flex-1 min-w-0 py-1">
            <div class="flex items-start justify-between mb-2">
              <div class="min-w-0">
                <h4 class="font-bold text-lg leading-snug truncate">${escapeHtml(taskDisplayTitle(task))}</h4>
                <div class="flex items-center gap-3 mt-1 text-xs text-on-surface-variant flex-wrap">
                  <span class="flex items-center gap-1"><span class="material-symbols-outlined text-sm">source</span> ${escapeHtml(taskDisplayBadge(task))}</span>
                  <span class="flex items-center gap-1"><span class="material-symbols-outlined text-sm">person</span> ${escapeHtml(taskDisplaySubtitle(task))}</span>
                  <span class="flex items-center gap-1"><span class="material-symbols-outlined text-sm">id_card</span> ${escapeHtml(task.bvid)}</span>
                </div>
              </div>
              <div class="text-right shrink-0">
                <p class="text-sm font-bold text-primary">${Math.round(progress)}%</p>
                <p class="text-[10px] text-on-surface-variant uppercase tracking-widest mt-0.5">剩余约 ${remainingMinutes}m</p>
              </div>
            </div>
            <div class="space-y-2">
              <div class="w-full h-2.5 bg-surface-container-low rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r ${taskAccent(task)} rounded-full transition-all duration-1000" style="width:${progress}%"></div>
              </div>
              <div class="flex items-center justify-between text-[11px] font-medium text-on-surface-variant gap-3">
                <div class="flex gap-4 flex-wrap">${stageChips.join("")}</div>
                <div class="flex gap-2 shrink-0">
                  ${task.subtitle_path ? `<button class="task-action px-3 py-1.5 rounded-full bg-primary/10 text-primary text-[11px] font-bold" data-task-id="${escapeHtml(task.id)}" data-action="open">打开目录</button>` : ""}
                  ${task.audio_path ? `<button class="task-action px-3 py-1.5 rounded-full bg-tertiary/10 text-tertiary text-[11px] font-bold" data-task-id="${escapeHtml(task.id)}" data-action="open-audio">音频</button>` : ""}
                </div>
              </div>
            </div>
          </div>
          <div class="flex lg:flex-col gap-2 shrink-0">
            ${actionButton}
            <button class="task-action p-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high rounded-xl transition-colors active:scale-95" data-task-id="${escapeHtml(task.id)}" data-action="delete" title="移除任务">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
      </div>`;
  }

  function currentLayerOnly(files) {
    return files.filter((file) => {
      const relativePath = file.webkitRelativePath || "";
      if (!relativePath) return true;
      const parts = relativePath.split("/").filter(Boolean);
      return parts.length === 2;
    });
  }

  function formatLocalSelection(files) {
    if (!files.length) {
      return "尚未选择文件";
    }

    const visible = files.slice(0, 4).map((file) => file.name).join("、");
    const extra = files.length > 4 ? ` 等 ${files.length} 个文件` : "";
    return `${visible}${extra}`;
  }

  function bindConsolePage() {
    const consoleSection = findSectionByHeading("初始化提取");
    const input = $("#biliglass-console-input") || consoleSection?.querySelector('input[type="text"]');
    const addButton = $("#biliglass-console-add") || consoleSection?.querySelector("button");
    const startButton = $("#biliglass-console-start") || $all("button").find((btn) => btn.textContent.includes("▶ 开始"));
    const localPageButton = $("#biliglass-open-local-page") || $all("button").find((btn) => btn.textContent.includes("本地文件转文字稿"));
    const pasteButton = $all("button").find((btn) => btn.textContent.includes("粘贴"));
    const stopButton = $all("button").find((btn) => btn.textContent.includes("⏹ 停止"));
    const retryButton = $all("button").find((btn) => btn.textContent.includes("🔄 重试"));
    const clearButton = $all("button").find((btn) => btn.textContent.includes("🗑 清空"));
    const taskSection = findSectionByHeading("正在处理的任务队列");
    const taskList = taskSection ? taskSection.querySelector(".space-y-4") : null;
    const badgeRow = taskSection ? taskSection.querySelector(".flex.items-center.justify-between.mb-6") : null;
    const badges = badgeRow ? badgeRow.querySelectorAll("span.text-xs.font-medium") : [];

    function addCurrentInput() {
      const value = input?.value?.trim();
      if (!value) {
        showToast("请输入 BV 号或视频链接", "error");
        return;
      }
      request("/api/tasks/add", {
        method: "POST",
        body: JSON.stringify({ input: value }),
      })
        .then(() => {
          input.value = "";
          showToast("任务已加入队列", "success");
          sync();
        })
        .catch((error) => showToast(error.message, "error"));
    }

    if (addButton && addButton.dataset.boundAdd !== "1") {
      addButton.dataset.boundAdd = "1";
      addButton.addEventListener("click", addCurrentInput);
    }

    if (localPageButton && !localPageButton.dataset.boundOpenLocal) {
      localPageButton.dataset.boundOpenLocal = "1";
      localPageButton.addEventListener("click", () => {
        window.location.href = "/_4/code.html";
      });
    }

    if (input && !input.dataset.boundEnter) {
      input.dataset.boundEnter = "1";
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          addCurrentInput();
        }
      });
    }

    if (pasteButton && !pasteButton.dataset.boundPaste) {
      pasteButton.dataset.boundPaste = "1";
      pasteButton.addEventListener("click", async () => {
        try {
          const text = await navigator.clipboard.readText();
          if (input) input.value = text;
          showToast("已粘贴剪贴板内容", "success");
        } catch {
          showToast("无法读取剪贴板", "error");
        }
      });
    }

    if (startButton && !startButton.dataset.boundStart) {
      startButton.dataset.boundStart = "1";
      startButton.addEventListener("click", () => {
        request("/api/tasks/start", { method: "POST", body: JSON.stringify({}) })
          .then(() => {
            showToast("已开始处理队列", "success");
            sync();
          })
          .catch((error) => showToast(error.message, "error"));
      });
    }

    if (stopButton && !stopButton.dataset.boundStop) {
      stopButton.dataset.boundStop = "1";
      stopButton.addEventListener("click", () => {
        request("/api/tasks/stop", { method: "POST", body: JSON.stringify({}) })
          .then(() => {
            showToast("已停止全部任务", "success");
            sync();
          })
          .catch((error) => showToast(error.message, "error"));
      });
    }

    if (retryButton && !retryButton.dataset.boundRetry) {
      retryButton.dataset.boundRetry = "1";
      retryButton.addEventListener("click", () => {
        request("/api/tasks/retry-failed", { method: "POST", body: JSON.stringify({}) })
          .then(() => {
            showToast("失败任务已重试", "success");
            sync();
          })
          .catch((error) => showToast(error.message, "error"));
      });
    }

    if (clearButton && !clearButton.dataset.boundClear) {
      clearButton.dataset.boundClear = "1";
      clearButton.addEventListener("click", () => {
        request("/api/tasks/clear-completed", { method: "POST", body: JSON.stringify({}) })
          .then(() => {
            showToast("已清空完成任务", "success");
            sync();
          })
          .catch((error) => showToast(error.message, "error"));
      });
    }

    if (taskList && !taskList.dataset.boundTasks) {
      taskList.dataset.boundTasks = "1";
      taskList.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-task-id]");
        if (!button) return;
        const { taskId, action } = button.dataset;
        if (!taskId || !action) return;

        let endpoint = null;
        if (action === "retry") endpoint = `/api/tasks/${taskId}/retry`;
        if (action === "stop") endpoint = `/api/tasks/${taskId}/stop`;
        if (action === "delete") endpoint = `/api/tasks/${taskId}/delete`;
        if (action === "open") endpoint = `/api/tasks/${taskId}/open`;
        if (action === "open-audio") endpoint = `/api/tasks/${taskId}/open-audio`;

        if (!endpoint) return;

        request(endpoint, { method: "POST", body: JSON.stringify({}) })
          .then((result) => {
            if (action === "open" || action === "open-audio") {
              showToast(result.target ? `已打开目录：${result.target}` : "已打开目录", "success");
            } else {
              showToast("操作已完成", "success");
            }
            sync();
          })
          .catch((error) => showToast(error.message, "error"));
      });
    }

    state.console = { input, taskList, badgeRow, badges };
  }

  function bindLocalPage() {
    const fileInput = $("#biliglass-local-files");
    const folderInput = $("#biliglass-local-folder");
    const chooseFileButton = $("#biliglass-local-choose-file");
    const chooseFolderButton = $("#biliglass-local-choose-folder");
    const uploadButton = $("#biliglass-local-upload");
    const clearSelectionButton = $("#biliglass-local-clear");
    const dropzone = $("#biliglass-local-dropzone");
    const taskList = $("#biliglass-local-task-list");

    function setSelection(files, sourceMode) {
      state.local.files = files;
      state.local.sourceMode = sourceMode;
      renderLocalSelection();
    }

    function onFilesPicked(fileList, sourceMode) {
      const files = Array.from(fileList || []);
      const filtered = sourceMode === "folder" ? currentLayerOnly(files) : files;
      setSelection(filtered, sourceMode);
      showToast(filtered.length ? `已选择 ${filtered.length} 个文件` : "未找到符合条件的文件", filtered.length ? "success" : "error");
    }

    function renderLocalSelection() {
      const countNode = $("#biliglass-local-selection-count");
      const summaryNode = $("#biliglass-local-selection-summary");
      if (countNode) {
        countNode.textContent = `${state.local.files.length} 个文件`;
      }
      if (summaryNode) {
        summaryNode.textContent = formatLocalSelection(state.local.files);
      }
    }

    async function uploadSelectedFiles() {
      if (!state.local.files.length) {
        showToast("请先选择文件或文件夹", "error");
        return;
      }

      const formData = new FormData();
      state.local.files.forEach((file) => {
        const relativeName = file.webkitRelativePath || file.name;
        formData.append("media_files", file, relativeName);
      });

      uploadButton?.setAttribute("disabled", "true");
      try {
        const response = await fetch(`${API_BASE}/api/local/upload`, {
          method: "POST",
          body: formData,
        });
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.error || "上传失败");
        }

        state.local.files = [];
        renderLocalSelection();
        showToast(`已加入 ${result.count || 0} 个本地任务`, "success");
        sync();
      } catch (error) {
        showToast(error.message, "error");
      } finally {
        uploadButton?.removeAttribute("disabled");
      }
    }

    if (chooseFileButton && !chooseFileButton.dataset.boundPickFile) {
      chooseFileButton.dataset.boundPickFile = "1";
      chooseFileButton.addEventListener("click", () => fileInput?.click());
    }

    if (chooseFolderButton && !chooseFolderButton.dataset.boundPickFolder) {
      chooseFolderButton.dataset.boundPickFolder = "1";
      chooseFolderButton.addEventListener("click", () => folderInput?.click());
    }

    if (uploadButton && !uploadButton.dataset.boundUpload) {
      uploadButton.dataset.boundUpload = "1";
      uploadButton.addEventListener("click", uploadSelectedFiles);
    }

    if (clearSelectionButton && !clearSelectionButton.dataset.boundClearSelection) {
      clearSelectionButton.dataset.boundClearSelection = "1";
      clearSelectionButton.addEventListener("click", () => {
        state.local.files = [];
        if (fileInput) fileInput.value = "";
        if (folderInput) folderInput.value = "";
        renderLocalSelection();
      });
    }

    if (fileInput && !fileInput.dataset.boundChange) {
      fileInput.dataset.boundChange = "1";
      fileInput.addEventListener("change", () => onFilesPicked(fileInput.files, "file"));
    }

    if (folderInput && !folderInput.dataset.boundChange) {
      folderInput.dataset.boundChange = "1";
      folderInput.addEventListener("change", () => onFilesPicked(folderInput.files, "folder"));
    }

    if (dropzone && !dropzone.dataset.boundDrop) {
      dropzone.dataset.boundDrop = "1";
      ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropzone.classList.add("ring-2", "ring-primary", "bg-primary/5");
        });
      });

      ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropzone.classList.remove("ring-2", "ring-primary", "bg-primary/5");
        });
      });

      dropzone.addEventListener("drop", (event) => {
        const droppedFiles = Array.from(event.dataTransfer?.files || []).filter((file) => file.type || file.name);
        onFilesPicked(droppedFiles, "file");
      });
    }

    if (taskList && !taskList.dataset.boundLocalTasks) {
      taskList.dataset.boundLocalTasks = "1";
      taskList.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-task-id]");
        if (!button) return;
        const { taskId, action } = button.dataset;
        if (!taskId || !action) return;

        let endpoint = null;
        if (action === "retry") endpoint = `/api/tasks/${taskId}/retry`;
        if (action === "stop") endpoint = `/api/tasks/${taskId}/stop`;
        if (action === "delete") endpoint = `/api/tasks/${taskId}/delete`;
        if (action === "open") endpoint = `/api/tasks/${taskId}/open`;
        if (action === "open-audio") endpoint = `/api/tasks/${taskId}/open-audio`;

        if (!endpoint) return;

        request(endpoint, { method: "POST", body: JSON.stringify({}) })
          .then((result) => {
            if (action === "open" || action === "open-audio") {
              showToast(result.target ? `已打开目录：${result.target}` : "已打开目录", "success");
            } else {
              showToast("操作已完成", "success");
            }
            sync();
          })
          .catch((error) => showToast(error.message, "error"));
      });
    }

    renderLocalSelection();
    state.local.taskList = taskList;
  }

  function renderConsole(bootstrap) {
    if (!state.bound) {
      bindConsolePage();
      state.bound = true;
    }

    renderStatusCards(bootstrap);

    if (state.console?.badges?.length >= 2) {
      state.console.badges[0].textContent = `${bootstrap.stats.running} 正在处理`;
      state.console.badges[1].textContent = `${bootstrap.stats.waiting} 等待中`;
    }

    if (state.console?.taskList) {
      const sortedTasks = [...bootstrap.tasks].sort((a, b) => b.created_at - a.created_at);
      if (sortedTasks.length === 0) {
        state.console.taskList.innerHTML = `
          <div class="rounded-3xl border border-dashed border-white/60 bg-white/60 p-10 text-center text-on-surface-variant">
            <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <span class="material-symbols-outlined">playlist_add</span>
            </div>
            <p class="text-sm font-bold text-on-surface">还没有任务</p>
            <p class="mt-1 text-xs text-on-surface-variant">先粘贴 BV 号或视频链接，再点击加入队列。</p>
          </div>`;
      } else {
        state.console.taskList.innerHTML = sortedTasks.map(renderTaskCard).join("");
      }
    }

    const activeBadge = $('span.px-2.py-0\\.5.rounded');
    if (activeBadge) {
      activeBadge.textContent = bootstrap.running ? "ACTIVE" : "IDLE";
      activeBadge.className = bootstrap.running
        ? "px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-widest"
        : "px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant text-[10px] font-bold uppercase tracking-widest";
    }

    const footerLoad = $all("footer p").find((node) => node.textContent.includes("System Load"));
    if (footerLoad) {
      footerLoad.textContent = `v2.4.0-pro | System Load: ${Math.min(99, 8 + bootstrap.stats.running * 20 + bootstrap.stats.waiting * 5)}%`;
    }

    const logRoot = $("#runtime-log-list");
    const logCount = $("#log-count");
    if (logRoot) {
      const logs = Array.isArray(bootstrap.logs) ? bootstrap.logs : [];
      if (logs.length === 0) {
        logRoot.innerHTML = '<div class="text-on-surface-variant">暂无日志，等待任务开始。</div>';
      } else {
        logRoot.innerHTML = logs
          .slice(-80)
          .reverse()
          .map((entry) => `
            <div class="flex items-start gap-3 rounded-xl bg-white/70 px-3 py-2 border border-white/60">
              <span class="mt-1 h-2 w-2 rounded-full bg-primary shrink-0"></span>
              <div class="min-w-0">
                <div class="text-[11px] text-on-surface-variant">${formatDate(entry.ts)}</div>
                <div class="text-sm text-on-surface break-words">${escapeHtml(entry.message)}</div>
              </div>
            </div>
          `)
          .join("");
      }
      if (logCount) {
        logCount.textContent = `${logs.length} 条记录`;
      }
      const logViewport = logRoot.parentElement;
      if (logViewport) {
        logViewport.scrollTop = 0;
      }
    }
  }

  function renderLibrary(bootstrap) {
    const root = $("#library-root");
    if (!root) return;

    const historyTasks = [...bootstrap.tasks]
      .filter((task) => ["COMPLETED", "FAILED", "STOPPED"].includes(task.status_key))
      .sort((a, b) => b.created_at - a.created_at);

    const finishedCount = historyTasks.filter((task) => task.status_key === "COMPLETED").length;
    const failedCount = historyTasks.filter((task) => task.status_key === "FAILED").length;
    const stoppedCount = historyTasks.filter((task) => task.status_key === "STOPPED").length;

    root.innerHTML = `
      <section class="max-w-6xl mx-auto space-y-8">
        <div class="bg-surface-container-lowest rounded-3xl p-8 shadow-[0_8px_32px_0_rgba(164,46,86,0.04)] border border-white relative overflow-hidden">
          <div class="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
          <div class="relative z-10 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h3 class="font-headline text-3xl font-bold mb-2">任务库</h3>
              <p class="text-on-surface-variant text-sm max-w-2xl">这里显示完成历史、失败记录和中断记录。你可以在这里回看输出、打开目录，或者重新处理失败任务。</p>
            </div>
            <button class="task-action inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-primary text-white font-bold shadow-lg shadow-primary/20" data-action="open-output">
              <span class="material-symbols-outlined text-[20px]">folder_open</span>
              打开输出目录
            </button>
          </div>
        </div>

        <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-surface-container-lowest p-6 rounded-2xl border border-white/50 shadow-sm flex items-start justify-between">
            <div>
              <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-1">已完成</p>
              <h4 class="text-3xl font-bold">${finishedCount}</h4>
              <p class="text-xs text-tertiary mt-2">成功生成字幕或转写文件</p>
            </div>
            <div class="p-3 rounded-xl bg-tertiary/10 text-tertiary"><span class="material-symbols-outlined">check_circle</span></div>
          </div>
          <div class="bg-surface-container-lowest p-6 rounded-2xl border border-white/50 shadow-sm flex items-start justify-between">
            <div>
              <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-1">失败记录</p>
              <h4 class="text-3xl font-bold">${failedCount}</h4>
              <p class="text-xs text-error mt-2">可重试并查看错误信息</p>
            </div>
            <div class="p-3 rounded-xl bg-error/10 text-error"><span class="material-symbols-outlined">error</span></div>
          </div>
          <div class="bg-surface-container-lowest p-6 rounded-2xl border border-white/50 shadow-sm flex items-start justify-between">
            <div>
              <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-1">中断任务</p>
              <h4 class="text-3xl font-bold">${stoppedCount}</h4>
              <p class="text-xs text-on-surface-variant mt-2">保留记录，方便恢复</p>
            </div>
            <div class="p-3 rounded-xl bg-surface-container-high text-on-surface-variant"><span class="material-symbols-outlined">pause_circle</span></div>
          </div>
        </section>

        <section class="space-y-6">
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="font-headline text-xl font-bold">完成历史记录</h3>
              <p class="text-sm text-on-surface-variant">按时间倒序显示最近处理结果</p>
            </div>
            <span class="text-xs font-medium px-3 py-1 bg-surface-container-high rounded-full">${historyTasks.length} 条记录</span>
          </div>
          <div class="space-y-4" id="library-root-list">
            ${historyTasks.length
              ? historyTasks.map(renderTaskCard).join("")
              : `<div class="rounded-3xl border border-dashed border-white/60 bg-white/60 p-10 text-center text-on-surface-variant">
                  <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <span class="material-symbols-outlined">history</span>
                  </div>
                  <p class="text-sm font-bold text-on-surface">还没有历史记录</p>
                  <p class="mt-1 text-xs text-on-surface-variant">等任务完成后，这里会显示完成历史、失败重试和中断记录。</p>
                </div>`}
          </div>
        </section>
      </section>`;

    const rootList = $("#library-root-list");
    if (rootList && !rootList.dataset.boundLibrary) {
      rootList.dataset.boundLibrary = "1";
      rootList.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-task-id]");
        if (!button) return;
        const { taskId, action } = button.dataset;
        if (!taskId || !action) return;

        let endpoint = null;
        if (action === "retry") endpoint = `/api/tasks/${taskId}/retry`;
        if (action === "stop") endpoint = `/api/tasks/${taskId}/stop`;
        if (action === "delete") endpoint = `/api/tasks/${taskId}/delete`;
        if (action === "open") endpoint = `/api/tasks/${taskId}/open`;
        if (action === "open-audio") endpoint = `/api/tasks/${taskId}/open-audio`;
        if (!endpoint) return;

        request(endpoint, { method: "POST", body: JSON.stringify({}) })
          .then((result) => {
            if (action === "open" || action === "open-audio") {
              showToast(result.target ? `已打开目录：${result.target}` : "已打开目录", "success");
            } else {
              showToast("操作已完成", "success");
            }
            sync();
          })
          .catch((error) => showToast(error.message, "error"));
      });
    }

    const openOutputButton = root.querySelector("button[data-action='open-output']");
    if (openOutputButton && !openOutputButton.dataset.boundOpenOutput) {
      openOutputButton.dataset.boundOpenOutput = "1";
      openOutputButton.addEventListener("click", () => {
        request("/api/output/open", { method: "POST", body: JSON.stringify({}) })
          .then((result) => showToast(`已打开输出目录：${result.target}`, "success"))
          .catch((error) => showToast(error.message, "error"));
      });
    }
  }

  function renderLocalPage(bootstrap) {
    if (!state.bound) {
      bindLocalPage();
      state.bound = true;
    }

    renderStatusCards(bootstrap);

    const localTasks = [...bootstrap.tasks]
      .filter((task) => task.source_type === "local")
      .sort((a, b) => b.created_at - a.created_at);

    const runningCount = localTasks.filter((task) => task.status_key === "TRANSCRIBING").length;
    const completedCount = localTasks.filter((task) => task.status_key === "COMPLETED").length;
    const failedCount = localTasks.filter((task) => task.status_key === "FAILED").length;

    updateTextInside(document, "#biliglass-local-total", `${localTasks.length}`);
    updateTextInside(document, "#biliglass-local-running", `${runningCount}`);
    updateTextInside(document, "#biliglass-local-running-inline", `${runningCount}`);
    updateTextInside(document, "#biliglass-local-completed", `${completedCount}`);
    updateTextInside(document, "#biliglass-local-failed", `${failedCount}`);

    if (state.local.taskList) {
      if (localTasks.length === 0) {
        state.local.taskList.innerHTML = `
          <div class="rounded-3xl border border-dashed border-white/60 bg-white/60 p-10 text-center text-on-surface-variant">
            <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <span class="material-symbols-outlined">audio_file</span>
            </div>
            <p class="text-sm font-bold text-on-surface">还没有本地任务</p>
            <p class="mt-1 text-xs text-on-surface-variant">先选择文件或文件夹，再点击上传并转写。</p>
          </div>`;
      } else {
        state.local.taskList.innerHTML = localTasks.map(renderTaskCard).join("");
      }
    }

    const logRoot = $("#runtime-log-list");
    const logCount = $("#log-count");
    if (logRoot) {
      const logs = Array.isArray(bootstrap.logs) ? bootstrap.logs : [];
      if (logs.length === 0) {
        logRoot.innerHTML = '<div class="text-on-surface-variant">暂无日志，等待任务开始。</div>';
      } else {
        logRoot.innerHTML = logs
          .slice(-80)
          .reverse()
          .map((entry) => `
            <div class="flex items-start gap-3 rounded-xl bg-white/70 px-3 py-2 border border-white/60">
              <span class="mt-1 h-2 w-2 rounded-full bg-primary shrink-0"></span>
              <div class="min-w-0">
                <div class="text-[11px] text-on-surface-variant">${formatDate(entry.ts)}</div>
                <div class="text-sm text-on-surface break-words">${escapeHtml(entry.message)}</div>
              </div>
            </div>
          `)
          .join("");
      }
      if (logCount) {
        logCount.textContent = `${logs.length} 条记录`;
      }
      const logViewport = logRoot.parentElement;
      if (logViewport) {
        logViewport.scrollTop = 0;
      }
    }

    const footerLoad = $all("footer p").find((node) => node.textContent.includes("System Load"));
    if (footerLoad) {
      footerLoad.textContent = `v2.4.0-pro | System Load: ${Math.min(99, 8 + bootstrap.stats.running * 20 + bootstrap.stats.waiting * 5)}%`;
    }
  }

  function mapModelLabelToValue(label) {
    const normalized = String(label || "").toLowerCase();
    if (normalized.includes("large")) return "large";
    if (normalized.includes("medium")) return "medium";
    if (normalized.includes("small")) return "small";
    if (normalized.includes("tiny")) return "tiny";
    return "base";
  }

  function renderSettings(bootstrap) {
    const textarea = $('textarea[placeholder*="Cookie"]');
    const modelSelect = $("select");
    const range = $('input[type="range"]');
    const outputDirLabel = $all(".bg-surface-container-low.rounded-xl.px-4.py-3.text-sm.text-zinc-600.truncate").find((node) => node.textContent.includes("/"));
    const folderButton = $all("button").find((btn) => btn.querySelector("span[data-icon='folder_open']"));
    const saveButton = $all("button").find((btn) => btn.textContent.includes("保存全部修改"));
    const cookieSaveButton = $all("button").find((btn) => btn.textContent.includes("验证并保存"));
    const cookieClearButton = $all("button").find((btn) => btn.textContent.trim() === "清空");

    const gpuButtons = $all("section").find((section) => section.querySelector("h3")?.textContent.includes("转录引擎配置"))?.querySelectorAll("button") || [];
    const formatChips = $all("section").find((section) => section.querySelector("h3")?.textContent.includes("转录引擎配置"))?.querySelectorAll("span.cursor-pointer") || [];
    const toggleRows = $all("section").find((section) => section.querySelector("h3")?.textContent.includes("常规偏好"))?.querySelectorAll("div.py-4.flex.items-center.justify-between") || [];

    if (textarea) {
      textarea.value = bootstrap.cookie.saved ? loadCookieTextFromStorage() : "";
      textarea.placeholder = bootstrap.cookie.saved ? textarea.placeholder : "请输入完整 Cookie 字符串或特定的 SESSDATA=...; bili_jct=...";
    }

    if (modelSelect) {
      const desired = bootstrap.settings.whisper_model || "base";
      const matchedOption = $all("option", modelSelect).find((option) => mapModelLabelToValue(option.textContent) === desired);
      if (matchedOption) modelSelect.value = matchedOption.value;
      state.selectedModel = desired;
    }

    if (range) {
      range.value = String(bootstrap.settings.download_concurrency || 3);
      state.selectedConcurrency = Number(range.value);
      const label = range.parentElement?.querySelector("span.px-3.py-1");
      if (label) label.textContent = `${range.value} 任务`;
    }

    state.selectedOutputDir = bootstrap.settings.output_dir || bootstrap.storage.output_dir;
    if (outputDirLabel) outputDirLabel.textContent = state.selectedOutputDir;

    state.selectedToggles.auto_open_dir = Boolean(bootstrap.settings.auto_open_dir);
    state.selectedToggles.delete_audio_after_transcribe = Boolean(bootstrap.settings.delete_audio_after_transcribe);
    state.selectedToggles.check_updates = Boolean(bootstrap.settings.check_updates);
    updateToggleRows(toggleRows);

    state.selectedDevice = bootstrap.settings.whisper_device || "auto";
    renderDeviceButtons(gpuButtons, state.selectedDevice);

    state.selectedOutputFormat = bootstrap.settings.output_format || "txt";
    renderFormatChips(formatChips, state.selectedOutputFormat);

    if (!state.settingsBound) {
      state.settingsBound = true;

      if (cookieClearButton) {
        cookieClearButton.addEventListener("click", () => {
          if (textarea) textarea.value = "";
          showToast("Cookie 输入已清空", "success");
        });
      }

      if (cookieSaveButton) {
        cookieSaveButton.addEventListener("click", () => saveCookieFromTextarea(textarea));
      }

      if (folderButton) {
        folderButton.addEventListener("click", async () => {
          const next = window.prompt("请输入输出目录路径", state.selectedOutputDir || bootstrap.settings.output_dir || "");
          if (!next) return;
          state.selectedOutputDir = next.trim();
          if (outputDirLabel) outputDirLabel.textContent = state.selectedOutputDir;
          showToast("输出目录已更新，记得点击保存全部修改", "success");
        });
      }

      if (saveButton) {
        saveButton.addEventListener("click", () => {
          const payload = collectSettingsFromPage();
          request("/api/settings/save", {
            method: "POST",
            body: JSON.stringify({ settings: payload }),
          })
            .then((result) => {
              showToast("设置已保存", "success");
              state.bootstrap.settings = result.settings;
              sync();
            })
            .catch((error) => showToast(error.message, "error"));
        });
      }

      if (modelSelect) {
        modelSelect.addEventListener("change", () => {
          state.selectedModel = mapModelLabelToValue(modelSelect.value);
        });
      }

      if (range) {
        range.addEventListener("input", () => {
          state.selectedConcurrency = Number(range.value);
          const label = range.parentElement?.querySelector("span.px-3.py-1");
          if (label) label.textContent = `${range.value} 任务`;
        });
      }

      gpuButtons.forEach((button) => {
        if (!button.textContent.includes("CUDA") && !button.textContent.includes("CPU")) return;
        button.addEventListener("click", () => {
          state.selectedDevice = button.textContent.includes("CUDA") ? "cuda" : "cpu";
          renderDeviceButtons(gpuButtons, state.selectedDevice);
        });
      });

      formatChips.forEach((chip) => {
        chip.addEventListener("click", () => {
          state.selectedOutputFormat = chip.textContent.replace(/\./g, "").trim().toLowerCase();
          renderFormatChips(formatChips, state.selectedOutputFormat);
        });
      });

      toggleRows.forEach((row, index) => {
        const toggle = row.querySelector(".w-12.h-6");
        if (!toggle) return;
        toggle.addEventListener("click", () => {
          if (index === 0) state.selectedToggles.auto_open_dir = !state.selectedToggles.auto_open_dir;
          if (index === 1) state.selectedToggles.delete_audio_after_transcribe = !state.selectedToggles.delete_audio_after_transcribe;
          if (index === 2) state.selectedToggles.check_updates = !state.selectedToggles.check_updates;
          updateToggleRows(toggleRows);
        });
      });
    }

    state.settings = {
      textarea,
      modelSelect,
      range,
      outputDirLabel,
      folderButton,
      saveButton,
      cookieSaveButton,
      cookieClearButton,
      gpuButtons,
      formatChips,
      toggleRows,
    };

    refreshCookieBadge(bootstrap.cookie);
  }

  function renderDeviceButtons(buttons, selected) {
    buttons.forEach((button) => {
      const isCuda = button.textContent.includes("CUDA");
      const active = (selected === "cuda" && isCuda) || (selected === "cpu" && !isCuda);
      button.className = active
        ? "flex items-center justify-center gap-2 py-3 rounded-xl bg-white border-2 border-[#fc739a]/20 text-[#fc739a] text-sm font-bold"
        : "flex items-center justify-center gap-2 py-3 rounded-xl bg-surface-container-low text-zinc-400 text-sm font-medium";
    });
  }

  function renderFormatChips(chips, selected) {
    chips.forEach((chip) => {
      const value = chip.textContent.replace(/\./g, "").trim().toLowerCase();
      const active = value === selected;
      chip.className = active
        ? "px-3 py-1.5 rounded-full bg-primary-container/20 text-[#fc739a] text-[11px] font-bold cursor-pointer"
        : "px-3 py-1.5 rounded-full bg-zinc-100 text-zinc-400 text-[11px] font-medium cursor-pointer";
    });
  }

  function updateToggleRows(rows) {
    rows.forEach((row, index) => {
      const toggle = row.querySelector(".w-12.h-6");
      const knob = row.querySelector(".w-4.h-4");
      const active = index === 0
        ? state.selectedToggles.auto_open_dir
        : index === 1
          ? state.selectedToggles.delete_audio_after_transcribe
          : state.selectedToggles.check_updates;

      if (!toggle || !knob) return;
      toggle.className = active
        ? "w-12 h-6 bg-[#fc739a] rounded-full relative flex items-center px-1 cursor-pointer"
        : "w-12 h-6 bg-zinc-200 rounded-full relative flex items-center px-1 cursor-pointer";
      knob.className = active ? "w-4 h-4 bg-white rounded-full ml-auto" : "w-4 h-4 bg-white rounded-full";
    });
  }

  function refreshCookieBadge(cookie) {
    const badge = $all("div.flex.items-center.gap-2.px-2 span").find((node) => node.textContent.includes("当前状态"));
    if (badge) {
      badge.textContent = cookie.saved ? `当前状态：${cookie.message}` : "当前状态：未配置 Cookie";
    }
  }

  function loadCookieTextFromStorage() {
    return window.localStorage.getItem("biliglass.cookie_text") || "";
  }

  function saveCookieTextToStorage(text) {
    window.localStorage.setItem("biliglass.cookie_text", text || "");
  }

  function saveCookieFromTextarea(textarea) {
    const value = textarea?.value?.trim();
    if (!value) {
      showToast("请输入 Cookie 字符串", "error");
      return;
    }
    saveCookieTextToStorage(value);
    request("/api/cookie/save", {
      method: "POST",
      body: JSON.stringify({ cookie_text: value }),
    })
      .then((result) => {
        showToast("Cookie 已验证并保存", "success");
        if (state.bootstrap) {
          state.bootstrap.cookie = result.cookie;
        }
        sync();
      })
      .catch((error) => showToast(error.message, "error"));
  }

  function collectSettingsFromPage() {
    const model = state.selectedModel || "base";
    const outputFormat = state.selectedOutputFormat || "txt";
    return {
      download_concurrency: Number(state.selectedConcurrency || (state.settings?.range?.value || 3)),
      whisper_model: model,
      whisper_device: state.selectedDevice || "auto",
      output_format: outputFormat,
      output_dir: state.selectedOutputDir || state.bootstrap?.settings?.output_dir,
      delete_audio_after_transcribe: Boolean(state.selectedToggles.delete_audio_after_transcribe),
      auto_open_dir: Boolean(state.selectedToggles.auto_open_dir),
      check_updates: Boolean(state.selectedToggles.check_updates),
      log_level: state.bootstrap?.settings?.log_level || "info",
    };
  }

  async function sync() {
    try {
      const bootstrap = await request("/api/bootstrap");
      state.bootstrap = bootstrap;
      state.backendErrorShown = false;

      if (PAGE === "console") {
        renderConsole(bootstrap);
      }

      if (PAGE === "library") {
        renderLibrary(bootstrap);
      }

      if (PAGE === "local-transcribe") {
        renderLocalPage(bootstrap);
      }

      if (PAGE === "settings") {
        renderSettings(bootstrap);
      }
    } catch (error) {
      if (!state.backendErrorShown) {
        showToast(`${error.message}。请先启动后端 server.py`, "error");
        state.backendErrorShown = true;
      }
      const title = $("h2");
      if (title) title.textContent = "后端未连接";
    }
  }

  function boot() {
    if (PAGE === "settings") {
      const cookieTextArea = $('textarea[placeholder*="Cookie"]');
      if (cookieTextArea) {
        cookieTextArea.value = loadCookieTextFromStorage();
      }
    }

    sync();
    state.pollTimer = setInterval(sync, 1800);
  }

  window.addEventListener("beforeunload", () => {
    if (state.pollTimer) clearInterval(state.pollTimer);
  });

  document.addEventListener("DOMContentLoaded", boot);
})();
