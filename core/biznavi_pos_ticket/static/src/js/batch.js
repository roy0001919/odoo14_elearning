odoo.define('biznavi_pos_ticket.batch', function (require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var chrome = require('point_of_sale.chrome');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var Model = require('web.DataModel');

var QWeb = core.qweb;
var _t = core._t;
var interval;

var load_date = todayStr(true);

setInterval(function(){
    if(load_date !== todayStr(true)){
        location.reload();
    }
}, 5000);

var DomCache = core.Class.extend({
    init: function(options){
        options = options || {};
        this.max_size = options.max_size || 2000;

        this.cache = {};
        this.access_time = {};
        this.size = 0;
    },
    cache_node: function(key,node){
        var cached = this.cache[key];
        this.cache[key] = node;
        this.access_time[key] = new Date().getTime();
        if(!cached){
            this.size++;
            while(this.size >= this.max_size){
                var oldest_key = null;
                var oldest_time = new Date().getTime();
                for(key in this.cache){
                    var time = this.access_time[key];
                    if(time <= oldest_time){
                        oldest_time = time;
                        oldest_key  = key;
                    }
                }
                if(oldest_key){
                    delete this.cache[oldest_key];
                    delete this.access_time[oldest_key];
                }
                this.size--;
            }
        }
        return node;
    },
    clear_node: function(key) {
        var cached = this.cache[key];
        if (cached) {
            delete this.cache[key];
            delete this.access_time[key];
            this.size --;
        }
    },
    get_node: function(key){
        var cached = this.cache[key];
        if(cached){
            this.access_time[key] = new Date().getTime();
        }
        return cached;
    },
});

models.load_models({
    model: 'product.template',
    fields: ['name','capacity','id', 'resource_ids', 'available_in_pos', 'pay_online'],
    domain: null,
    loaded: function(self, product_templates){
        self.product_templates = product_templates;
        var max_seats = {};
        for (var i =0 ; i < product_templates.length ; i++) {
            self.db.product_tmpl_by_id[product_templates[i].id] = product_templates[i];
            if(!max_seats[product_templates[i].resource_ids[0]]) {
                max_seats[product_templates[i].resource_ids[0]] = 0;
            }
            if (product_templates[i].capacity > max_seats[product_templates[i].resource_ids[0]]) {
                max_seats[product_templates[i].resource_ids[0]] = product_templates[i].capacity;
            }
        }
        self.max_seats = max_seats;
    },
});

models.load_models({
     model: 'sale.order.line',
     fields: ['name', 'order_id', 'sale_order_name', 'salesman_id', 'origin', 'ticket', 'ref_ticket', 'state', 'product_id', 'partner_id', 'booking_batch', 'booking_start', 'booking_end', 'product_uom_qty', 'state', 'buyer', 'buyer_tel', 'contact_usr', 'contact_tel', 'product_cate', 'product_entry', 'write_date'],
     domain: function(self){ return [['booking_start','>=',todayStr(true)],['booking_end','<',todayStr(false)],['state','in',['sale','sent']]]; },
     loaded: function(self, order_lines){
        self.db.add_order_lines(order_lines);
     }
 });

function todayStr(day_start) {
    var d = new Date();
    d.setHours(0,0,0,0);
    if (!day_start) {
        d.setTime(d.getTime() + 86400000);
    }
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
}

models.load_models({
     model: 'resource.calendar.attendance',
     fields: ['name','hour_from','hour_to', 'date_from', 'date_to', 'dayofweek', 'calendar_id', 'pos_quota'],
     loaded: function(self, attendance){
         self.attendance = attendance;
     },
});

models.load_models({
     model: 'resource.calendar.leaves',
     fields: ['name','date_from','date_to', 'calendar_id'],
     loaded: function(self, leaves){
         self.leaves = leaves;
     },
});

models.load_models({
    model: 'resource.resource',
    fields: ['name', 'color', 'duration_mins', 'reserve_days', 'calendar_id', 'product_ids'],
    domain: function(self){ return [['to_calendar','=',true]]; },
    loaded: function(self,calendars){
        self.plans = [];
        self.plans_by_id = {};
        self.db.batches_by_num = {};
        for (var i = 0; i < calendars.length; i++) {
            var calendar = calendars[i];
            var available_in_pos = false;
            for (var c = 0; c < calendar.product_ids.length; c++) {
                if (self.db.get_product_tmpl_by_id(calendar.product_ids[c]).available_in_pos)
                    available_in_pos = true;
            }
            if (!available_in_pos) continue;
            // console.log(self.db.get_product_by_id(calendar.product_ids[0].id).available_in_pos);
            var plan = {"sequence": i, "id": calendar.id, "name": calendar.name};
//            console.log(JSON.stringify(self.attendance));
            var today = new Date();
            var hour_from = undefined
            var hour_to = undefined;
            var time_starts = [];
            var int_times = [];
            for (var a = 0 ;  a < self.attendance.length; a++) {
                var dow = (self.attendance[a].dayofweek==6)?0:parseInt(self.attendance[a].dayofweek) + 1;
                var date_from = (self.attendance[a].date_from)?new Date(self.attendance[a].date_from + " 00:00:00"):false;
                var date_to = (self.attendance[a].date_to)?new Date(self.attendance[a].date_to + " 23:59:59"):false;
                if(calendar.calendar_id[0] == self.attendance[a].calendar_id[0] && dow === today.getDay() && (!date_from || today > date_from) && (!date_to || today < date_to)) {
                    // if(!hour_from || self.attendance[a].hour_from < hour_from) {
                    //     hour_from = self.attendance[a].hour_from;
                    // }
                    // if(!hour_to || self.attendance[a].hour_to > hour_to) {
                    //     hour_to = self.attendance[a].hour_to;
                    // }
                    if(self.attendance[a].pos_quota > 0) {
                        self.max_seats[calendar.id] = self.attendance[a].pos_quota;
                    }
                    var time_start = number2Date(today, self.attendance[a].hour_from);
                    var time_over = number2Date(today, self.attendance[a].hour_to);
                    while (time_start < time_over) {
                        var time_end = new Date(time_start.getTime() + calendar.duration_mins * 60000);
                        if (int_times.indexOf(time_start.getTime()) < 0) {
                            int_times.push(time_start.getTime());
                            time_starts.push(time_start);
                        }
                        time_start = time_end;
                    }
                }
            }
            time_starts.sort();
            var batch_num = 1;
            var batches = [];
            for (var s = 0; s < time_starts.length; s++) {
                var time_start = time_starts[s];
                var time_end = new Date(time_start.getTime() + calendar.duration_mins * 60000);
                var batch_info = "【" + batch_num + "】 " + date2time(time_start) + " ~ " + date2time(time_end);
                var batch_count = self.max_seats[calendar.id] - ((self.db.count_by_batch[calendar.id + '|' + batch_num])?self.db.count_by_batch[calendar.id + '|' + batch_num]:0);
                var rows = 6;
                var batch = {
                                 "booking_batch":batch_num,
                                 "booking_start":time_start,
                                 "booking_end":time_end,
                                 "batch_info":batch_info,
                                 "name":batch_info,
                                 "position_h":-121 + 182 * parseInt((batch_num-1)/rows),
                                 "position_v":5 + 90 * ((batch_num-1)%rows),
//                                 "color":calendar.color,
                                 "plan_id":[plan.id,plan.name],
                                 "height":80,
                                 "width":173,
                                 "shape":"square",
                                 "seats":batch_count,
                                 "id":plan.id * 10000 + batch_num
                             };
                batches.push(batch);
                batch_num ++;
            }


            for (var l = 0 ;  l < self.leaves.length; l++) {
                if (calendar.calendar_id[0] === self.leaves[l].calendar_id[0]) {
                    var leave_start = toUTCDate(self.leaves[l].date_from);
                    var leave_end = toUTCDate(self.leaves[l].date_to);
                    for (var t = 0; t < batches.length; t++) {
                        if (batches[t].booking_start > leave_start && batches[t].booking_end < leave_end) {
                            batches[t].color = "pink";
                        }
                    }
                }
            }




            plan.batches = [];
            self.db.batches_by_id = {};

            if (batches.length > 0 || (calendars.length === i + 1 && self.plans.length === 0)) {
                self.plans.push(plan);
                self.plans_by_id[calendar.id] = plan;
                for (var j = 0; j < batches.length; j++) {
                    self.db.batches_by_id[batches[j].id] = batches[j];
                    self.db.batches_by_num[calendar.id + '|' + batches[j].booking_batch] = batches[j];
                    var plan = self.plans_by_id[batches[j].plan_id[0]];
                    if (plan) {
                        if (batches[j].booking_end < new Date() || batches[j].seats <= 0){
                            batches[j].color = "gray";
                        }
                        plan.batches.push(batches[j]);
                        batches[j].plan = plan;
                    }
                }
            }
        }

        var reservation = {"sequence": 10000, "background_color": null, "id": 0, "name": _t("Reservation"), "batches": []};
        self.plans.push(reservation);
        self.plans_by_id[0] = reservation;


        // Make sure they display in the correct order
        self.plans = self.plans.sort(function(a,b){ return a.sequence - b.sequence; });

        // Ignore schedule features if no plan specified.
        self.config.iface_schedule = !!self.plans.length;


        function number2Date(date, time) {
            return (function(i) {return new Date(date.getFullYear(), date.getMonth(), date.getDate(), i, Math.round(((time-i)*60),10));})(parseInt(time, 10));
        }
        function date2time(date) {
            return ((date.getHours()<10)?'0'+date.getHours():date.getHours()) + ":" + ((date.getMinutes()<10)?'0'+date.getMinutes():date.getMinutes());
        }
        function toUTCDate(s) {
            var d = new Date(s);
            return new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes(), d.getSeconds()));
        }
    },
});

// The Batch GUI element, should always be a child of the ReserveScreenWidget
var BatchWidget = PosBaseWidget.extend({
    template: 'BatchWidget',
    init: function(parent, options){
        this._super(parent, options);
        this.batch    = options.batch;
        this.selected = false;
        this.moved    = false;
        this.dragpos  = {x:0, y:0};
        this.handle_dragging = false;
        this.handle   = null;
    },
    // computes the absolute position of a DOM mouse event, used
    // when resizing batches
    event_position: function(event){
        if(event.touches && event.touches[0]){
            return {x: event.touches[0].screenX, y: event.touches[0].screenY};
        }else{
            return {x: event.screenX, y: event.screenY};
        }
    },
    // when a batch is clicked, go to the batch's orders
    // but if we're editing, we select/deselect it.
    click_handler: function(){
        var self = this;
        var schedule = this.getParent();
        schedule.pos.reservation = null;
        if(this.batch.color === '' || this.batch.color === undefined) {
            schedule.pos.set_batch(this.batch);
            self.products_by_resource_id(schedule.plan.id);
            clearInterval(interval);
            interval = null;
        }
    },
    perform_product_search: function(query, category, buy_result){
        var products;
        if(!category) {
            category = this.pos.db.get_category_by_id(this.pos.db.root_category_id);
        }
        if(query){
            products = this.pos.db.search_product_in_category(category.id,query);
            if(buy_result && products.length === 1){
                    this.pos.get_order().add_product(products[0]);
                    this.clear_search();
            }else{
                this.pos.product_list_widget.set_product_list(products);
            }
        }else{
            products = this.pos.db.get_product_by_category(category.id);
            this.pos.product_list_widget.set_product_list(products);
        }
    },
    products_by_resource_id: function(resource_id){
        var products;
        var start_categ_id = this.pos.config.iface_start_categ_id ? this.pos.config.iface_start_categ_id[0] : this.pos.db.root_category_id;
        var category = this.pos.db.get_category_by_id(start_categ_id);
        products = this.pos.db.get_product_by_category(category.id);
        for (var i = products.length-1; i >= 0; i--) {
            var resources = this.pos.db.product_tmpl_by_id[products[i].product_tmpl_id].resource_ids;
            for (var r = 0; r < resources.length; r++ ) {
                var rid = resources[r];
                // if (rid && resource_id !== rid || products[i].display_name.indexOf('三地門') !== -1) {
                if (rid && resource_id !== rid) {
                    products.splice(i, 1);
                }
            }
        }
        products.sort(function (a, b) {
            var name_a = a.display_name.substring(0, a.display_name.indexOf('('));
            var name_b = b.display_name.substring(0, b.display_name.indexOf('('));
            if(name_a === name_b) {
                return (a.price < b.price) ? 1 : (a.price > b.price) ? 0 : -1;
            } else {
                return (name_a < name_b) ? -1 : 1;
            }
            // if(a.price === b.price) {
            //     return (name_a < name_b) ? -1 : (name_a > name_b) ? 0 : 1;
            // } else {
            //     return (a.price > b.price) ? -1 : 1;
            // }
         // return a.price > b.price ? 1 : -1;
        });
        this.pos.product_list_widget.set_product_list(products);
    },
    set_batch_color: function(color){
        this.batch.color = _.escape(color);
        this.$el.css({'background': this.batch.color});
    },
    set_batch_name: function(name){
        if (name) {
            this.batch.name = name;
            this.renderElement();
        }
    },
    set_batch_seats: function(seats){
        this.batch.seats = Number(seats);
        this.renderElement();
    },
    // The batch's positioning is handled via css absolute positioning,
    // which is handled here.
    batch_style: function(){
        var batch = this.batch;
        function unit(val){ return '' + val + 'px'; }
        var style = {
            'width':        unit(batch.width),
            'height':       unit(batch.height),
            'line-height':  unit(batch.height),
            'margin-left':  unit(-batch.width/2),
            'margin-top':   unit(-batch.height/2),
            'top':          unit(batch.position_v + batch.height/2),
            'left':         unit(batch.position_h + batch.width/2),
            'border-radius': batch.shape === 'round' ?
                    unit(Math.max(batch.width,batch.height)/2) : '3px',
        };
        if (batch.color) {
            style.background = batch.color;
        }
        if (batch.height >= 150 && batch.width >= 150) {
            style['font-size'] = '32px';
        }

        return style;
    },
    // convert the style dictionary to a ; separated string for inclusion in templates
    batch_style_str: function(){
        var style = this.batch_style();
        var str = "";
        var s;
        for (s in style) {
            str += s + ":" + style[s] + "; ";
        }
        return str;
    },
    // select the batch (should be called via the schedule)
    select: function() {
        this.selected = true;
        this.renderElement();
    },
    // deselect the batch (should be called via the schedule)
    deselect: function() {
        this.selected = false;
        this.renderElement();
        this.save_changes();
    },
    update_click_handlers: function(editing){
        var self = this;
        this.$el.off('click');
        // this.$el.off('mouseup touchend click dragend');
        this.$el.on('click', function(event){ self.click_handler(event,$(this)); });
        // this.$el.on('mouseup touchend click dragend', function(event){ self.click_handler(event,$(this)); });

        // if (editing) {
        //     this.$el.on('mouseup touchend touchcancel', function(event){ self.click_handler(event,$(this)); });
        // } else {
        //     this.$el.on('click dragend', function(event){ self.click_handler(event,$(this)); });
        // }
    },
    renderElement: function(){
        var self = this;
        this.order_count    = this.pos.get_batch_orders(this.batch).length;
//        this.customer_count = this.pos.get_customer_count(this.batch);
        this.fill           = Math.min(1,Math.max(0,this.customer_count / this.batch.seats));
//        this.notifications  = this.get_notifications();
        this._super();

        this.update_click_handlers();

        this.$el.on('dragstart', function(event,drag){ self.dragstart_handler(event,$(this),drag); });
        this.$el.on('drag',      function(event,drag){ self.dragmove_handler(event,$(this),drag); });
        this.$el.on('dragend',   function(event,drag){ self.dragend_handler(event,$(this),drag); });

        var handles = this.$el.find('.batch-handle');
        handles.on('dragstart',  function(event,drag){ self.handle_dragstart_handler(event,$(this),drag); });
        handles.on('drag',       function(event,drag){ self.handle_dragmove_handler(event,$(this),drag); });
        handles.on('dragend',    function(event,drag){ self.handle_dragend_handler(event,$(this),drag); });
    }
});


var ReservationWidget = PosBaseWidget.extend({
    template: 'ReservationWidget',
    init: function(parent, options){
        this._super(parent, options);
        this.reservation_cache = new DomCache();
    },
    render_list: function(order_lines){
        var self = this;
        var parent   = this.$('.reservation-list').parent();
        var contents = this.$el[0].querySelector('.reservation-list-contents');
        contents.innerHTML = "";
        for(var i = 0, len = Math.min(order_lines.length,3000); i < len; i++){
            var reservation = order_lines[i];
            if(!reservation) {
                break;
            }
            reservation.number = reservation.sale_order_name;
            var ns = reservation.name.indexOf("(");
            var ne = reservation.name.indexOf(")");
            reservation.ticket_name = (ns > 0 && ne >0)?reservation.name.substring(ns+1,ne):reservation.name;
            var reservationline = this.reservation_cache.get_node(reservation.id);
            if(!reservationline || $(reservationline).find("[name='ref_ticket']").html() == ""){
                var reservationline_html = QWeb.render('ReservationLine',{widget: this, reservation:reservation});
                var reservationline = document.createElement('tbody');
                reservationline.innerHTML = reservationline_html;
                reservationline = reservationline.childNodes[1];
                this.reservation_cache.cache_node(reservation.id,reservationline);
            }
            if($(reservationline).find("[name='ref_ticket']").html() != "") {
                $(reservationline).css({"background-color":"Pink", "cursor":"default"});
                $(reservationline).find("[name='action_btn']").html("");
            }
            $(reservationline).find("[name='reprint_btn']").click(function(event){
                // event.preventDefault();
                event.stopPropagation();
                var line = $(this).parent();
                setTimeout(function(){
                    self.pos.reservation = self.pos.db.reservation_by_id[line.data("id")];
                    var client = null;
                    if (self.pos.reservation.partner_id[0]) {
                        client = self.pos.db.get_partner_by_id(self.pos.reservation.partner_id[0]);
                        if (!client) {
                            console.error('ERROR: trying to load a parner not available in the pos');
                        }
                    }
                    var product = self.pos.db.get_product_by_id(self.pos.reservation.product_id[0]);
                    var rid = self.pos.db.product_tmpl_by_id[product.product_tmpl_id].resource_ids[0];
                    self.pos.set_batch(self.pos.db.batches_by_num[rid + '|' + self.pos.reservation.booking_batch]);
                    var order = self.pos.get_order();
                    order.add_product(product, { quantity: self.pos.reservation.product_uom_qty, price: 0});
                    order.set_client(client);
                    self.products_by_resource_id(rid);
                    $('.pay').click();
                    order.name = self.pos.reservation.number;
                    for (var i = 0 ; i < order.orderlines.models.length ; i++) {
                        order.orderlines.models[i].ticket = self.pos.reservation.ticket;
                    }
                    // order.set_ticket(self.pos.reservation.ticket);
                    $('.paymentmethod').click();
                    $("span:contains('核驗')").click();
                    order.destroy({'reason':'abandon'});
                    // self.pos.db.remove_order(order.id);
                    // order.state = 'cancel';

                }, 70);
                // console.log($(reservationline).html());
                // var line = $(this).parent();
                // var json = {};
                // var order = init_from_JSON(json)
                // var env = {
                //     widget:  self,
                //     pos: self.pos,
                //     order: order,
                //     receipt: order.export_for_printing(),
                //     paymentlines: order.get_paymentlines()
                // };
                // var receipt = QWeb.render('XmlReceipt',env);
                //
                // self.pos.proxy.print_receipt(receipt);
                // this.pos.get_order()._printed = true;
            });
            $(reservationline).find("[name='action_btn']").click(function(event){
                // event.preventDefault();
                event.stopPropagation();
                // console.log($(reservationline).html());
                var line = $(this).parent();
                new Model('pos.order.line').call('sync_cancel_sale_order', [line.data("id")]).then(function(result) {
                    line.remove();
                });
            });
            contents.appendChild(reservationline);

        }
//        var new_height = $(contents).height();
//        parent.scrollTop(parent.scrollTop() + new_height);

        this.update_click_handlers();
    },
    click_handler: function(event, el){
        var self = this;
        var order_id = $(el).parent().attr('data-id');
        if ($(el).css('cursor') == "pointer"){
            $(el).addClass('highlight');
            self.pos.reservation = self.pos.db.reservation_by_id[order_id];
            if(!self.pos.reservation.pay_online) {
                setTimeout(function(){
                    var client = null;
                    if (self.pos.reservation.partner_id[0]) {
                        client = self.pos.db.get_partner_by_id(self.pos.reservation.partner_id[0]);
                        if (!client) {
                            console.error('ERROR: trying to load a parner not available in the pos');
                        }
                    }
                    var product = self.pos.db.get_product_by_id(self.pos.reservation.product_id[0]);
                    var rid = self.pos.db.product_tmpl_by_id[product.product_tmpl_id].resource_ids[0];
                    self.pos.set_batch(self.pos.db.batches_by_num[rid + '|' + self.pos.reservation.booking_batch]);
                    var order = self.pos.get_order();

                    order.add_product(product, { quantity: self.pos.reservation.product_uom_qty});


                    order.set_client(client);
                    self.products_by_resource_id(rid);
                    $(el).removeClass('highlight');
                }, 70);
            }
        }
    },
    products_by_resource_id: function(resource_id){
        var products;
        var category = this.pos.db.get_category_by_id(this.pos.db.root_category_id);
        products = this.pos.db.get_product_by_category(category.id);
        for (var i = products.length-1; i >= 0; i--) {
            var rid = this.pos.db.product_tmpl_by_id[products[i].product_tmpl_id].resource_ids[0];
            if (rid && resource_id != rid) {
                products.splice(i, 1);
            }
        }
        this.pos.product_list_widget.set_product_list(products);
    },
    update_click_handlers: function(editing){
        var self = this;
        self.$el.find('.reservation-cell').each(function(index, element){
            $(element).off('click');
            $(element).on('click', function(event){ self.click_handler(event,$(element)); });

            // if (editing) {
            //     $(element).on('mouseup touchend touchcancel', function(event){ self.click_handler(event,$(element)); });
            // } else {
            //     $(element).on('click dragend', function(event){ self.click_handler(event,$(element)); });
            // }
        });
    }
});

// The screen that allows you to select the plan, see and select the batch,
// as well as edit them.
var PlanScreenWidget = screens.ScreenWidget.extend({
    template: 'PlanScreenWidget',

    // Ignore products, discounts, and client barcodes
    barcode_product_action: function(code){},
    barcode_discount_action: function(code){},
    barcode_client_action: function(code){},

    init: function(parent, options) {
        this._super(parent, options);
        this.plan = this.pos.plans[0];
        this.plan_batch_widgets = {};
        this.reservation_widget = null;
        this.selected_batch = null;
        this.editing = false;
    },
    hide: function(){
        this._super();
        if (this.editing) {
            this.toggle_editing();
        }
        this.chrome.widget.order_selector.show();
    },
    show: function(){
        this._super();
        var self = this;
        self.chrome.widget.order_selector.hide();
        var batch_widgets = self.plan_batch_widgets[self.plan.id];
        for (var i = 0; i < batch_widgets.length; i++) {
            batch_widgets[i].renderElement();
        }
        self.check_empty_plan();

        $("span[name=amt_0]").text('#' + self.pos.db.reservation_amt);
        for (var p = 0; p < self.pos.plans.length; p++) {
            var pid = self.pos.plans[p].id;
            if (pid > 0) {
                $("span[name=amt_" + pid + "]").text('#' + self.pos.db.pos_amt);
            }
        }
        try {
            setTimeout(function(){self.pos.reload_sale_order_lines(self)}, 15000);
        } catch(err) {
            console.log(err);
        }
        if(!interval) {
            interval = setInterval(function(){
                // if(!self.$('.keywordbox input').is(":focus")){
                //     self.$('.keywordbox input').keyup();
                // }
                try {
                    self.pos.reload_sale_order_lines(self);
                } catch(err) {
                    console.log(err);
                }
            }, 15000);
        }
    },
    click_plan_button: function(event,$el){
        var plan = this.pos.plans_by_id[$el.data('id')];
        if (plan !== this.plan) {
            if (this.editing) {
                this.toggle_editing();
            }
            this.plan = plan;
            this.selected_batch = null;
            this.renderElement();
            this.check_empty_plan();
            $("span[name=amt_0]").text('#' + this.pos.db.reservation_amt);
            for (var p = 0; p < this.pos.plans.length; p++) {
                var pid = this.pos.plans[p].id;
                if (pid > 0) {
                    $("span[name=amt_" + pid + "]").text('#' + this.pos.db.pos_amt);
                }
            }
        }
    },
    background_image_url: function(plan) {
        return '/web/image?model=restaurant.plan&id='+plan.id+'&field=background_image';
    },
    get_plan_style: function() {
        var style = "";
        if (this.plan.background_image) {
            style += "background-image: url(" + this.background_image_url(this.plan) + "); ";
        }
        if (this.plan.background_color) {
            style += "background-color: " + _.escape(this.plan.background_color) + ";";
        }
        return style;
    },
    set_background_color: function(background) {
        var self = this;
        this.plan.background_color = background;
        (new Model('restaurant.plan'))
            .call('write',[[this.plan.id], {'background_color': background}]).fail(function(err, event){
                self.gui.show_popup('error',{
                    'title':_t('Changes could not be saved'),
                    'body': _t('You must be connected to the internet to save your changes.')
                });
                event.stopPropagation();
                event.preventDefault();
            });
        this.$('.plan-map').css({"background-color": _.escape(background)});
    },
    check_empty_plan: function(){
        if (!this.plan.batches.length && this.plan.id != 0) {
//            if (!this.editing) {
//                this.toggle_editing();
//            }
            this.$('.empty-plan').removeClass('oe_hidden');
        } else {
            this.$('.empty-plan').addClass('oe_hidden');
        }
    },
    perform_search: function(query, associate_result){
        this.reservation_widget.render_list(this.pos.db.search_order_line(query));
    },
    clear_search: function(){
        var customers = this.pos.db.get_partners_sorted(1000);
        this.reservation_widget.render_list(this.pos.db.reservations);
        this.$('.keywordbox input')[0].value = '';
        this.$('.keywordbox input').focus();
    },
    renderElement: function(){
        var self = this;
        var batch_widgets = [];
        if (self.plan_batch_widgets[self.plan.id]) {
            batch_widgets = self.plan_batch_widgets[self.plan.id];
        } else {
            self.plan_batch_widgets[self.plan.id] = batch_widgets;
        }
        // cleanup batch widgets from previous renders
        for (var i = 0; i < batch_widgets.length; i++) {
            batch_widgets[i].destroy();
        }
        if (this.reservation_widget)
            this.reservation_widget.destroy();

        this._super();

        for (var i = 0; i < this.plan.batches.length; i++) {
            var tw = new BatchWidget(this,{
                batch: this.plan.batches[i],
            });
            tw.appendTo(this.$('.plan-map .batches'));
            batch_widgets.push(tw);
        }
        if (this.plan.id == 0) {
            var rw = new ReservationWidget(this,{});
            this.reservation_widget = rw;
            rw.appendTo(this.$('.plan-map .batches'));
            rw.render_list(this.pos.db.reservations);
        }


        this.$('.plan-selector .button').click(function(event){
            self.click_plan_button(event,$(this));
        });

        this.$('.plan-map,.plan-map .batches').click(function(event){
            if (event.target === self.$('.plan-map')[0] ||
                event.target === self.$('.plan-map .batches')[0]) {
//                self.deselect_batches();
            }
        });

        this.$('.keywordbox input').on('keyup',function(event){
            clearTimeout(search_timeout);

            var query = this.value;

            var search_timeout = setTimeout(function(){
                self.perform_search(query);
            },70);
        });

        this.$('.keywordbox input').click(function(){
            self.clear_search();
        });

    }
});

gui.define_screen({
    'name': 'plan',
    'widget': PlanScreenWidget,
    'condition': function(){
        return this.pos.config.iface_schedule;
    }
});

// Add the PlanScreen to the GUI, and set it as the default screen
chrome.Chrome.include({
    build_widgets: function(){
        this._super();
        if (this.pos.config.iface_schedule) {
            this.gui.set_startup_screen('plan');
        }
    },
});




// New orders are now associated with the current batch, if any.
var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
    initialize: function() {
        _super_order.initialize.apply(this,arguments);
        if (!this.batch) {
            this.batch = this.pos.batch;
        }
        this.booking_batch = false;
        this.booking_start = undefined;
        this.booking_end = undefined;
        this.batch_info = false;

        this.save_to_db();
    },
    init_from_JSON: function(json) {
        _super_order.init_from_JSON.apply(this,arguments);
        this.batch = this.pos.db.batches_by_id[json.batch_id];
        this.plan = this.batch ? this.pos.plans_by_id[json.plan_id] : undefined;
//        this.customer_count = json.customer_count || 1;
    },
    export_as_JSON: function() {
        var json = _super_order.export_as_JSON.apply(this,arguments);
        this.booking_batch = json.booking_batch = this.batch ? this.batch.booking_batch : false;
        this.booking_start = json.booking_start = this.batch ? this.batch.booking_start : undefined;
        this.booking_end = json.booking_end = this.batch ? this.batch.booking_end : undefined;
        this.batch_info = json.batch_info = this.batch ? this.batch.batch_info : false;
        this.origin = json.origin = this.pos.reservation ? this.pos.reservation.number : null;
        this.ticket = json.ticket = this.pos.ticket ? this.pos.ticket : '';

        // console.log("order=> export_as_JSON:" + JSON.stringify(json));
        return json;
    },
});

var _super_order_line = models.Orderline.prototype;
models.Orderline = models.Orderline.extend({
    initialize: function() {
        _super_order_line.initialize.apply(this, arguments);
        this.booking_batch = false;
        this.booking_start = undefined;
        this.booking_end = undefined;
        this.batch_info = false;
        this.ticket = '';
    },
    export_as_JSON: function() {
        var json = _super_order_line.export_as_JSON.apply(this,arguments);
        this.booking_batch = json.booking_batch = this.order.booking_batch;
        this.booking_start = json.booking_start = this.order.booking_start;
        this.booking_end = json.booking_end = this.order.booking_end;
        this.batch_info = json.batch_info = this.order.batch_info;
        this.origin = json.origin = this.pos.reservation ? this.pos.reservation.number : null;
        // this.ticket = json.ticket = this.pos.ticket ? this.pos.ticket : '';
        json.ticket = this.get_ticket(json);

       // console.log("order line => export_as_JSON:" + JSON.stringify(json));
        return json;
    },
    export_for_printing: function() {
        var json = _super_order_line.export_for_printing.apply(this,arguments);
        json.booking_batch = this.booking_batch;
        json.booking_start = this.booking_start;
        json.booking_end = this.booking_end;
        json.batch_info = this.batch_info;
        json.origin = this.origin;
        json.ticket = this.ticket;

       // console.log("order line => export_for_printing:" + JSON.stringify(json));
        return json;
    },
    set_ticket: function(ticket){
        this.ticket = ticket;
    },
    get_ticket: function(json){
        if(this.ticket == ''){
            // console.log(this.order.ticket);
            this.ticket = SHA512(this.order.pos_session_id + "cenoq" + this.order.uid + "BizNavi" + json.product_id);
        }
        return this.ticket;
    },
});


// We need to modify the OrderSelector to hide itself when we're on
// the schedule
chrome.OrderSelectorWidget.include({
    plan_button_click_handler: function(){
        this.pos.set_batch(null);
    },
    hide: function(){
        this.$el.addClass('oe_invisible');
    },
    show: function(){
        this.$el.removeClass('oe_invisible');
    },
    renderElement: function(){
        var self = this;
        this._super();
        if (this.pos.config.iface_schedule) {
            if (this.pos.get_order()) {
                if (this.pos.batch && this.pos.batch.plan) {
                    this.$('.orders').prepend(QWeb.render('BackToPlanButton',{batch: this.pos.batch, plan:this.pos.batch.plan}));
                    this.$('.plan-button').click(function(){
                        self.plan_button_click_handler();
                    });
                }
                this.$el.removeClass('oe_invisible');
            } else {
                this.$el.addClass('oe_invisible');
            }
        }
    },
});

// We need to change the way the regular UI sees the orders, it
// needs to only see the orders associated with the current batch,
// and when an order is validated, it needs to go back to the plan map.
//
// And when we change the batch, we must create an order for that batch
// if there is none.
var _super_posmodel = models.PosModel.prototype;
var updating = false;
models.PosModel = models.PosModel.extend({
    initialize: function(session, attributes) {
        this.batch = null;
        return _super_posmodel.initialize.call(this,session,attributes);
    },

    transfer_order_to_different_batch: function () {
        this.order_to_transfer_to_different_batch = this.get_order();

        // go to 'plans' screen, this will set the order to null and
        // eventually this will cause the gui to go to its
        // default_screen, which is 'plans'
        this.set_batch(null);
    },

    // reload the list of order_line, returns as a deferred that resolves if there were
    // updated orders, and fails if not
    reload_sale_order_lines: function(plan_widget){
        var self = this;
        var def  = new $.Deferred();
        var fields = _.find(this.models,function(model){ return model.model === 'sale.order.line'; }).fields;
        var batch_widgets = plan_widget.plan_batch_widgets[plan_widget.plan.id];
        // console.log(self.db.checkpoint);
        // new Model('pos.order').call('pos_sync', [self.config.id]).then(function(to_sync) {
            // if(to_sync) {
            if(!updating) {
                updating = true;
                try {
                    new Model('sale.order.line')
                        .query(fields)
                        .filter([['booking_start','>=',todayStr(true)],['booking_end','<',todayStr(false)],['state','in',['sale','sent']],['write_date','>',self.db.checkpoint]])
                        .all({'timeout':60000, 'shadow': true})
                        .then(function(order_lines){
                            // console.log(order_lines);
                            self.db.add_order_lines(order_lines);
                            for (var i = 0; i < batch_widgets.length; i++) {
                                var count = self.db.count_by_batch[plan_widget.plan.id + '|' + batch_widgets[i].batch.booking_batch];
                                var seats = self.max_seats[plan_widget.plan.id] - ((count)?count:0);
                                batch_widgets[i].set_batch_seats(seats);
                                if (batch_widgets[i].batch.color != 'pink') {
                                    if (batch_widgets[i].batch.booking_end < new Date() || seats <= 0) {
                                        batch_widgets[i].set_batch_color("gray");
                                    } else {
                                        batch_widgets[i].set_batch_color("");
                                    }
                                }
                            }
                            $("span[name=amt_0]").text('#' + self.db.reservation_amt);
                            for (var p = 0; p < plan_widget.pos.plans.length; p++) {
                                var pid = plan_widget.pos.plans[p].id;
                                if (pid > 0) {
                                    $("span[name=amt_" + pid + "]").text('#' + self.db.pos_amt);
                                }
                            }
                            updating = false;
                        }, function(err,event){
                            event.preventDefault();
                            def.reject();
                            updating = false;
                        });
                } catch(err) {
                    console.log(err);
                    updating = false;
                }
            }
            // } else {
            //     for (var i =0; i < batch_widgets.length; i++) {
            //         var count = self.db.count_by_batch[plan_widget.plan.id + '|' + batch_widgets[i].batch.booking_batch];
            //         var seats = self.max_seats[plan_widget.plan.id] - ((count)?count:0);
            //         batch_widgets[i].set_batch_seats(seats);
            //         if (batch_widgets[i].batch.booking_end < new Date() || seats <= 0) {
            //             batch_widgets[i].set_batch_color("gray");
            //         } else {
            //             batch_widgets[i].set_batch_color("");
            //         }
            //     }
            // }
        // });
        return def;
    },


    // changes the current batch.
    set_batch: function(batch) {
        if (!batch) { // no batch ? go back to the schedule, see ScreenSelector
            this.set_order(null);
        } else if (this.order_to_transfer_to_different_batch) {
            this.order_to_transfer_to_different_batch.batch = batch;
            this.order_to_transfer_to_different_batch.save_to_db();
            this.order_to_transfer_to_different_batch = null;

            // set this batch
            this.set_batch(batch);

        } else {
            this.batch = batch;
            var orders = this.get_order_list();
            if (orders.length) {
                for (var i = 0; i < orders.length; i++) {
                    orders[i].destroy();
                }
            }
            // this.delete_current_order();
            this.add_new_order();
            // var orders = this.get_order_list();
            // if (orders.length) {
            //     this.set_order(orders[0]); // and go to the first one ...
            // } else {
            //     this.add_new_order();  // or create a new order with the current batch
            // }
        }
    },

    // if we have batches, we do not load a default order, as the default order will be
    // set when the user selects a batch.
    set_start_order: function() {
        if (!this.config.iface_schedule) {
            _super_posmodel.set_start_order.apply(this,arguments);
        }
    },

    // we need to prevent the creation of orders when there is no
    // batch selected.
    add_new_order: function() {
        if (this.config.iface_schedule) {
            if (this.batch) {
                _super_posmodel.add_new_order.call(this);
            } else {
                console.warn("WARNING: orders cannot be created when there is no active batch in restaurant mode");
            }
        } else {
            _super_posmodel.add_new_order.apply(this,arguments);
        }
    },


    // get the list of unpaid orders (associated to the current batch)
    get_order_list: function() {
        var orders = _super_posmodel.get_order_list.call(this);
        if (!this.config.iface_schedule) {
            return orders;
        } else if (!this.batch) {
            return [];
        } else {
            var t_orders = [];
            for (var i = 0; i < orders.length; i++) {
                if ( orders[i].batch === this.batch) {
                    t_orders.push(orders[i]);
                }
            }
            return t_orders;
        }
    },

    // get the list of orders associated to a batch. FIXME: should be O(1)
    get_batch_orders: function(batch) {
        var orders   = _super_posmodel.get_order_list.call(this);
        var t_orders = [];
        for (var i = 0; i < orders.length; i++) {
//            if (orders[i].batch === batch) {
                t_orders.push(orders[i]);
//            }
        }
        return t_orders;
    },

    // get customer count at batch
    get_customer_count: function(batch) {
        var orders = this.get_batch_orders(batch);
        var count  = 0;
        for (var i = 0; i < orders.length; i++) {
            count += orders[i].get_customer_count();
        }
        return count;
    },

    // When we validate an order we go back to the schedule.
    // When we cancel an order and there is multiple orders
    // on the batch, stay on the batch.
    on_removed_order: function(removed_order,index,reason){
        if (this.config.iface_schedule) {
            var order_list = this.get_order_list();
            if( (reason === 'abandon' || removed_order.temporary) && order_list.length > 0){
                this.set_order(order_list[index] || order_list[order_list.length -1]);
            }else{
                // back to the schedule
                this.set_batch(null);
            }
        } else {
            _super_posmodel.on_removed_order.apply(this,arguments);
        }
    }


});


screens.OrderWidget.include({
    update_summary: function(){
        this._super();
        if (this.getParent().action_buttons &&
            this.getParent().action_buttons.guests) {
            this.getParent().action_buttons.guests.renderElement();
        }
    },
});

screens.ProductScreenWidget.include({
    start: function(){
        this._super();
        this.pos.product_list_widget = this.product_list_widget;
    },
});

var TransferOrderButton = screens.ActionButtonWidget.extend({
    template: 'TransferOrderButton',
    button_click: function() {
        this.pos.transfer_order_to_different_batch();
    },
});

screens.define_action_button({
    'name': 'transfer',
    'widget': TransferOrderButton,
    'condition': function(){
        return this.pos.config.iface_schedule;
    },
});

function SHA512(r){function e(r,e){this.highOrder=r,this.lowOrder=e}function n(r,n){var w,h,d,O;return w=(65535&r.lowOrder)+(65535&n.lowOrder),h=(r.lowOrder>>>16)+(n.lowOrder>>>16)+(w>>>16),d=(65535&h)<<16|65535&w,w=(65535&r.highOrder)+(65535&n.highOrder)+(h>>>16),h=(r.highOrder>>>16)+(n.highOrder>>>16)+(w>>>16),O=(65535&h)<<16|65535&w,new e(O,d)}function w(r,n){return n<=32?new e(r.highOrder>>>n|r.lowOrder<<32-n,r.lowOrder>>>n|r.highOrder<<32-n):new e(r.lowOrder>>>n|r.highOrder<<32-n,r.highOrder>>>n|r.lowOrder<<32-n)}function h(r,n){return n<=32?new e(r.highOrder>>>n,r.lowOrder>>>n|r.highOrder<<32-n):new e(0,r.highOrder<<32-n)}var d,O,o,i,g,l,t,u,c,f,a=[new e(1779033703,4089235720),new e(3144134277,2227873595),new e(1013904242,4271175723),new e(2773480762,1595750129),new e(1359893119,2917565137),new e(2600822924,725511199),new e(528734635,4215389547),new e(1541459225,327033209)],v=[new e(1116352408,3609767458),new e(1899447441,602891725),new e(3049323471,3964484399),new e(3921009573,2173295548),new e(961987163,4081628472),new e(1508970993,3053834265),new e(2453635748,2937671579),new e(2870763221,3664609560),new e(3624381080,2734883394),new e(310598401,1164996542),new e(607225278,1323610764),new e(1426881987,3590304994),new e(1925078388,4068182383),new e(2162078206,991336113),new e(2614888103,633803317),new e(3248222580,3479774868),new e(3835390401,2666613458),new e(4022224774,944711139),new e(264347078,2341262773),new e(604807628,2007800933),new e(770255983,1495990901),new e(1249150122,1856431235),new e(1555081692,3175218132),new e(1996064986,2198950837),new e(2554220882,3999719339),new e(2821834349,766784016),new e(2952996808,2566594879),new e(3210313671,3203337956),new e(3336571891,1034457026),new e(3584528711,2466948901),new e(113926993,3758326383),new e(338241895,168717936),new e(666307205,1188179964),new e(773529912,1546045734),new e(1294757372,1522805485),new e(1396182291,2643833823),new e(1695183700,2343527390),new e(1986661051,1014477480),new e(2177026350,1206759142),new e(2456956037,344077627),new e(2730485921,1290863460),new e(2820302411,3158454273),new e(3259730800,3505952657),new e(3345764771,106217008),new e(3516065817,3606008344),new e(3600352804,1432725776),new e(4094571909,1467031594),new e(275423344,851169720),new e(430227734,3100823752),new e(506948616,1363258195),new e(659060556,3750685593),new e(883997877,3785050280),new e(958139571,3318307427),new e(1322822218,3812723403),new e(1537002063,2003034995),new e(1747873779,3602036899),new e(1955562222,1575990012),new e(2024104815,1125592928),new e(2227730452,2716904306),new e(2361852424,442776044),new e(2428436474,593698344),new e(2756734187,3733110249),new e(3204031479,2999351573),new e(3329325298,3815920427),new e(3391569614,3928383900),new e(3515267271,566280711),new e(3940187606,3454069534),new e(4118630271,4000239992),new e(116418474,1914138554),new e(174292421,2731055270),new e(289380356,3203993006),new e(460393269,320620315),new e(685471733,587496836),new e(852142971,1086792851),new e(1017036298,365543100),new e(1126000580,2618297676),new e(1288033470,3409855158),new e(1501505948,4234509866),new e(1607167915,987167468),new e(1816402316,1246189591)],s=new Array(64),A=8,p=(r=function(r){return unescape(encodeURIComponent(r))}(r)).length*A;(r=function(r){for(var e=[],n=(1<<A)-1,w=r.length*A,h=0;h<w;h+=A)e[h>>5]|=(r.charCodeAt(h/A)&n)<<32-A-h%32;return e}(r))[p>>5]|=128<<24-p%32,r[31+(p+128>>10<<5)]=p;for(m=0;m<r.length;m+=32){d=a[0],O=a[1],o=a[2],i=a[3],g=a[4],l=a[5],t=a[6],u=a[7];for(var b=0;b<80;b++)s[b]=b<16?new e(r[2*b+m],r[2*b+m+1]):function(r,n,w,h){var d,O,o,i;return d=(65535&r.lowOrder)+(65535&n.lowOrder)+(65535&w.lowOrder)+(65535&h.lowOrder),O=(r.lowOrder>>>16)+(n.lowOrder>>>16)+(w.lowOrder>>>16)+(h.lowOrder>>>16)+(d>>>16),o=(65535&O)<<16|65535&d,d=(65535&r.highOrder)+(65535&n.highOrder)+(65535&w.highOrder)+(65535&h.highOrder)+(O>>>16),O=(r.highOrder>>>16)+(n.highOrder>>>16)+(w.highOrder>>>16)+(h.highOrder>>>16)+(d>>>16),i=(65535&O)<<16|65535&d,new e(i,o)}(function(r){var n=w(r,19),d=w(r,61),O=h(r,6);return new e(n.highOrder^d.highOrder^O.highOrder,n.lowOrder^d.lowOrder^O.lowOrder)}(s[b-2]),s[b-7],function(r){var n=w(r,1),d=w(r,8),O=h(r,7);return new e(n.highOrder^d.highOrder^O.highOrder,n.lowOrder^d.lowOrder^O.lowOrder)}(s[b-15]),s[b-16]),c=function(r,n,w,h,d){var O,o,i,g;return O=(65535&r.lowOrder)+(65535&n.lowOrder)+(65535&w.lowOrder)+(65535&h.lowOrder)+(65535&d.lowOrder),o=(r.lowOrder>>>16)+(n.lowOrder>>>16)+(w.lowOrder>>>16)+(h.lowOrder>>>16)+(d.lowOrder>>>16)+(O>>>16),i=(65535&o)<<16|65535&O,O=(65535&r.highOrder)+(65535&n.highOrder)+(65535&w.highOrder)+(65535&h.highOrder)+(65535&d.highOrder)+(o>>>16),o=(r.highOrder>>>16)+(n.highOrder>>>16)+(w.highOrder>>>16)+(h.highOrder>>>16)+(d.highOrder>>>16)+(O>>>16),g=(65535&o)<<16|65535&O,new e(g,i)}(u,function(r){var n=w(r,14),h=w(r,18),d=w(r,41);return new e(n.highOrder^h.highOrder^d.highOrder,n.lowOrder^h.lowOrder^d.lowOrder)}(g),function(r,n,w){return new e(r.highOrder&n.highOrder^~r.highOrder&w.highOrder,r.lowOrder&n.lowOrder^~r.lowOrder&w.lowOrder)}(g,l,t),v[b],s[b]),f=n(function(r){var n=w(r,28),h=w(r,34),d=w(r,39);return new e(n.highOrder^h.highOrder^d.highOrder,n.lowOrder^h.lowOrder^d.lowOrder)}(d),function(r,n,w){return new e(r.highOrder&n.highOrder^r.highOrder&w.highOrder^n.highOrder&w.highOrder,r.lowOrder&n.lowOrder^r.lowOrder&w.lowOrder^n.lowOrder&w.lowOrder)}(d,O,o)),u=t,t=l,l=g,g=n(i,c),i=o,o=O,O=d,d=n(c,f);a[0]=n(d,a[0]),a[1]=n(O,a[1]),a[2]=n(o,a[2]),a[3]=n(i,a[3]),a[4]=n(g,a[4]),a[5]=n(l,a[5]),a[6]=n(t,a[6]),a[7]=n(u,a[7])}for(var C=[],m=0;m<a.length;m++)C.push(a[m].highOrder),C.push(a[m].lowOrder);return function(r){for(var e,n="",w=4*r.length,h=0;h<w;h+=1)e=r[h>>2]>>8*(3-h%4),n+="0123456789abcdef".charAt(e>>4&15)+"0123456789abcdef".charAt(15&e);return n}(C)}

});
