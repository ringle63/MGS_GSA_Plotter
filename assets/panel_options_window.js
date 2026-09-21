(function () {
    "use strict";

    /*
     * IMPORTANT:
     * Do not move the dialog out of the Dash/React DOM tree.
     *
     * Re-parenting the dialog to document.body breaks React event
     * handling for Dash components inside the window. That is why
     * Dropdowns, Custom Groups, and other callbacks stopped working.
     *
     * Instead, temporarily remove clipping from the dialog's
     * ancestors while it is open. The dialog remains exactly where
     * Dash rendered it, so all Dash/React controls keep working.
     */

    const ancestorState = new WeakMap();

    function getPanelId(element) {
        return element && element.getAttribute("data-panel-id");
    }

    function getDialog(panelId) {
        return document.getElementById(
            "panel-options-dialog-" + panelId
        );
    }

    function clamp(value, min, max) {
        return Math.max(
            min,
            Math.min(
                max,
                value
            )
        );
    }

    function rememberStyle(element, property) {
        return {
            value: element.style.getPropertyValue(property),
            priority: element.style.getPropertyPriority(property)
        };
    }

    function restoreStyle(element, property, state) {
        if (!state) {
            return;
        }

        if (state.value) {
            element.style.setProperty(
                property,
                state.value,
                state.priority || ""
            );
        } else {
            element.style.removeProperty(
                property
            );
        }
    }

    function unlockDialogAncestors(dialog) {
        if (!dialog || ancestorState.has(dialog)) {
            return;
        }

        const states = [];

        let element = dialog.parentElement;

        while (
            element
            && element !== document.body
            && element !== document.documentElement
        ) {
            const computed = window.getComputedStyle(
                element
            );

            const state = {
                element: element,

                overflow: rememberStyle(
                    element,
                    "overflow"
                ),

                overflowX: rememberStyle(
                    element,
                    "overflow-x"
                ),

                overflowY: rememberStyle(
                    element,
                    "overflow-y"
                ),

                clipPath: rememberStyle(
                    element,
                    "clip-path"
                ),

                contain: rememberStyle(
                    element,
                    "contain"
                ),

                zIndex: rememberStyle(
                    element,
                    "z-index"
                )
            };

            states.push(
                state
            );

            element.style.setProperty(
                "overflow",
                "visible",
                "important"
            );

            element.style.setProperty(
                "overflow-x",
                "visible",
                "important"
            );

            element.style.setProperty(
                "overflow-y",
                "visible",
                "important"
            );

            if (
                computed.clipPath
                && computed.clipPath !== "none"
            ) {
                element.style.setProperty(
                    "clip-path",
                    "none",
                    "important"
                );
            }

            if (
                computed.transform !== "none"
                || element.classList.contains(
                    "react-grid-item"
                )
            ) {
                element.style.setProperty(
                    "z-index",
                    "9999",
                    "important"
                );
            }

            element = element.parentElement;
        }

        ancestorState.set(
            dialog,
            states
        );
    }

    function restoreDialogAncestors(dialog) {
        if (!dialog) {
            return;
        }

        const states = ancestorState.get(
            dialog
        );

        if (!states) {
            return;
        }

        states.forEach(
            function (state) {

                const element = state.element;

                if (!element) {
                    return;
                }

                restoreStyle(
                    element,
                    "overflow",
                    state.overflow
                );

                restoreStyle(
                    element,
                    "overflow-x",
                    state.overflowX
                );

                restoreStyle(
                    element,
                    "overflow-y",
                    state.overflowY
                );

                restoreStyle(
                    element,
                    "clip-path",
                    state.clipPath
                );

                restoreStyle(
                    element,
                    "contain",
                    state.contain
                );

                restoreStyle(
                    element,
                    "z-index",
                    state.zIndex
                );
            }
        );

        ancestorState.delete(
            dialog
        );
    }

    function closeDialog(dialog) {
        if (!dialog) {
            return;
        }

        if (
            typeof dialog.close
            === "function"
        ) {

            if (dialog.open) {
                dialog.close();
            }

        } else {

            dialog.removeAttribute(
                "open"
            );
        }

        restoreDialogAncestors(
            dialog
        );
    }

    /*
     * position: fixed becomes relative to an RGL transformed ancestor.
     * Find that ancestor so drag coordinates can be converted from
     * viewport coordinates to the dialog's actual containing block.
     */
    function getFixedContainingBlock(dialog) {
        let element = dialog.parentElement;

        while (
            element
            && element !== document.body
            && element !== document.documentElement
        ) {
            const computed = window.getComputedStyle(
                element
            );

            if (
                computed.transform !== "none"
                || computed.perspective !== "none"
                || computed.filter !== "none"
            ) {
                return element;
            }

            element = element.parentElement;
        }

        return null;
    }

    function getContainingBlockRect(dialog) {
        const containingBlock = (
            getFixedContainingBlock(
                dialog
            )
        );

        if (!containingBlock) {
            return {
                left: 0,
                top: 0
            };
        }

        const rect = (
            containingBlock
                .getBoundingClientRect()
        );

        return {
            left: rect.left,
            top: rect.top
        };
    }


    // --------------------------------------------------------
    // Open / Close / Override Selection
    // --------------------------------------------------------

    document.addEventListener(
        "click",
        function (event) {

            const openButton = event.target.closest(
                ".panel-options-open"
            );

            if (openButton) {

                const panelId = getPanelId(
                    openButton
                );

                const dialog = getDialog(
                    panelId
                );

                if (!dialog) {
                    return;
                }

                /*
                 * Keep one options window open at a time.
                 */
                document
                    .querySelectorAll(
                        ".panel-options-window[open]"
                    )
                    .forEach(
                        function (other) {

                            if (other !== dialog) {
                                closeDialog(
                                    other
                                );
                            }
                        }
                    );

                unlockDialogAncestors(
                    dialog
                );

                /*
                 * Non-modal: the rest of the app remains clickable.
                 * Crucially, the dialog stays inside Dash's DOM tree.
                 */
                if (
                    typeof dialog.show
                    === "function"
                ) {

                    if (!dialog.open) {
                        dialog.show();
                    }

                } else {

                    dialog.setAttribute(
                        "open",
                        ""
                    );
                }

                return;
            }

            /*
             * Override Selection remains purely client-side.
             * Opening it cannot update panel-store or rerender the panel.
             */
            const overrideButton = (
                event.target.closest(
                    ".panel-override-toggle"
                )
            );

            if (overrideButton) {

                const panelId = getPanelId(
                    overrideButton
                );

                const content = (
                    document.getElementById(
                        "panel-override-content-"
                        + panelId
                    )
                );

                if (!content) {
                    return;
                }

                const isOpen = (
                    content.style.display
                    !== "none"
                );

                content.style.display = (
                    isOpen
                    ? "none"
                    : "block"
                );

                overrideButton.textContent = (
                    isOpen
                    ? "▶ Override Selection"
                    : "▼ Override Selection"
                );

                event.preventDefault();
                event.stopPropagation();

                return;
            }

            const closeButton = (
                event.target.closest(
                    ".panel-options-close, "
                    + ".panel-options-cancel, "
                    + ".panel-options-apply"
                )
            );

            if (closeButton) {

                const panelId = getPanelId(
                    closeButton
                );

                closeDialog(
                    getDialog(
                        panelId
                    )
                );
            }
        }
    );


    // --------------------------------------------------------
    // Dragging
    // --------------------------------------------------------

    let drag = null;

    document.addEventListener(
        "pointerdown",
        function (event) {

            const header = event.target.closest(
                ".panel-options-window-header"
            );

            if (
                !header
                || event.target.closest(
                    ".panel-options-close"
                )
            ) {
                return;
            }

            const dialog = header.closest(
                ".panel-options-window"
            );

            if (!dialog) {
                return;
            }

            const dialogRect = (
                dialog.getBoundingClientRect()
            );

            const containingRect = (
                getContainingBlockRect(
                    dialog
                )
            );

            /*
             * Convert the centered CSS position to explicit coordinates
             * without visually jumping the window.
             */
            dialog.style.transform = "none";

            dialog.style.left = (
                dialogRect.left
                - containingRect.left
                + "px"
            );

            dialog.style.top = (
                dialogRect.top
                - containingRect.top
                + "px"
            );

            drag = {
                dialog: dialog,

                pointerId:
                    event.pointerId,

                offsetX:
                    event.clientX
                    - dialogRect.left,

                offsetY:
                    event.clientY
                    - dialogRect.top
            };

            try {

                header.setPointerCapture(
                    event.pointerId
                );

            } catch (error) {

                // Pointer capture is optional.
            }

            event.preventDefault();
        }
    );


    document.addEventListener(
        "pointermove",
        function (event) {

            if (
                !drag
                || event.pointerId
                !== drag.pointerId
            ) {
                return;
            }

            const dialog = drag.dialog;

            const rect = (
                dialog.getBoundingClientRect()
            );

            const containingRect = (
                getContainingBlockRect(
                    dialog
                )
            );

            const desiredLeft = clamp(
                event.clientX
                - drag.offsetX,
                0,
                Math.max(
                    0,
                    window.innerWidth
                    - Math.min(
                        rect.width,
                        window.innerWidth
                    )
                )
            );

            const desiredTop = clamp(
                event.clientY
                - drag.offsetY,
                0,
                Math.max(
                    0,
                    window.innerHeight - 44
                )
            );

            dialog.style.left = (
                desiredLeft
                - containingRect.left
                + "px"
            );

            dialog.style.top = (
                desiredTop
                - containingRect.top
                + "px"
            );
        }
    );


    document.addEventListener(
        "pointerup",
        function (event) {

            if (
                !drag
                || event.pointerId
                !== drag.pointerId
            ) {
                return;
            }

            drag = null;
        }
    );


    document.addEventListener(
        "pointercancel",
        function () {
            drag = null;
        }
    );

})();