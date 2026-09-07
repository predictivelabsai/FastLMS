/* Safe Plotly renderer for streamed and persisted FastLearn visual explanations. */

(() => {
    function textElement(tag, className, text) {
        const element = document.createElement(tag);
        element.className = className;
        element.textContent = text || '';
        return element;
    }

    function dataTable(spec) {
        const table = spec.table || {};
        const ui = spec.ui || {};
        if (!Array.isArray(table.columns) || !Array.isArray(table.rows)) return null;
        const details = document.createElement('details');
        details.className = 'visual-data';
        details.appendChild(textElement('summary', '', ui.accessible_data || 'View accessible data'));
        const scroll = document.createElement('div');
        scroll.className = 'visual-data-scroll';
        const element = document.createElement('table');
        const head = document.createElement('thead');
        const heading = document.createElement('tr');
        table.columns.forEach((column) => {
            const cell = document.createElement('th');
            cell.scope = 'col';
            cell.textContent = String(column);
            heading.appendChild(cell);
        });
        head.appendChild(heading);
        element.appendChild(head);
        const body = document.createElement('tbody');
        table.rows.forEach((row) => {
            const record = document.createElement('tr');
            row.forEach((value) => {
                const cell = document.createElement('td');
                cell.textContent = String(value);
                record.appendChild(cell);
            });
            body.appendChild(record);
        });
        element.appendChild(body);
        scroll.appendChild(element);
        details.appendChild(scroll);
        return details;
    }

    function mount(container, spec) {
        if (!container || container.dataset.mounted === '1') return;
        if (!spec || spec.version !== 1 || spec.renderer !== 'plotly' || !Array.isArray(spec.data)) return;
        container.dataset.mounted = '1';
        container.dataset.sourceKey = spec.source_key || '';

        const card = document.createElement('section');
        card.className = 'visual-card';
        card.appendChild(textElement('h3', 'visual-title', spec.title));
        card.appendChild(textElement('p', 'visual-description', spec.description));
        const plot = document.createElement('div');
        plot.className = 'visual-plot';
        plot.setAttribute('role', 'img');
        const ui = spec.ui || {};
        plot.setAttribute('aria-label', spec.alt_text || spec.title || ui.interactive_visualization || 'Interactive visualization');
        card.appendChild(plot);
        card.appendChild(textElement('p', 'visual-alt', spec.alt_text));
        const table = dataTable(spec);
        if (table) card.appendChild(table);
        card.appendChild(textElement('p', 'visual-source', spec.source_note));
        container.appendChild(card);

        if (!window.Plotly) {
            plot.appendChild(textElement('p', 'visual-error', ui.load_error || 'The interactive chart could not load. Use the accessible data below.'));
            return;
        }
        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            scrollZoom: false,
            ...(spec.config || {}),
        };
        window.Plotly.react(plot, spec.data, spec.layout || {}, config).catch(() => {
            plot.replaceChildren(textElement('p', 'visual-error', ui.load_error || 'The interactive chart could not load. Use the accessible data below.'));
        });
    }

    window.FastLearnVisualizations = { mount };
})();
