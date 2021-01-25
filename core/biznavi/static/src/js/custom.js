openerp.biznavi = function(instance, local) {
    instance.web.WebClient.include({
        init: function(parent, client_options) {
            this._super(parent, client_options);
            this.set('title_part', {"odoo": "BizNavi"});
        },
        set_title: function(title) {
             title = _.str.clean(title);
             var sep = _.isEmpty(title) ? '' : ' - ';
             document.title = title + sep + 'BizNavi';
        },
        show_announcement_bar: function() {
            return;
        }
    });
}


odoo.define('biznavi.shelf', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.DataModel');
var ListView = require('web.ListView');

var QWeb = core.qweb;
var _t = core._t;


var ShelfListView = ListView.extend({

    render_buttons: function ($node) {
		var self = this;
        self._super($node);
        if(self.$buttons.length==0){
            self.$buttons = $('<div class="oe_list_buttons"></div>');
        }
		var Inst = new Model(self.dataset.model);
        Inst.call("shelf_buttons",[self.dataset.context.tender_id,self.dataset.context]).fail(function(unused, e){
                e.preventDefault();
                return;
            }).then(function(result) {
				for(var i in result){
					var s = (result[i]['style'])?result[i]['style']:'btn-default';
					var name = (result[i]['name'])?result[i]['name']:'Extra';
					var button = $('<button type="button" class="btn btn-sm '+s+' o_list_'+result[i]['method']+'">'+name+'</button>');
	                self.$buttons.append(button);
	                self.$buttons.append("&nbsp;");
					button.bind('click', {func: result[i]['method']}, function(e) {
				        Inst.call(e.data.func,[self.dataset.context.tender_id,self.dataset.context]).then(function(result) {
				            if(result){
					            self.do_action(result, {
                                    on_close: function() {
                                        self.reload();
                                    }
				                });
				            }
				            else{
				                self.reload();
				            }
						});
					});
				}
        });
        $node = $node || self.options.$buttons;
        if ($node) {
            self.$buttons.appendTo($node);
        } else{
            self.$('.oe_list_buttons').replaceWith(self.$buttons);
        }
    }
});

core.view_registry.add('shelf', ShelfListView);

});


