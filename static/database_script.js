document.addEventListener('DOMContentLoaded', () => {
    const diagramContainer = document.getElementById('diagram-container');
    const addTableButton = document.getElementById('add-table-button');

    let tableIdCounter = 1;

    const addTable = (tableName = `Table ${tableIdCounter++}`, columns = ['Column 1', 'Column 2']) => {
        const tableBox = document.createElement('div');
        tableBox.className = 'table-box';
        tableBox.id = `table-${tableIdCounter}`;

        const tableHeader = document.createElement('div');
        tableHeader.className = 'table-header';
        tableHeader.contentEditable = true;
        tableHeader.textContent = tableName;
        tableBox.appendChild(tableHeader);

        const columnsDiv = document.createElement('div');
        columnsDiv.className = 'columns';

        columns.forEach(columnName => {
            const columnDiv = document.createElement('div');
            columnDiv.className = 'column';
            columnDiv.contentEditable = true;
            columnDiv.textContent = columnName;
            columnsDiv.appendChild(columnDiv);
        });

        tableBox.appendChild(columnsDiv);
        diagramContainer.appendChild(tableBox);

        jsPlumb.draggable(tableBox);
        jsPlumb.addEndpoint(tableBox, {
            anchors: ["TopCenter", "BottomCenter", "LeftMiddle", "RightMiddle"],
            endpoint: "Dot",
            paintStyle: { fill: "#3498db", radius: 5 },
            isSource: true,
            isTarget: true
        });

        return tableBox.id;
    };

    addTableButton.onclick = () => {
        addTable();
    };

    // Example initial tables
    const table1Id = addTable('Customers', ['Id', 'Name', 'Email']);
    const table2Id = addTable('Orders', ['OrderId', 'CustomerId', 'Total']);

    // Example join
    jsPlumb.ready(() => {
        jsPlumb.connect({
            source: table1Id,
            target: table2Id,
            anchors: ["RightMiddle", "LeftMiddle"],
            connector: ["Flowchart", { stub: 30 }],
            paintStyle: { stroke: "#456", strokeWidth: 2 },
            overlays: [
                ["Arrow", { width: 10, length: 10, location: 1 }],
                ["Label", { label: "One-to-many", location: 0.5 }]
            ]
        });
    });
});
