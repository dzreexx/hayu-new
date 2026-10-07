odoo.define('fky_paket_sales.ListRefreshButton', function (require) {
    'use strict';

    var core = require('web.core');
    var ListController = require('web.ListController');

    var _t = core._t;

    ListController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.modelName === 'fky.paket.sales' && this.$buttons) {
                var self = this;
                var $refreshBtn = $('<button>', {
                    type: 'button',
                    class: 'btn btn-secondary o_list_button_refresh_all',
                    text: _t('Refresh All Progress'),
                });
                $refreshBtn.on('click', function () {
                    self._rpc({
                        model: 'fky.paket.sales',
                        method: 'refresh_all_progress',
                        args: [],
                    }).then(function (action) {
                        self.reload();
                        if (action) {
                            self.do_action(action);
                        }
                    });
                });
                this.$buttons.append($refreshBtn);
            }
        },
    });
});
