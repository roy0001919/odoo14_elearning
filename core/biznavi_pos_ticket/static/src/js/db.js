odoo.define('pos_ticket.DB', function (require) {

    "use strict";

    var DB = require("point_of_sale.DB");

    DB.include({
        init: function (options) {
            this._super(options);
            this.product_tmpl_by_id = {};
        },
        search_order_line: function (query) {
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.');
                query = query.replace(' ', '.+');
                var re = RegExp("([0-9]+):.*?" + query, "gi");
            } catch (e) {
                return [];
            }
            var results = [];
            for (var i = 0; i < 100; i++) {
                var r = re.exec(this.reservation_search_string);
                if (r) {
                    var id = Number(r[1]);
                    results.push(this.reservation_by_id[id]);
                } else {
                    break;
                }
            }
            return results;
        },
        get_product_tmpl_by_id: function (id) {
            return this.product_tmpl_by_id[id];
        },
        add_order_lines: function (order_lines) {
            if (!this.order_lines) {
                this.order_lines = [];
                this.reservations = [];
                this.count_by_batch = {};
                this.reservation_by_id = {};
                this.reservation_search_string = "";
                this.reservation_amt = 0;
                this.pos_amt = 0;
            }

            var taken_orders = [];
            for (var i = 0; i < order_lines.length; i++) {
                if (order_lines[i].origin) {
                    taken_orders.push(order_lines[i].origin);
                }
            }
            var line_no = {};
            for (var i = 0; i < order_lines.length; i++) {
                if(this.get_product_by_id(order_lines[i].product_id[0])) {
                    var old_lines = this.order_lines.filter(function(line){ return line.id == order_lines[i].id });
                    var old_line = (old_lines.length>0)?old_lines[0]:null;
                    if (old_line > 0) {
                        this.order_lines = this.order_lines.filter(function(line){ return line.id != order_lines[i].id });
                    }
                    var product_tmpl_id = this.get_product_tmpl_by_id(this.get_product_by_id(order_lines[i].product_id[0]).product_tmpl_id);
                    var batch_id = product_tmpl_id.resource_ids[0] + '|' + order_lines[i].booking_batch;
                    if (order_lines[i].state == 'sale' || (order_lines[i].state == 'sent' && (taken_orders.indexOf(order_lines[i].order_id[1]) < 0))) {
                        if (this.count_by_batch[batch_id]) {
                            this.count_by_batch[batch_id] -= (old_line)?old_line.product_uom_qty:0;
                            this.count_by_batch[batch_id] += order_lines[i].product_uom_qty;
                        } else {
                            this.count_by_batch[batch_id] = order_lines[i].product_uom_qty;
                        }
                    }

                    if (order_lines[i].state == 'sale') {
                        this.order_lines.push(order_lines[i]);
                    }
                    if (order_lines[i].state == 'sent' && !product_tmpl_id.pay_online) {
                        var reservation = order_lines[i];
                        reservation.number = reservation.order_id[1];
                        var ns = reservation.name.indexOf("(");
                        var ne = reservation.name.indexOf(")");
                        reservation.ticket = (ns > 0 && ne > 0) ? reservation.name.substring(ns + 1, ne - 1) : reservation.name;
                        this.reservations.push(reservation);
                        this.reservation_by_id[order_lines[i].id] = order_lines[i];
                        this.reservation_search_string += this._reservation_search_string(order_lines[i]);
                    }
                    if (order_lines[i].state == 'sale' && product_tmpl_id.pay_online) {
                        if(!order_lines[i].salesman_id) {
                            var reservation = order_lines[i];
                            var reserv = this.reservations.filter(function(line){ return line.id == reservation.id });
                            if (reserv.length ==0) {
                                reservation.pay_online = true;
                                reservation.number = reservation.sale_order_name;
                                var ns = reservation.name.indexOf("(");
                                var ne = reservation.name.indexOf(")");
                                reservation.ticket_name = (ns > 0 && ne > 0) ? reservation.name.substring(ns + 1, ne - 1) : reservation.name;
                                this.reservations.push(reservation);
                                this.reservation_by_id[order_lines[i].id] = order_lines[i];
                                this.reservation_search_string += this._reservation_search_string(order_lines[i]);
                                this.reservation_amt -= (old_line)?old_line.product_uom_qty:0;
                                this.reservation_amt += order_lines[i].product_uom_qty;
                            }
                        } else{
                            this.pos_amt -= (old_line)?old_line.product_uom_qty:0;
                            this.pos_amt += order_lines[i].product_uom_qty;
                        }
                    }
                    if (!this.checkpoint || (this.checkpoint && order_lines[i].write_date > this.checkpoint)) {
                        this.checkpoint = order_lines[i].write_date;
                    }
                }
            }
        },
        _reservation_search_string: function (order_line) {
            var str = order_line.order_id[1];
            if (order_line.sale_order_name) {
                str += '|' + order_line.sale_order_name;
            }
            if (order_line.buyer) {
                str += '|' + order_line.buyer;
            }
            if (order_line.buyer_tel) {
                str += '|' + order_line.buyer_tel.split(' ').join('');
            }
            if (order_line.contact_usr) {
                str += '|' + order_line.contact_usr;
            }
            if (order_line.contact_tel) {
                str += '|' + order_line.contact_tel.split(' ').join('');
            }
            str = '' + order_line.id + ':' + str.replace(':', '') + '\n';
            return str;
        }
    });

    return DB;

});

