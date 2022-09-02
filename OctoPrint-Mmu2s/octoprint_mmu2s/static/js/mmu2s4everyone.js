/*
 * View model for MMU2S
 *
 * Author: Bjarne Dietrich
 * License: AGPLv3
 */
/*
$(function () {
    function Mmu2s4everyoneViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];
        self.mmu2s_buttonText = ko.observable();
        self.selected_port = ko.observable();
        var startupLock = true;

        self.mmu2s_refresh = function () {
            OctoPrint.simpleApiCommand("mmu2s4everyone", "get_ports").done(function (
                response
            ) {
                let ports = response["ports"];

                let p = document.getElementById("mmu2s_ports");
                while (p.firstChild) {
                    p.removeChild(p.firstChild);
                }
                ports.forEach(function (port) {
                    let option = document.createElement("option");
                    option.value = port;
                    option.text = port;
                    p.append(option);
                });
            });
        };
        self.change = function (n) {
            console.log("Change!");
            if (!startupLock) {
                OctoPrint.simpleApiCommand("mmu2s4everyone", "change", {id: n});
            }
        };

        self.load = function (n) {
            if (!startupLock) {
                OctoPrint.simpleApiCommand("mmu2s4everyone", "load", {id: n});
            }
        };

        self.stealth = function () {
            if (!startupLock) {
                OctoPrint.simpleApiCommand("mmu2s4everyone", "stealth", {value: 1});
            }
        };

        self.mmu2s_connect = function () {
            if (!startupLock) {
                let e = document.getElementById("mmu2s_ports");
                let value = e.options[e.selectedIndex].value;
                OctoPrint.simpleApiCommand("mmu2s4everyone", "connect", {port: value});
            }
        };

        self.onStartupComplete = function () {
            startupLock = false;
            self.mmu2s_buttonText.text = "Hello Ben.";
            self.mmu2s_refresh();
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
/*
OCTOPRINT_VIEWMODELS.push({
    construct: Mmu2s4everyoneViewModel,
    // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
    dependencies: [
        "settingsViewModel",
        "loginStateViewModel",
        "connectionViewModel",
        "terminalViewModel"
    ],
    // Elements to bind to, e.g. #settings_plugin_mmu2s4everyone, #tab_plugin_mmu2s4everyone, ...
    elements: ["#sidebar_plugin_mmu2s4everyone", "#tab_plugin_mmu2s4everyone"]
});
});
*/
