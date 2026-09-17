/*
PCA full-report PNG export.

This uses a document-level click listener rather than a Dash
clientside callback. That avoids callback-registration issues
with dynamically rendered PCA panels.

Requires html2canvas, which is loaded through app.py.
*/

(function () {
    "use strict";

    function getPanelId(button) {
        const dataValue = button.getAttribute("data-panel-id");

        if (dataValue !== null && dataValue !== "") {
            return dataValue;
        }

        const prefix = "download-pca-report-";

        if (
            button.id
            && button.id.indexOf(prefix) === 0
        ) {
            return button.id.substring(prefix.length);
        }

        return null;
    }


    async function exportPcaReport(button) {
        const panelId = getPanelId(button);

        if (panelId === null) {
            console.error(
                "PCA report export: panel id was not found."
            );
            return;
        }

        if (typeof window.html2canvas === "undefined") {
            console.error(
                "PCA report export: html2canvas is not loaded."
            );

            window.alert(
                "PNG report export could not start because "
                + "html2canvas is not loaded."
            );

            return;
        }

        const target = document.getElementById(
            "pca-report-" + panelId
        );

        if (!target) {
            console.error(
                "PCA report export: report element was not found.",
                panelId
            );
            return;
        }

        const originalText = button.textContent;
        const originalDisabled = button.disabled;

        button.disabled = true;
        button.textContent = "Exporting PNG…";

        try {
            /*
            Plotly graphs may still be finishing their responsive
            layout after a panel resize. Waiting two animation
            frames lets the browser finish layout before capture.
            */
            await new Promise(function (resolve) {
                requestAnimationFrame(function () {
                    requestAnimationFrame(resolve);
                });
            });

            const canvas = await window.html2canvas(
                target,
                {
                    scale: 2,

                    backgroundColor: "#ffffff",

                    useCORS: true,

                    logging: false,

                    /*
                    Capture the full PCA report, not only the
                    currently visible part of the scrollable panel.
                    */
                    width: target.scrollWidth,

                    height: target.scrollHeight,

                    windowWidth: Math.max(
                        target.scrollWidth,
                        document.documentElement.clientWidth
                    ),

                    windowHeight: Math.max(
                        target.scrollHeight,
                        document.documentElement.clientHeight
                    ),

                    scrollX: 0,

                    scrollY: -window.scrollY
                }
            );

            const link = document.createElement("a");

            link.download =
                "MGS_GSA_PCA_Report_Panel_"
                + panelId
                + ".png";

            link.href = canvas.toDataURL(
                "image/png"
            );

            document.body.appendChild(link);

            link.click();

            document.body.removeChild(link);

        } catch (error) {
            console.error(
                "PCA report PNG export failed:",
                error
            );

            window.alert(
                "PCA report PNG export failed. "
                + "See the browser console for details."
            );

        } finally {
            button.disabled = originalDisabled;
            button.textContent = originalText;
        }
    }


    /*
    Event delegation is intentional.

    PCA panels are dynamically created, duplicated, removed, and
    rerendered by Dash, so we listen at the document level rather
    than attaching a listener to one specific button at startup.
    */
    document.addEventListener(
        "click",
        function (event) {
            const button = event.target.closest(
                '[id^="download-pca-report-"]'
            );

            if (!button) {
                return;
            }

            event.preventDefault();

            exportPcaReport(button);
        }
    );
})();