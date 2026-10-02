/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PackageButton extends Component {
    static template = "kranti_einvoice_aretx.PackageButtonTemplate";
    static props = ["*"];

    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
    }

    async onClick() {
        const root = this.props.record.model.root;

        // Get the exact position of the clicked order line
        const lines = root.data.order_line.records;
        const lineIndex = lines.indexOf(this.props.record);

        if (lineIndex === -1) {
            this.notification.add(
                "Unable to identify the selected order line.",
                { type: "warning" }
            );
            return;
        }

        // Automatically save the Sale Order and its order lines
        const saved = await root.save();

        if (!saved || !root.resId) {
            this.notification.add(
                "Unable to save the Sales Order.",
                { type: "warning" }
            );
            return;
        }

        // Get the SAME line using its original position
        const freshLines = root.data.order_line.records;
        const freshRecord = freshLines[lineIndex];

        if (!freshRecord || !freshRecord.resId) {
            this.notification.add(
                "Unable to save the selected order line.",
                { type: "warning" }
            );
            return;
        }

        // Open Package Selection Wizard for the clicked line
        await this.action.doActionButton({
            type: "object",
            name: "action_open_package_wizard",
            resModel: "sale.order.line",
            resId: freshRecord.resId,
            resIds: [freshRecord.resId],
            onClose: () => root.load(),
        });
    }
}

registry.category("view_widgets").add("package_button", {
    component: PackageButton,
});