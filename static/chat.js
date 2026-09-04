/* FastLMS — client-side chat handler (SSE streaming) */

function toggleCanvas(open) {
    const pane = document.getElementById('right-pane');
    if (pane) pane.classList.toggle('open', open);
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    const sendButton = form && form.querySelector('.chat-send');
    if (!form || !input || !messages) return;

    function addChoices(container, choices) {
        const previous = container.querySelector('.chat-choices');
        if (previous) previous.remove();
        if (!Array.isArray(choices) || !choices.length) return;
        const choicesDiv = document.createElement('div');
        choicesDiv.className = 'chat-choices';
        choices.forEach((choice) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'chat-choice';
            button.dataset.choice = choice.key;
            const key = document.createElement('span');
            key.className = 'chat-choice-key';
            key.textContent = choice.key;
            const label = document.createElement('span');
            label.textContent = choice.label;
            button.append(key, label);
            choicesDiv.appendChild(button);
        });
        container.appendChild(choicesDiv);
    }

    messages.addEventListener('click', (event) => {
        const choice = event.target.closest('.chat-choice');
        if (!choice) return;
        input.value = choice.dataset.choice || '';
        form.requestSubmit();
    });

    document.querySelectorAll('.prompt-chip').forEach((button) => {
        button.addEventListener('click', () => {
            input.value = button.dataset.prompt || button.textContent;
            input.focus();
        });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (form.dataset.busy === '1') return;
        const text = input.value.trim();
        if (!text) return;
        form.dataset.busy = '1';
        if (sendButton) sendButton.disabled = true;

        messages.querySelectorAll('.chat-choices').forEach((choices) => choices.remove());

        // Add user message
        const userDiv = document.createElement('div');
        userDiv.className = 'msg msg-user';
        userDiv.textContent = text;
        messages.appendChild(userDiv);
        input.value = '';
        messages.scrollTop = messages.scrollHeight;

        // Add thinking indicator
        const thinking = document.createElement('div');
        thinking.className = 'thinking-indicator';
        thinking.textContent = form.dataset.thinking || 'Thinking…';
        messages.appendChild(thinking);

        // Start SSE
        const chatId = form.dataset.chatId || '';
        const params = new URLSearchParams({ message: text, chat: chatId });

        try {
            const response = await fetch('/app/chat/stream?' + params.toString());
            if (!response.ok || !response.body) throw new Error(`Chat request failed (${response.status})`);
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            // Remove thinking indicator and create assistant bubble
            thinking.remove();
            const assistantDiv = document.createElement('div');
            assistantDiv.className = 'msg msg-assistant';

            const header = document.createElement('div');
            header.className = 'msg-header';
            header.textContent = form.dataset.tutor || 'FastLearn';
            assistantDiv.appendChild(header);

            const content = document.createElement('div');
            content.className = 'msg-content';
            assistantDiv.appendChild(content);
            messages.appendChild(assistantDiv);

            let buffer = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (typeof data.html === 'string') {
                                // HTML is rendered and sanitised by the server from
                                // the complete Markdown response accumulated so far.
                                content.innerHTML = data.html;
                                messages.scrollTop = messages.scrollHeight;
                            }
                            if (data.done) {
                                if (data.lesson_id !== undefined && data.lesson_id !== null) {
                                    form.dataset.lessonId = String(data.lesson_id);
                                }
                                addChoices(assistantDiv, data.choices || []);
                            } else if (data.error) {
                                content.textContent = 'Error: ' + data.error;
                            }
                        } catch (err) {
                            // Skip malformed SSE lines
                        }
                    }
                }
            }
        } catch (err) {
            thinking.remove();
            const errDiv = document.createElement('div');
            errDiv.className = 'msg msg-assistant';
            errDiv.textContent = form.dataset.connectionError || 'Connection error. Please try again.';
            messages.appendChild(errDiv);
        }

        form.dataset.busy = '0';
        if (sendButton) sendButton.disabled = false;
        messages.scrollTop = messages.scrollHeight;
    });

    // Allow Enter to send, Shift+Enter for newline
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.requestSubmit();
        }
    });
});
