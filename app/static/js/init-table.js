var $table = $('#table'),
    $remove = $('#remove'),
    selections = [];

function getHeight() {
    return $(window).height() - $('#remove').outerHeight(true) - $('.nav').outerHeight(true);
}

function initTable() {
    console.log(getHeight());
    $table.bootstrapTable({
        height: getHeight(),
        columns: [
            {
                field: 'state',
                checkbox: true,
                align: 'center',
                valign: 'middle'
            }, {
                title: 'ID',
                field: 'id_registro',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Onda',
                field: 'id_onda',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Cliente',
                field: 'cliente',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Cod.',
                field: 'id_produto',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Descrição',
                field: 'descricao_produto',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Colaborador',
                field: 'colaborador',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Tarefa',
                field: 'tipo_tarefa',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Erro',
                field: 'erro',
                align: 'center',
                valign: 'middle',
                sortable: true
            }, {
                title: 'Data Cadastro',
                field: 'data_cadastro',
                align: 'center',
                valign: 'middle',
                sortable: true
            }
        ]
    });
};

$('#eventsTable').on('check.bs.table uncheck.bs.table check-all.bs.table uncheck-all.bs.table', function() {
    console.log('Funcionou');
    console.log(getIdSelections());
});

function getIdSelections() {
    return $.map($table.bootstrapTable('getSelections'), function(row) {
        return row.id
    });
}

setTimeout(function() {
    $table.bootstrapTable('resetView');
}, 200);

$(function(){
  initTable();
})
