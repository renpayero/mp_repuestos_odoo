/** @odoo-module **/

import { Component, useState, useRef, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

export class DakoPasswordField extends Component {
    static template = "dako_password.PasswordField";
    static props = { ...standardFieldProps };

    setup() {
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.visibility = useService("dako_password.visibility");
        this.visState = useState(this.visibility.state);
        this.rootRef = useRef("root");

        // Limpia tooltips nativos del <td>/<tr> padre que podrían filtrar la contraseña.
        useEffect(() => {
            const root = this.rootRef.el;
            if (!root) return;
            const cleanAttrs = (el) => {
                if (!el) return;
                el.removeAttribute("title");
                el.removeAttribute("data-tooltip");
                el.removeAttribute("data-tooltip-info");
                el.removeAttribute("data-original-title");
            };
            const td = root.closest("td");
            cleanAttrs(td);
            cleanAttrs(root);
            if (!td) return;
            const observer = new MutationObserver(() => cleanAttrs(td));
            observer.observe(td, {
                attributes: true,
                attributeFilter: ["title", "data-tooltip", "data-tooltip-info", "data-original-title"],
            });
            return () => observer.disconnect();
        });
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    get isReadonly() {
        return this.props.readonly;
    }

    get isVisible() {
        if (this.visState.showAll) {
            return true;
        }
        const id = this.props.record.resId;
        return id != null && this.visState.visibleIds.includes(id);
    }

    get displayValue() {
        if (this.isVisible) {
            return this.value;
        }
        if (!this.value) {
            return "";
        }
        return "•".repeat(Math.min(this.value.length, 12));
    }

    onToggleClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.visibility.toggleRecord(this.props.record.resId);
    }

    onCopyClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const value = this.value;
        if (!value) {
            this.notification.add(_t("No hay contraseña para copiar"), { type: "warning" });
            return;
        }
        const fallback = () => {
            const ta = document.createElement("textarea");
            ta.value = value;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            try {
                document.execCommand("copy");
                this.notification.add(_t("Contraseña copiada al portapapeles"), { type: "success" });
            } catch {
                this.notification.add(_t("No se pudo copiar la contraseña"), { type: "danger" });
            }
            document.body.removeChild(ta);
        };
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(value).then(
                () => this.notification.add(_t("Contraseña copiada al portapapeles"), { type: "success" }),
                () => fallback(),
            );
        } else {
            fallback();
        }
    }

    onInput(ev) {
        this.props.record.update({ [this.props.name]: ev.target.value });
    }

    async onGenerate(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const newValue = await this.orm.call("dako.password", "generate_password_value", [], {
            length: 16,
            use_symbols: true,
        });
        await this.props.record.update({ [this.props.name]: newValue });
        this.notification.add(_t("Contraseña generada"), { type: "success" });
    }
}

export const dakoPasswordField = {
    component: DakoPasswordField,
    displayName: "Contraseña Dako",
    supportedTypes: ["char"],
};

registry.category("fields").add("dako_password", dakoPasswordField);
