odoo.define('website_booking_calendar.website_booking_calendar', function (require) {
    "use strict";

    (function (self, $) {

        var ajax = require('web.ajax');
        var core = require('web.core');
        var _t = core._t;

        self.DTF = 'YYYY-MM-DD HH:mm:ss';
        self.DF = 'YYYY-MM-DD';
        self.MIN_TIME_SLOT = 1; //hours
        self.SLOT_START_DELAY_MINS = 15; //minutes
        self.resources = [];
        self.bookings = [];
        // self.session = openerp.website.session || new openerp.Session();
        self.domain = [];
        self.colors = {};

        self.loadSlots = function (start, end, timezone, callback) {
            var d = new Date();
            var offset = d.getTimezoneOffset();
            ajax.jsonRpc("/booking/calendar/slots", 'call', {
                start: start.add(offset, 'minutes').format(self.DTF),
                end: end.add(offset, 'minutes').format(self.DTF),
                tz: offset,
                domain: self.domain
            }).then(function (response) {
                callback(response);
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
                $(element).find('th.fc-day-header').css({'cursor': 'pointer'})
                    .click(function () {
                        var m = moment($(this).text(), view.calendar.option('dayOfMonthFormat'));
                        if (m < view.start) {
                            m.year(view.end.year());
                        }
                        view.calendar.changeView('agendaDay');
                        view.calendar.gotoDate(m);
                    });
            }
            $("#add_to_cart").css({'pointer-events':'none', 'cursor': 'default', 'opacity': '0.4'});
        };
        self.eventAfterRender = function (event, element, view) {
            if (view.name == 'month') {
                $(element).parent().parent().parent().find("tr").each(function(i){
                    if(i > 0) {
                        this.remove();
                    }else{
                        $(element).parent().css({'text-align':'center'}).empty()
                            .append("<div class='btn btn-primary btn-xs'>" + _t('Book') + "</div>")
                            .click(function(e){
                            view.calendar.changeView('agendaDay');
                            view.calendar.gotoDate(event.start);
                        });
                    }
                });
            }
        };

        /* initialize the external events
         -----------------------------------------------------------------*/
        self.init = function () {
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
                timezone: 'local',
                locale: 'zh_TW',
                weekNumbers: false,
                eventSources: [
                    {events: self.loadSlots}
                    // {events: self.loadBookings}
                ],
                viewRender: self.viewRender,
                eventAfterRender: self.eventAfterRender,
                eventClick: self.eventClick,
                // customButtons: {
                //     confirm: {
                //         text: 'Add to Cart',
                //         click: self.confirm
                //     }
                // },
                header: {
                    left: 'confirm prev,next today',
                    center: 'title',
                    right: 'month,agendaDay' // right: 'agendaWeek,list'
                },
                slotEventOverlap: false
            });

            $('#booking-dialog-confirm').click(function () {
                var $form = $('#booking-dialog').find('form');
                var d = new Date();
                $form.find("[name=timezone]").val(d.getTimezoneOffset());
                $form.submit();
            });

        };

        self.confirm = function () {
            var $contentBlock = $('#booking-dialog').find('.modal-body');
            $contentBlock.load('/booking/calendar/confirm/form', {
                events: JSON.stringify(self.getBookingsInfo()),
            }, function () {
                $('.booking-product').change(function () {
                    var price = $(this).find(':selected').data('price');
                    var currency = $(this).find(':selected').data('currency');
                    $(this).closest('tr').find('.booking-price').text(price);
                    $(this).closest('tr').find('.booking-currency').text(currency);
                });
                $('#booking-dialog').modal('show');
            });
        };

        self.eventClick = function (calEvent, jsEvent, view) {
            var $slot = $(this);
            if ($(this).hasClass('booked_slot')) {
                return;
            }
            var booked = false;
            $('.selected').each(function(i){
                if (self.colors['unselect']) {
                    $(this).css(self.colors['unselect']);
                }
                $(this).removeClass('selected');
            });
            _.each(self.bookings, function (b, k) {
                if (b._id == calEvent._id) {
                    booked = true;
                    $slot.removeClass('selected');
                    if (self.colors[calEvent._id]) {
                        $slot.css(self.colors[calEvent._id]);
                    }
                    self.bookings.splice(k, 1);
                }
            });
            $("#add_to_cart").css({'pointer-events':'none', 'cursor': 'default', 'opacity': '0.4'});
            self.bookings = [];
            if (!booked) {
                self.bookings.push(calEvent);
                $slot.addClass('selected');
                self.colors[calEvent._id] = {
                    'background-color': $slot.css('background-color'),
                    'border-color': $slot.css('border-color'),
                };
                self.colors['unselect'] = {
                    'background-color': $slot.css('background-color'),
                    'border-color': $slot.css('border-color'),
                };
                $slot.css('background-color', '');
                $slot.css('border-color', '');
                $("#add_to_cart").css({'pointer-events':'auto', 'cursor': 'pointer', 'opacity': '1'});

                var s_name = 'product_id[' + self.bookings[0].resource_id ;
                s_name += '][' + self.bookings[0].start.format(self.DTF);
                s_name += '-' + self.bookings[0].end.format(self.DTF) + ']';
                s_name += '[' + self.bookings[0].batch + ']';

            }
        };
    }(window.booking_calendar = window.booking_calendar || {}, jQuery));

    $(document).ready(function () {
        booking_calendar.init();
    });

});