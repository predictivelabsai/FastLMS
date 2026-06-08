/* FastLMS — client-side chat handler (SSE streaming) */

function toggleCanvas(open) {
    const pane = document.getElementById('right-pane');
    if (pane) pane.classList.toggle('open', open);
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    if (!form || !input || !messages) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

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
        thinking.textContent = 'Thinking...';
        messages.appendChild(thinking);

        // Start SSE
        const lessonId = form.dataset.lessonId || '';
        const params = new URLSearchParams({ message: text, lesson_id: lessonId });

        try {
            const response = await fetch('/app/chat/stream?' + params.toString());
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            // Remove thinking indicator and create assistant bubble
            thinking.remove();
            const assistantDiv = document.createElement('div');
            assistantDiv.className = 'msg msg-assistant';

            const header = document.createElement('div');
            header.className = 'msg-header';
            header.textContent = 'AI Tutor';
            assistantDiv.appendChild(header);

            const content = document.createElement('div');
            content.className = 'msg-content';
            assistantDiv.appendChild(content);
            messages.appendChild(assistantDiv);

            let buffer = '';
            let fullText = '';

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
                            if (data.token) {
                                fullText += data.token;
                                if (typeof marked !== 'undefined') {
                                    content.innerHTML = marked.parse(fullText);
                                } else {
                                    content.textContent = fullText;
                                }
                                messages.scrollTop = messages.scrollHeight;
                            } else if (data.done) {
                                // Stream complete
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
            errDiv.textContent = 'Connection error. Please try again.';
            messages.appendChild(errDiv);
        }

        messages.scrollTop = messages.scrollHeight;
    });

    // Allow Enter to send, Shift+Enter for newline
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });
});
