odoo.define('biznavi_ticket.website_booking_calendar', function (require) {
    "use strict";

    (function (self, $) {

        var ajax = require('web.ajax');
        var core = require('web.core');
        var _t = core._t;

        self.DTF = 'YYYY-MM-DD HH:mm:ss';
        self.DF = 'YYYY/MM/DD';
        self.TF = 'HH:mm';
        self.MIN_TIME_SLOT = 1; //hours
        self.SLOT_START_DELAY_MINS = 15; //minutes
        self.resources = [];
        self.bookings = [];
        // self.session = openerp.website.session || new openerp.Session();
        self.domain = [];
        self.colors = {};

        self.loadSlots = function (start, end, timezone, callback) {
            self.start_loading("名額查詢中...");
            var d = new Date();
            var offset = d.getTimezoneOffset();
            ajax.jsonRpc("/booking/calendar/slots", 'call', {
                start: start.add(offset, 'minutes').format(self.DTF),
                end: end.add(offset, 'minutes').format(self.DTF),
                tz: offset,
                domain: self.domain
            }).then(function (response) {
                callback(response);
                self.stop_loading();
                if(getUrlParameter('i')){
                    $("div[class='btn btn-primary btn-xs']").click();
                }
            });
        };
        self.loadBookings = function (start, end, timezone, callback) {
            var d = new Date();
            var offset = d.getTimezoneOffset();
            ajax.jsonRpc("/booking/calendar/slots/booked", 'call', {
                start: start.add(offset, 'minutes').format(self.DTF),
                end: end.add(offset, 'minutes').format(self.DTF),
                tz: d.getTimezoneOffset(),
                domain: self.domain
            }).then(function (response) {
                callback(response);
            });
        };

        self.warn = function (text) {
            var $bookingWarningDialog = $('#booking_warning_dialog');
            $bookingWarningDialog.find('.modal-body').text(text);
            $bookingWarningDialog.modal('show');
        };

        self.start_loading = function (text) {
            var $loading_modal = $('#loading_modal');
            if (text) {
                $loading_modal.find('.oe_throbber_message-body').text(text);
            }
            $loading_modal.modal('show');
        };

        self.stop_loading = function () {
            var $loading_modal = $('#loading_modal');
            $loading_modal.modal('hide');
        };

        self.getBookingsInfo = function (toUTC) {
            var res = [];
            _.each(self.bookings, function (b) {
                var start = b.start.clone();
                var end = b.end ? b.end.clone() : start.clone().add(1, 'hours');
                if (toUTC) {
                    start.utc();
                    end.utc();
                }
                res.push({
                    'resource': b.resource_id,
                    'start': start.format(self.DTF),
                    'end': end.format(self.DTF)
                });
            });
            return res;
        };

        self.viewRender = function (view, element) {
            if (view.name == 'agendaWeek') {
                $(element).find('th.fc-day-header').css({ 'cursor': 'pointer' })
                    .click(function () {
                        var m = moment($(this).text(), view.calendar.option('dayOfMonthFormat'));
                        if (m < view.start) {
                            m.year(view.end.year());
                        }
                        view.calendar.changeView('agendaDay');
                        view.calendar.gotoDate(m);
                    });
            }
            // else if (view.name == 'basicDay'){
            //     // $('.fc-widget-content').css('height', '41px');
            //     $(element).find('td.fc-time').each(function(i){
            //         $(this).append("span").text(_t("第 ") + (i+1) + _t(" 梯"));
            //     });
            // }
            if (view.name == 'basicDay') {
                $('.fc-day').css({ 'text-align': 'center', 'vertical-align': 'middle' }).text('未開放預約');
            }
            $('#booking_info').text("請先挑選一個日期和梯次");
            $('.fc-month-button').text('選擇日期');
            $("#add_to_cart").css({ 'pointer-events': 'none', 'cursor': 'default', 'opacity': '0.4' });
        };
        self.eventRender = function (event, element, view) {
        };
        self.eventAfterRender = function (event, element, view) {
            if (view.name == 'month') {
                $(element).parent().parent().parent().find("tr").each(function (i) {
                    if (i > 0) {
                        $(this).remove();
                    } else {
                        $(element).parent().css({ 'text-align': 'center' }).empty()
                            .append("<div class='btn btn-primary btn-xs'>" + _t('預約') + "</div>")
                            .click(function (e) {
                                view.calendar.changeView('basicDay');
                                view.calendar.gotoDate(event.start);
                            });
                    }
                    // view.calendar.gotoDate(new Date(new Date().getTime() + 24 * 60 * 60 * 1000));
                });
            } else if (view.name == 'basicDay') {
                $('.fc-event').css({ 'height': '36px', 'text-align': 'center' });
                $('.fc-content').css({ 'padding': '9px' });
                $('.fc-title').css({ 'font-size': '16px', 'color': '#FFF' });
                if ($(element).html().indexOf("額滿") >= 0) {
                    $(element).addClass('booked_slot');
                    // $(element).css({ 'background-color': 'gray','border-color': 'gray'});
                }
                $('.fc-day').text('');
                // $('.fc-event').css({'height':'40px'});
                // $('.fc-event').css('top', function(i, v) {
                //     console.log(i);
                //     return (i*21) + 'px';
                // });
            }
        };

        var getUrlParameter = function getUrlParameter(sParam) {
            var sPageURL = decodeURIComponent(window.location.search.substring(1)),
                sURLVariables = sPageURL.split('&'),
                sParameterName,
                i;

            for (i = 0; i < sURLVariables.length; i++) {
                sParameterName = sURLVariables[i].split('=');

                if (sParameterName[0] === sParam) {
                    return sParameterName[1] === undefined ? true : sParameterName[1];
                }
            }
        };
        /* initialize the external events
         -----------------------------------------------------------------*/
        self.init = function () {
            var rc = getUrlParameter('RC');
            if (rc) {
                if (rc == '14') {
                    alert('卡號錯誤!');
                } else if (rc == '01') {
                    alert('請查詢發卡銀行!');
                } else if (rc == '54') {
                    alert('卡片過期!');
                } else if (rc == '62') {
                    alert('尚未開卡!');
                } else if (rc == 'G1') {
                    alert('交易逾時!');
                } else if (rc == 'GA') {
                    alert('無效的持卡人資料!');
                } else if (rc == 'GD') {
                    alert('查無訂單編號!');
                } else if (rc == 'GG') {
                    alert('交易失敗!');
                } else if (rc == 'GT') {
                    alert('交易時間逾時!');
                } else if (rc == 'timeover') {
                    alert('本梯次已截止訂票! 請重新預約。');
                } else if (rc != 'GR' && rc != 'G6') {
                    alert('刷卡交易錯誤!');
                }
            }

            self.domain.push({'product_id':parseInt($('input[name=product_tpl_id]').val())});
            self.$calendar = $('#calendar');
            // page is now ready, initialize the calendar...
            self.$calendar.fullCalendar({
                handleWindowResize: true,
                height: 'auto',
                eventResourceField: 'resource_id',
                minTime: '09:00:00',
                maxTime: '16:00:00',
                slotDuration: '00:30:00',
                allDayDefault: false,
                allDaySlot: false,
                displayEventTime: false,
                firstDay: 1,
                defaultView: 'month',
                defaultDate: new Date(new Date().getTime() + 24 * 60 * 60 * 1000),
                timezone: 'local',
                locale: 'zh_TW',
                weekNumbers: false,
                eventSources: [
                    { events: self.loadSlots }
                    // {events: self.loadBookings}
                ],
                viewRender: self.viewRender,
                eventAfterRender: self.eventAfterRender,
                eventRender: self.eventRender,
                eventClick: self.eventClick,
                // customButtons: {
                //     confirm: {
                //         text: 'Change Date',
                //         click: self.confirm
                //     }
                // },
                header: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'month'
                    // right: 'agendaWeek,agendaDay'
                },
                slotEventOverlap: false
                // dayClick: function(date, jsEvent, view) {
                //     alert(jsEvent.start);
                //     if(date > moment().add(2,'days')){
                //         view.calendar.changeView('agendaDay');
                //         view.calendar.gotoDate(date);
                //     }
                // },
                // views: {
                //     month: {
                //         eventLimit: 1
                //     }
                // }
            });

            $("form[class='js_add_cart_variants']").submit(function (ev) {
                var pass = true;
                // if ($("#contact_usr").is(":visible")) {
                if ($('.product_id').val() == 7) {
                    if ($("input[name=contact_usr]").val().trim() == "") {
                        $("div[name=contact_usr]").addClass('has-error');
                        $("span[name=contact_usr_msg]").text("(必須填寫)");
                        pass = false;
                    } else {
                        $("div[name=contact_usr]").removeClass('has-error');
                        $("span[name=contact_usr_msg]").text("");
                    }
                    if ($("input[name=contact_tel]").val().trim() == "") {
                        $("div[name=contact_tel]").addClass('has-error');
                        $("span[name=contact_tel_msg]").text("(必須填寫)");
                        pass = false;
                    } else {
                        $("div[name=contact_tel]").removeClass('has-error');
                        $("span[name=contact_tel_msg]").text("");
                    }
                }
                var max_qty = parseInt($("input[name=add_qty]").attr('data-max'));
                if ($("input[name=add_qty]").val() > max_qty) {
                    alert("超過本梯次剩餘名額: " + max_qty + "，請改選其它梯次。");
                    pass = false;
                }
                if (!pass) {
                    return false;
                } else {
                    self.start_loading("預約處理中...");
                }
            });



            $('#booking-dialog-confirm').click(function () {
                var $form = $('#booking-dialog').find('form');
                var d = new Date();
                $form.find("[name=timezone]").val(d.getTimezoneOffset());
                $form.submit();
            });


            $('.panel-heading').click(function (e) {
                var qrnode = $(this).parent().find('#qrcode');
                if (!qrnode.html()) {
                    var code = $(this).parent().find('#ticket').html();
                    qrnode.qrcode({ width: 200, height: 200, text: code });
                }
            });
            $('.panel-heading').click();

            $("button[name='refund_btn']").click(function (e) {
                e.stopPropagation();
            });

            $("form[name='refund_form']").submit(function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                if (confirm(_t("確定要退票嗎?"))) {
                    // $("body").addClass("loading_modal");
                    $(ev.currentTarget).attr('disabled', true);
                    var form = $(this);
                    self.start_loading("退款處理中...");
                    form.find("button").prepend('<i class="fa fa-refresh fa-spin"></i> ');
                    $.ajax({
                        type: "POST",
                        url: form.attr('action'),
                        data: 'csrf_token=' + core.csrf_token,
                        success: function (data) {
                            self.stop_loading("退款處理中...");
                            alert(data);
                            self.start_loading("重新整理中...");
                            location.reload();
                        },
                        error: function (data) {
                            alert(data);
                            self.start_loading("重新整理中...");
                            location.reload();
                        }
                    });
                }
            });

            $("form[name='cancel_form']").submit(function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                if (confirm(_t("確定要取消預約嗎?"))) {
                    // $("body").addClass("loading_modal");
                    $(ev.currentTarget).attr('disabled', true);
                    var form = $(this);
                    self.start_loading("預約取消中...");
                    form.find("button").prepend('<i class="fa fa-refresh fa-spin"></i> ');
                    $.ajax({
                        type: "POST",
                        url: form.attr('action'),
                        data: 'csrf_token=' + core.csrf_token,
                        success: function (data) {
                            self.stop_loading("預約取消中...");
                            self.start_loading("重新整理中...");
                            location.reload();
                        },
                        error: function (data) {
                            alert(data);
                            self.start_loading("重新整理中...");
                            location.reload();
                        }
                    });
                }
            });

            $("button[name='contact_modify_btn']").click(function (e) {
                e.stopPropagation();
                var form = $(this).parent();
                form.find("button[name='contact_save_btn']").show();
                form.find("button[name='contact_cancel_btn']").show();
                form.find("#contact_editor").show();
                form.find("#contact_span").hide();
                $(this).hide();
            });

            $("button[name='contact_cancel_btn']").click(function (e) {
                e.stopPropagation();
                var form = $(this).parent();
                form.find("button[name='contact_modify_btn']").show();
                form.find("#contact_span").show();
                form.find("#contact_editor").hide();
                form.find("button[name='contact_save_btn']").hide();
                $(this).hide();
            });

            $("form[name='contact_modify_form']").find("input").click(function (e) {
                e.stopPropagation();
            });

            $("button[name='contact_save_btn']").click(function (e) {
                e.stopPropagation();
                var form = $(this).parent();
                form.find("button[name='contact_modify_btn']").show();
                form.find("#contact_span").show();
                form.find("#contact_editor").hide();
                form.find("button[name='contact_cancel_btn']").hide();
                $(this).hide();
            });

            $("form[name='contact_modify_form']").submit(function (ev) {
                ev.preventDefault();
                ev.stopPropagation();
                $(ev.currentTarget).attr('disabled', true);
                var form = $(this);
                self.start_loading("儲存更新中...");
                $.ajax({
                    type: "POST",
                    url: form.attr('action'),
                    data: form.serialize() + '&csrf_token=' + core.csrf_token,
                    success: function (data) {
                        var json = JSON.parse(data);
                        if(json.contact_tel) {
                            form.find("input[name=contact_usr]").val(json.contact_usr);
                            form.find("input[name=contact_tel]").val(json.contact_tel);
                            alert("修改失敗!! 參訪人或團體帶隊人及聯絡電話都必須填寫!");
                        } else{
                            form.find("#contact_span").text(json.contact_usr);
                        }
                        self.stop_loading();
                    },
                    error: function (data) {
                        var json = JSON.parse(data);
                        alert(json.msg);
                        self.stop_loading();
                    }
                });
            });

            $('#booking_info').click(function (e) {
                $('#product_details').addClass('hidden-xs');
                self.$calendar.removeClass('hidden-xs');
            });
            $('#product_details').addClass('hidden-xs');

            $('form.js_add_cart_variants').on('keyup keypress', function (e) {
                var keyCode = e.keyCode || e.which;
                if (keyCode === 13) {
                    e.preventDefault();
                    return false;
                }
            });

            $("input[name=add_qty]").change(function (e) {
                if ($("#add_to_cart").css('pointer-events') == 'none') {
                    alert("請先選擇梯次!");
                    $(this).val($("input[name=add_qty]").defaultValue);
                }
                var max_qty = parseInt($("input[name=add_qty]").attr('data-max'));
                if ($(this).val() > max_qty) {
                    alert("超過本梯次剩餘名額: " + max_qty + "，請改選其它梯次或減少人數。");
                    $(this).val(max_qty);
                } else if ($(this).val() > 0) {
                    $("input[name=add_qty]").attr('data-min', $(this).val());
                }

                if (($('.product_id').val() == 15 || $('.product_id').val() == 18 || $('.product_id').val() == 21) && $(this).val() > 10) {
                    alert("最多只能預約10位。");
                    $(this).val(10);
                }

                if (($('.product_id').val() == 7 || $('.product_id').val() == 22) && $(this).val() < 30) {
                    $(this).val(30);
                }

                // var min_qty = 1;
                // if (($('.product_id').val() == 7 || $('.product_id').val() == 22) && $(this).val() < 30) {
                //     $(this).val(30);
                // } else{
                //     min_qty = 1;
                // }
                //
                // if ($(this).val() < min_qty) {
                //     $(this).val(min_qty);
                // }
            });

            $("a[href='/shop/confirm_order']").click(function(e){
                self.start_loading("預約確認中...");
            });


            $('ul.js_add_cart_variants li:first input.js_variant_change').change(function (e) {
                // alert("var" + $(this).val());
                $("div[name=contact_usr]").removeClass('has-error');
                $("span[name=contact_usr_msg]").text("");
                $("div[name=contact_tel]").removeClass('has-error');
                $("span[name=contact_tel_msg]").text("");
                if ($(this).val() == '11' || $(this).val() == '5') {
                    var min_qty = 30;
                    if ($("input[name=add_qty]").val() < min_qty) {
                        $("input[name=add_qty]").val(min_qty);
                    }
                    // $("#contact_usr").show();
                    $("span[name=contact_usr_title]").text("團體帶隊人");
                } else if ($(this).val() == '6' || $(this).val() == '2' || $(this).val() == '3') {
                    if ($("input[name=add_qty]").val() > 10) {
                        $("input[name=add_qty]").val(10);
                    }
                    $("span[name=contact_usr_title]").text("參訪人");
                } else {
                    $("input[name=add_qty]").val($("input[name=add_qty]").attr('data-min'));
                    $("span[name=contact_usr_title]").text("參訪人");
                    // $("#contact_usr").hide();
                }
            });

            $('ul.js_add_cart_variants li:first input.js_variant_change').change();

            $('ul.js_add_cart_variants li input.js_variant_change').each(function (e) {
                if ($(this).val() == '11') {
                    $(this).parent().find('span').after(" (應購買全票者三十人以上之團體適用之)");
                }
                if ($(this).val() == '10') {
                    $(this).parent().find('span').after(" (適用對象詳參網站注意事項收費標準)");
                }
                if ($(this).val() == '14') {
                    $(this).parent().find('span').after(" (瑪家【原住民族文化發展中心】➡ 三地門)");
                }
                if ($(this).val() == '15') {
                    $(this).parent().find('span').after(" (三地門 ➡ 瑪家【原住民族文化發展中心】)");
                }
            });
            $('ul.js_add_cart_variants li strong:last').text("入口 (參訪動線)");

             if (new Date() < new Date(2018, 1, 6) && new Date()  > new Date(2017, 9, 1)) {
                 $('ul.js_add_cart_variants li:eq(5) input.js_variant_change').prop('checked', true);
                 $('ul.js_add_cart_variants li:eq(6)').hide();
             }

            $("input[name=add_qty]").val(1);
        };

        // self.confirm = function () {
        //     var $contentBlock = $('#booking-dialog').find('.modal-body');
        //     $contentBlock.load('/booking/calendar/confirm/form', {
        //         events: JSON.stringify(self.getBookingsInfo()),
        //     }, function () {
        //         $('.booking-product').change(function () {
        //             var price = $(this).find(':selected').data('price');
        //             var currency = $(this).find(':selected').data('currency');
        //             $(this).closest('tr').find('.booking-price').text(price);
        //             $(this).closest('tr').find('.booking-currency').text(currency);
        //         });
        //         $('#booking-dialog').modal('show');
        //     });
        // };

        var bg;
        self.eventClick = function (calEvent, jsEvent, view) {
            var $slot = $(this);
            if ($(this).hasClass('booked_slot')) {
                return;
            }
            // if (!($("[name=is_logged]").val())) {
            //     window.location = '/web/login?redirect=' + encodeURIComponent(window.location);
            //     return;
            // }
            // if($(window).width()<=768) {
            //     location.hash = "#product_details";
            // }
            $('#booking_info').text(calEvent.start.format(self.DF) + ' ' + _t("第 ") + calEvent.batch + _t(" 梯") + ' (' + calEvent.start.format(self.TF) + ' ~ ' + calEvent.end.format(self.TF) + ')');
            // $("ul.js_add_cart_variants").find("span").each(function(i){
            //     var txt = $(this).html()
            //     if(txt.indexOf("(")>0){
            //         txt = txt.substring(0, txt.indexOf("("));
            //     }
            //     $(this).html(txt + " (250)");
            // });

            var booked = false;

            $('.selected').each(function (i) {
                $(this).removeClass('selected');
                $(this).css('background-color', bg);
            });
            _.each(self.bookings, function (b, k) {
                if (b._id == calEvent._id) {
                    $('#booking_info').text("請先挑選一個日期和梯次");
                    booked = true;
                    $slot.removeClass('selected');
                    if (self.colors[calEvent._id]) {
                        $slot.css(self.colors[calEvent._id]);
                    }
                    self.bookings.splice(k, 1);
                }
            });
            $("#add_to_cart").css({ 'pointer-events': 'none', 'cursor': 'default', 'opacity': '0.4' });
            self.bookings = [];
            if (!booked) {
                self.bookings.push(calEvent);
                if (bg!=''){
                    bg = $slot.css('background-color');
                }
                $slot.css('background-color', '');
                $slot.addClass('selected');
                setTimeout(function () {
                    self.$calendar.addClass('hidden-xs');
                }, 300);
                $('#product_details').removeClass('hidden-xs');
                // self.colors[calEvent._id] = {
                //     'background-color': $slot.css('background-color'),
                //     'border-color': $slot.css('border-color')
                // };
                // self.colors['unselect'] = {
                //     'background-color': $slot.css('background-color'),
                //     'border-color': $slot.css('border-color')
                // };
                // $slot.css('background-color', '');
                // $slot.css('border-color', '');
                $("#add_to_cart").css({ 'pointer-events': 'auto', 'cursor': 'pointer', 'opacity': '1' });
                var s_name = 'product_id[' + self.bookings[0].resource_id;
                s_name += '][' + self.bookings[0].start.format(self.DTF);
                s_name += '-' + self.bookings[0].end.format(self.DTF) + ']';
                s_name += '[' + self.bookings[0].batch + ']';
                $('.product_id').attr('name', s_name);
                var s = calEvent.title.indexOf("餘額");
                // $("input[name=add_qty]").attr('data-max', (s > 0) ? calEvent.title.substring(s + 3, calEvent.title.length - 1) : ((self.bookings[0].start  < new Date(2018, 0, 1) && self.bookings[0].start  > new Date(2017, 9, 1))?250:400));
                $("input[name=add_qty]").attr('data-max', calEvent.title.substring(s + 3, calEvent.title.length - 1));
                // $("input[name=add_qty]").change();
                 if (self.bookings[0].start  < new Date(2018, 1, 6) && self.bookings[0].start  > new Date(2017, 9, 1)) {
                     $('ul.js_add_cart_variants li:eq(5) input.js_variant_change').prop('checked', true);
                     $('ul.js_add_cart_variants li:eq(6)').hide();
                 } else {
                     $('ul.js_add_cart_variants li:eq(6)').show();
                 }
            }
            $("input[name=add_qty]").change();
        };
    } (window.booking_calendar = window.booking_calendar || {}, jQuery));

    $(document).ready(function () {
        booking_calendar.init();
    });

    // $(document).on({
    //     ajaxStart: function() { $("body").addClass("loading"); },
    //     ajaxStop: function() { $("body").removeClass("loading"); }    
    // });
});