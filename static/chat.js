/* FastLearn — SSE chat and rich guided-exercise interactions */

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

    const pieceGlyph = {
        K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
        k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
    };

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

    function piecesFromFen(fen) {
        const pieces = {};
        const rows = String(fen || '8/8/8/8/8/8/8/8').split(' ')[0].split('/');
        rows.forEach((row, rowIndex) => {
            let file = 0;
            for (const token of row) {
                if (/\d/.test(token)) file += Number(token);
                else {
                    pieces[String.fromCharCode(97 + file) + String(8 - rowIndex)] = token;
                    file += 1;
                }
            }
        });
        return pieces;
    }

    function answerLabel(exercise, answer) {
        if (exercise.exercise_type === 'multiple_choice') return `${String.fromCharCode(65 + answer.answer)}. ${exercise.choices[answer.answer]}`;
        if (answer.squares) return answer.squares.join(', ');
        if (answer.moves) return answer.moves.join(' → ');
        if (answer.placements) return answer.placements.map((item) => `${item.piece}@${item.square}`).join(', ');
        return 'Board answer';
    }

    function addUserMessage(text) {
        const bubble = document.createElement('div');
        bubble.className = 'msg msg-user';
        bubble.textContent = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
    }

    function addThinking() {
        const thinking = document.createElement('div');
        thinking.className = 'thinking-indicator';
        thinking.textContent = form.dataset.thinking || 'Thinking…';
        messages.appendChild(thinking);
        return thinking;
    }

    async function streamAssistant(response, thinking) {
        if (!response.ok || !response.body) throw new Error(`Chat request failed (${response.status})`);
        thinking.remove();
        const assistant = document.createElement('div');
        assistant.className = 'msg msg-assistant';
        const header = document.createElement('div');
        header.className = 'msg-header';
        header.textContent = form.dataset.tutor || 'FastLearn';
        const content = document.createElement('div');
        content.className = 'msg-content';
        assistant.append(header, content);
        messages.appendChild(assistant);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const data = JSON.parse(line.slice(6));
                    if (typeof data.html === 'string') content.innerHTML = data.html;
                    if (data.done) {
                        if (data.lesson_id !== undefined && data.lesson_id !== null) form.dataset.lessonId = String(data.lesson_id);
                        if (data.interactive) {
                            const holder = document.createElement('div');
                            holder.className = 'chat-interactive';
                            assistant.appendChild(holder);
                            mountInteractive(holder, data.interactive);
                        }
                        addChoices(assistant, data.choices || []);
                        if (data.redirect_url) window.setTimeout(() => window.location.assign(data.redirect_url), 450);
                    } else if (data.error) content.textContent = `Error: ${data.error}`;
                } catch (_error) {
                    // Ignore malformed partial events and continue streaming.
                }
            }
            messages.scrollTop = messages.scrollHeight;
        }
        return assistant;
    }

    function mountInteractive(container, exercise) {
        if (!container || container.dataset.mounted === '1') return;
        container.dataset.mounted = '1';
        const startedAt = Date.now();
        const pieces = piecesFromFen(exercise.fen);
        const selectedSquares = new Set();
        const placements = {};
        const moves = [];
        let selectedPiece = null;
        let moveFrom = Object.keys(pieces).find((square) => /[A-Z]/.test(pieces[square])) || null;
        let multipleChoice = null;

        const card = document.createElement('section');
        card.className = 'chess-card';
        const meta = document.createElement('div');
        meta.className = 'chess-meta';
        meta.textContent = `${exercise.ui?.level || 'Level'} ${exercise.difficulty_band} · ${exercise.cognitive_layer}`;
        card.appendChild(meta);
        const board = document.createElement('div');
        board.className = 'chess-board';
        board.setAttribute('role', 'grid');
        board.setAttribute('aria-label', exercise.prompt || 'Chessboard');

        function updateStatus() {
            if (exercise.exercise_type === 'select_squares') status.textContent = [...selectedSquares].join(', ');
            else if (['path', 'move_sequence'].includes(exercise.exercise_type)) status.textContent = moves.join(' → ');
            else if (exercise.exercise_type === 'place_pieces') status.textContent = Object.entries(placements).map(([square, piece]) => `${piece}@${square}`).join(', ');
            else status.textContent = multipleChoice === null ? '' : String.fromCharCode(65 + multipleChoice);
        }

        function renderBoard() {
            board.replaceChildren();
            for (let rank = 8; rank >= 1; rank -= 1) {
                for (let file = 0; file < 8; file += 1) {
                    const square = String.fromCharCode(97 + file) + String(rank);
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = `chess-square ${(rank + file) % 2 ? 'light' : 'dark'}`;
                    if (selectedSquares.has(square)) button.classList.add('selected');
                    if (moveFrom === square && ['path', 'move_sequence'].includes(exercise.exercise_type)) button.classList.add('from');
                    button.dataset.square = square;
                    button.setAttribute('role', 'gridcell');
                    button.setAttribute('aria-label', `${square}${pieces[square] ? ` ${pieces[square]}` : ''}`);
                    button.textContent = pieceGlyph[pieces[square]] || '';
                    const coordinate = document.createElement('span');
                    coordinate.className = 'square-coordinate';
                    coordinate.textContent = square;
                    button.appendChild(coordinate);
                    board.appendChild(button);
                }
            }
        }

        board.addEventListener('click', (event) => {
            const squareButton = event.target.closest('.chess-square');
            if (!squareButton) return;
            const square = squareButton.dataset.square;
            if (exercise.exercise_type === 'select_squares') {
                if (selectedSquares.has(square)) selectedSquares.delete(square);
                else selectedSquares.add(square);
            } else if (exercise.exercise_type === 'place_pieces' && selectedPiece) {
                pieces[square] = selectedPiece;
                placements[square] = selectedPiece;
            } else if (['path', 'move_sequence'].includes(exercise.exercise_type)) {
                if (!moveFrom && pieces[square]) moveFrom = square;
                else if (moveFrom && square !== moveFrom) {
                    moves.push(moveFrom + square);
                    pieces[square] = pieces[moveFrom];
                    delete pieces[moveFrom];
                    moveFrom = square;
                }
            }
            renderBoard();
            updateStatus();
        });
        renderBoard();
        card.appendChild(board);

        if (exercise.exercise_type === 'multiple_choice') {
            const options = document.createElement('div');
            options.className = 'chess-options';
            (exercise.choices || []).forEach((label, index) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'chess-option';
                button.textContent = `${String.fromCharCode(65 + index)}. ${label}`;
                button.addEventListener('click', () => {
                    multipleChoice = index;
                    options.querySelectorAll('button').forEach((item) => item.classList.toggle('selected', item === button));
                    updateStatus();
                });
                options.appendChild(button);
            });
            card.appendChild(options);
        }

        if (exercise.exercise_type === 'place_pieces') {
            const palette = document.createElement('div');
            palette.className = 'chess-palette';
            [...new Set(exercise.pieces || [])].forEach((piece) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'chess-piece-choice';
                button.textContent = pieceGlyph[piece] || piece;
                button.setAttribute('aria-label', `Place ${piece}`);
                button.addEventListener('click', () => {
                    selectedPiece = piece;
                    palette.querySelectorAll('button').forEach((item) => item.classList.toggle('selected', item === button));
                });
                palette.appendChild(button);
            });
            card.appendChild(palette);
            const help = document.createElement('div');
            help.className = 'chess-place-help';
            help.textContent = exercise.ui?.place || 'Choose a piece, then choose its square';
            card.appendChild(help);
        }

        const status = document.createElement('div');
        status.className = 'chess-answer-status';
        card.appendChild(status);
        const submit = document.createElement('button');
        submit.type = 'button';
        submit.className = 'chess-submit';
        submit.textContent = exercise.ui?.check || 'Check answer';
        submit.addEventListener('click', async () => {
            let answer = null;
            if (exercise.exercise_type === 'multiple_choice' && multipleChoice !== null) answer = { answer: multipleChoice };
            if (exercise.exercise_type === 'select_squares' && selectedSquares.size) answer = { squares: [...selectedSquares] };
            if (exercise.exercise_type === 'place_pieces' && Object.keys(placements).length) answer = { placements: Object.entries(placements).map(([square, piece]) => ({ square, piece })) };
            if (['path', 'move_sequence'].includes(exercise.exercise_type) && moves.length) answer = { moves };
            if (!answer || submit.disabled) return;
            submit.disabled = true;
            addUserMessage(answerLabel(exercise, answer));
            const thinking = addThinking();
            try {
                const response = await fetch('/app/chat/exercise/stream', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chat: form.dataset.chatId || '', exercise_id: exercise.id, answer,
                        duration_seconds: Math.max(0, Math.round((Date.now() - startedAt) / 1000)),
                    }),
                });
                container.closest('.msg-assistant')?.querySelectorAll('button').forEach((button) => { button.disabled = true; });
                await streamAssistant(response, thinking);
            } catch (_error) {
                thinking.remove();
                const error = document.createElement('div');
                error.className = 'msg msg-assistant';
                error.textContent = form.dataset.connectionError || 'Connection error. Please try again.';
                messages.appendChild(error);
                submit.disabled = false;
            }
            messages.scrollTop = messages.scrollHeight;
        });
        card.appendChild(submit);
        container.appendChild(card);
    }

    messages.addEventListener('click', (event) => {
        const choice = event.target.closest('.chat-choice');
        if (!choice) return;
        input.value = choice.dataset.choice || '';
        form.requestSubmit();
    });

    document.querySelectorAll('.chat-interactive[data-exercise]').forEach((container) => {
        try { mountInteractive(container, JSON.parse(container.dataset.exercise)); } catch (_error) { /* invalid card */ }
    });

    document.querySelectorAll('.prompt-chip').forEach((button) => {
        button.addEventListener('click', () => {
            input.value = button.dataset.prompt || button.textContent;
            input.focus();
        });
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (form.dataset.busy === '1') return;
        const text = input.value.trim();
        if (!text) return;
        form.dataset.busy = '1';
        if (sendButton) sendButton.disabled = true;
        messages.querySelectorAll('.chat-choices').forEach((choices) => choices.remove());
        addUserMessage(text);
        input.value = '';
        const thinking = addThinking();
        try {
            const params = new URLSearchParams({ message: text, chat: form.dataset.chatId || '' });
            await streamAssistant(await fetch('/app/chat/stream?' + params.toString()), thinking);
        } catch (_error) {
            thinking.remove();
            const error = document.createElement('div');
            error.className = 'msg msg-assistant';
            error.textContent = form.dataset.connectionError || 'Connection error. Please try again.';
            messages.appendChild(error);
        }
        form.dataset.busy = '0';
        if (sendButton) sendButton.disabled = false;
        messages.scrollTop = messages.scrollHeight;
    });

    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });
});
