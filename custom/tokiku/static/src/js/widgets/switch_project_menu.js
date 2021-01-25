odoo.define('web.SwitchProjectMenu', function(require) {
"use strict";

var Model = require('web.Model');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');
var core = require('web.core');
var _t = core._t;

var SwitchProjectMenu = Widget.extend({
    template: 'SwitchProjectMenu',
    willStart: function() {
        if (!session.user_projects) {
            return $.Deferred().reject();
        }
        return this._super();
    },
    start: function() {
        var self = this;
        this.$el.on('click', '.dropdown-menu li a[data-menu]', _.debounce(function(ev) {
            ev.preventDefault();
            var project_id = $(ev.currentTarget).data('project-id');
            new Model('res.users').call('write', [[session.uid], {'project_id': project_id}]).then(function() {
                // location.reload();
                location.replace('/web');
            });
        }, 1500, true));

        self.$('.oe_topbar_project').text(_t('Project: ') + session.user_projects.current_project[1]);

        var projects_list = '';
        _.each(session.user_projects.allowed_projects, function(project) {
            var a = '';
            if (project[0] === session.user_projects.current_project[0]) {
                a = '<i class="fa fa-check o_current_project"></i>';
            } else {
                a = '<span class="o_project"/>';
            }
            projects_list += '<li><a href="#" data-menu="project" data-project-id="' + project[0] + '">' + a + project[1] + '</a></li>';
        });
        self.$('.dropdown-menu').html(projects_list);
        return this._super();
    },
});

var SwitchContractMenu = Widget.extend({
    template: 'SwitchContractMenu',
    willStart: function() {
        if (!session.user_contracts) {
            return $.Deferred().reject();
        }
        return this._super();
    },
    start: function() {
        var self = this;
        this.$el.on('click', '.dropdown-menu li a[data-menu]', _.debounce(function(ev) {
            ev.preventDefault();
            var contract_id = $(ev.currentTarget).data('contract-id');
            new Model('res.users').call('write', [[session.uid], {'contract_id': contract_id}]).then(function() {
                // location.reload();
                location.replace('/web');
            });
        }, 1500, true));

        self.$('.oe_topbar_contract').text(_t('Contract: ') + session.user_contracts.current_contract[1]);

        var contracts_list = '';
        _.each(session.user_contracts.allowed_contracts, function(contract) {
            var a = '';
            if (contract[0] === session.user_contracts.current_contract[0]) {
                a = '<i class="fa fa-check o_current_contract"></i>';
            } else {
                a = '<span class="o_contract"/>';
            }
            contracts_list += '<li><a href="#" data-menu="contract" data-contract-id="' + contract[0] + '">' + a + contract[1] + '</a></li>';
        });
        self.$('.dropdown-menu').html(contracts_list);
        return this._super();
    },
});

SystrayMenu.Items.push(SwitchContractMenu);
SystrayMenu.Items.push(SwitchProjectMenu);

});
