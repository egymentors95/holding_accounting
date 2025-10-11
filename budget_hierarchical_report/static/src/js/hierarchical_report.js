odoo.define('budget_hierarchical_report.hierarchical_chart', function (require) {
    "use strict";


    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var Widget = require('web.Widget');
    var QWeb = core.qweb;
    var _t = core._t;

    var hierarchicalChart =  AbstractAction.extend({
        hasControlPanel: true,
        template: "budget_hierarchical_report.hierarchical_chart_temp",
        init: function (parent, params) {
            this._super(parent, params);
            this.params = params;
        },

        start: function () {
            var self = this;
            var call_data = {
                model: 'crossovered.budget.lines',
                method: "hierarchical_chart_details",
                args: [this.params['context']['model']],
            }
            rpc.query(call_data)
                .then(function (result) {
                    self.chart_data = result
                    $('.account_chart_list').html(QWeb.render('budget_hierarchical_report.chartList', { widget: self }));
                    $('#basic').simpleTreeTable({
                        expander: $('#expander'),
                        collapser: $('#collapser')
                    });

                    var supportsPdfMimeType = typeof navigator.mimeTypes["application/pdf"] !== "undefined"
                    var isIE = function () {
                        return !!(window.ActiveXObject || "ActiveXObject" in window)
                    }
                    var supportsPdfActiveX = function () {
                        return !!(createAXO("AcroPDF.PDF") || createAXO("PDF.PdfCtrl"))
                    }
                    var supportsPDFs = supportsPdfMimeType || isIE() && supportsPdfActiveX();

                    if (supportsPDFs) {
                        $('#basic').DataTable({
                            dom: 'Bfrtip',
                            paging: false,
                            "ordering": false,
                            "searching": false,
                            "autoWidth": false,
                            "language": {
                                "info": "Showing _MAX_ enteries",
                            },
                            buttons: [
                                'copyHtml5',
                                'excelHtml5',
                                'csvHtml5',
                                {
                                    extend: 'print',
                                    text: 'PDF',
                                },
                                'colvis',
                            ]
                        });
                    }
                    else {
                        $('#basic').DataTable({
                            dom: 'Bfrtip',
                            paging: false,
                            "ordering": false,
                            "searching": false,
                            "autoWidth": false,
                            "language": {
                                "info": "Showing _MAX_ enteries",
                            },
                            buttons: [
                                'copyHtml5',
                                'excelHtml5',
                                'csvHtml5',
                            ]
                        });
                    }
                });
            return this._super();
        },
    });

    core.action_registry.add('budget_hierarchical_report.hierarchical_chart', hierarchicalChart);


    return hierarchicalChart;

});