/* Active learning-time heartbeat: visible, recent interaction, 30-second cap. */
(function () {
    const match = location.pathname.match(/^\/app\/(lesson|quiz)\/(\d+)/);
    let resourceType = match ? match[1] : null;
    let resourceId = match ? Number(match[2]) : null;
    if (location.pathname === '/app/chat') {
        resourceType = 'tutor';
        resourceId = Number(new URLSearchParams(location.search).get('lesson_id')) || null;
    }
    if (!resourceType) return;

    let lastInteraction = Date.now();
    let lastSent = Date.now();
    let sending = false;
    const active = () => !document.hidden && Date.now() - lastInteraction <= 90000;
    const touch = () => { lastInteraction = Date.now(); };
    ['pointerdown', 'keydown', 'scroll', 'touchstart'].forEach((event) =>
        addEventListener(event, touch, { passive: true })
    );

    async function heartbeat() {
        const now = Date.now();
        if (!active() || sending) {
            lastSent = now;
            return;
        }
        const seconds = Math.max(1, Math.min(30, Math.round((now - lastSent) / 1000)));
        lastSent = now;
        sending = true;
        try {
            await fetch('/app/activity/heartbeat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ resource_type: resourceType, resource_id: resourceId, seconds }),
                credentials: 'same-origin',
                keepalive: true,
            });
        } finally {
            sending = false;
        }
    }
    setInterval(heartbeat, 30000);
    document.addEventListener('visibilitychange', () => {
        lastSent = Date.now();
        if (!document.hidden) touch();
    });
})();
