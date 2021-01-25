odoo.define('web_listview_sticky_header.stick_header', function (require) {
    'use strict';
    var ListView = require('web.ListView');
    ListView.include({
        load_list: function () {
            var $this = this;
            return this._super.apply(this, arguments).done(function () {
                // if ($this.ViewManager.views && $this.ViewManager.views.list.fields_view.arch.attrs.nowrap == 1) {
                //     $this.$el.find('table.o_list_view').find('th, td').css("white-space", "nowrap");
                // }
                if ($this.ViewManager.action && $this.ViewManager.action.target == 'new')
                    return;
                var o_content_area = $(".o_content")[0];

                // fixed_column start
                if ($this.ViewManager.views && $this.ViewManager.views.list) {
                    var cols = $this.ViewManager.views.list.fields_view.arch.children;
                    var pinned = false;
                    var header_groups = {};
                    cols.forEach(function (c) {
                        if (c.attrs['pinned'] && c.attrs['pinned'] != 0) {
                            pinned = true;
                        }
                        if (c.attrs['header_group'] && c.attrs['header_group'] != 0) {
                            header_groups[c.attrs['name']] = c.attrs['header_group'];
                        }
                    });
                    var table = $this.$el.find('table.o_list_view');
                    var has_group = !jQuery.isEmptyObject(header_groups);

                    if (pinned && !table.hasClass("o_list_view_grouped")) {
                        var clone = table.clone(true).addClass('fixed_column').css('width', '0px');
                        cols.forEach(function (c) {
                            var invisible = c.attrs['modifiers']?JSON.parse(c.attrs['modifiers'])['tree_invisible']:false;
                            if (!c.attrs['pinned'] || c.attrs['pinned'] == 0 || invisible) {
                                var idx = clone.find('[data-id=' + c.attrs['name'] + ']').index();
                                if (idx != -1) {
                                    clone.find('tr').find('td:eq(' + idx + '),th:eq(' + idx + ')').remove();
                                }
                            }
                        });
                        clone.children('tfoot').remove();
                        clone.find('.o_list_record_selector input').click(function () {
                            var ctr = $(this).closest('tr');
                            var tr = table.find('[data-id=' + ctr.attr('data-id') + ']');
                            var val = $(this).prop('checked');
                            var chk = tr.find('td.o_list_record_selector input');
                            if (tr.length == 0) {
                                chk = table.find('th.o_list_record_selector input');
                                clone.find('.o_list_record_selector input').prop('checked', val);
                            }
                            if (chk.prop('checked') != val) {
                                chk.click();
                            }
                            ctr.find('td').toggleClass('row_selected', val);
                            tr.find('td').toggleClass('row_selected', val);

                        });
                        table.parent('div').append(clone);
                        table.find('tbody tr').mouseover(function () {
                            table.parent('div').find('tr').removeClass('row_hover');
                            clone.find('tbody tr:eq(' + $(this).index() + ')').addClass('row_hover');
                        });
                        clone.find('tbody tr').mouseover(function () {
                            table.parent('div').find('tr').removeClass('row_hover');
                            table.find('tbody tr:eq(' + $(this).index() + ')').addClass('row_hover');
                        });
                        group_header(clone, header_groups, has_group);
                        clone.find('thead tr:last th').css('border-bottom', '1px grey solid');
                        $(o_content_area).scroll(function () {
                            clone.css('left', $(o_content_area).scrollLeft());
                        });
                    }
                    group_header(table, header_groups, has_group);
                    table.find('thead tr:last th').css('border-bottom', '1px grey solid');
                }

                function group_header(table, header_groups, has_group) {
                    if (has_group) {
                        var header = table.find('thead tr');
                        var header_group = header.clone(true);
                        var selector_idx = header_group.find('th.o_list_record_selector').index();
                        header_group.find('th.o_list_record_selector').css('border-bottom', '1px transparent solid').html('&nbsp;');
                        header.before(header_group);
                        var colspan = 1;
                        var last_group, group_th;
                        header_group.find('th').each(function () {
                            var col_name = $(this).attr('data-id');
                            var group_header = header_groups[$(this).attr('data-id')];
                            if (group_header) {
                                if (group_header == last_group) {
                                    colspan += 1;
                                    $(this).remove();
                                    group_th.attr('colspan', colspan).css({
                                        'border-bottom': '1px grey solid',
                                        'text-align': 'center'
                                    });
                                } else {
                                    $(this).text(group_header);
                                    last_group = group_header;
                                    group_th = $(this);
                                    colspan = 1;
                                }
                            } else if ($(this).index() > selector_idx) {
                                header.find('th[data-id=' + col_name + ']').remove();
                                $(this).attr('rowspan', 2).css('border-bottom', '1px grey solid');;
                            }
                        });
                    }
                }


                // fixed_column end

                function stick() {
                    if ($this.$el.parent(".o_form_field").length === 0) {
                        $this.$el.find('table.o_list_view').each(function () {

                            // $(this).stickyTableHeaders({scrollableArea: o_content_area, fixedOffset: 0.1});
                            $(this).stickyTableHeaders({scrollableArea: o_content_area});
                        });

                        // table.stickyTableHeaders({scrollableArea: o_content_area});
                    }
                }

                if ($this.$el.parent(".o_form_field").length === 0) {
                    stick();
                    $(window).unbind('resize', stick).bind('resize', stick);
                }


                function fix_body(position) {
                    $("body").css({
                        'position': position,
                    });
                }

                if ($this.$el.parents('.o_field_one2many').length === 0) {
                    stick();
                    fix_body("fixed");
                    $(window).unbind('resize', stick).bind('resize', stick);
                } else {
                    fix_body("relative");
                }
                $("div[class='o_sub_menu']").css("z-index", 4);
                $("div[class='o_sub_menu']").css("background", '#f0eeee');
            });
        }
    });

    ListView.List.include({
        render: async function () {
            await this._super.apply(this, arguments);

            var o_content_area = $(".o_content")[0];
            var pos = $(o_content_area).scrollTop();
            $('.o_list_view_grouped').each(function() {
                $(this).find('tbody input').click(function() {
                    var ctr = $(this).closest('tr');
                    var val = $(this).prop('checked');
                    ctr.find('td').toggleClass('row_selected', val);
                });
            });

            $(o_content_area).scrollTop(0);
            setTimeout(function(){$(o_content_area).scrollTop(pos)}, 50);

            // $('tr.o_group_header').click(function() {
            //     var l = $(this).find('th.fa-caret-down');
            //     console.log(l);
            //     alert(l);
            // });
        }
    });
});
