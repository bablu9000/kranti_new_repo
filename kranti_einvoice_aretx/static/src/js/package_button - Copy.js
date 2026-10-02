/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PackageButton extends Component {
    static template = "kranti_einvoice_aretx.PackageButtonTemplate";
    static props = ["*"];

    setup() {
        this.action = useService("action");
    }

    async onClick() {
    const saved = await this.props.record.model.root.save();
    if (!saved) {
        return;
    }

    // IMPORTANT: save() ke baad props.record ko dobara access karo,
    // purana captured reference stale ho sakta hai (naya real resId nahi hoga usme)
    const record = this.props.record;

    if (!record.resId) {
        // safety net: agar tab bhi resId na mile
        this.notificationService?.add(
            "Line save nahi ho payi, dobara try karein.",
            { type: "warning" }
        );
        return;
    }

    await this.action.doActionButton({
        type: "object",
        name: "action_open_package_wizard",
        resModel: "sale.order.line",
        resId: record.resId,
        resIds: [record.resId],
        onClose: () => record.model.root.load(),
    });
}
}

registry.category("view_widgets").add("package_button", {
    component: PackageButton,
});