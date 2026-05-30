/** @odoo-module **/

import { reactive } from "@odoo/owl";
import { registry } from "@web/core/registry";

export const passwordVisibilityService = {
    start() {
        const state = reactive({
            showAll: false,
            visibleIds: [],
        });

        return {
            state,
            toggleAll() {
                state.showAll = !state.showAll;
            },
            isVisibleFor(recordId) {
                if (state.showAll) {
                    return true;
                }
                return recordId != null && state.visibleIds.includes(recordId);
            },
            toggleRecord(recordId) {
                if (recordId == null) {
                    return;
                }
                const idx = state.visibleIds.indexOf(recordId);
                if (idx >= 0) {
                    state.visibleIds.splice(idx, 1);
                } else {
                    state.visibleIds.push(recordId);
                }
            },
        };
    },
};

registry.category("services").add("dako_password.visibility", passwordVisibilityService);
