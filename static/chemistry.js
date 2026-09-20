/* Guided, answer-safe chemistry activities.  3Dmol.js is optional at runtime:
 * each activity retains a text and form-based fallback for unsupported WebGL. */
(() => {
    const molecules = {
        water: `3\nwater\nO 0.000 0.000 0.000\nH 0.958 0.000 0.000\nH -0.239 0.927 0.000`,
        methane: `5\nmethane\nC 0.000 0.000 0.000\nH 0.629 0.629 0.629\nH -0.629 -0.629 0.629\nH -0.629 0.629 -0.629\nH 0.629 -0.629 -0.629`,
    };

    const element = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    };

    function moleculeViewer(exercise) {
        const wrap = element('div', 'chemistry-viewer-wrap');
        const canvas = element('div', 'chemistry-viewer');
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', exercise.molecule === 'water' ? 'Three dimensional water molecule. Oxygen is red and hydrogen atoms are white.' : 'Three dimensional molecular model.');
        wrap.appendChild(canvas);
        const description = element('p', 'chemistry-viewer-description', exercise.molecule === 'water'
            ? '3D model: water has one oxygen atom and two hydrogen atoms.'
            : '3D molecular model. Drag to rotate, scroll or pinch to zoom.');
        wrap.appendChild(description);
        const controls = element('div', 'chemistry-viewer-controls');
        let viewer = null;
        if (window.$3Dmol && molecules[exercise.molecule]) {
            try {
                viewer = window.$3Dmol.createViewer(canvas, {backgroundColor: '#f7fbff'});
                viewer.addModel(molecules[exercise.molecule], 'xyz');
                viewer.setStyle({}, {stick: {radius: 0.16}, sphere: {scale: 0.34}});
                viewer.zoomTo();
                viewer.zoom(1.8);
                viewer.render();
            } catch (_error) { viewer = null; }
        }
        if (!viewer) {
            canvas.classList.add('chemistry-viewer-fallback');
            canvas.textContent = exercise.molecule === 'water'
                ? 'H — O — H\n3D model unavailable on this device'
                : '3D model unavailable on this device';
        }
        const reset = element('button', 'chemistry-mini-button', exercise.ui?.reset || 'Reset view');
        reset.type = 'button';
        reset.addEventListener('click', () => { if (viewer) { viewer.zoomTo(); viewer.zoom(1.8); viewer.render(); } });
        controls.appendChild(reset);
        if (exercise.scene === 'particle-state') {
            const state = element('span', 'chemistry-state-label', 'Solid: particles closest together');
            const heat = element('button', 'chemistry-mini-button', exercise.ui?.heat || 'Heat');
            const cool = element('button', 'chemistry-mini-button', exercise.ui?.cool || 'Cool');
            let warmth = 0;
            const update = () => {
                const names = ['Solid: particles closest together', 'Liquid: particles can move past each other', 'Gas: particles spread out'];
                state.textContent = names[warmth];
                if (viewer) {
                    viewer.setBackgroundColor(['#e8f4ff', '#fff8d7', '#ffe8de'][warmth]);
                    viewer.render();
                }
            };
            heat.type = cool.type = 'button';
            heat.addEventListener('click', () => { warmth = Math.min(2, warmth + 1); update(); });
            cool.addEventListener('click', () => { warmth = Math.max(0, warmth - 1); update(); });
            controls.append(cool, heat, state);
        }
        wrap.appendChild(controls);
        return wrap;
    }

    function choices(exercise, getAnswer) {
        const list = element('div', 'chemistry-options');
        let selected = null;
        (exercise.choices || []).forEach((label, index) => {
            const button = element('button', 'chemistry-option', `${String.fromCharCode(65 + index)}. ${label}`);
            button.type = 'button';
            button.addEventListener('click', () => {
                selected = index;
                list.querySelectorAll('button').forEach((item) => item.classList.toggle('selected', item === button));
            });
            list.appendChild(button);
        });
        getAnswer.current = () => selected === null ? null : {choice: selected};
        return list;
    }

    function equationInputs(exercise, getAnswer) {
        const row = element('div', 'chemistry-equation');
        const fields = [];
        (exercise.equation || []).forEach((term, index) => {
            const input = element('input', 'chemistry-coefficient');
            input.type = 'number'; input.min = '0'; input.max = '99'; input.inputMode = 'numeric';
            input.value = '1'; input.setAttribute('aria-label', `${exercise.ui?.coefficient || 'Coefficient'} for ${term}`);
            row.appendChild(input); row.appendChild(element('span', 'chemistry-formula', term));
            fields.push(input);
            const operator = (exercise.operators || ["+", "→"])[index];
            if (operator) row.appendChild(element('span', 'chemistry-operator', operator));
        });
        getAnswer.current = () => ({coefficients: fields.map((input) => Number(input.value))});
        return row;
    }

    function atomInputs(exercise, getAnswer) {
        const grid = element('div', 'chemistry-number-grid');
        const values = {};
        [['protons', exercise.ui?.protons || 'Protons'], ['neutrons', exercise.ui?.neutrons || 'Neutrons'], ['electrons', exercise.ui?.electrons || 'Electrons']].forEach(([key, label]) => {
            const field = element('label', 'chemistry-number-field');
            field.appendChild(element('span', '', label));
            const input = element('input'); input.type = 'number'; input.min = '0'; input.max = '118'; input.inputMode = 'numeric'; input.value = '0';
            input.addEventListener('input', () => { values[key] = Number(input.value); });
            values[key] = 0; field.appendChild(input); grid.appendChild(field);
        });
        const hint = element('p', 'chemistry-hint', `${exercise.atom || 'Atom'}: atomic number ${exercise.atomic_number}, mass number ${exercise.mass_number}`);
        grid.appendChild(hint);
        getAnswer.current = () => ({protons: values.protons, neutrons: values.neutrons, electrons: values.electrons});
        return grid;
    }

    function numberInput(exercise, getAnswer) {
        const field = element('label', 'chemistry-number-field');
        field.appendChild(element('span', '', `${exercise.ui?.answer || 'Answer'} (${exercise.unit || ''})`));
        const input = element('input'); input.type = 'number'; input.step = 'any'; input.inputMode = 'decimal';
        field.appendChild(input);
        getAnswer.current = () => input.value.trim() ? {value: Number(input.value)} : null;
        return field;
    }

    function textInput(exercise, getAnswer) {
        const field = element('label', 'chemistry-number-field');
        field.appendChild(element('span', '', exercise.ui?.text_answer || 'Type your answer'));
        const input = element('input'); input.type = 'text'; input.autocomplete = 'off';
        input.placeholder = exercise.placeholder || '';
        field.appendChild(input);
        getAnswer.current = () => input.value.trim() ? {text: input.value.trim()} : null;
        return field;
    }

    function labelFor(exercise, answer) {
        if (answer?.choice !== undefined) return `${String.fromCharCode(65 + answer.choice)}. ${(exercise.choices || [])[answer.choice] || ''}`;
        if (answer?.coefficients) return answer.coefficients.join(', ');
        if (answer?.value !== undefined) return `${answer.value} ${exercise.unit || ''}`.trim();
        if (answer?.text !== undefined) return answer.text;
        if (answer?.protons !== undefined) return `p ${answer.protons}, n ${answer.neutrons}, e ${answer.electrons}`;
        return 'Chemistry answer';
    }

    function mount(container, exercise, submitAnswer) {
        if (!container || container.dataset.mounted === '1') return;
        container.dataset.mounted = '1';
        const startedAt = Date.now();
        const card = element('section', 'chemistry-card');
        card.appendChild(element('div', 'chemistry-meta', `${exercise.ui?.level || 'Guided chemistry'} · level ${exercise.difficulty_band || 1}`));
        if (exercise.molecule) card.appendChild(moleculeViewer(exercise));
        const answer = {current: () => null};
        if (['multiple_choice', 'material_sort', 'molecule_geometry', 'spectra_choice', 'mechanism_choice'].includes(exercise.exercise_type)) card.appendChild(choices(exercise, answer));
        else if (exercise.exercise_type === 'equation_balance') card.appendChild(equationInputs(exercise, answer));
        else if (exercise.exercise_type === 'atom_builder') card.appendChild(atomInputs(exercise, answer));
        else if (['mole_calculation', 'numeric_calculation'].includes(exercise.exercise_type)) card.appendChild(numberInput(exercise, answer));
        else if (['formula_builder', 'short_answer'].includes(exercise.exercise_type)) card.appendChild(textInput(exercise, answer));
        const status = element('div', 'chemistry-answer-status');
        status.setAttribute('aria-live', 'polite'); card.appendChild(status);
        const check = element('button', 'chemistry-submit', exercise.ui?.check || 'Check answer');
        check.type = 'button';
        check.addEventListener('click', () => {
            const value = answer.current();
            if (!value || check.disabled) { status.textContent = 'Choose or enter an answer first.'; return; }
            check.disabled = true;
            submitAnswer(value, labelFor(exercise, value), startedAt, check);
        });
        card.appendChild(check); container.appendChild(card);
    }

    window.FastLearnChemistry = {mount};
})();
