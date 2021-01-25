odoo.define('web_widget_grid.widget', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;
    var formats = require('web.formats');
    var FieldOne2Many = core.form_widget_registry.get('one2many');
    var Model = require('web.Model');
    var data = require('web.data');
    var $ = require('jquery');
    var utils = require('web.utils');

    var WidgetX2ManyGrid = FieldOne2Many.extend({
        template: 'FieldX2ManyGrid',
        widget_class: 'web_widget_grid',

        // those will be filled with rows from the dataset
        by_x_axis: {},
        by_y_axis: {},
        by_id: {},
        // configuration values
        // x: 'x',
        field_label_x_axis: 'x',
        y_axis: false,
        field_label_y_axis: 'y',
        field_value: 'value',
        x_axis_clickable: true,
        y_axis_clickable: true,
        // information about our datatype
        is_numeric: false,
        show_row_totals: true,
        show_column_totals: true,
        // this will be filled with the model's fields_get
        fields: {},
        // Store fields used to fill HTML attributes
        fields_att: {},

        parse_boolean: function (val) {
            if (val.toLowerCase() === 'true' || val === '1') {
                return true;
            }
            return false;
        },

        // read parameters
        init: function (field_manager, node) {
            // this.x = node.attrs.x || this.x;
            // if(this.x.slice(-1) == '*')this.x=this.x.slice(0,-1);
            this.y_axis = node.attrs.y_axis || this.y_axis;
            // this.field_label_x_axis = node.attrs.field_label_x_axis || this.x;
            this.field_label_y_axis = node.attrs.field_label_y_axis || this.y_axis;
            this.x_axis_clickable = this.parse_boolean(node.attrs.x_axis_clickable || '1');
            this.y_axis_clickable = this.parse_boolean(node.attrs.y_axis_clickable || '1');
            this.field_value = node.attrs.field_value || this.field_value;
            for (var property in node.attrs) {
                if (property.startsWith("field_att_")) {
                    this.fields_att[property.substring(10)] = node.attrs[property];
                }
            }
            this.field_editability = node.attrs.field_editability || this.field_editability;
            this.show_row_totals = this.parse_boolean(node.attrs.show_row_totals || '1');
            this.show_column_totals = this.parse_boolean(node.attrs.show_column_totals || '1');
            return this._super(field_manager, node);
        },

        get_locale_text: function () {
            return {
                // for filter panel
                page: _t('page'),
                more: _t('more'),
                to: _t('to'),
                of: _t('of'),
                next: _t('Next'),
                last: _t('Last'),
                first: _t('First'),
                previous: _t('Previous'),
                loadingOoo: _t('Loading...'),

                // for set filter
                selectAll: _t('Select All'),
                searchOoo: _t('Search...'),
                blanks: _t('blanks'),

                // for number filter and text filter
                filterOoo: _t('Filter...'),
                applyFilter: _t('Apply Filter...'),

                // for number filter
                equals: _t('Equals'),
                lessThan: _t('Less han'),
                greaterThan: _t('Greater Than'),

                // for text filter
                contains: _t('contains'),
                startsWith: _t('starts with'),
                endsWith: _t('ends with'),

                // the header of the default group column
                group: _t('Group'),

                // tool panel
                columns: _t('Columns'),
                rowGroupColumns: _t('Pivot Cols'),
                rowGroupColumnsEmptyMessage: _t('drag cols to group'),
                valueColumns: _t('Value Cols'),
                pivotMode: _t('Pivot-Mode'),
                groups: _t('Groups'),
                values: _t('Values'),
                pivots: _t('Pivots'),
                valueColumnsEmptyMessage: _t('drag cols to aggregate'),
                pivotColumnsEmptyMessage: _t('drag here to pivot'),

                // other
                noRowsToShow: _t('No rows to show'),

                // enterprise menu
                pinColumn: _t('Pin Column'),
                valueAggregation: _t('Value Aggregation'),
                autosizeThiscolumn: _t('Autosize This'),
                autosizeAllColumns: _t('Autosize All'),
                groupBy: _t('Group by'),
                ungroupBy: _t('UnGroup by'),
                resetColumns: _t('Reset Those Cols'),
                expandAll: _t('Expand All'),
                collapseAll: _t('Collapse All'),
                toolPanel: _t('Tool Panel'),
                export: _t('Export'),
                csvExport: _t('CSV Export'),
                excelExport: _t('Excel Export'),

                // enterprise menu pinning
                pinLeft: _t('Pin Left'),
                pinRight: _t('Pin Right'),
                noPin: _t('No Pin'),

                // enterprise menu aggregation and status panel
                sum: _t('Sum'),
                min: _t('Min'),
                max: _t('Max'),
                none: _t('None'),
                count: _t('Count'),
                average: _t('Average'),

                // standard menu
                copy: _t('Copy'),
                copyWithHeaders: _t('Copy With Headers'),
                ctrlC: _t('ctrl + C'),
                paste: _t('Paste'),
                ctrlV: _t('ctrl + V')
            }
        },

        // return a field's value, id in case it's a one2many field
        get_field_value: function (row, field, many2one_as_name) {
            if(this.fields[field]) {
                if (this.fields[field].type == 'many2one' && _.isArray(row[field])) {
                    if (many2one_as_name) {
                        return row[field][1];
                    }
                    else {
                        return row[field][0];
                    }
                } else if (this.fields[field].type == 'selection') {
                    var selections = this.fields[field].selection;
                    for (var s = 0; s < selections.length; s++) {
                        if (selections[s][0] === row[field]) {
                            if (many2one_as_name) {
                                return selections[s][1];
                            }
                            else {
                                return selections[s][0];
                            }
                        }
                    }
                }
            }
            return row[field];

        },

        // setup our datastructure for simple access in the template
        set_value: function (value_) {
            var self = this,
                result = this._super(value_);

            self.by_x_axis = {};
            self.by_y_axis = {};
            self.by_id = {};

            return $.when(result).then(function () {
                return self.dataset._model.call('fields_get').then(function (fields) {
                    self.fields = fields;
                    // console.log(self.field_value);
                    self.is_numeric = (fields[self.field_value] ? fields[self.field_value].type == 'float' : false);
                    self.show_row_totals &= self.is_numeric;
                    self.show_column_totals &= self.is_numeric;
                })
                // if there are cached writes on the parent dataset, read below
                // only returns the written data, which is not enough to properly
                // set up our data structure. Read those ids here and patch the
                // cache
                    .then(function () {
                        var ids_written = _.map(
                            self.dataset.to_write, function (x) {
                                return x.id
                            });
                        if (!ids_written.length) {
                            return;
                        }
                        return (new data.Query(self.dataset._model))
                            .filter([['id', 'in', ids_written]])
                            .all()
                            .then(function (rows) {
                                _.each(rows, function (row) {
                                    var cache = _.find(
                                        self.dataset.cache,
                                        function (x) {
                                            return x.id == row.id
                                        }
                                    );
                                    _.extend(cache.values, row, _.clone(cache.values));
                                })
                            })
                    })
                    .then(function () {
                        return self.dataset.read_ids(self.dataset.ids, self.fields).then(function (rows) {
                            // setup data structure
                            _.each(rows, function (row) {
                                if (self.y_axis) {
                                    var view_fields = self.field.views.tree.arch.children;
                                    for (var i in view_fields) {
                                        if (view_fields[i].attrs['x_axis']) {
                                            self.add_xy_row(row, view_fields[i].attrs['x_axis']);
                                        }
                                    }
                                } else {
                                    self.add_xy_row(row);
                                }
                            });
                            {
                                var view_fields = self.field.views.tree.arch.children;
                                var default_order = self.field.views.tree.arch.attrs['default_order'];
                                var sortKeys = [];
                                var sortDirs = [];
                                if(default_order) {
                                    var sortArr = default_order.split(',');
                                    for (var s = 0; s < sortArr.length; s ++) {
                                        sortKeys.push(sortArr[s].indexOf(' ') > 0 ? sortArr[s].split(' ')[0]:sortArr[s]);
                                        sortDirs.push(sortArr[s].indexOf(' ') > 0 ? sortArr[s].split(' ')[1]:'asc');
                                    }
                                }
                                // console.log(self.field.views.tree);
                                var columnDefs = [];
                                var xxColumnDefs = {};
                                var rowData = [];
                                self.idMap = {};
                                var MyHeaderComponent = function () {
                                }

                                MyHeaderComponent.prototype.init = function (agParams) {
                                    this.agParams = agParams;
                                    this.eGui = document.createElement('div');
                                    this.eGui.innerHTML = '' +
                                        '<div class="customHeaderMenuButton"><i class="fa ' + this.agParams.menuIcon + '"></i></div>' +
                                        '<div class="customHeaderLabel">' + this.agParams.displayName + '</div>' +
                                        '<div class="customSortDownLabel inactive"><i class="fa fa-long-arrow-down"></i></div>' +
                                        '<div class="customSortUpLabel inactive"><i class="fa fa-long-arrow-up"></i></div>' +
                                        '<div class="customSortRemoveLabel inactive"><i class="fa fa-times"></i></div>';

                                    this.eMenuButton = this.eGui.querySelector(".customHeaderMenuButton");
                                    this.eSortDownButton = this.eGui.querySelector(".customSortDownLabel");
                                    this.eSortUpButton = this.eGui.querySelector(".customSortUpLabel");
                                    this.eSortRemoveButton = this.eGui.querySelector(".customSortRemoveLabel");


                                    if (this.agParams.enableMenu) {
                                        this.onMenuClickListener = this.onMenuClick.bind(this);
                                        this.eMenuButton.addEventListener('click', this.onMenuClickListener);
                                    } else {
                                        this.eGui.removeChild(this.eMenuButton);
                                    }

                                    if (this.agParams.enableSorting) {
                                        this.onSortAscRequestedListener = this.onSortRequested.bind(this, 'asc');
                                        this.eSortDownButton.addEventListener('click', this.onSortAscRequestedListener);
                                        this.onSortDescRequestedListener = this.onSortRequested.bind(this, 'desc');
                                        this.eSortUpButton.addEventListener('click', this.onSortDescRequestedListener);
                                        this.onRemoveSortListener = this.onSortRequested.bind(this, '');
                                        this.eSortRemoveButton.addEventListener('click', this.onRemoveSortListener);


                                        this.onSortChangedListener = this.onSortChanged.bind(this);
                                        this.agParams.column.addEventListener('sortChanged', this.onSortChangedListener);
                                        this.onSortChanged();
                                    } else {
                                        this.eGui.removeChild(this.eSortDownButton);
                                        this.eGui.removeChild(this.eSortUpButton);
                                        this.eGui.removeChild(this.eSortRemoveButton);
                                    }
                                };

                                MyHeaderComponent.prototype.onSortChanged = function () {
                                    function deactivate(toDeactivateItems) {
                                        toDeactivateItems.forEach(function (toDeactivate) {
                                            toDeactivate.className = toDeactivate.className.split(' ')[0]
                                        });
                                    }

                                    function activate(toActivate) {
                                        toActivate.className = toActivate.className + " active";
                                    }

                                    if (this.agParams.column.isSortAscending()) {
                                        deactivate([this.eSortUpButton, this.eSortRemoveButton]);
                                        activate(this.eSortDownButton)
                                    } else if (this.agParams.column.isSortDescending()) {
                                        deactivate([this.eSortDownButton, this.eSortRemoveButton]);
                                        activate(this.eSortUpButton)
                                    } else {
                                        deactivate([this.eSortUpButton, this.eSortDownButton]);
                                        activate(this.eSortRemoveButton)
                                    }
                                };

                                MyHeaderComponent.prototype.getGui = function () {
                                    return this.eGui;
                                };

                                MyHeaderComponent.prototype.onMenuClick = function () {
                                    this.agParams.showColumnMenu(this.eMenuButton);
                                };

                                MyHeaderComponent.prototype.onSortRequested = function (order, event) {
                                    this.agParams.setSort(order, event.shiftKey);
                                };

                                MyHeaderComponent.prototype.destroy = function () {
                                    if (this.onMenuClickListener) {
                                        this.eMenuButton.removeEventListener('click', this.onMenuClickListener)
                                    }
                                    this.eSortDownButton.removeEventListener('click', this.onSortRequestedListener);
                                    this.eSortUpButton.removeEventListener('click', this.onSortRequestedListener);
                                    this.eSortRemoveButton.removeEventListener('click', this.onSortRequestedListener);
                                    this.agParams.column.removeEventListener('sortChanged', this.onSortChangedListener);
                                };

                                self.MyHeaderComponent = MyHeaderComponent;


                                var MyHeaderGroupComponent = function () {
                                }

                                MyHeaderGroupComponent.prototype.init = function (params) {
                                    this.params = params;
                                    this.eGui = document.createElement('div');
                                    this.eGui.className = 'ag-header-group-cell-label';
                                    this.eGui.innerHTML = '' +
                                        '<div class="customHeaderLabel">' + this.params.displayName + '</div>' +
                                        '<div class="customExpandButton"><i class="fa fa-arrow-right"></i></div>';

                                    this.onExpandButtonClickedListener = this.expandOrCollapse.bind(this);
                                    this.eExpandButton = this.eGui.querySelector(".customExpandButton");
                                    this.eExpandButton.addEventListener('click', this.onExpandButtonClickedListener);

                                    this.onExpandChangedListener = this.syncExpandButtons.bind(this);
                                    this.params.columnGroup.getOriginalColumnGroup().addEventListener('expandedChanged', this.onExpandChangedListener);

                                    this.syncExpandButtons();
                                };

                                MyHeaderGroupComponent.prototype.getGui = function () {
                                    return this.eGui;
                                };

                                MyHeaderGroupComponent.prototype.expandOrCollapse = function () {
                                    var currentState = this.params.columnGroup.getOriginalColumnGroup().isExpanded();
                                    this.params.setExpanded(!currentState);
                                };

                                MyHeaderGroupComponent.prototype.syncExpandButtons = function () {
                                    function collapsed(toDeactivate) {
                                        toDeactivate.className = toDeactivate.className.split(' ')[0] + ' collapsed';
                                    }

                                    function expanded(toActivate) {
                                        toActivate.className = toActivate.className.split(' ')[0] + ' expanded';
                                    }

                                    if (this.params.columnGroup.getOriginalColumnGroup().isExpanded()) {
                                        expanded(this.eExpandButton);
                                    } else {
                                        collapsed(this.eExpandButton);
                                    }
                                };

                                MyHeaderGroupComponent.prototype.destroy = function () {
                                    this.eExpandButton.removeEventListener('click', this.onExpandButtonClickedListener);
                                };

                                self.MyHeaderGroupComponent = MyHeaderGroupComponent;

                                for (var i in self.by_id) {
                                    var row = {};
                                    for (var f in self.by_id[i]) {
                                        if (f.startsWith('xx_')) {
                                            var cols = JSON.parse(self.by_id[i][f]);
                                            // console.log(self.by_id[i][f]);
                                            for (var h in cols[0]) {
                                                if (rowData.length == 1) {
                                                    var key = f + "|" + h;
                                                    if (!xxColumnDefs[f]) xxColumnDefs[f] = [];
                                                    xxColumnDefs[f].push({headerName: cols[0][h], field: key});
                                                }
                                            }
                                            for (var d in cols[1]) {
                                                var key = f + "|" + d;
                                                row[key] = cols[1][d];
                                            }
                                        } else {
                                            // row[f] = self.get_field_value(self.by_id[i], f, true);
                                            row[f] = self.by_id[i][f];
                                        }
                                    }
                                    self.idMap[rowData.length] = row.id;
                                    // console.log(row);
                                    rowData.push(row);
                                }
                                var header_group = false;
                                // var first_col = true;
                                columnDefs.push({
                                    headerName: "",
                                    width: 40,
                                    headerComponent: false,
                                    suppressFilter: true,
                                    suppressMenu: true,
                                    suppressSorting: true,
                                    suppressResize: true,
                                    suppressSizeToFit: true,
                                    pinned: 'left',
                                    cellStyle: {
                                        'text-align': 'center',
                                        'background-color': '#eeeeee',
                                        'border-bottom': '1px solid #808080'
                                    },
                                    valueGetter: 'node.rowIndex',
                                    editable: false,
                                    headerCellRenderer: function (params) {
                                        function b64toBlob(b64Data, contentType) {
                                            var sliceSize = 512;

                                            var byteCharacters = atob(b64Data);
                                            var byteArrays = [];

                                            for (var offset = 0; offset < byteCharacters.length; offset += sliceSize) {
                                                var slice = byteCharacters.slice(offset, offset + sliceSize);

                                                var byteNumbers = new Array(slice.length);
                                                for (var i = 0; i < slice.length; i++) {
                                                    byteNumbers[i] = slice.charCodeAt(i);
                                                }

                                                var byteArray = new Uint8Array(byteNumbers);

                                                byteArrays.push(byteArray);
                                            }

                                            var blob = new Blob(byteArrays, {type: contentType});
                                            return blob;
                                        }
                                        function download(params, content) {
                                            var fileNamePresent = params && params.fileName && params.fileName.length !== 0;
                                            var fileName = fileNamePresent ? params.fileName : 'download.xlsx';

                                            var blobObject = b64toBlob(content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');

                                            // Internet Explorer
                                            if (window.navigator.msSaveOrOpenBlob) {
                                                window.navigator.msSaveOrOpenBlob(blobObject, fileName);
                                            } else {
                                                // Chrome
                                                var downloadLink = document.createElement('a');
                                                downloadLink.href = URL.createObjectURL(blobObject);
                                                downloadLink.download = fileName;

                                                document.body.appendChild(downloadLink);
                                                downloadLink.click();
                                                document.body.removeChild(downloadLink);
                                            }
                                        }
                                        if (self.view.el.className.indexOf('o_form_editable') == -1) {
                                            var eb = document.createElement('button');
                                            eb.setAttribute('class', 'fa fa-download');
                                            eb.setAttribute('style', 'border:0;padding:1px;background-color:rgba(0,0,0,0);');
                                            eb.addEventListener('click', function (e) {
                                                var columnKeys = [];
                                                for (var i in view_fields) {
                                                    var modifiers = JSON.parse(view_fields[i].attrs.modifiers);
                                                    if (view_fields[i].attrs.name != 'sequence' && !modifiers['tree_invisible']) {
                                                        columnKeys.push(view_fields[i].attrs.name);
                                                    }
                                                }
                                                params.columnKeys = columnKeys;
                                                params.processCellCallback = function(attrs) {
                                                    if (attrs.value instanceof Array) {
                                                        return attrs.value[1];
                                                    }
                                                    return attrs.value;
                                                };
                                                var content = params.api.getDataAsExcel(params);
                                                var workbook = XLSX.read(content, {type: 'binary'});
                                                var xlsxContent = XLSX.write(workbook, {bookType: 'xlsx', type: 'base64'});
                                                download(params, xlsxContent);
                                            });
                                            return eb;

                                        }
                                        var ab = document.createElement('button');
                                        ab.setAttribute('class', 'fa fa-check-circle');
                                        ab.setAttribute('style', 'border:0;padding:1px;background-color:rgba(0,0,0,0);');

                                        ab.addEventListener('click', function (e) {
                                            var ids = params.api.getSelectedNodes().map(function (item, index, array) {
                                                return self.idMap[item.id];
                                            });
                                            if (ids.length > 0) {
                                                var del_ids = [];
                                                var del_rows = [];
                                                for (var i in self.idMap) {
                                                    if (ids.indexOf(self.idMap[i]) == -1 && params.api.getRowNode(i)) {
                                                        del_ids.push(self.idMap[i]);
                                                        del_rows.push(params.api.getRowNode(i).data);
                                                    }
                                                }
                                                var def = $.Deferred();
                                                self.dataset.unlink(del_ids).done(function () {
                                                    if (params.api.getRowNode(i)) {
                                                        params.api.updateRowData({remove: del_rows});
                                                    }
                                                    def.resolve();
                                                    params.api.deselectAll();
                                                });
                                            }
                                            $(this)[0].blur();
                                        });
                                        return ab;
                                    },
                                    cellRenderer: function (params) {
                                        if (params.value !== undefined) {
                                            return parseInt(params.value) + 1;
                                        }
                                        // else {
                                        //     return '<img src="../images/loading.gif">'
                                        // }
                                    }
                                });
                                columnDefs.push({
                                    headerName: '',
                                    field: 'id',
                                    headerComponent: false,
                                    suppressFilter: true,
                                    suppressMenu: true,
                                    suppressSorting: true,
                                    pinned: 'left',
                                    width: 30,
                                    hide: true,
                                    editable: false,
                                    cellStyle: {'text-align': 'center'},
                                    checkboxSelection: true,
                                    // checkboxSelection: function (params) {
                                    //     return params.data.id;
                                    // },
                                    headerCellRenderer: function (params) {
                                        // var cb = document.createElement('button');
                                        // cb.setAttribute('class', 'fa fa-times-circle');
                                        // cb.setAttribute('style', 'border:0;padding:1px;background-color:rgba(0,0,0,0);');
                                        var cb = document.createElement('input');
                                        cb.setAttribute('type', 'checkbox');
                                        cb.setAttribute('class', 'ag-selection-checkbox');

                                        cb.addEventListener('click', function (e) {
                                            // var ids = params.api.getSelectedNodes().map(function (item, index, array) {
                                            //     return self.idMap[item.id];
                                            // });
                                            // var def = $.Deferred();
                                            // self.dataset.unlink(ids).done(function () {
                                            //     params.api.updateRowData({remove: params.api.getSelectedRows()});
                                            //     def.resolve();
                                            // });
                                            // $(this)[0].blur();
                                            if ($(this)[0].checked) {
                                                // params.api.selectAll();
                                                params.api.selectAllFiltered();
                                            } else {
                                                params.api.deselectAll();
                                            }
                                        });
                                        return cb;
                                    },
                                    cellRenderer: function (params) {
                                        return '';
                                        // return '<button class="fa fa-trash-o" style="border:0;padding:0;background-color:rgba(0,0,0,0);" data-action-type="remove" name="delete"/>';
                                    }
                                });
                                for (var i in view_fields) {
                                    var attr_type = view_fields[i].tag;
                                    if (attr_type === 'field') {
                                        attr_type = self.fields[view_fields[i].attrs.name].type;
                                    }
                                    var header = view_fields[i].attrs.string || self.field.views.tree.fields[view_fields[i].attrs.name].string;
                                    // if (header.indexOf('(') > 0) {
                                    //     header = header.replace('(', '<br/>(');
                                    // }
                                    // if (!modifiers['tree_invisible']) {
                                        var col_header;
                                        if (view_fields[i].attrs.name.startsWith('xx_') && xxColumnDefs[view_fields[i].attrs.name]) {
                                            col_header = xxColumnDefs[view_fields[i].attrs.name];
                                        } else{
                                            col_header = [{
                                                headerName: attr_type === 'button' ? '' : header,
                                                field: view_fields[i].attrs.name,
                                                cellClassRules: {
                                                    'highlight': function (params) {
                                                        if (params.data.invalid_fields)
                                                            return JSON.parse(params.data.invalid_fields).indexOf(params.colDef.field) > -1;
                                                        return false;
                                                    },
                                                    'miss': function (params) {
                                                        if (params.data.invalid_fields)
                                                            return JSON.parse(params.data.invalid_fields).indexOf('*') > -1;
                                                        return false;
                                                    }
                                                }
                                            }];
                                        }
                                            // if(first_col) {
                                            //     col_header[0]['checkboxSelection'] = true;
                                            //     first_col = false;
                                            // }
                                        for (var c = 0; c < col_header.length; c++) {
                                            if (attr_type === 'char') {
                                                col_header[c]['valueParser'] = function (params) {
                                                    return !params.newValue ? '' : params.newValue.toString();
                                                };
                                                col_header[c]['valueFormatter'] = function (params) {
                                                    return !params.value ? '' : params.value;
                                                };
                                            } else if (attr_type === 'many2one') {
                                                col_header[c]['valueFormatter'] = function (params) {
                                                    // return self.get_field_value(params.data, params.column.colId, true);
                                                    return params.value[1];
                                                };
                                                col_header[c]['keyCreator'] = function(params) {
                                                    if (params.value instanceof Array) {
                                                        return params.value[1];
                                                    }
                                                    return params.value;
                                                };
                                            } else if (attr_type === 'integer') {
                                                col_header[c]['valueParser'] = function (params) {
                                                    return Number(params.newValue.toString().trim());
                                                };
                                                col_header[c]['valueFormatter'] = function (params) {
                                                    if (params.value)
                                                        return params.value.toString().trim().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,");
                                                };
                                            } else if (attr_type === 'float') {
                                                col_header[c]['valueParser'] = function (params) {
                                                    return Number(params.newValue.toString().trim());
                                                };
                                                if (view_fields[i].attrs['precision_0'] !== undefined) {
                                                    col_header[c]['valueFormatter'] = function (params) {
                                                        if (params.value) {
                                                            var ret = utils.round_decimals(params.value, 0).toString().trim();
                                                            return parseInt(ret).toString();
                                                        }
                                                    };
                                                }
                                                if (view_fields[i].attrs['precision_3'] !== undefined) {
                                                    col_header[c]['valueFormatter'] = function (params) {
                                                        if (params.value){
                                                            var ret3 = utils.round_decimals(params.value, 3).toString().trim();
                                                            return (parseInt(parseFloat(ret3)*1000)/1000).toString();
                                                        }
                                                    };
                                                }
                                            } else if (attr_type === 'selection') {
                                                col_header[c]['valueFormatter'] = function (params) {
                                                    return self.get_field_value(params.data, params.column.colId, true);
                                                };
                                            } else if (attr_type === 'button' && self.view.el.className.indexOf('o_form_editable') === -1) {
                                                col_header[c]['cellRenderer'] = function (params) {
                                                    var btn = document.createElement('button');
                                                    btn.innerHTML = header;
                                                    btn.addEventListener('click', function (e) {
                                                        // console.log(self.dataset.context);
                                                        self.dataset._model.call(params.column.colId, [
                                                            [params.data.id], self.dataset.context]).then(function (res) {
                                                                // console.log(res);
                                                                return self.do_action(res);
                                                        });

                                                        // self.do_execute_action(action, self.dataset, params.data.id);
                                                    });
                                                    // console.log(self);
                                                    return btn;
                                                };
                                            }
                                        }

                                        if (view_fields[i].tag === 'field') {
                                            var modifiers = JSON.parse(view_fields[i].attrs.modifiers);
                                            if (modifiers['tree_invisible']) {
                                                for (var c = 0; c < col_header.length; c++) {
                                                    col_header[c]['hide'] = true;
                                                }
                                            }
                                        }
                                        if (view_fields[i].attrs['readonly'] === '1') {
                                            for (var c = 0; c < col_header.length; c++) {
                                                col_header[c]['editable'] = false;
                                            }
                                        }
                                        if (view_fields[i].attrs['open_show'] === '1') {
                                            for (var c = 0; c < col_header.length; c++) {
                                                col_header[c]['columnGroupShow'] = 'open';
                                            }
                                        }
                                        if (view_fields[i].attrs['pinned']) {
                                            for (var c = 0; c < col_header.length; c++) {
                                                col_header[c]['pinned'] = view_fields[i].attrs['pinned'];
                                            }
                                        }
                                        var sortIdx = sortKeys.indexOf(view_fields[i].attrs.name);
                                        if (sortIdx != -1) {
                                            for (var c = 0; c < col_header.length; c++) {
                                                col_header[c]['sort'] = sortDirs[sortIdx]
                                            }
                                        }
                                        if (view_fields[i].attrs['header_group']) {
                                            if (view_fields[i].attrs['header_group'] === header_group) {
                                                var sub_header = columnDefs[columnDefs.length - 1]['children'];
                                                sub_header.push.apply(sub_header, col_header);
                                            } else {
                                                header_group = view_fields[i].attrs['header_group'];
                                                var col_group = {
                                                    headerName: header_group,
                                                    headerGroupComponent: self.MyHeaderGroupComponent,
                                                    children: col_header
                                                };
                                                columnDefs.push(col_group);
                                            }
                                        } else {
                                            columnDefs.push.apply(columnDefs, col_header);
                                            header_group = false;
                                        }
                                    // }
                                }

                                self.emptyRow = function () {
                                    var row = {};
                                    for (var f in view_fields) {
                                        row[view_fields[f].attrs.name] = ""
                                    }
                                    return row;
                                };
                                self.columnDefs = columnDefs;
                                self.rowData = rowData;

                                self.renderElement();
                                // self.compute_totals();
                                // self.setup_many2one_axes();
                                // self.$el.find('.edit').on(
                                //     'change', self.proxy(self.xy_value_change));
                                // self.effective_readonly_change();
                            }
                        });
                    });
            });
        },

        // do whatever needed to setup internal data structure
        add_xy_row: function (row, x_axis) {
            // if(this.x.slice(-1) == '*')this.x=this.x.slice(0,-1);
            if (this.y_axis) {
                var x = this.get_field_value(row, x_axis),
                    y = this.get_field_value(row, this.y_axis);
                // row is a *copy* of a row in dataset.cache, fetch
                // a reference to this row in order to have the
                // internal data structure point to the same data
                // the dataset manipulates
                _.every(this.dataset.cache, function (cached_row) {
                    if (cached_row.id == row.id) {
                        row = cached_row.values;
                        // new rows don't have that
                        row.id = cached_row.id;
                        return false;
                    }
                    return true;
                });
                this.by_x_axis[x] = this.by_x_axis[x] || {};
                this.by_y_axis[y] = this.by_y_axis[y] || {};
                this.by_x_axis[x][y] = row;
                this.by_y_axis[y][x] = row;
                this.by_id[row.id] = row;
            } else {
                this.by_id[row.id] = row;
            }
        },

        setup_many2one_axes: function () {
            // if(this.fields[this.x].type == 'many2one' && this.x_axis_clickable)
            // {
            //     this.$el.find('th[data-x]').addClass('oe_link')
            //     .click(_.partial(
            //         this.proxy(this.many2one_axis_click),
            //         this.x, 'x'));
            // }
            if (this.y_axis && this.fields[this.y_axis].type == 'many2one' && this.y_axis_clickable) {
                this.$el.find('tr[data-y] th').addClass('oe_link')
                    .click(_.partial(
                        this.proxy(this.many2one_axis_click),
                        this.y_axis, 'y'));
            }
        },

        many2one_axis_click: function (field, id_attribute, e) {
            this.do_action({
                type: 'ir.actions.act_window',
                name: this.fields[field].string,
                res_model: this.fields[field].relation,
                res_id: $(e.currentTarget).data(id_attribute),
                views: [[false, 'form']],
                target: 'current',
            })
        },

        load_views: function () {

            // Needed for removing the initial empty tree view when the widget
            // is loaded
            var self = this,
                result = this._super();

            return $.when(result).then(function () {
                self.renderElement();

            });
        },
        // reload_current_view: function () {
        //     var self = this,
        //         result = this._super();
        //
        //     return $.when(result).then(function()
        //     {
        //         self.renderElement();
        //     });
        // },

        renderElement: function () {
            this._super();
            this.renderGrid();
        },
        renderGrid: function () {
            var self = this;


            // used in our jasmine test
            function selectAllRows() {
                gridOptions.api.selectAll();
            }

            // wait for the document to be loaded, otherwise ag-Grid will not find the div in the document.

            if (self.$el.parent().height()) {
                var eGridDiv = self.$el[0];
                $(eGridDiv).addClass('ag-fresh');
                eGridDiv.style.width = '100%';
                var bottom = $(".o_form_sheet_bg").length ? 43 : 13;
                if ($(".modal-footer").length) {
                    bottom += 70;
                }
                eGridDiv.style.height = (jQuery(window).height() - self.$el.offset().top - bottom) + 'px';

                var no_empty_row = self.field.views.tree.arch.attrs['no_empty_row'];
                if (self.view.el.className.indexOf('o_form_editable') !== -1 && no_empty_row !== '1') {
                    var empty_rows = 10;
                    if (self.rowData.length === 0) {
                        empty_rows = 200;
                    }
                    for (var i = 0; i < empty_rows; i++) {
                        self.rowData.push(self.emptyRow());
                    }
                }
                // $.getScript( "/web_widget_grid/static/lib/grid/js/grid.min.js", function( data, textStatus, jqxhr ){
                // let the grid know which columns and what data to use
                var gridOptions = {
                    columnDefs: self.columnDefs,
                    rowData: self.rowData,
                    editType: 'fullRow',
                    defaultColDef: {
                        editable: (self.view.el.className.indexOf('o_form_editable') !== -1),
                        width: 120,
                        headerComponent: self.MyHeaderComponent
                        // headerComponentParams : {
                        //     menuIcon: 'fa-bars'
                        // }
                    },
                    // singleClickEdit: true,
                    // domLayout: 'autoHeight',
                    enableRangeSelection: true,
                    // headerHeight: 48,
                    enableColResize: true,
                    floatingFilter: true,
                    enableSorting: true,
                    multiSortKey: 'ctrl',
                    enableFiltering: true,
                    stopEditingWhenGridLosesFocus: true,
                    rowSelection: 'multiple',
                    suppressRowClickSelection: true,
                    animateRows: true,
                    enableStatusBar: true,
                    alwaysShowStatusBar: false,
                    // icons: {
                    //     checkboxChecked: '<i class="fa fa-trash-o" name="delete"/>',
                    //     checkboxUnchecked: '<i class="fa fa-trash-o" name="delete"/>',
                    //     checkboxIndeterminate: '<i class="fa fa-trash-o" name="delete"/>'
                    // },
                    // rowModelType: 'infinite',
                    // paginationPageSize: 100,
                    // singleClickEdit:true,
                    processCellFromClipboard: function (params) {
                        if (params.node.id == gridOptions.rowData.length - 1) {
                            gridOptions.rowData.push(self.emptyRow());
                            gridOptions.api.setRowData(gridOptions.rowData);
                        }
                        var fieldData = {};
                        fieldData[params.column.colId] = params.value.trim();
                        if (self.idMap[params.node.id]) {
                            self.dataset.write(self.idMap[params.node.id], fieldData);
                        } else {
                            self.dataset.create(fieldData, {'internal_dataset_changed': true}).then(function (id) {
                                self.dataset.ids.push(id);
                                self.idMap[params.node.id] = id;
                            });
                        }
                        return params.value
                    },
                    onGridSizeChanged: function (event) {
                        // gridOptions.api.sizeColumnsToFit();
                        var allColumnIds = [];
                        self.columnDefs.forEach(function (columnDef) {
                            if (columnDef.field) {
                                allColumnIds.push(columnDef.field);
                                if (columnDef.children) {
                                    columnDef.children.forEach(function (cColumnDef) {
                                        allColumnIds.push(cColumnDef.field);
                                    });
                                }
                            }
                        });
                        gridOptions.columnApi.autoSizeColumns(allColumnIds);
                    },
                    onRowValueChanged: function (event) {
                        var data = JSON.parse(JSON.stringify(event.data));
                        for (var d in data) {
                            data[d] = self.get_field_value(data, d, false);
                        }
                        var data_id = self.idMap[event.node.id];
                        if (data_id == gridOptions.rowData.length - 1) {
                            gridOptions.rowData.push(self.emptyRow());
                            // gridOptions.api.setRowData(gridOptions.rowData);
                        }
                        var idArr = Object.values(self.idMap);
                        for (var key in idArr) {
                            idArr[key] = String(idArr[key]);
                        }
                        if (idArr.indexOf(String(data_id)) > -1) {
                            self.dataset.write(data_id, data);
                        } else {
                            self.dataset.create(data, {'internal_dataset_changed': true}).then(function (id) {
                                self.dataset.ids.push(id);
                                self.idMap[data_id] = id;
                            });
                        }
                    },
                    onRowClicked: function (e) {
                        var data = e.node.data;
                        if (Object.values(data).join('') != '') {
                            if (e.event.target !== undefined && e.event.target.getAttribute("data-action-type") === 'remove') {
                                var def = $.Deferred();
                                self.dataset.unlink([self.idMap[e.node.id]]).done(function () {
                                    gridOptions.api.updateRowData({remove: [data]});
                                    def.resolve();
                                });
                            } else if (e.event.target.getAttribute("colId") == 0) {
                                e.node.setSelected(!e.node.isSelected());
                                e.event.target.blur();
                            }
                        }
                        // else {
                        //     gridOptions.api.deselectAll();
                        // }
                    },
                    // onCellEditingStarted: function(cell) {
                    //     if (cell.colDef.field === 'id') {
                    //         gridOptions.columnApi.setColumnVisible('id', false);
                    //     }
                    // },
                    // onRowEditingStopped: function(row) {
                    //     gridOptions.columnApi.setColumnVisible('id', true);
                    // },
                    onGridReady: function () {
                        gridOptions.columnApi.setColumnVisible('id', self.view.el.className.indexOf('o_form_editable') !== -1);
                        var allColumnIds = [];
                        self.columnDefs.forEach(function (columnDef) {
                            allColumnIds.push(columnDef.field);
                            if (columnDef.children) {
                                columnDef.children.forEach(function (cColumnDef) {
                                    allColumnIds.push(cColumnDef.field);
                                });
                            }
                        });

                        if (self.view.el.className.indexOf('o_form_editable') !== -1) {
                            self.$el[0].addEventListener('keyup', function (e) {
                                if (e.key == 'Delete' || e.key == 'Backspace') {
                                    var ids = gridOptions.api.getSelectedNodes().map(function (item, index, array) {
                                        return self.idMap[item.id];
                                    });
                                    var def = $.Deferred();
                                    self.dataset.unlink(ids).done(function () {
                                        gridOptions.api.updateRowData({remove: gridOptions.api.getSelectedRows()});
                                        def.resolve();
                                    });
                                    var rangeSelections = gridOptions.api.getRangeSelections();
                                    for (var r in rangeSelections) {
                                        var range = rangeSelections[r];
                                        var startRow = Math.min(range.start.rowIndex, range.end.rowIndex);
                                        var endRow = Math.max(range.start.rowIndex, range.end.rowIndex);
                                        for (var rowIndex = startRow; rowIndex <= endRow; rowIndex++) {
                                            var rowModel = gridOptions.api.getModel();
                                            var rowNode = rowModel.getRow(rowIndex);
                                            range.columns.forEach(function (column) {
                                                if (range.start.rowIndex != range.end.rowIndex || range.start.column != range.end.column) {
                                                    gridOptions.api.startEditingCell({
                                                        rowIndex: rowIndex,
                                                        colKey: column.colId
                                                    });
                                                    gridOptions.api.stopEditing(true);
                                                }
                                                rowNode.setDataValue(column, '');
                                                // gridOptions.api.getValue(column, rowNode);
                                            });
                                        }
                                        // if (range.start.rowIndex != range.end.rowIndex || range.start.column != range.end.column) {
                                        //     gridOptions.api.startEditingCell({
                                        //         rowIndex: range.start.rowIndex,
                                        //         colKey: range.start.column.colId
                                        //     });
                                        // }
                                    }
                                }
                            });
                        }

                        gridOptions.columnApi.autoSizeColumns(allColumnIds);
                        // var columns = gridOptions.columnApi.getAllDisplayedVirtualColumns();
                        // var colIds = columns.map(function (column) {return column.colId});
                        // columns.forEach(function (column) {
                        //     console.log(column.colId);
                        //     var element = document.querySelector("div[colid=" + column.colId + "] div.ag-header-cell-label");
                        //     console.log(element);
                        //     element.addEventListener('keydown', function (e) {
                        //         alert(e.key);
                        //         e.preventDefault();
                        //     });
                        // });
                        // gridOptions.api.sizeColumnsToFit();
                    },
                    // getRowClass: function (params) {
                    //     if (params.data.invalid) {
                    //         return 'highlightRow';
                    //     }
                    // },

                    localeText: self.get_locale_text()
                };
                self.eGrid = new agGrid.Grid(eGridDiv, gridOptions);
                // gridOptions.defaultColDef.editable = true;
                // gridOptions.api.doLayout();
                // });
            }
        }

    });

    core.form_widget_registry.add('grid', WidgetX2ManyGrid);

    return WidgetX2ManyGrid;
});
