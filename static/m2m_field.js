/**
 * Created by 12 on 2018/1/19 0019.
 */

function initM2MField(name, filter_args) {
    M2MFieldFunc(name);
    //绑定动态筛选
    bindM2MFilterChange(name, filter_args);
    initM2MFilter(name, filter_args);
}

function M2MFieldFunc(prefix) {
    //双击左右互换
    $('.m2m_' + prefix + " select[id='id_" + prefix + "']").on('dblclick', 'option', function () {
        $(this).prependTo($('.m2m_' + prefix + " select[id='id_" + prefix + "_choices']"))

    });
    $('.m2m_' + prefix + " select[id='id_" + prefix + "_choices']").on('dblclick', 'option', function () {
        $(this).prependTo($('.m2m_' + prefix + " select[id='id_" + prefix + "']"))

    });
    //提交前全选
    $("form").submit(function () {
        var ele_opts = $('.m2m_' + prefix + " select[id='id_" + prefix + "']").find('option');
        ele_opts.each(function () {
            $(this).prop('selected', true);
        });
        return true
    });
}

function bindM2MFilterChange(prefix, args) {
    $.each(args, function () {
        $("select[id='id_" + this + "']").on('change', function () {
            initM2MFilter(prefix, args)
        })
    })
}
function initM2MFilter(prefix, args) {
    var choices_opts = $('.m2m_' + prefix + " select[id='id_" + prefix + "_choices']").find('option');
    $.each(choices_opts, function () {
        var result = true;
        var opt = $(this);
        $.each(args, function () {
            var opt_vals = opt.attr(this).split('-');
            var filter_val = $("select[id='id_" + this + "']").val();
            if (in_array(filter_val, opt_vals)) {
                result = result && true
            } else {
                result = result && false;
                return false
            }
        });
        if (result) {
            $(this).removeClass('hidden')
        } else {
            $(this).addClass('hidden')
        }
    })
}

function in_array(stringToSearch, arrayToSearch) {
    for (var i = 0; i < arrayToSearch.length; i++) {
        thisEntry = arrayToSearch[i].toString();
        if (thisEntry === stringToSearch) {
            return true;
        }
    }
    return false;
}
