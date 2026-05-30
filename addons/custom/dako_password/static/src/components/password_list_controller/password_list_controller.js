/** @odoo-module **/

import { useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

export class DakoPasswordListController extends ListController {
    static template = "dako_password.ListView";

    setup() {
        super.setup();
        this.visibility = useService("dako_password.visibility");
        this.visState = useState(this.visibility.state);
    }

    onToggleAll() {
        this.visibility.toggleAll();
    }

    onClickExport() {
        const records = this.model.root.records || [];
        const ids = records.map((r) => r.resId).filter(Boolean);
        const url = ids.length
            ? `/dako_password/export/xlsx?ids=${ids.join(",")}`
            : `/dako_password/export/xlsx`;
        window.open(url, "_blank");
    }
}

export const dakoPasswordListView = {
    ...listView,
    Controller: DakoPasswordListController,
};

registry.category("views").add("dako_password_list", dakoPasswordListView);
