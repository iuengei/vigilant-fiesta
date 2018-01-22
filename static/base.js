/**
 * Created by 12 on 2018/1/19 0019.
 */

function initPagination() {
    var current_page = arguments[0] ? arguments[0] : 1;
    var items_pre = arguments[1] ? arguments[1] : 15;
    createPagination({
        items_per: items_pre,
        num_edge_entries: 1, //边缘页数
        num_display_entries: 10, //主体页数
        entries_class: ".items_hidden .item",
        show_class: ".items_show",
        current_page: current_page - 1 //默认0，表示第一页
    });
}

function bindSortFunc() {
    $('.glyphicon-sort').on('click', function () {
        var sign = $(this).attr('id');
        var sort_type = $(this).attr('type');

        var items_hidden = $('.items_hidden');
        var items = items_hidden.children('.item');

        //升序
        function sort_by_asc(a, b) {
            var valueA = $(a).find('.' + sign).text();
            var valueB = $(b).find('.' + sign).text();
            valueA = parseInt(valueA) || valueA;
            valueB = parseInt(valueB) || valueB;
            return valueA > valueB ? 1 : -1
        }

        //降序
        function sort_by_desc(a, b) {
            var valueA = $(a).find('.' + sign).text();
            var valueB = $(b).find('.' + sign).text();
            valueA = parseInt(valueA) || valueA;
            valueB = parseInt(valueB) || valueB;
            return valueA < valueB ? 1 : -1
        }

        if (sort_type === 'desc') {
            items.sort(sort_by_asc);
            $(this).attr('type', 'asc')
        } else {
            items.sort(sort_by_desc);
            $(this).attr('type', 'desc')
        }
        items.appendTo(items_hidden);


        //排序后重置分页
        var current_page = $('#Pagination .prev').nextAll('span:first').text();
        initPagination(current_page);

    })
}


function bindSearchButton() {
    $(window).keydown(function (event) {
        switch (event.keyCode) {
            case 13:
                if ($('.search_content:focus').length === 1) {
                    $('.search_button').click();
                }
        }
    });

    $('.search_button').on('click', function () {
        var search_content = $('.search_content').val().split(' ');
        var items = $('.items_hidden').children().removeClass('item');
        if (search_content[0] !== "") {
            $.each(items, function () {
                var item_text = $(this).text();
                var result = true;
                $.each(search_content, function () {
                    if (item_text.indexOf(this) < 0) {
                        result = false;
                        return false
                    }

                });
                if (result) {
                    $(this).addClass('item')
                }
            })
        } else {
            $.each(items, function () {
                $(this).addClass('item')
            })
        }

        //搜索后重置分页
        initPagination();

        $('.items_total').text($('.items_hidden .item').length)
    })
}