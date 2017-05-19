/* ########################################################################
  FUNCOES GERAIS
######################################################################## */

// Evento para buscar os colaboradores na tela de Cadastro de erros
function getColaborador(){
  if(($('#id_produto').val() != '') && ($('#tipo_tarefa').val() != '' && ($('#id_onda').val() != ''))){
    var val01 = $('#id_onda').serialize();
    var val02 = $('#id_produto').serialize();
    var option = $('#tipo_tarefa').serialize();
    var data = val01+'&'+val02+'&'+option;

    $.ajax({
        type: "GET",
        url: "/wmserros/informar_erros/colaborador",
        dataType: "json",
        data: data,
        success: function(data) {
          $(data).each(function(key, value){
            $('#colaborador').html('');

            if(data.length > 0){
              if(data.length > 1){
                $('#colaborador').removeAttr('readonly');
              }else{
                $('#colaborador').attr('readonly', 'readonly');
              }
              $(data).each(function(key, value){
                $('#colaborador').append(
                  '<option value="'+value.id+'">'+value.nome+'</option>'
                );
              });
            }
          })
        },
        error:
          $.ajax({
              type: "GET",
              url: "/wmserros/informar_erros/colaborador",
              dataType: "json",
              success: function(data) {
                  console.log(data);
                  $('#colaborador').html(
                    '<option></option>'
                  );

                  if(data.length > 0){
                    $(data).each(function(key, value){
                      $('#colaborador').append(
                        '<option value="'+value.id+'">'+value.nome+'</option>'
                      );
                    });
                  }

                  $('#colaborador').removeAttr('readonly');
              },
              error: function() {
                  console.log('');
              }
          })
    });
  }
  else{
    var attr = $('#colaborador').attr('readonly');
    // For some browsers, `attr` is undefined; for others,
    // `attr` is false.  Check for both.
    if (typeof attr == typeof undefined || attr == false) {
        console.log(attr);
        $('#colaborador').attr('readonly', 'readonly')
        $('#colaborador').html(
          '<option></option>'
        );
    }
  }
}

$(function() {
    $("#messages").delay(3000).toggle(700);

    $(".button-hidden").bind("click", function(e){
      e.preventDefault();
      var index = $(this).closest("tr").index() + 2;
      console.log(index);
      var obj = $("#mytable tbody tr:eq("+index+")");
      $(obj).toggle();
    })

    /* ########################################################################
      EVENTOS JAVASCRIPT DA PAGINA DE CADASTRO DE ERROS DOS COLABORADORES
    ######################################################################## */

    //Chama o Ajax para buscar o cliente da onda digitada
    $('#id_onda').on('blur', function(){
        busca_dados($('#id_onda'), $('#id_produto'), $('#nome_cliente'), $('#form-onda'), '/wmserros/informar_erros/onda')
      }
    );

    //Chama o Ajax para buscar a descrição do produto digitado
    $('#id_produto').on('blur', function(){
        busca_dados($('#id_produto'), $('#id_onda'), $('#descricao_produto'), $('#form-produto'), '/wmserros/informar_erros/produto')
      }
    );

    //Função Ajax para buscar os dados de cliente da onda e produto
    function busca_dados(id_input, id_input_02, id_descricao, div, source) {
        $(div).removeClass('has-error');
        $(div).find('span').remove();
        $(id_descricao).val('');
        $('#colaborador').val('');
        $(id_input).attr('placeholder', 'Digite aqui...');

        if ($(id_input).val() != '') {
            var txt = $(id_input).serialize();
            var id = $(id_input).val();
            $(id_input).val('');
            $(id_input).attr('readonly', 'readonly');

            $.ajax({
                type: "GET",
                url: source,
                dataType: "json",
                data: txt,
                success: function(data) {
                    console.log(data);
                    $(id_descricao).val(data);
                    $(id_input).val(id);
                    $(id_input).removeAttr('readonly');
                    $(id_input).attr('placeholder', 'Digite aqui...');
                    getColaborador();
                },
                error: function() {
                    $(id_descricao).val('');
                    $(id_input).val(id);
                    $(id_input).removeAttr('readonly');
                    $(div).addClass('has-error');
                    $(div).append(
                        '<span id="helpBlock2" class="help-block">' +
                        'O valor informado nao foi encontrado.' +
                        '</span>'
                    )
                    getColaborador();
                }
            });
        }
        else {
          getColaborador();
        }
    }

    //Evento para buscar tarefas
    $('#tipo_tarefa').on('change', function(){
      var id_tarefa = $('#tipo_tarefa').serialize();
      console.log(id_tarefa);

      if(id_tarefa){
        $.ajax({
            type: "GET",
            url: "/wmserros/informar_erros/tarefa",
            dataType: "json",
            data: id_tarefa,
            success: function(data) {
                $('#tipo_erro').html('');
                if(data.length > 0){
                  $(data).each(function(key, value){
                    $('#tipo_erro').append(
                      '<option value="'+value.id+'">'+value.descricao+'</option>'
                    );
                    $('#tipo_erro').removeAttr('disabled');
                  });
                }
            },
            error: function() {
                $('#colaborador').val('');
            }
        });
      }else{
        $('#tipo_erro').html('');
        $('#tipo_erro').attr('disabled', 'disabled');
        $('#colaborador').val('');
      }
      getColaborador();
    });
});
