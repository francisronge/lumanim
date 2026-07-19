(() => {
  const stages = [...document.querySelectorAll('[data-lumanim-stage][data-live="true"]')];
  if (!stages.length) return;

  const makeController = (stage) => {
    const declaredRoot = stage.closest("[data-lumanim-experience]");
    if (stages.length > 1 && !declaredRoot) return;
    const root = declaredRoot || document;
    const visualId = declaredRoot?.dataset.lumanimExperience || null;
    const video = stage.querySelector("[data-lumanim-fallback]");
    const canvas = stage.querySelector("[data-lumanim-live-frame]");
    if (!video || !canvas) return;

    const explore = root.querySelector("[data-lumanim-explore]");
    const replay = root.querySelector("[data-lumanim-replay]");
    const reconnect = root.querySelector("[data-lumanim-reconnect]");
    const controlsPanel = root.querySelector("[data-lumanim-controls]");
    const controls = [...root.querySelectorAll("[data-lumanim-control]")];
    const outputs = [...root.querySelectorAll("[data-lumanim-output]")];
    const context = canvas.getContext("2d", { alpha: false });
    let runtimeAvailable = false;
    let busy = false;
    let pending = null;
    let scheduled = false;

    const setMode = (mode) => {
      stage.dataset.mode = mode;
    };

    const setControlsEnabled = (enabled) => {
      controls.forEach((control) => { control.disabled = !enabled; });
    };

    const stateFromControls = () => Object.fromEntries(
      controls.map((control) => [control.dataset.lumanimControl, Number(control.value)])
    );

    const updateReadout = (control) => {
      const output = outputs.find(
        (candidate) => candidate.dataset.lumanimOutput === control.dataset.lumanimControl
      );
      if (output) output.textContent = `${Math.round(Number(control.value) * 100)}%`;
    };

    const showVideo = () => {
      stage.dataset.view = "video";
      video.hidden = false;
      canvas.hidden = true;
      if (controlsPanel) controlsPanel.hidden = true;
      if (explore) explore.hidden = !runtimeAvailable;
      if (replay) replay.hidden = true;
      setMode(runtimeAvailable ? "ready" : "rendered");
    };

    const showRecovery = () => {
      runtimeAvailable = false;
      setControlsEnabled(false);
      showVideo();
      if (controlsPanel) controlsPanel.hidden = false;
      if (explore) explore.hidden = true;
      if (replay) replay.hidden = true;
      if (reconnect) reconnect.hidden = false;
    };

    const drawFrame = async (blob) => {
      const bitmap = await createImageBitmap(blob);
      if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
      }
      context.drawImage(bitmap, 0, 0);
      bitmap.close();
    };

    const render = async (state) => {
      if (busy) {
        pending = state;
        return;
      }
      busy = true;
      try {
        const response = await fetch("/api/frame", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(state),
          cache: "no-store",
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        await drawFrame(await response.blob());
        video.hidden = true;
        canvas.hidden = false;
        stage.dataset.view = "live";
        setMode("live");
      } catch (error) {
        showRecovery();
      } finally {
        busy = false;
        if (pending) {
          const next = pending;
          pending = null;
          render(next);
        }
      }
    };

    const scheduleRender = () => {
      pending = stateFromControls();
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        const next = pending;
        pending = null;
        render(next);
      });
    };

    const checkRuntime = async () => {
      const local = location.protocol === "http:" && ["127.0.0.1", "localhost"].includes(location.hostname);
      if (!local) {
        runtimeAvailable = false;
        setControlsEnabled(false);
        if (explore) explore.hidden = true;
        setMode("rendered");
        return false;
      }
      try {
        const response = await fetch("/api/status", { cache: "no-store" });
        if (!response.ok) throw new Error("runtime unavailable");
        const status = await response.json();
        if (visualId && status.visual_id !== visualId) {
          runtimeAvailable = false;
          setControlsEnabled(false);
          if (explore) explore.hidden = true;
          setMode("rendered");
          return false;
        }
        runtimeAvailable = true;
        setControlsEnabled(true);
        if (explore) {
          explore.disabled = false;
          explore.hidden = false;
        }
        if (reconnect) reconnect.hidden = true;
        setMode("ready");
        return true;
      } catch (error) {
        runtimeAvailable = false;
        setControlsEnabled(false);
        if (explore) {
          explore.disabled = false;
          explore.hidden = true;
        }
        setMode("rendered");
        return false;
      }
    };

    const enterLive = async () => {
      if (!runtimeAvailable && !(await checkRuntime())) {
        showRecovery();
        return;
      }
      video.pause();
      if (controlsPanel) controlsPanel.hidden = false;
      if (explore) explore.hidden = true;
      if (replay) replay.hidden = false;
      await render(stateFromControls());
    };

    controls.forEach((control) => {
      updateReadout(control);
      control.addEventListener("input", () => {
        updateReadout(control);
        if (stage.dataset.view === "live") scheduleRender();
      });
    });
    explore?.addEventListener("click", enterLive);
    reconnect?.addEventListener("click", enterLive);
    replay?.addEventListener("click", () => {
      showVideo();
      video.currentTime = 0;
      video.play().catch(() => {});
    });
    video.addEventListener("ended", () => explore?.classList.add("is-invited"));

    setControlsEnabled(false);
    showVideo();
    checkRuntime();
  };

  stages.forEach(makeController);
})();
