odoo.define('pos_ticket.devices', function (require) {
"use strict";

var core = require('web.core');
var devices = require("point_of_sale.devices");
var Model = require('web.DataModel');
var QWeb = core.qweb;

devices.ProxyDevice = devices.ProxyDevice.extend({
        print_sale_details: function() {
            var self = this;
            new Model('report.point_of_sale.report_saledetails').call('get_sale_details_by_config', [self.pos.config.id]).then(function(result){
                var env = {
                    company: self.pos.company,
                    pos: self.pos,
                    products: result.products,
                    payments: result.payments,
                    taxes: result.taxes,
                    total_paid: result.total_paid,
                    date: (new Date()).toLocaleString(),
                };
                var report = QWeb.render('SaleDetailsReport', env);
                self.print_receipt(report);
            })
        }
    });
});

