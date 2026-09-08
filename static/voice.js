/* FastLearn voice tutor — browser PCM16 audio over xAI Realtime WebSocket. */
(function () {
    "use strict";

    const rate = 24000;
    const form = document.getElementById("chat-form");
    const button = document.getElementById("voice-btn");
    const messages = document.getElementById("chat-messages");
    if (!form || !button || !messages) return;

    let socket = null;
    let active = false;
    let starting = false;
    let microphoneContext = null;
    let playbackContext = null;
    let microphoneStream = null;
    let processor = null;
    let sourceNode = null;
    let silentGain = null;
    let nextPlaybackTime = 0;
    let playing = [];
    let assistantBubble = null;
    let userBubble = null;
    let assistantTranscript = "";
    let lastUserTranscript = "";

    const label = (name, fallback) => form.dataset[name] || fallback;
    const waveMarkup = '<span class="voice-wave" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>';

    function setButtonState(isActive) {
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
        const text = isActive ? label("voiceStop", "End voice") : label("voiceStart", "Start voice tutor");
        button.setAttribute("aria-label", text);
        button.setAttribute("title", text);
    }

    function showPanel(state, text) {
        let panel = document.getElementById("voice-panel");
        if (!panel) {
            panel = document.createElement("div");
            panel.id = "voice-panel";
            panel.className = "voice-panel";
            panel.setAttribute("role", "status");
            panel.setAttribute("aria-live", "polite");
            panel.innerHTML = waveMarkup
                + '<span class="voice-status" id="voice-status"></span>'
                + '<button type="button" class="voice-stop" id="voice-stop"></button>';
            form.parentElement.insertBefore(panel, form);
            document.getElementById("voice-stop").addEventListener("click", stopVoice);
        }
        panel.dataset.state = state;
        document.getElementById("voice-status").textContent = text;
        document.getElementById("voice-stop").textContent = label("voiceStop", "End voice");
        return panel;
    }

    function hidePanel() {
        const panel = document.getElementById("voice-panel");
        if (panel) panel.remove();
    }

    function addBubble(role, text, pending) {
        const bubble = document.createElement("div");
        bubble.className = `msg msg-${role} voice-transcript${pending ? " voice-transcript-pending" : ""}`;
        if (role === "assistant") {
            const header = document.createElement("div");
            header.className = "msg-header";
            header.textContent = form.dataset.tutor || "FastLearn";
            const content = document.createElement("div");
            content.className = "msg-content";
            content.textContent = text || "";
            bubble.append(header, content);
        } else {
            bubble.textContent = text || "";
        }
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
        return role === "assistant" ? bubble.querySelector(".msg-content") : bubble;
    }

    function persistTranscript(role, content) {
        if (!content) return;
        fetch("/app/voice/transcript", {
            method: "POST",
            credentials: "same-origin",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({chat: form.dataset.chatId || "", role, content}),
        }).catch(function () { /* The live conversation remains usable if persistence fails. */ });
    }

    function updateUserTranscript(text, done) {
        const transcript = String(text || "").trim();
        if (!transcript) return;
        if (!userBubble) userBubble = addBubble("user", transcript, true);
        else userBubble.textContent = transcript;
        if (done && transcript !== lastUserTranscript) {
            userBubble.classList.remove("voice-transcript-pending");
            persistTranscript("user", transcript);
            lastUserTranscript = transcript;
            userBubble = null;
        }
    }

    function updateAssistantTranscript(text, done, cumulative) {
        const incoming = String(text || "");
        if (cumulative) assistantTranscript = incoming;
        else assistantTranscript += incoming;
        if (!assistantTranscript && !done) return;
        if (!assistantBubble) assistantBubble = addBubble("assistant", assistantTranscript, true);
        else assistantBubble.textContent = assistantTranscript;
        if (done && assistantTranscript.trim()) {
            assistantBubble.closest(".voice-transcript").classList.remove("voice-transcript-pending");
            persistTranscript("assistant", assistantTranscript.trim());
            assistantBubble = null;
            assistantTranscript = "";
        }
    }

    function floatToPCM16(samples) {
        const output = new Int16Array(samples.length);
        for (let index = 0; index < samples.length; index += 1) {
            const sample = Math.max(-1, Math.min(1, samples[index]));
            output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
        }
        return output;
    }

    function downsample(samples, inputRate) {
        if (inputRate === rate) return floatToPCM16(samples);
        const ratio = inputRate / rate;
        const output = new Int16Array(Math.floor(samples.length / ratio));
        for (let index = 0; index < output.length; index += 1) {
            const start = Math.floor(index * ratio);
            const end = Math.floor((index + 1) * ratio);
            let total = 0;
            let count = 0;
            for (let source = start; source < end && source < samples.length; source += 1) {
                total += samples[source];
                count += 1;
            }
            const sample = Math.max(-1, Math.min(1, count ? total / count : samples[start] || 0));
            output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
        }
        return output;
    }

    function encodePCM16(samples) {
        const bytes = new Uint8Array(samples.buffer);
        let binary = "";
        for (let index = 0; index < bytes.length; index += 0x8000) {
            binary += String.fromCharCode.apply(null, bytes.subarray(index, index + 0x8000));
        }
        return window.btoa(binary);
    }

    function playPCM16(encoded) {
        if (!playbackContext || !encoded) return;
        const binary = window.atob(encoded);
        const bytes = new Uint8Array(binary.length);
        for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
        const samples = new Int16Array(bytes.buffer);
        const floats = new Float32Array(samples.length);
        for (let index = 0; index < samples.length; index += 1) floats[index] = samples[index] / 0x8000;
        const buffer = playbackContext.createBuffer(1, floats.length, rate);
        buffer.getChannelData(0).set(floats);
        const source = playbackContext.createBufferSource();
        source.buffer = buffer;
        source.connect(playbackContext.destination);
        const now = playbackContext.currentTime;
        if (nextPlaybackTime < now) nextPlaybackTime = now;
        source.start(nextPlaybackTime);
        nextPlaybackTime += buffer.duration;
        source.onended = function () { playing = playing.filter((item) => item !== source); };
        playing.push(source);
    }

    function stopPlayback() {
        playing.forEach(function (source) { try { source.stop(); } catch (_error) { /* already stopped */ } });
        playing = [];
        nextPlaybackTime = 0;
    }

    function handleEvent(event) {
        const type = event.type || "";
        if (type === "session.updated") {
            showPanel("listening", label("voiceListening", "Listening…"));
        } else if (type === "input_audio_buffer.speech_started") {
            stopPlayback();
            showPanel("listening", label("voiceListening", "Listening…"));
        } else if (type === "input_audio_buffer.speech_stopped") {
            updateUserTranscript(event.transcript, Boolean(event.transcript));
            showPanel("thinking", label("voiceThinking", "Thinking…"));
        } else if (type === "conversation.item.input_audio_transcription.updated"
                || type === "input_audio_buffer.input_audio_transcription.updated") {
            updateUserTranscript(event.transcript, false);
        } else if (type === "conversation.item.input_audio_transcription.completed"
                || type === "input_audio_buffer.input_audio_transcription.completed") {
            updateUserTranscript(event.transcript, true);
        } else if (type === "response.output_audio.delta" || type === "response.audio.delta") {
            playPCM16(event.delta || event.audio || "");
            showPanel("speaking", label("voiceSpeaking", "Speaking…"));
        } else if (type === "response.output_audio_transcript.delta") {
            updateAssistantTranscript(event.delta, false, false);
        } else if (type === "response.output_audio_transcript.updated") {
            updateAssistantTranscript(event.transcript, false, true);
        } else if (type === "response.output_audio_transcript.done") {
            updateAssistantTranscript(event.transcript || "", true, Boolean(event.transcript));
        } else if (type === "response.done") {
            updateAssistantTranscript("", true, false);
            showPanel("listening", label("voiceListening", "Listening…"));
        } else if (type === "error") {
            showPanel("error", label("voiceUnavailable", "Voice is temporarily unavailable."));
        }
    }

    async function requestSession() {
        const response = await fetch("/app/voice/session", {
            method: "POST",
            credentials: "same-origin",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({chat: form.dataset.chatId || "", lang: form.dataset.lang || "en"}),
        });
        const payload = await response.json().catch(function () { return {}; });
        if (!response.ok || !payload.client_secret) throw new Error(payload.error || "Voice unavailable");
        return payload;
    }

    async function startVoice() {
        if (active || starting) return;
        starting = true;
        hidePanel();
        showPanel("connecting", label("voiceMicrophone", "Requesting microphone…"));
        try {
            microphoneStream = await navigator.mediaDevices.getUserMedia({
                audio: {channelCount: 1, echoCancellation: true, noiseSuppression: true},
            });
        } catch (_error) {
            starting = false;
            showPanel("error", label("voiceBlocked", "Microphone blocked — allow access and try again."));
            return;
        }

        try {
            const session = await requestSession();
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            microphoneContext = new AudioContext();
            playbackContext = new AudioContext({sampleRate: rate});
            await Promise.all([microphoneContext.resume(), playbackContext.resume()]);

            socket = new WebSocket(
                `wss://api.x.ai/v1/realtime?model=${encodeURIComponent(session.model)}`,
                [`xai-client-secret.${session.client_secret}`],
            );
            socket.addEventListener("open", function () {
                active = true;
                starting = false;
                setButtonState(true);
                socket.send(JSON.stringify({
                    type: "session.update",
                    session: {
                        voice: session.voice,
                        instructions: session.instructions,
                        turn_detection: {type: "server_vad"},
                        audio: {
                            input: {
                                format: {type: "audio/pcm", rate},
                                transcription: {model: "grok-transcribe"},
                            },
                            output: {format: {type: "audio/pcm", rate}},
                        },
                    },
                }));
                showPanel("listening", label("voiceListening", "Listening…"));
            });
            socket.addEventListener("message", function (message) {
                try { handleEvent(JSON.parse(message.data)); } catch (_error) { /* Ignore malformed events. */ }
            });
            socket.addEventListener("error", function () {
                showPanel("error", label("voiceUnavailable", "Voice is temporarily unavailable."));
            });
            socket.addEventListener("close", function () {
                if (active || starting) stopVoice();
            });

            sourceNode = microphoneContext.createMediaStreamSource(microphoneStream);
            processor = microphoneContext.createScriptProcessor(4096, 1, 1);
            silentGain = microphoneContext.createGain();
            silentGain.gain.value = 0;
            sourceNode.connect(processor);
            processor.connect(silentGain);
            silentGain.connect(microphoneContext.destination);
            processor.onaudioprocess = function (audioEvent) {
                if (!socket || socket.readyState !== WebSocket.OPEN) return;
                const pcm = downsample(audioEvent.inputBuffer.getChannelData(0), microphoneContext.sampleRate);
                socket.send(JSON.stringify({type: "input_audio_buffer.append", audio: encodePCM16(pcm)}));
            };
        } catch (_error) {
            stopVoice(false);
            showPanel("error", label("voiceUnavailable", "Voice is temporarily unavailable."));
        }
    }

    function stopVoice(hide) {
        active = false;
        starting = false;
        if (processor) processor.onaudioprocess = null;
        try { if (processor) processor.disconnect(); } catch (_error) { /* already disconnected */ }
        try { if (sourceNode) sourceNode.disconnect(); } catch (_error) { /* already disconnected */ }
        try { if (silentGain) silentGain.disconnect(); } catch (_error) { /* already disconnected */ }
        if (microphoneStream) microphoneStream.getTracks().forEach(function (track) { track.stop(); });
        stopPlayback();
        if (microphoneContext) microphoneContext.close().catch(function () {});
        if (playbackContext) playbackContext.close().catch(function () {});
        if (socket && socket.readyState < WebSocket.CLOSING) socket.close();
        socket = microphoneContext = playbackContext = microphoneStream = processor = sourceNode = silentGain = null;
        assistantBubble = userBubble = null;
        assistantTranscript = "";
        setButtonState(false);
        if (hide !== false) hidePanel();
    }

    function showMobileHandoff() {
        if (new URLSearchParams(window.location.search).get("voice") !== "1") return;
        const panel = showPanel("ready", label("voiceTap", "Tap the microphone to start talking with your tutor."));
        const stop = panel.querySelector(".voice-stop");
        const start = stop.cloneNode(true);
        stop.replaceWith(start);
        start.textContent = label("voiceStart", "Start voice tutor");
        start.addEventListener("click", startVoice, {once: true});
        button.classList.add("voice-invite");
    }

    window.toggleVoice = function () { if (active || starting) stopVoice(); else startVoice(); };
    window.addEventListener("pagehide", function () { if (active || starting) stopVoice(); });
    setButtonState(false);
    showMobileHandoff();
})();
